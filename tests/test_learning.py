"""Real HTTP + SQL integration checks; no model or production database calls."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from backend import analytics, database, generator, learning, socratic
from backend.main import app
from backend.schemas import TutorTurn


def uid():
    return str(uuid4())


TOKEN = 'test-participant-credential-00000001'
OTHER = 'test-participant-credential-00000002'


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = create_engine(f"sqlite:///{tmp_path / 'learning.sqlite3'}", connect_args={"check_same_thread": False})
    monkeypatch.setattr(learning, 'engine', lambda: db)
    monkeypatch.setenv('LEARNING_EXPERIMENT_ID', 'test-pilot')
    monkeypatch.setattr(generator, '_REGISTRY', {'q1': {
        'id': 'q1', 'stem': 'What is the derivative of x?', 'topic': 'Derivatives',
        'type': 'single_choice', 'difficulty': 'easy', 'language': 'en',
        'options': ['0', '1'], 'correct_indices': [1], 'final_answer': '1',
        'quality_version': 2, 'attempts': 99,
    }})
    monkeypatch.setattr(socratic, 'process_turn', lambda **kwargs: TutorTurn(
        tutor_message='Apply the power rule.', reasoning_assessment='partial', action='hint',
        asks_for_explanation=True, hint_level=1, mastery=10, is_solved=False,
    ))
    learning.init()
    http = TestClient(app)
    yield http
    http.close()
    db.dispose()


def post(client, path, data, token=TOKEN, status=200):
    response = client.post('/learning' + path, json=data, headers={'X-Learning-Token': token})
    assert response.status_code == status, response.text
    return response.json()


def start(client, token=TOKEN, class_id='calc1-a'):
    return post(client, '/start', {'run_id': uid(), 'class_id': class_id, 'consent': True}, token)['run_id']


def expose(client, run, token=TOKEN, mode='free', presented=True):
    exposure = uid()
    post(client, '/exposures', {'run_id': run, 'exposure_id': exposure, 'question_id': 'q1',
                             'mode': mode, 'presented': presented}, token)
    return exposure


def attempt(client, exposure, answer=1, token=TOKEN):
    return post(client, '/attempts', {'exposure_id': exposure, 'attempt_id': uid(), 'answer': {'single': answer}}, token)


def ask(client, run, exposure=None, token=TOKEN):
    return post(client, '/tutor', {'run_id': run, 'exposure_id': exposure, 'request_id': uid(), 'text': 'Help me reason'}, token)


def report(client, class_id='calc1-a'):
    response = client.get('/analytics/class', params={'class_id': class_id, 'scope': 'learning'})
    assert response.status_code == 200
    return response.json()


def test_persistence_idempotency_and_frozen_ai_status(client):
    run = start(client)
    exposure = expose(client, run)
    body = {'exposure_id': exposure, 'attempt_id': uid(), 'answer': {'single': 0}}
    first = post(client, '/attempts', body)
    assert first['attempt_no'] == 1 and not first['correct']
    # Snapshot survives cache eviction and later help never relabels this answer.
    generator._REGISTRY.clear()
    turn = ask(client, run, exposure)
    uncertain = attempt(client, exposure)
    assert uncertain['assistance_status'] == 'unknown'
    post(client, '/replies/' + turn['reply_id'] + '/presented', {})
    post(client, '/replies/' + turn['reply_id'] + '/presented', {})
    third = attempt(client, exposure)
    assert third['attempt_no'] == 3 and third['assistance_status'] == 'received'
    assert post(client, '/attempts', body) == first
    post(client, '/attempts', {**body, 'answer': {'single': 1}}, status=409)
    data = report(client)
    assert data['n_students'] == 1 and data['practice_submission_count'] == 3
    assert data['practice']['correct_rate'] == .667
    assert data['practice']['practice_completion_modes'] == [
        {'mode': 'independent', 'count': 1}, {'mode': 'ai_assisted', 'count': 1}, {'mode': 'unknown', 'count': 1}]
    rows = learning.list_events()
    submitted = [e for e in rows if e['event'] == 'practice_grade']
    assert submitted[0]['answer'] == {'single': 0}
    assert submitted[0]['assistance_status'] == 'none'
    assert data['reasoning_sample_count'] == 1
    # Close all connections, read persisted state and replay without any cache.
    learning.engine().dispose()
    assert post(client, '/attempts', body) == first
    assert report(client)['practice_submission_count'] == 3


def test_identity_class_scope_and_participant_union(client, monkeypatch):
    run = start(client)
    exposure = expose(client, run)
    attempt(client, exposure)
    other_run = start(client, OTHER)
    ask(client, other_run, token=OTHER)
    assert report(client)['n_students'] == 2  # one submitter + different requester
    post(client, '/attempts', {'exposure_id': exposure, 'attempt_id': uid(), 'answer': {'single': 1}}, OTHER, 403)
    class_b = start(client, OTHER, 'calc1-b')
    b_exposure = expose(client, class_b, OTHER)
    attempt(client, b_exposure, token=OTHER)
    assert report(client)['practice_submission_count'] == 1
    assert report(client, 'calc1-b')['n_students'] == 1
    assert report(client, 'demo')['practice_submission_count'] == 0
    # New teacher scope never touches historical/demo event loaders.
    monkeypatch.setattr(analytics, '_load_events', lambda: pytest.fail('legacy logs used'))
    data = report(client)
    assert data['experiment_id'] == 'test-pilot' and data['metric_version'] == 'pilot-v2'
    assert 'participating_students' in analytics._facts_block(analytics.compute('calc1-a', scope='learning'))
    monkeypatch.setenv('LEARNING_EXPERIMENT_ID', 'next-pilot')
    assert report(client)['practice_submission_count'] == 0
    post(client, '/attempts', {'exposure_id': exposure, 'attempt_id': uid(), 'answer': {'single': 1}}, status=409)


def test_concurrent_transport_retries_count_once(client):
    exposure = expose(client, start(client))
    body = {'exposure_id': exposure, 'attempt_id': uid(), 'answer': {'single': 1}}
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: post(client, '/attempts', body), range(8)))
    assert all(r == results[0] for r in results)
    assert report(client)['practice_submission_count'] == 1


def test_challenge_atomic_lock_and_unseen_skips(client):
    run = start(client)
    first = expose(client, run, mode='challenge')
    second = expose(client, run, mode='challenge', presented=False)
    post(client, '/tutor', {'run_id': run, 'exposure_id': first, 'request_id': uid(), 'text': 'Help'}, status=409)
    post(client, '/attempts', {'exposure_id': first, 'attempt_id': uid(), 'answer': {'single': 1}}, status=409)
    body = {'run_id': run, 'submission_id': uid(), 'entries': [
        {'exposure_id': first, 'attempt_id': uid(), 'answer': {'single': 1}},
        {'exposure_id': second, 'attempt_id': uid(), 'answer': {'single': 1}},
    ]}
    post(client, '/challenges', body, status=409)  # unseen answer invalid; rollback first too
    assert report(client)['practice_submission_count'] == 0
    body['entries'][1]['answer'] = None
    result = post(client, '/challenges', body)
    assert result['results'][0]['correct'] and result['results'][1] is None
    assert post(client, '/challenges', body) == result
    post(client, '/challenges', {**body, 'submission_id': uid()}, status=409)
    assert report(client)['practice_submission_count'] == 1
    assert len([e for e in learning.list_events() if e['event'] == 'question_presented']) == 1
    assert [e for e in learning.list_events() if e['event'] == 'question_skipped'][0]['presented'] is False
    turn = ask(client, run, first)
    post(client, '/replies/' + turn['reply_id'] + '/presented', {})
    assert report(client)['practice']['ai_help_count'] == 0


def test_failures_are_not_help_or_reasoning_samples(client, monkeypatch):
    run = start(client)
    exposure = expose(client, run)
    def fail(**kwargs):
        raise RuntimeError('offline')
    monkeypatch.setattr(socratic, 'process_turn', fail)
    body = {'run_id': run, 'exposure_id': exposure, 'request_id': uid(), 'text': 'Help'}
    post(client, '/tutor', body, status=503)
    post(client, '/tutor', body, status=503)
    monkeypatch.setattr(socratic, 'process_turn', lambda **kwargs: TutorTurn(
        tutor_message='Service unavailable', reasoning_assessment='none', action='probe',
        asks_for_explanation=True, hint_level=0, mastery=0, is_solved=False, response_status='unavailable'))
    turn = ask(client, run, exposure)
    post(client, '/replies/' + turn['reply_id'] + '/presented', {})
    assert attempt(client, exposure)['assistance_status'] == 'unknown'
    assert report(client)['reasoning_sample_count'] == 0
    assert report(client)['practice']['ai_help_count'] == 0


def test_validation_and_consent(client):
    post(client, '/start', {'run_id': uid(), 'class_id': 'calc1-a', 'consent': False}, status=400)
    post(client, '/start', {'run_id': uid(), 'class_id': 'not-a-class', 'consent': True}, status=400)
    post(client, '/start', {'run_id': uid(), 'class_id': 'calc1-a', 'consent': True}, token='short', status=401)
    exposure = expose(client, start(client))
    for answer in ({}, {'single': 'bad'}, {'multiple': [0]}, {'single': -1}, {'single': 2}):
        post(client, '/attempts', {'exposure_id': exposure, 'attempt_id': uid(), 'answer': answer}, status=422)
    assert report(client)['practice_submission_count'] == 0


def test_config_and_class_list_share_authoritative_identifiers(client):
    classes = client.get('/classes').json()
    assert client.get('/learning/config').json()['classes'] == classes
    for legacy_id in ['class-a', 'class-b']:
        result = post(client, '/start', {'run_id': uid(), 'class_id': legacy_id, 'consent': True}, status=400)
        assert result['detail']['code'] == 'UNKNOWN_CLASS'
    assert learning.list_events() == []


def test_unknown_learning_route_does_not_return_frontend_html(client):
    response = client.get('/learning/unknown-endpoint')
    assert response.status_code == 404
    assert 'application/json' in response.headers['content-type']


@pytest.mark.parametrize('kind,private,answer', [
    ('multiple_choice', {'correct_indices': [0, 1]}, {'multiple': [0, 1]}),
    ('fill_blank', {'blank_answers': [['1', 'one']]}, {'blanks': ['one']}),
    ('drag_order', {'steps_correct': ['apply rule', 'simplify']}, {'order': ['apply rule', 'simplify']}),
])
def test_supported_answer_formats(client, kind, private, answer):
    generator._REGISTRY['q1'].update(type=kind, **private)
    exposure = expose(client, start(client))
    result = post(client, '/attempts', {'exposure_id': exposure, 'attempt_id': uid(), 'answer': answer})
    assert result['correct'] and result['attempt_no'] == 1
    assert next(e for e in learning.list_events() if e['event'] == 'practice_grade')['answer'] == answer


def test_question_from_shared_database_when_worker_cache_misses(client, monkeypatch):
    db = learning.engine()
    database.metadata.create_all(db)
    monkeypatch.setattr(database, 'engine', lambda: db)
    monkeypatch.setattr(database, 'enabled', lambda: True)
    database.save_generated_question(generator._REGISTRY.pop('q1'))
    exposure = expose(client, start(client))
    assert attempt(client, exposure)['correct']


def test_numeric_equivalent_blank_answer_is_not_marked_wrong(client):
    generator._REGISTRY['q1'].update(type='fill_blank', blank_answers=[['3/2']])
    exposure = expose(client, start(client))
    result = post(client, '/attempts', {'exposure_id': exposure, 'attempt_id': uid(), 'answer': {'blanks': ['6/4']}})
    assert result['correct']


def test_incomplete_challenge_answer_is_preserved_without_grading(client):
    generator._REGISTRY['q1'].update(type='fill_blank', blank_answers=[['1'], ['2']])
    run = start(client)
    exposure = expose(client, run, mode='challenge')
    body = {'run_id': run, 'submission_id': uid(), 'entries': [
        {'exposure_id': exposure, 'attempt_id': uid(), 'answer': None, 'draft_answer': {'blanks': ['1', '']}},
    ]}
    result = post(client, '/challenges', body)
    assert result['results'] == [None]
    skip = next(e for e in learning.list_events() if e['event'] == 'question_skipped')
    assert skip['draft_answer'] == {'blanks': ['1', '']}
    assert skip['reason'] == 'incomplete'
    assert report(client)['practice_submission_count'] == 0


def test_tutor_raw_input_and_prior_submission_are_separate(client, monkeypatch):
    run = start(client)
    exposure = expose(client, run)
    previous = attempt(client, exposure, answer=0)
    calls = []
    original = socratic.process_turn
    def capture(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)
    monkeypatch.setattr(socratic, 'process_turn', capture)
    post(client, '/tutor', {'run_id': run, 'exposure_id': exposure, 'request_id': uid(),
                          'text': 'I do not understand the power rule.', 'submitted_attempt_id': previous['attempt_id']})
    request = next(e for e in learning.list_events() if e['event'] == 'tutor_requested')
    assert request['student_text'] == 'I do not understand the power rule.'
    assert request['submitted_attempt_id'] == previous['attempt_id']
    assert calls[0]['student_text'] == request['student_text']
    assert calls[0]['prior_answer'] == {'single': 0}
    assert calls[0]['history'] == []


@pytest.mark.parametrize('answer', [{'single': True}, {'single': '1'}, {'single': 1, 'blanks': ['fake']}])
def test_noncanonical_answer_payload_does_not_pollute_metrics(client, answer):
    exposure = expose(client, start(client))
    post(client, '/attempts', {'exposure_id': exposure, 'attempt_id': uid(), 'answer': answer}, status=422)
    assert report(client)['practice_submission_count'] == 0


def test_complete_challenge_answer_cannot_be_hidden_as_a_draft(client):
    run = start(client)
    exposure = expose(client, run, mode='challenge')
    post(client, '/challenges', {'run_id': run, 'submission_id': uid(), 'entries': [
        {'exposure_id': exposure, 'attempt_id': uid(), 'draft_answer': {'single': 0}},
    ]}, status=422)
    assert not any(e['event'] == 'question_skipped' for e in learning.list_events())
