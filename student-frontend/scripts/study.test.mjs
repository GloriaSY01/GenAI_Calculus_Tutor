import test from 'node:test'
import assert from 'node:assert/strict'
import { hasAnswer, challengePlan, roundSummary, submittedAnswerText } from '../src/pages/student/study.js'

test('tutor gets the submitted work, never an inferred correct answer', () => {
  const q = {type: 'single_choice', options: ['$6t-2$', '$6t+4$']}
  assert.equal(submittedAnswerText(q, null), '')
  assert.equal(submittedAnswerText(q, {single: 1}), '$6t+4$')
  assert.equal(submittedAnswerText(q, {single: 99}), '')
  assert.equal(submittedAnswerText({type:'multiple_choice', options:['a','b','c']}, {multiple:[0,2]}), 'a; c')
  assert.equal(submittedAnswerText({type:'fill_blank'}, {blanks:['2x']}), '2x')
  assert.equal(submittedAnswerText({type:'drag_order'}, {order:['first','last']}), 'first → last')
})
test('challenge covers every selected chapter section exactly once', () => {
  assert.deepEqual(challengePlan([{id:'1.1'},{id:'1.2'},{id:'1.3'}]), ['1.1','1.2','1.3'])
})
test('unvisited order and partially filled questions are unanswered', () => {
  assert.equal(hasAnswer({q:{type:'drag_order',steps:['a','b']},answer:{}}),false)
  assert.equal(hasAnswer({q:{type:'drag_order',steps:['a','b']},answer:{order:['a','b']}}),true)
  assert.equal(hasAnswer({q:{type:'fill_blank',n_blanks:2},answer:{blanks:['1',' ']}}),false)
  assert.equal(hasAnswer({q:{type:'single_choice'},answer:{single:0}}),true)
})
test('review tutoring cannot change the submitted result', () => {
  const answered = {q:{type:'single_choice'},answer:{single:0}}
  const summary = roundSummary({items:[{...answered,first:{correct:false},grade:{correct:true},assisted:true},{...answered,first:{correct:true}},{q:{type:'single_choice'},answer:{}}]})
  assert.deepEqual(summary,{correct:1,incorrect:1,unanswered:1})
})
