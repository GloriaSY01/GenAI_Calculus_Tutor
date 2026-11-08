"""Recompute the browser audit from read-only SQLite data, without app imports."""
import json
import sqlite3
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path


def main():
    output = Path(__file__).resolve().parents[1] / 'tmp' / 'learning-flow-audit'
    browser = json.loads((output / 'browser-evidence.json').read_text(encoding='utf-8'))
    database = Path(browser['snapshot']['database'])
    assert database.resolve().parent == output and database.name.startswith('audit-')
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
        records = {key: (kind, owner, json.loads(payload)) for key, kind, owner, payload
                   in connection.execute('SELECT id, kind, owner, payload FROM learning_records_v2')}
        events = []
        for key, experiment, cls, ts, payload in connection.execute(
            'SELECT id, experiment_id, class_id, created_at, payload '
            'FROM learning_events_v2 ORDER BY created_at, id'
        ):
            event = json.loads(payload)
            assert (key, experiment, cls, ts) == tuple(
                event[field] for field in ('event_id', 'experiment_id', 'class_id', 'ts'))
            events.append(event)

    grades, skips, requests, replies = [], [], {}, {}
    shown, presented, assigned = set(), set(), set()
    attempts = defaultdict(list)
    for event in events:
        cls, run, identity = (event[key] for key in ('class_id', 'run_id', 'student_id'))
        kind, owner, run_data = records[run]
        assert (kind, owner, run_data['class_id']) == ('run', identity, cls)
        assert run_data['experiment_id'] == event['experiment_id'] == 'controlled-learning-audit'
        exposure = event.get('exposure_id')
        if exposure:
            kind, owner, item = records[exposure]
            assert (kind, owner, item['run_id']) == ('exposure', identity, run)

        name = event['event']
        if name == 'question_assigned':
            assigned.add(exposure)
        elif name == 'question_presented':
            assert exposure in assigned and exposure not in presented
            presented.add(exposure)
        elif name == 'tutor_requested':
            request_id = event['event_id'].removeprefix('request:')
            request = records[request_id][2]['request']
            assert request['text'] == event['student_text']
            assert event['submitted_attempt_id'] == request['submitted_attempt_id']
            if request['submitted_attempt_id']:
                assert any(g['attempt_id'] == request['submitted_attempt_id'] for g in attempts[exposure])
            requests[request_id] = event
        elif name == 'turn':
            reply = event['reply_id']
            assert event['student_text'] == requests[reply]['student_text']
            replies[reply] = event
        elif name == 'tutor_response_presented':
            reply = replies[event['reply_id']]
            if valid_turn(reply):
                shown.add(exposure)
        elif name == 'question_skipped':
            assert event['presented'] == (exposure in presented)
            assert item['unsubmitted_answer'] == event['draft_answer']
            assert not attempts[exposure]
            skips.append(event)
        elif name == 'practice_grade':
            assert exposure in presented
            attempt_id = event['attempt_id']
            kind, owner, attempt = records[attempt_id]
            assert (kind, owner, attempt['exposure_id']) == ('attempt', identity, exposure)
            assert attempt_id == event['event_id']
            assert attempt['answer'] == event['answer']
            assert attempt['attempt_no'] == event['attempt_no'] == len(attempts[exposure]) + 1
            assert event['question_id'] == item['question_id']
            assert 0 <= event['elapsed_ms'] and item['presented_at'] <= attempt['submitted_at'] <= event['ts']
            question, answer = item['question'], attempt['answer']
            if question['type'] == 'single_choice':
                correct = answer['single'] in question['correct_indices']
            else:
                assert question['type'] == 'fill_blank' and answer == {'blanks': ['6/4']}
                correct = Fraction(answer['blanks'][0]) == Fraction(question['blank_answers'][0][0])
            assert event['correct'] == attempt['result']['correct'] == correct
            status = ('received' if exposure in shown else 'unknown'
                      if any(r['exposure_id'] == exposure for r in requests.values()) else 'none')
            assert event['assistance_status'] == attempt['assistance_status'] == status
            attempts[exposure].append(event)
            grades.append(event)

    assert sum(record[0] == 'attempt' for record in records.values()) == len(grades) == 7
    assert Counter(event['reason'] for event in skips) == {'incomplete': 1, 'unanswered': 1}
    report = {}
    for cls, expected in [('calc1-a', (2, 6, 4, 4)), ('calc1-b', (1, 1, 1, 0))]:
        rows = [g for g in grades if g['class_id'] == cls]
        tutor = [r for r in requests.values() if r['class_id'] == cls]
        turns = Counter(r['reasoning_assessment'] for r in replies.values()
                        if r['class_id'] == cls and valid_turn(r))
        participants = len({event['student_id'] for event in rows + tutor})
        correct = sum(g['correct'] for g in rows)
        assert (participants, len(rows), correct, turns.total()) == expected
        teacher = browser['snapshot']['teacher'][cls]
        assert (teacher['n_students'], teacher['practice_submission_count'],
                teacher['practice']['correct_rate'], teacher['reasoning_sample_count']) == (
                    participants, len(rows), round(correct / len(rows), 3), turns.total())
        groups = {}
        counts = {row['mode']: row['count'] for row in teacher['practice']['practice_completion_modes']}
        for state, key in [('none', 'independent'), ('received', 'ai_assisted'), ('unknown', 'unknown')]:
            group = [g for g in rows if g['assistance_status'] == state]
            group_correct = sum(g['correct'] for g in group)
            groups[state] = [group_correct, len(group)]
            assert counts.get(key, 0) == len(group)
            rate_key = 'unknown_rate' if key == 'unknown' else key + '_solve_rate'
            assert teacher['practice'][rate_key] == (round(group_correct / len(group), 3) if group else 0)
        for difficulty in teacher['practice']['by_difficulty_completion']:
            group = [g for g in rows if g['difficulty'] == difficulty['difficulty']]
            assert difficulty['attempts'] == len(group)
            assert difficulty['correct'] == sum(g['correct'] for g in group)
        for level, share in teacher['reasoning_distribution'].items():
            assert share == (round(turns[level] / turns.total(), 3) if turns else 0)
        first = [g for g in rows if g['attempt_no'] == 1]
        final = {g['exposure_id']: g for g in rows}.values()
        report[cls] = dict(participants=participants, correct=correct, submissions=len(rows),
                           first=[sum(g['correct'] for g in first), len(first)],
                           final=[sum(g['correct'] for g in final), len(final)],
                           assistance=groups, reasoning=dict(turns))
    assert report['calc1-a']['assistance'] == {'none': [2, 4], 'received': [1, 1], 'unknown': [1, 1]}
    report['events'] = Counter(e['event'] for e in events)
    result = json.dumps(report, indent=2)
    (output / 'sql-verification.json').write_text(result, encoding='utf-8')
    print(result)


def valid_turn(reply):
    return reply['response_status'] == 'ok' and not reply['safety_event'] and reply['action'] != 'blocked'


if __name__ == '__main__':
    main()
