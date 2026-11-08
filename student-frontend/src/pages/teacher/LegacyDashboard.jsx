import { useEffect, useState } from 'react'
import { useLang } from '../../i18n.jsx'
import { api } from '../../api.js'
import { useAsync } from '../../components/hooks.js'
import { MathText } from '../../components/math.jsx'
import { displayLabel } from '../../localization.js'
import snapshot from './legacy82.json'
import darkCss from './legacy82-dark.json'
import './legacy82.css'

const pct = value => `${Math.round((value || 0) * 100)}%`
const templates = {
  foundation: [['single_choice','easy',4],['fill_blank','easy',3],['single_choice','medium',2]],
  mixed: [['single_choice','medium',3],['multiple_choice','medium',2],['fill_blank','medium',3],['drag_order','medium',2]],
  challenge: [['multiple_choice','medium',2],['fill_blank','hard',3],['drag_order','hard',2]],
}
const block = (topic,qtype='single_choice',difficulty='easy',count=3) => ({id:crypto.randomUUID(),topic,qtype,difficulty,count})
const total = items => items.reduce((sum,x) => sum+x.count,0)
const minutes = items => Math.max(1,Math.round(items.reduce((sum,x)=>sum+({single_choice:1.5,multiple_choice:2,fill_blank:3,drag_order:3}[x.qtype])*({easy:.8,medium:1,hard:1.4}[x.difficulty])*x.count,0)))
const levels=['none','weak','partial','adequate','strong']
function useCopy() {
  const {lang}=useLang()
  const t=(key,values={}) => Object.entries(values).reduce((s,[k,v])=>s.replaceAll(`{${k}}`,String(v)),snapshot.strings[key]?.[lang] ?? snapshot.strings[key]?.en ?? key)
  const label=topic=>snapshot.strings['topic.'+topic]?.[lang] ?? displayLabel(topic,lang)
  return {t,label,lang}
}
function Header({icon,title,sub}) {return <div className="ph"><div className="ph-icon">{icon}</div><div><h3 className="ph-title">{title}</h3>{sub&&<div className="ph-desc">{sub}</div>}</div></div>}
function Panel({children}) {return <section className="legacy-panel">{children}</section>}
function Metric({label,value,help}) {return <div className="legacy-metric"><span>{label}</span><strong>{value}</strong>{help&&<small>{help}</small>}</div>}
function Empty({children}) {return <div className="empty">{children}</div>}
const dashboardCopy = {
 overview: ['班级概览', 'Class overview'],
 participants: ['参与学生', 'Participating students'],
 participantNote: ['当前实验中提交答案或向 AI 提问的参与者并集，不代表全班人数。', 'Unique participants who submitted answers or requested AI help in this experiment; not enrollment.'],
 submissions: ['练习提交', 'Practice submissions'],
 submissionNote: ['已判分，包含重试与章节挑战。', 'Graded submissions, including retries and challenges.'],
 accuracy: ['提交正确率', 'Submission accuracy'],
 accuracyNote: ['答对 {correct} 次 / 已判分 {total} 次', '{correct} correct / {total} graded'],
 topics: ['知识点表现', 'Topic performance'],
 topicNote: ['数字为答对次数 / 提交次数，包含重试。正确率较低的排在前面；少于 5 次提交的列在后面，仅供参考。点击知识点可关联教学助手。', 'Counts show correct / total submissions, including retries. Lowest accuracy first; topics with fewer than 5 submissions appear last. Select a topic to give the teaching assistant context.'],
 topic: ['知识点', 'Topic'],
 smallSample: ['样本少', 'Small sample'],
 empty: ['该班暂无已判分的练习提交。', 'No graded practice submissions for this class yet.'],
 moreTopics: ['查看其余 {count} 个知识点', 'View {count} more topics'],
 details: ['更多量化指标', 'More metrics'],
 detailNote: ['括号内为提交次数，包含重试；— 表示无样本。按提交时的本题记录分组：未记录帮助、已展示有效 AI 回复、请求后展示情况未确认。答题后求助不改变先前记录；组间差异不代表 AI 效果。', 'Counts include retries; — means no samples. Help status is frozen at submission for this question exposure. Later help does not change earlier attempts. Group differences do not measure AI effects.'],
 independent: ['未记录本题 AI 帮助', 'No AI help recorded for this question'],
 assisted: ['已获得 AI 帮助', 'AI help displayed'],
 difficulty: ['按难度比较提交正确率', 'Submission accuracy by difficulty'],
 all: ['全部难度', 'All difficulties'],
 reasoning: ['导师对话推理分布', 'Reasoning in tutor conversations'],
 reasoningNote: ['按对话轮次统计，由模型评估，仅供参考。', 'Model ratings per conversation turn, for reference only.'],
 noPracticeSamples: ['暂无提交数据，以下保留全部统计维度；提交后自动汇总。', 'No submission data yet. All dimensions are shown below and will populate as submissions arrive.'],
 noReasoningSamples: ['暂无有效对话数据，各推理等级暂不计算占比。', 'No valid conversation data yet; reasoning percentages are not calculated.'],
 assignments: ['练习配置', 'Practice setup'],
 loading: ['正在加载班级数据…', 'Loading class data…'],
 retry: ['重新加载', 'Reload'],
}
const difficultyOrder = ['easy', 'medium', 'hard', 'unknown']
const topicRows = data => (data?.practice?.practice_by_topic || [])
  .filter(row => row.attempts > 0 && row.topic !== 'General / Free chat')
  .sort((a, b) => Number(a.attempts < 5) - Number(b.attempts < 5) ||
    a.correct_rate - b.correct_rate || b.attempts - a.attempts || a.topic.localeCompare(b.topic))

function useDashboardCopy() {
 const {lang} = useLang()
 return (key, values = {}) => Object.entries(values).reduce(
   (message, [name, value]) => message.replaceAll('{' + name + '}', String(value)),
   dashboardCopy[key][lang === 'zh' ? 0 : 1],
 )
}

function ClassOverview({data, rows, topic, onTopic}) {
 const copy = useDashboardCopy()
 const {label} = useCopy()
 const submissions = data.practice_submission_count || 0
 const correct = submissions - (data.practice?.not_correct_count ?? 0)
 const renderRows = entries => <ul className="teacher-topic-list">{entries.map(row => <li key={row.topic}>
  <div className="teacher-topic-label">
   <button type="button" className="teacher-topic-button" aria-pressed={topic === row.topic} onClick={() => onTopic(topic === row.topic ? '' : row.topic)}>{label(row.topic)}</button>
   {row.attempts < 5 && <small>{copy('smallSample')}</small>}
  </div>
  <meter min="0" max="1" value={row.correct_rate} aria-label={label(row.topic) + ' · ' + copy('accuracy')}/>
  <span className="teacher-topic-score"><strong>{pct(row.correct_rate)}</strong> <small>{row.correct}/{row.attempts}</small></span>
 </li>)}</ul>
 return <>
  <section id="teacher-overview" className="legacy-panel teacher-overview">
   <h2>{copy('overview')}</h2>
   <div className="teacher-summary-metrics">
    <Metric label={copy('participants')} value={data.n_students || 0} help={copy('participantNote')}/>
    <Metric label={copy('submissions')} value={submissions} help={copy('submissionNote')}/>
    <Metric label={copy('accuracy')} value={submissions ? pct(data.practice?.correct_rate) : '—'} help={submissions ? copy('accuracyNote', {correct, total: submissions}) : undefined}/>
   </div>
  </section>
  <section id="teacher-topics" className="legacy-panel teacher-overview">
   <h2>{copy('topics')}</h2>
   {rows.length ? <>
    <p className="legacy-caption">{copy('topicNote')}</p>
    {renderRows(rows.slice(0, 5))}
    {rows.length > 5 && <details className="teacher-more-topics">
     <summary>{copy('moreTopics', {count: rows.length - 5})}</summary>
     {renderRows(rows.slice(5))}
    </details>}
   </> : <Empty>{copy('empty')}</Empty>}
  </section>
 </>
}

function MetricsDetail({data}) {
 const copy = useDashboardCopy()
 const {t,lang} = useCopy()
 const practice = data.practice || {}
 const distribution = data.reasoning_distribution || {}
 const reasoningCount = data.reasoning_sample_count ?? data.n_turns ?? 0
 const hasReasoning = reasoningCount > 0 && Object.values(distribution).some(value => value > 0)
 const recordedDifficulties = practice.by_difficulty_completion || []
 const difficulties = difficultyOrder
   .filter(difficulty => difficulty !== 'unknown' || recordedDifficulties.some(row => row.difficulty === difficulty))
   .map(difficulty => recordedDifficulties.find(row => row.difficulty === difficulty) || {difficulty})
 const modes = practice.practice_completion_modes || []
 const totalMode = mode => modes.find(item => item.mode === mode)?.count || 0
 const cell = (rate, count) => count > 0 ? pct(rate) + ' (' + count + ')' : '— (0)'
 return <details id="teacher-metrics" className="legacy-panel teacher-disclosure">
  <summary>{copy('details')}</summary>
   <h3>{copy('difficulty')}</h3>
   {!(practice.n_answers > 0) && <p className="legacy-caption">{copy('noPracticeSamples')}</p>}
   <div className="legacy-table-scroll">
    <table className="teacher-metrics-table">
     <thead><tr><th scope="col">{t('teacher.difficulty')}</th><th scope="col">{copy('independent')}</th><th scope="col">{copy('assisted')}</th><th scope="col">{lang==='zh'?'帮助状态未知':'Help status unknown'}</th></tr></thead>
     <tbody>
      <tr><th scope="row">{copy('all')}</th><td>{cell(data.independent_solve_rate, totalMode('independent'))}</td><td>{cell(data.ai_assisted_solve_rate, totalMode('ai_assisted'))}</td><td>{cell(practice.unknown_rate, practice.unknown_submissions)}</td></tr>
      {difficulties.map(row => <tr key={row.difficulty}><th scope="row">{row.difficulty === 'unknown' ? (lang === 'zh' ? '难度未知' : 'Unknown difficulty') : t('difficulty.' + row.difficulty)}</th><td>{cell(row.independent_rate, row.independent_submissions)}</td><td>{cell(row.ai_assisted_rate, row.ai_assisted_submissions)}</td><td>{cell(row.unknown_rate, row.unknown_submissions)}</td></tr>)}
     </tbody>
    </table>
   </div>
   <p className="legacy-caption">{copy('detailNote')}</p>
  <section>
   <h3>{copy('reasoning')}</h3>
   <p className="legacy-caption">{copy('reasoningNote')} {lang==='zh'?'有效对话轮次：':'Valid turns: '}{reasoningCount}</p>
   {!hasReasoning && <p className="legacy-caption">{copy('noReasoningSamples')}</p>}
   <dl className="teacher-reasoning-values">{levels.map(level => <div key={level}><dt>{(lang === 'zh' ? ['未体现', '较弱', '部分', '充分', '较强'] : ['Not demonstrated', 'Weak', 'Partial', 'Adequate', 'Strong'])[levels.indexOf(level)]}</dt><dd>{hasReasoning ? pct(distribution[level]) : '—'}</dd></div>)}</dl>
  </section>
 </details>
}
function Assignments({topics,data,classId}) {
 const {t,label,lang}=useCopy();const list=useAsync(()=>api.teacherAssignments(classId),[classId])
 const [items,setItems]=useState(()=>[block(topics[0])]);const [title,setTitle]=useState('');const [note,setNote]=useState('');const [prefill,setPrefill]=useState(null);const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [success,setSuccess]=useState(false)
 const setTemplate=(kind,topic=items[0]?.topic||topics[0])=>setItems(templates[kind].map(([q,d,c])=>block(topic,q,d,c)))
 const apply=row=>{const kind=row.correct_rate<.4?'foundation':row.correct_rate<=.7?'mixed':'challenge';setTemplate(kind,row.topic);setTitle(t('teacher.assign_title_suggest',{topic:label(row.topic)}));setPrefill(kind)}
 const reset=()=>{setPrefill(null);setItems([block(topics[0])]);setTitle('');setNote('')}
 const submit=async()=>{setError('');setSuccess(false);if(!title.trim()){setError(t('teacher.assign_need_title'));return}if(!items.length){setError(t('teacher.assign_need_items'));return}if(items.some(x=>!Number.isInteger(x.count)||x.count<1||x.count>10))return;setBusy(true);try{await api.teacherCreate({title:title.trim(),note:note.trim(),items:items.map(({topic,qtype,difficulty,count})=>({topic,qtype,difficulty,count})),class_id:classId});reset();list.reload();setSuccess(true)}catch(e){setError(e.message)}finally{setBusy(false)}}
 const remove=async id=>{try{await api.teacherDelete(id);list.reload()}catch(e){setError(e.message)}}
 const titleLabel=value=>lang==='en'?({'「导数」巩固练习':'Derivatives practice set','极限复习综合':'Limits review set'}[value]||value):value
 const countText=values=>t('teacher.assign_total',{n:total(values),m:minutes(values)})
 const update=(id,key,value)=>setItems(items.map(x=>x.id===id?{...x,[key]:value}:x))
 return <div className="legacy-cols assign"><Panel><div id="teacher-new-assignment"/><Header icon="✏️" title={t('teacher.assign_new')} sub={t('teacher.assign_caption')}/>
 {topicRows(data).some(row=>row.attempts>=5&&row.correct_rate<.7)&&<><p className="legacy-caption">{t('teacher.assign_quick')}</p><div className="legacy-cols three">{topicRows(data).filter(row=>row.attempts>=5&&row.correct_rate<.7).slice(0,3).map(row=><button className="btn" key={row.topic} disabled={!topics.includes(row.topic)} onClick={()=>apply(row)}>{label(row.topic)}</button>)}</div></>}
 {prefill&&<div className="legacy-prefill"><div className="legacy-info">{t('teacher.assign_prefill',{source:t('teacher.assign_quick_source')})}<p>{t('teacher.assign_prefill_tpl',{tpl:t('teacher.tpl_'+prefill)})}</p></div><button className="btn" onClick={reset}>{t('teacher.assign_clear_prefill')}</button></div>}
 <label className="legacy-field">{t('teacher.assign_title')}<input className="inp" value={title} placeholder={t('teacher.assign_title_ph')} onChange={e=>setTitle(e.target.value)}/></label>
 <p className="legacy-caption">{t('teacher.assign_templates')}</p><div className="legacy-cols three">{Object.keys(templates).map(k=><button className="btn" key={k} title={t('teacher.tpl_'+k+'_help')} onClick={()=>setTemplate(k)}>{t('teacher.tpl_'+k)}</button>)}</div>
 <p className="legacy-caption">{t('teacher.assign_items_heading')}</p><div className="legacy-block-header">{['topic','format','difficulty','count'].map(k=><span key={k}>{t('teacher.'+k)}</span>)}</div>
 {items.map(x=><div className="legacy-block" key={x.id}><select aria-label={t('teacher.topic')} className="inp" value={x.topic} onChange={e=>update(x.id,'topic',e.target.value)}>{topics.map(k=><option key={k} value={k}>{label(k)}</option>)}</select><select aria-label={t('teacher.format')} className="inp" value={x.qtype} onChange={e=>update(x.id,'qtype',e.target.value)}>{['single_choice','multiple_choice','fill_blank','drag_order'].map(k=><option key={k} value={k}>{t('qtype.'+k)}</option>)}</select><select aria-label={t('teacher.difficulty')} className="inp" value={x.difficulty} onChange={e=>update(x.id,'difficulty',e.target.value)}>{['easy','medium','hard'].map(k=><option key={k} value={k}>{t('difficulty.'+k)}</option>)}</select><input aria-label={t('teacher.count')} className="inp" type="number" min="1" max="10" value={x.count} onChange={e=>update(x.id,'count',Number(e.target.value))}/><button className="btn" onClick={()=>setItems(items.filter(b=>b.id!==x.id))}>✕</button></div>)}
 {items.length<8&&<button className="btn legacy-full" onClick={()=>setItems([...items,block(items.at(-1)?.topic||topics[0])])}>{t('teacher.assign_add_block')}</button>}
 {!!items.length&&<div className="stat-strip" style={{gridTemplateColumns:'1fr'}}><div className="stat-item"><span className="stat-label">{countText(items)}</span></div></div>}
 <label className="legacy-field">{t('teacher.note')}<textarea className="inp" rows={3} value={note} onChange={e=>setNote(e.target.value)}/></label>
 {error&&<div role="alert" className="legacy-warning">{error}</div>}{success&&<div role="status" className="legacy-info">✅ {t('teacher.assign_created')}</div>}
 <button className="btn primary legacy-full" disabled={busy} onClick={submit}>{t('teacher.assign_btn')}</button>
 </Panel><Panel><div id="teacher-current-assignments"/><Header icon="📋" title={t('teacher.current_assignments')} sub={t('teacher.assign_not_connected')}/>
 {list.error?<div role="alert">{list.error.message}</div>:list.loading?<p>…</p>:!list.data?.length?<Empty>{t('teacher.no_assignments')}</Empty>:<div style={list.data.length>3?{maxHeight:460,overflowY:'auto'}:undefined}>{list.data.map(x=><div className="legacy-assignment" key={x.id}><button className="btn legacy-delete" title={t('teacher.delete')} onClick={()=>remove(x.id)}>✕</button><b>{titleLabel(x.title)}</b><p className="legacy-caption">{countText(x.items)} · {t('teacher.assign_completion')}: -</p>{x.items.map((b,i)=><p className="legacy-caption" key={i}>· {label(b.topic)} · {b.count}× {t('qtype.'+b.qtype)} · {t('difficulty.'+b.difficulty)}</p>)}{x.note&&<p className="legacy-caption">📝 {x.note}</p>}</div>)}</div>}
 </Panel></div>
}
function Assistant({classId,topic}) {
 const {t,label,lang}=useCopy();const [open,setOpen]=useState(false);const [history,setHistory]=useState([]);const [question,setQuestion]=useState('');const [busy,setBusy]=useState(false)
 const ask=async text=>{if(busy)return;if(!text.trim())return;setBusy(true);const prior=history;setHistory([...prior,{role:'user',content:text}]);setQuestion('');try{const r=await api.teacherAsk({question:text,class_id:classId,selected_topic:topic,language:lang,history:prior.map(({role,content})=>({role,content}))});setHistory(h=>[...h,{role:'assistant',content:r.answer,offline:r.llm_available===false}])}catch(e){setHistory(h=>[...h,{role:'assistant',content:t('common.backend_error')+' '+e.message}])}finally{setBusy(false)}}
 return <><button className="legacy-ai-launcher" onClick={()=>setOpen(!open)}>✦ {t('teacher.float_ai_button')}</button>{open&&<aside className="legacy-ai-drawer" role="dialog" aria-label={t('teacher.float_ai_title')}><button className="legacy-ai-close" onClick={()=>setOpen(false)}>×</button><small>{t('teacher.float_ai_kicker')}</small><h2>{t('teacher.float_ai_title')}</h2><p>{t('teacher.float_ai_sub')}</p>{topic&&<p className="legacy-caption">{t('teacher.float_ai_topic_synced',{topic:label(topic)})}</p>}
 {!!history.length&&<div className="legacy-ai-history">{history.map((x,i)=><div className={'legacy-ai-message '+x.role} key={i}>{x.offline&&<div className="legacy-warning">{t('teacher.assistant_offline')}</div>}<MathText>{x.content}</MathText></div>)}</div>}
 <p className="legacy-caption">{t('teacher.float_ai_try')}</p>{['ai_help','explain','dashboard'].map(k=><button className="btn legacy-full" key={k} disabled={busy} onClick={()=>ask(t('teacher.float_ai_'+k))}>{t('teacher.float_ai_'+k)}</button>)}
 {topic&&<><p className="legacy-caption">{t('teacher.float_ai_topic_questions',{topic:label(topic)})}</p>{['explain','next','practice'].map(k=><button className="btn legacy-full" key={k} disabled={busy} onClick={()=>ask(t('teacher.float_ai_'+k+'_topic',{topic:label(topic)}))}>{t('teacher.float_ai_'+k+'_topic',{topic:label(topic)})}</button>)}</>}
 <form onSubmit={e=>{e.preventDefault();ask(question)}}><textarea className="inp" value={question} placeholder={t('teacher.float_ai_placeholder')} onChange={e=>setQuestion(e.target.value)}/><button className="btn primary legacy-full" disabled={busy}>{t('teacher.ask')}</button></form>{busy&&<p>{t('teacher.assistant_thinking')}</p>}{!!history.length&&<button className="btn legacy-full" disabled={busy} onClick={()=>setHistory([])}>{t('teacher.assistant_clear')}</button>}</aside>}</>
}
export default function LegacyDashboard({theme,setTheme,onStudent}) {
 const {t,label,lang}=useCopy();const copy=useDashboardCopy();const {setLang}=useLang();const query=new URLSearchParams(window.location.search)
 const [classId,setClassId]=useState(()=>['demo','calc1-a','calc1-b'].includes(query.get('class_id'))?query.get('class_id'):'calc1-a');const [topic,setTopic]=useState('')
 const classOptions=useAsync(()=>api.teacherClasses(),[])
 const result=useAsync(()=>Promise.all([api.teacherData(classId),api.teacherTopics()]).then(([data,topics])=>({data,topics,classId})),[classId])
 useEffect(()=>{if(['zh','en'].includes(query.get('lang')))setLang(query.get('lang'));if(['light','dark'].includes(query.get('theme')))setTheme(query.get('theme'))},[])
 const s=result.data
 const links=[['teacher-overview','overview'],['teacher-topics','topics'],['teacher-metrics','details'],['teacher-act','assignments']]
 return <div className={'teacher-legacy '+(theme==='dark'?'legacy-dark':'')}>
 <style>{snapshot.css.replace(/<\/?style>/g,'')}</style>
 {theme==='dark'&&<style>{darkCss.replace(/<\/?style>/g,'')}</style>}
 <nav className="teacher-toc" aria-label={t('teacher.toc')}><div className="teacher-toc-title">{t('teacher.toc')}</div>{links.map(([id,key])=><a key={id} href={'#'+id} className="teacher-toc-standalone" onClick={()=>{const section=document.getElementById(id);if(section?.tagName==='DETAILS')section.open=true}}>{copy(key)}</a>)}</nav>
 <main className="legacy-main"><header className="sw-header"><button className="sw-brand"><span>∫</span><div>{t('teacher.shell_brand')}<small>{t('teacher.shell_sub')}</small></div></button><div className="sw-account"><select className="inp" aria-label={t('teacher.class_label')} value={classId} onChange={e=>{setClassId(e.target.value);setTopic('')}}>{(classOptions.data || [{id:classId,label:classId}]).map(c=><option key={c.id} value={c.id}>{label(c.label)}</option>)}</select><details className="sw-preferences"><summary>{t('teacher.settings')}</summary><div className="teacher-settings-panel"><div className="teacher-settings-divider"/><div className="teacher-role-switch"><span className="teacher-setting-pill active">{t('teacher.role_teacher')}</span><button className="teacher-setting-pill" onClick={onStudent}>{t('teacher.role_student')}</button></div><button className="teacher-theme-row" onClick={()=>setTheme(theme==='dark'?'light':'dark')}>{t('teacher.theme_'+theme)}<span className={'teacher-switch '+(theme==='dark'?'on':'')}><span/></span></button><div className="teacher-lang-row">{['zh','en'].map(l=><button key={l} className={'teacher-lang-pill '+(l===lang?'active':'')} onClick={()=>setLang(l)}>{l==='zh'?'中文':'EN'}</button>)}</div></div></details></div></header>
 <div className="sw-main-spacer"/>
 {result.error ? <div role="alert" className="legacy-warning">{t('common.backend_error')} {result.error.message} <button className="btn" onClick={result.reload}>{copy('retry')}</button></div>
 : result.loading || !s || s.classId !== classId ? <p role="status">{copy('loading')}</p>
 : <div className="legacy-content" key={classId}>
  <div className="teacher-toolbar"><p className="legacy-caption">{lang==='zh'?'当前班级 · 实验 ':'Current class · Experiment '}{s.data.experiment_id} · {s.data.metric_version}</p><button className="btn" onClick={result.reload}>{copy('retry')}</button></div>
  <ClassOverview data={s.data} rows={topicRows(s.data)} topic={topic} onTopic={setTopic}/>
  <MetricsDetail data={s.data}/>
  <details id="teacher-act" className="legacy-panel teacher-disclosure">
   <summary>{copy('assignments')}</summary>
   {s.topics.length>0&&<Assignments topics={s.topics} data={s.data} classId={classId}/>}
  </details>
 </div>}
 </main><Assistant key={classId} classId={classId} topic={topic}/></div>
}
