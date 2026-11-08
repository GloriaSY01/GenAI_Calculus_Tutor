"""Isolated browser-audit server. Never connects to a configured production DB.

Run from the repository root, then run audit_learning_browser.cjs. Question
generation and tutor replies are controlled fixtures; UI, persistence, grading
and teacher aggregation use the application code. Do not deploy this server.
"""
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUTPUT = ROOT / 'tmp' / 'learning-flow-audit'
OUTPUT.mkdir(parents=True, exist_ok=True)
DB_PATH = OUTPUT / f'audit-{uuid4().hex[:10]}.sqlite3'
os.environ['DATABASE_URL'] = 'sqlite:///' + str(DB_PATH)
os.environ['LEARNING_EXPERIMENT_ID'] = 'controlled-learning-audit'
from backend import database
database.init()
from backend import analytics, generator, learning, localization, rag, socratic, textbook
from backend.main import app
from backend.schemas import TutorTurn
from fastapi.routing import APIRoute
from sqlalchemy import select

rag.warmup = lambda: None
catalog = textbook.catalog_tree()
catalog['chapters'] = catalog['chapters'][:1]
catalog['chapters'][0]['sections'] = catalog['chapters'][0]['sections'][:3]
textbook.catalog_tree = lambda: catalog
localization.translate_texts = lambda texts, language: texts
real_generate = generator.generate_question
serial = 0


def controlled_question(qtype, topic, difficulty, language='en', exclude_stems=None, purpose='practice'):
    global serial
    serial += 1
    section = generator._resolve_section(topic)
    if purpose == 'challenge' and section['label'] != '1.2':
        return real_generate('single_choice', topic, 'medium', language=language,
                             exclude_stems=exclude_stems, purpose='challenge')
    if purpose == 'challenge':
        qtype = 'fill_blank'
        data = dict(stem='For $s(t)=3t^2$, enter the velocities at t=1 and t=2: ___ and ___.',
                    blanks=[{'answer':'6'}, {'answer':'12'}], explanation='The derivative is 6t.',
                    key_idea='Instantaneous velocity', solution_steps=['Differentiate 3t².', 'Evaluate 6t at both times.'])
    elif qtype == 'fill_blank':
        data = dict(stem='A position changes by 3 meters in 2 seconds. The average velocity is ___ m/s.',
                    blanks=[{'answer':'3/2'}], explanation='Average velocity is displacement divided by time.',
                    key_idea='Average velocity', solution_steps=['Divide 3 meters by 2 seconds.'])
    else:
        qtype = 'single_choice'
        speed = serial + 2
        data = dict(stem=f'Position is $s(t)={speed}t+2$. What is the velocity?',
                    options=[str(speed-1), str(speed), str(speed+1), str(speed+2)], correct_index=1,
                    explanation=f'The coefficient of t is {speed}.', key_idea='Slope is velocity',
                    solution_steps=['Read the coefficient of t.'])
    record = generator._build_record(qid='audit-'+uuid4().hex, qtype=qtype, topic=section['display_title'],
                                    section_id=section['id'], difficulty=difficulty, data=data,
                                    source='generated', citations=[], language='en')
    record['generation_method'] = 'audit-controlled-v1'
    generator._register(record)
    return generator._public(record)


def controlled_tutor(**kwargs):
    raw = kwargs['student_text']
    if raw == 'Simulate a service outage.':
        return TutorTurn(tutor_message='The tutor is temporarily unavailable.', reasoning_assessment='none',
                         action='probe', asks_for_explanation=True, hint_level=0, mastery=0,
                         is_solved=False, response_status='unavailable')
    if 'guessed' in raw:
        time.sleep(.4)
    assessment = 'none' if kwargs['problem'] is None else 'weak' if 'do not understand' in raw else 'partial'
    return TutorTurn(tutor_message='Compare how much the position changes when time increases by one.',
                     reasoning_assessment=assessment, action='hint', asks_for_explanation=True,
                     hint_level=kwargs['hint_level']+1, mastery=0, is_solved=False)


generator.generate_question = controlled_question
socratic.process_turn = controlled_tutor


def snapshot():
    with database.engine().connect() as con:
        records = [dict(row) for row in con.execute(select(learning.records)).mappings()]
        events = [row[0] for row in con.execute(select(learning.events.c.payload).order_by(learning.events.c.created_at))]
        questions = {row[0]: row[1] for row in con.execute(select(database.generated_questions.c.question_id, database.generated_questions.c.record))}
    return {'database':str(DB_PATH), 'records':records, 'events':events, 'questions':questions,
            'teacher':{c:analytics.compute(c,scope='learning').model_dump() for c in ['calc1-a','calc1-b']}}


# This private fixture route is intentionally absent from backend/main.py.
app.router.routes.insert(0, APIRoute('/_audit/snapshot', snapshot, methods=['GET']))
(OUTPUT / 'latest.json').write_text(json.dumps({'database':str(DB_PATH)},indent=2),encoding='utf-8')
if __name__ == '__main__':
    import uvicorn
    print('Isolated audit database:', DB_PATH, flush=True)
    uvicorn.run(app, host='127.0.0.1', port=8019, log_level='warning')
