import test from 'node:test'
import assert from 'node:assert/strict'
import { hasAnswer, challengePlan, roundSummary } from '../src/pages/student/study.js'
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
