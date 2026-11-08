// Durable request journal: persist IDs and immutable payloads BEFORE sending.
// Transport retries (including after reload) replay the same database write.
const BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.DEV ? '/api' : '')
const read = key => JSON.parse(localStorage.getItem(key) || 'null')
const write = (key, value) => localStorage.setItem(key, JSON.stringify(value))
const uuid = () => crypto.randomUUID()

export function createLearningClient(student, classId) {
  const identityKey = 'calculus-learning-identity:' + (student.trim() || 'guest')
  let token = null
  let run = null
  let prefix = ''
  async function request(path, body) {
    const response = await fetch(BASE + '/learning' + path, {
      method: body === undefined ? 'GET' : 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Learning-Token': token },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
    const contentType = response.headers.get('content-type') || ''
    if (!contentType.includes('application/json')) {
      const error = new Error('学习记录接口未正确连接：服务器返回了网页。请确认后端已更新并重启，且前端代理指向正确的后端地址。 / Learning API returned a web page. Restart the updated backend and check the API proxy.')
      error.status = response.status
      error.code = 'LEARNING_API_NOT_AVAILABLE'
      throw error
    }
    const data = await response.json()
    if (!response.ok) {
      const error = new Error(typeof data.detail === 'string' ? data.detail : data.detail?.message || 'Learning data could not be saved')
      error.status = response.status
      error.code = data.detail?.code
      throw error
    }
    return data
  }
  function journal(key, payload) {
    const storageKey = prefix + ':' + key
    let record = read(storageKey)
    if (!record) { record = { payload }; write(storageKey, record) }
    return { storageKey, record }
  }
  async function replay(key, path, payload) {
    const { storageKey, record } = journal(key, payload)
    if (!record.result) {
      try { record.result = await request(path, record.payload) }
      catch (error) {
        // A validation rejection commits nothing. Let an edited answer create a
        // fresh ID; network errors must retain the original immutable request.
        if (error.status === 422) localStorage.removeItem(storageKey)
        throw error
      }
      write(storageKey, record)
    }
    return { ...record.result, submitted_answer: record.payload.answer }
  }
  function ready() {
    if (!run) throw new Error('请先连接学习记录服务 / Connect learning records first')
  }
  return {
    async connect(consent = false) {
      if (!token) {
        token = read(identityKey)
        if (!token) { token = uuid() + uuid(); write(identityKey, token) }
      }
      const config = await request('/config')
      if (!config?.experiment_id || !config?.consent_version) {
        throw new Error('学习记录接口版本不匹配，请更新并重启后端。 / Learning API version mismatch; restart the updated backend.')
      }
      if (!Array.isArray(config.classes)) {
        throw new Error('后端未提供有效班级，请更新并重启后端。 / Update the backend to load valid classes.')
      }
      if (!config.classes.some(c => c.id === classId)) {
        const error = new Error('班级已失效，请重新选择。 / This class is no longer available; please select again.')
        error.code = 'UNKNOWN_CLASS'
        throw error
      }
      prefix = 'calculus-learning:' + JSON.stringify([student.trim() || 'guest', classId, config.experiment_id])
      const consentKey = prefix + ':consent:' + config.consent_version
      if (!consent && !read(consentKey)) return null
      if (consent) write(consentKey, true)
      const { record } = journal('start', { run_id: uuid(), class_id: classId, consent: true })
      run = await request('/start', record.payload)
      return run
    },
    async expose(item, mode = 'free', presented = true) {
      ready()
      if (!item.trackingId) throw new Error('Question identity missing; reload this page')
      const { storageKey, record } = journal('exposure:' + item.trackingId, {
        run_id: run.run_id, exposure_id: uuid(), question_id: item.q.id, mode,
      })
      if (presented && !record.presented) {
        record.presented = true
        write(storageKey, record)
      }
      await request('/exposures', { ...record.payload, presented: !!record.presented })
      return record.payload.exposure_id
    },
    async submit(item, mode) {
      const exposure_id = await this.expose(item, mode)
      const result = await replay('attempt:' + exposure_id + ':' + (item.attemptNo || 0), '/attempts', {
        exposure_id, attempt_id: uuid(), answer: item.answer,
      })
      return { ...result, recovered: JSON.stringify(result.submitted_answer) !== JSON.stringify(item.answer) }
    },
    async challenge(round, hasAnswer) {
      ready()
      const entries = []
      for (const item of round.items) {
        const exposure_id = await this.expose(item, 'challenge', false)
        entries.push({ exposure_id, attempt_id: uuid(), answer: hasAnswer(item) ? item.answer : null,
          draft_answer: hasAnswer(item) ? null : item.answer })
      }
      const key = 'challenge:' + round.items[0].trackingId
      const { record } = journal(key, { run_id: run.run_id, submission_id: uuid(), entries })
      const result = await replay(key, '/challenges', record.payload)
      return { ...result, entries: record.payload.entries }
    },
    async ask(item, mode, text, topic, language, submitted_attempt_id = null) {
      ready()
      const exposure_id = item ? await this.expose(item, mode) : null
      const key = prefix + ':pending-tutor:' + (exposure_id || run.run_id)
      let payload = read(key)
      if (!payload) {
        payload = { run_id: run.run_id, exposure_id, request_id: uuid(), text, topic, language, submitted_attempt_id }
        write(key, payload)
      } else if (payload.text !== text) {
        throw new Error('上次请求尚未确认，请先重发原问题 / Retry the previous question: ' + payload.text)
      }
      try {
        const result = await request('/tutor', payload)
        // Keep until displayed: an unmounted chat must not lose an unacknowledged reply.
        return { ...result, pendingKey: key }
      } catch (error) {
        if (error.code === 'TUTOR_FAILED') localStorage.removeItem(key)
        throw error
      }
    },
    async presented(reply) {
      await request('/replies/' + reply.reply_id + '/presented', {})
      if (read(reply.pendingKey)?.request_id === reply.reply_id) localStorage.removeItem(reply.pendingKey)
    },
  }
}
