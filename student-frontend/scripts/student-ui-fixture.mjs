// Local UI fixture only. Never used by the application in normal operation.
import http from 'node:http'
let sequence = 0
const chapters = [{ id: 'ui-ch1', title: '1 Limits', sections: [{ id: 'ui-sec1', title: 'Limits', label: '1.1' }, { id: 'ui-sec2', title: 'Continuity', label: '1.2' }] }, { id: 'ui-ch2', title: '2 Derivatives', sections: [{ id: 'ui-sec3', title: 'Derivatives', label: '2.1' }] }]
http.createServer(async (req, res) => {
  let raw = ''
  for await (const chunk of req) raw += chunk
  const body = raw ? JSON.parse(raw) : {}
  let data
  if (req.url === '/classes') data = [{ id: 'ui-test', label: 'UI test class' }]
  else if (req.url === '/catalog') data = { chapters }
  else if (req.url.startsWith('/concept')) data = { title: 'Test concept', summary: 'A short textbook idea.', content: [{ id: 'concept', content_type: 'concept', text: 'Learn the idea, then practice.', formulas: ['f(x)=x'], figures: [] }] }
  else if (req.url.startsWith('/favorites')) data = req.method === 'GET' ? [] : { ok: true }
  else if (req.url === '/generate') {
    sequence++
    data = { id: 'ui-question-' + sequence, type: body.type, topic: body.topic, difficulty: body.difficulty,
      stem: 'UI test ' + sequence + ': Evaluate $\\lim_{x\\to 1}x$.', source: 'generated',
      options: ['1', '2', '0'], n_blanks: 1, steps: ['Use continuity', 'Substitute x = 1'] }
  } else if (req.url === '/grade') data = { correct: body.single === 0 || body.multiple?.length === 1 && body.multiple[0] === 0 || body.blanks?.[0] === '1' || body.order?.[0] === 'Use continuity', feedback: 'UI test feedback', attempts: 1 }
  else if (req.url === '/session/start') data = { session_id: 'ui-session', opening_message: 'UI test tutor' }
  else if (req.url.includes('/message')) {
    const question = JSON.parse(body.text)
    data = { tutor_message: 'UI test tutor: saved answer ' + JSON.stringify(question.current_answer), citations: [] }
  } else { res.writeHead(404); res.end('{}'); return }
  res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(data))
}).listen(4101, '127.0.0.1', () => console.log('UI fixture listening on 127.0.0.1:4101'))

