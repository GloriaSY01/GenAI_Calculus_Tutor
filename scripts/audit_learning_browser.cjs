// Controlled novice simulation; run audit_learning_server.py first.
const path=require('node:path'), fs=require('node:fs'), assert=require('node:assert/strict')
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright')
const BASE='http://127.0.0.1:8019', OUTPUT=path.resolve(__dirname,'../tmp/learning-flow-audit')
async function run(){
 const browser=await chromium.launch({headless:true})
 const errors=[],steps=[]
 try{
  async function student(code,cls){
   const context=await browser.newContext({viewport:{width:1440,height:1050}})
   const page=await context.newPage()
   page.on('pageerror',e=>errors.push(e.message))
   await page.addInitScript(({code,cls})=>{localStorage.setItem('lang','en');localStorage.setItem('stu_name',code);localStorage.setItem('stu_class',cls)},{code,cls})
   await page.route('**/concept?*',r=>r.fulfill({json:{summary:'Velocity measures the rate of change of position.',definition:'Slope',content:[],formulas:[]}}))
   await page.goto(BASE)
   await page.getByRole('button',{name:'Agree and start',exact:true}).click()
   await page.getByText('Learning records connected',{exact:false}).waitFor()
   return page
  }
  async function snapshot(page){return (await page.request.get(BASE+'/_audit/snapshot')).json()}
  async function current(page){
   return page.evaluate(()=>{
    const key='calculus-study-v3:'+JSON.stringify([localStorage.getItem('stu_name'),localStorage.getItem('stu_class')])
    const state=JSON.parse(localStorage.getItem(key)).state,round=state.rounds[state.active]
    return round.items[round.cursor].q
   })
  }
  async function select(page,correct){
   const q=await current(page),raw=(await snapshot(page)).questions[q.id]
   assert.equal(q.type,'single_choice')
   const index=correct?raw.correct_indices[0]:raw.options.findIndex((_,i)=>!raw.correct_indices.includes(i))
   await page.locator('.sw-answer input[type=radio]').nth(index).check()
  }
  async function submit(page,correct){
   await page.getByRole('button',{name:'Submit answer',exact:true}).click()
   await page.locator(correct?'.grade-box.ok':'.grade-box.bad').first().waitFor()
  }
  async function ask(page,text,{hide=false}={}){
   await page.getByRole('button',{name:'Open Learning Agent',exact:true}).click()
   await page.locator('.floating-agent textarea').fill(text)
   const response=page.waitForResponse(r=>r.url().endsWith('/learning/tutor')&&r.status()===200)
   const acknowledgment=hide?null:page.waitForResponse(r=>r.url().includes('/presented')&&r.status()===200)
   await page.getByRole('button',{name:'Send question',exact:true}).click()
   if(hide)await page.getByRole('button',{name:'Close Learning Agent',exact:true}).first().click()
   const reply=await (await response).json()
   if(acknowledgment){await acknowledgment;await page.getByRole('button',{name:'Close Learning Agent',exact:true}).first().click()}
   return reply
  }
  async function formats(page,format){
   await page.locator('.sw-settings summary').click()
   await page.locator('.sw-settings select').selectOption(format)
   await page.locator('.sw-settings summary').click()
  }
  async function log(page,label){
   const s=await snapshot(page),a=s.teacher['calc1-a']
   steps.push({label,participants:a.n_students,submissions:a.practice_submission_count,correct_rate:a.practice.correct_rate})
  }

  const p1=await student('sim-novice-a','calc1-a')
  await p1.locator('.sw-section-card').first().click()
  await formats(p1,'single_choice')
  await p1.getByRole('button',{name:'Start practicing',exact:true}).click()
  await p1.locator('.sw-answer input[type=radio]').first().waitFor()
  const first=await current(p1)
  await select(p1,false)
  let lost=false
  await p1.route('**/learning/attempts',async r=>{if(!lost){lost=true;await r.fetch();return r.abort('failed')}return r.continue()})
  await p1.getByRole('button',{name:'Submit answer',exact:true}).click()
  await p1.locator('.sw-grade-error').waitFor()
  assert.equal((await snapshot(p1)).teacher['calc1-a'].practice_submission_count,1)
  await p1.reload()
  await submit(p1,false)
  assert.equal((await snapshot(p1)).teacher['calc1-a'].practice_submission_count,1)
  await log(p1,'首次答错；响应丢失后刷新重发仍为1次')
  await ask(p1,'I do not understand why I should use the coefficient.')
  await select(p1,true);await submit(p1,true)
  await log(p1,'获得已展示提示后，同一题重试答对')
  await formats(p1,'fill_blank')
  await p1.getByRole('button',{name:'Next question',exact:true}).click()
  await p1.locator('.sw-answer').getByRole('textbox').first().fill('6/4')
  await submit(p1,true)
  await log(p1,'独立填入等值分数6/4，标准答案3/2，判对')
  await formats(p1,'single_choice')
  await p1.getByRole('button',{name:'Next question',exact:true}).click()
  await p1.locator('.sw-answer input[type=radio]').first().waitFor()
  await select(p1,false);await submit(p1,false)
  const hidden=await ask(p1,'I guessed the answer. How can I check it?',{hide:true})
  await select(p1,true);await submit(p1,true)
  let snap=await snapshot(p1),last=snap.events.filter(e=>e.event==='practice_grade').at(-1)
  assert.equal(last.assistance_status,'unknown')
  const acknowledged=p1.waitForResponse(r=>r.url().endsWith('/'+hidden.reply_id+'/presented')&&r.status()===200)
  await p1.getByRole('button',{name:'Open Learning Agent',exact:true}).click();await acknowledged
  await p1.getByRole('button',{name:'Close Learning Agent',exact:true}).first().click()
  assert.equal((await snapshot(p1)).events.find(e=>e.event_id===last.event_id).assistance_status,'unknown')
  await log(p1,'提示未展示就提交，记未知；事后展示不追溯改写')
  await p1.getByRole('button',{name:'Chapter home',exact:true}).click()
  await p1.getByRole('button',{name:/Start chapter challenge/}).click()
  await p1.getByRole('button',{name:'Start challenge',exact:true}).click()
  await p1.waitForFunction(()=>document.querySelectorAll('.sw-questionnav button').length===3)
  await select(p1,true)
  await p1.locator('.sw-questionnav button').nth(1).click()
  await p1.locator('.sw-answer').getByRole('textbox').first().fill('6')
  p1.once('dialog',d=>d.accept())
  await p1.getByRole('button',{name:'Submit challenge',exact:true}).click()
  await p1.getByRole('heading',{name:'Review this attempt',exact:true}).waitFor()
  await log(p1,'挑战：1题答对、1题只填第1空、1题未展示未作答')
  snap=await snapshot(p1)
  const skips=snap.events.filter(e=>e.event==='question_skipped')
  assert.equal(skips.length,2)
  assert.equal(skips.find(e=>e.reason==='incomplete').draft_answer.blanks[0],'6')
  assert.equal(skips.find(e=>e.reason==='unanswered').presented,false)
  await p1.locator('.sw-reviewrow').nth(1).click()
  assert.equal(await p1.locator('.sw-answer').getByRole('textbox').first().inputValue(),'6')
  await p1.locator('.sw-questionnav button').first().click()
  await ask(p1,'I used the rate formula. Why does this work?')
  await p1.getByRole('button',{name:'Chapter home',exact:true}).click()
  await ask(p1,'Simulate a service outage.')
  await log(p1,'交卷后求助不改变成绩；AI服务回退不计推理样本')

  const p2=await student('sim-chat-only','calc1-a')
  await ask(p2,'What does velocity mean?')
  const p3=await student('sim-view-only','calc1-a')
  await p3.locator('.sw-section-card').first().click()
  await p3.getByRole('button',{name:'Start practicing',exact:true}).click()
  await p3.locator('.sw-question').waitFor()
  const pb=await student('sim-class-b','calc1-b')
  await pb.locator('.sw-section-card').first().click()
  await pb.getByRole('button',{name:'Start practicing',exact:true}).click()
  await pb.locator('.sw-answer input[type=radio]').first().waitFor()
  await select(pb,true);await submit(pb,true)
  await log(p1,'加入仅提问者、仅浏览者及B班学生，检查参与并集与班级隔离')
  snap=await snapshot(p1)
  assert.equal(snap.teacher['calc1-a'].n_students,2)
  assert.equal(snap.teacher['calc1-a'].practice_submission_count,6)
  assert.equal(snap.teacher['calc1-a'].practice.correct_rate,.667)
  assert.equal(snap.teacher['calc1-a'].reasoning_sample_count,4)
  assert.equal(snap.teacher['calc1-b'].practice_submission_count,1)
  assert.equal(snap.teacher['calc1-b'].practice.correct_rate,1)
  const grades=snap.events.filter(e=>e.event==='practice_grade')
  assert.equal(new Set(grades.map(e=>e.attempt_id)).size,7)
  assert.equal(grades.filter(e=>e.question_id===first.id).length,2)
  assert(snap.events.filter(e=>e.event==='tutor_requested').every(e=>!e.student_text.includes("Student's submitted answer")))

  const teacher=await browser.newPage({viewport:{width:1440,height:1050}})
  await teacher.addInitScript(()=>{localStorage.setItem('role','teacher');localStorage.setItem('lang','zh')})
  await teacher.goto(BASE+'/overview?class_id=calc1-a')
  await teacher.getByRole('heading',{name:'班级概览',exact:true}).waitFor()
  const metrics=teacher.locator('.teacher-summary-metrics strong')
  assert.deepEqual(await metrics.allTextContents(),['2','6','67%'])
  await teacher.locator('#teacher-metrics summary').click()
  const row=await teacher.locator('.teacher-metrics-table tbody tr').first().innerText()
  assert.match(row,/50% \(4\)/);assert.equal((row.match(/100% \(1\)/g)||[]).length,2)
  await teacher.screenshot({path:path.join(OUTPUT,'teacher-class-a.png'),fullPage:true})
  await teacher.locator('.sw-account > select').selectOption('calc1-b')
  await teacher.waitForFunction(()=>[...document.querySelectorAll('.teacher-summary-metrics strong')].map(e=>e.textContent).join('|')==='1|1|100%')
  await teacher.screenshot({path:path.join(OUTPUT,'teacher-class-b.png'),fullPage:true})
  assert.deepEqual(errors,[])
  fs.writeFileSync(path.join(OUTPUT,'browser-evidence.json'),JSON.stringify({steps,snapshot:snap,console_errors:errors},null,2))
  console.log('PASS: novice workflow; A = 2 participants, 6 submissions, 4 correct; B = 1/1/1. Raw evidence saved to '+OUTPUT)
 }finally{await browser.close()}
}
run().catch(e=>{console.error(e);process.exitCode=1})
