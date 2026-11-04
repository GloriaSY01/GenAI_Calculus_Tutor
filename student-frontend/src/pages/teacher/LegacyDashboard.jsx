import { useEffect, useRef, useState } from 'react'
import { useLang } from '../../i18n.jsx'
import { api } from '../../api.js'
import { useAsync } from '../../components/hooks.js'
import { Chart as BaseChart } from '../../components/ui.jsx'
import { MathText } from '../../components/math.jsx'
import { displayLabel } from '../../localization.js'
import snapshot from './legacy82.json'
import darkCss from './legacy82-dark.json'
import './legacy82.css'

const pct = value => `${Math.round((value || 0) * 100)}%`
const tied = rows => (rows || []).filter(row => row.topic !== 'General / Free chat')
const weakest = rows => [...tied(rows)].sort((a,b) => a.solve_rate-b.solve_rate || a.avg_reasoning-b.avg_reasoning)[0]
const templates = {
  foundation: [['single_choice','easy',4],['fill_blank','easy',3],['single_choice','medium',2]],
  mixed: [['single_choice','medium',3],['multiple_choice','medium',2],['fill_blank','medium',3],['drag_order','medium',2]],
  challenge: [['multiple_choice','medium',2],['fill_blank','hard',3],['drag_order','hard',2]],
}
const block = (topic,qtype='single_choice',difficulty='easy',count=3) => ({id:crypto.randomUUID(),topic,qtype,difficulty,count})
const total = items => items.reduce((sum,x) => sum+x.count,0)
const minutes = items => Math.max(1,Math.round(items.reduce((sum,x)=>sum+({single_choice:1.5,multiple_choice:2,fill_blank:3,drag_order:3}[x.qtype])*({easy:.8,medium:1,hard:1.4}[x.difficulty])*x.count,0)))
const levels=['none','weak','partial','adequate','strong']
function Chart(props) {
 const ref=useRef(null);const [width,setWidth]=useState(0)
 useEffect(()=>{const observer=new ResizeObserver(entries=>setWidth(Math.round(entries[0].contentRect.width)));observer.observe(ref.current);return()=>observer.disconnect()},[])
 return <div ref={ref} style={{width:'100%',minWidth:0,overflow:'hidden'}}><BaseChart key={width} {...props}/></div>
}
function useCopy() {
  const {lang}=useLang()
  const t=(key,values={}) => Object.entries(values).reduce((s,[k,v])=>s.replaceAll(`{${k}}`,String(v)),snapshot.strings[key]?.[lang] ?? snapshot.strings[key]?.en ?? key)
  const label=topic=>snapshot.strings['topic.'+topic]?.[lang] ?? displayLabel(topic,lang)
  return {t,label,lang}
}
function Header({icon,title,sub}) {return <div className="ph"><div className="ph-icon">{icon}</div><div><h3 className="ph-title">{title}</h3>{sub&&<div className="ph-desc">{sub}</div>}</div></div>}
function Panel({children}) {return <section className="legacy-panel">{children}</section>}
function Section({step,title,sub,id}) {return <><span id={id} className="teacher-anchor"/><header className="legacy-section"><div className="sec-eyebrow">{step}</div><h2 className="sec-title">{title}</h2>{sub&&<div className="sec-sub">{sub}</div>}</header></>}
function Metric({label,value,help}) {return <div className="legacy-metric" title={help}><span>{label}</span><strong>{value}</strong></div>}
function Empty({children}) {return <div className="empty">{children}</div>}
function Brief({data}) {
 const {t,label}=useCopy(); const weak=weakest(data.by_topic)
 const rows=[['flat_focus',weak?label(weak.topic):t(data.n_sessions?'teacher.flat_no_weak_topic':'teacher.flat_no_data_focus')],['flat_evidence',weak?`${pct(weak.solve_rate)} ${t('teacher.flat_solved')} · ${weak.avg_reasoning}/4 ${t('teacher.flat_reasoning')}`:t(data.n_sessions?'teacher.flat_enough_data':'teacher.flat_no_data_evidence')],['flat_next_action',t(weak?'teacher.flat_action_assign':data.n_sessions?'teacher.flat_action_monitor':'teacher.flat_action_collect')]]
 return <Panel><div id="teacher-summary"/><Header icon="🧭" title={t('teacher.flat_brief_title')} sub={t('teacher.flat_brief_sub')}/><div className="legacy-cols three">{rows.map(([key,value])=><div key={key}><b>{t('teacher.'+key)}</b><p className="legacy-caption">{t('teacher.'+key+'_help')}</p><div className="legacy-info">{value}</div></div>)}</div></Panel>
}
function KPIs({data}) {
 const {t}=useCopy()
 return <div id="teacher-class-status">{data.n_sim_sessions>0&&<div className="legacy-warning">{t('teacher.badge_sim',{n:data.n_sim_sessions})}</div>}<div className="legacy-cols four">{[
 ['kpi_students',data.n_students||0,'kpi_students_sub'],['kpi_practice_submissions',data.practice_submission_count||0,'kpi_practice_submissions_help'],['kpi_independent_solve',pct(data.independent_solve_rate),'kpi_independent_solve_help'],['kpi_ai_assisted_solve',pct(data.ai_assisted_solve_rate),'kpi_ai_assisted_solve_help'],
 ].map(([key,value,help])=><Metric key={key} label={t('teacher.'+key)} value={value} help={t('teacher.'+help)}/>)}</div></div>
}
function Practice({practice={},catalog,onTopic}) {
 const {t,label}=useCopy(); const [chosen,setChosen]=useState('')
 const real=practice.n_answers>0&&practice.by_difficulty_completion?.length
 const difficulties=real?practice.by_difficulty_completion:[{difficulty:'easy',independent_rate:.78,ai_assisted_rate:.64},{difficulty:'medium',independent_rate:.62,ai_assisted_rate:.58},{difficulty:'hard',independent_rate:.41,ai_assisted_rate:.49}]
 const ordered=[...difficulties].sort((a,b)=>['easy','medium','hard','unknown'].indexOf(a.difficulty)-['easy','medium','hard','unknown'].indexOf(b.difficulty))
 const rows=real?practice.practice_by_topic||[]:[]
 const topics=[...new Set([...(catalog?.chapters||[]).flatMap(ch=>ch.sections.map(s=>s.title)),...rows.map(x=>x.topic)])]
 const initial=[...rows].sort((a,b)=>a.correct_rate-b.correct_rate||b.attempts-a.attempts)[0]?.topic||topics[0]||''
 const current=topics.includes(chosen)?chosen:initial
 const selected=rows.find(x=>x.topic===current)
 useEffect(()=>{onTopic(current)},[current,onTopic])
 const rate=value=>value==null?t('teacher.practice_topic_no_data_value'):pct(value<=1?value:value/100)
 return <section id="teacher-practice-results"><Header icon="📝" title={t('teacher.practice_overview')} sub={t('teacher.practice_overview_sub')}/>
 {!real&&<div className="legacy-info">{t('teacher.practice_demo_note')}</div>}
 <h4>{t('teacher.practice_difficulty_chart')}</h4><p className="legacy-caption">{t('teacher.practice_difficulty_chart_sub')}</p>
 <Chart height={350} option={{animation:false,legend:{bottom:0},grid:{left:56,right:16,top:22,bottom:60,containLabel:true},tooltip:{trigger:'axis',valueFormatter:v=>pct(v)},xAxis:{type:'category',name:t('teacher.difficulty'),nameLocation:'middle',nameGap:28,data:ordered.map(x=>t('difficulty.'+x.difficulty))},yAxis:{type:'value',max:1,axisLabel:{formatter:v=>pct(v)}},series:['independent','ai_assisted'].map((mode,i)=>({name:t('teacher.practice_'+mode),type:'bar',barMaxWidth:55,itemStyle:{color:['#1D4ED8','#93C5FD'][i],borderRadius:[4,4,0,0]},label:{show:true,position:'top',formatter:x=>pct(x.value)},data:ordered.map(x=>x[mode+'_rate'])}))}}/>
 <h4>{t('teacher.practice_topic_table')}</h4>{topics.length>0&&<label className="legacy-field">{t('teacher.practice_topic_filter')}<select className="inp" value={current} onChange={e=>setChosen(e.target.value)}>{topics.map(x=><option key={x} value={x}>{label(x)}</option>)}</select></label>}
 <p className="legacy-caption">{t('teacher.practice_topic_selected')}: {label(current)}</p>
 <div className="legacy-cols four">{[['submissions',selected?.attempts||0],['correct_rate',rate(selected?.correct_rate)],['independent_rate',rate(selected?.independent_rate)],['ai_assisted_rate',rate(selected?.ai_assisted_rate)]].map(([key,value])=><Metric key={key} label={t('teacher.practice_topic_'+key)} value={value} help={t('teacher.practice_topic_'+key+'_help')}/>)}</div>
 </section>
}
function Attitude({data}) {
 const {t,label}=useCopy(); const cards=[]
 const add=(kind,severity,params={})=>cards.push({title:t('insight.'+kind+'.title',params),detail:t('insight.'+kind+'.detail',params),severity})
 const rows=tied(data.by_topic); const ranked=rows.filter(x=>x.attempts>=3); const weak=weakest(ranked.length?ranked:rows)
 if(weak&&weak.solve_rate<.6)add('weak_topic','warning',{topic:label(weak.topic),n:weak.attempts,solve:Math.round(weak.solve_rate*100),reasoning:weak.avg_reasoning})
 if(data.gaming_rate>=.3)add('gaming_high','critical',{rate:Math.round(data.gaming_rate*100)});else if(data.gaming_rate>0)add('gaming_low','info',{rate:Math.round(data.gaming_rate*100)})
 if(data.n_turns>0){if(data.avg_reasoning<1.5)add('low_reasoning','warning',{score:data.avg_reasoning});else if(data.avg_reasoning>=3)add('high_reasoning','info',{score:data.avg_reasoning})}
 if((data.n_sessions||0)<5)add('coverage','info',{n:data.n_sessions||0})
 if(!cards.length)add('healthy','info')
 return <section id="teacher-learning-attitude"><Header icon="💡" title={t('teacher.insights')} sub={t('teacher.insights_caption')}/><div className="legacy-cols three">{[['kpi_help_seeking',data.practice?.ai_help_rate],['kpi_gaming',data.gaming_rate],['kpi_guardrail',data.guardrail_rate]].map(([key,value])=><Metric key={key} label={t('teacher.'+key)} value={pct(value)} help={t('teacher.'+key+'_help')}/>)}</div><div className="legacy-findings">{cards.map((x,i)=><div key={i} className={'insight sev-'+x.severity}><div className="insight-title">{{info:'🟢',warning:'🟠',critical:'🔴'}[x.severity]} {x.title}</div><div className="insight-detail">{x.detail}</div></div>)}</div></section>
}
function TopicHealth({data}) {
 const {t,label}=useCopy(); const rows=tied(data.by_topic);const untied=(data.by_topic||[]).filter(x=>x.topic==='General / Free chat').reduce((n,x)=>n+x.attempts,0)
 const demo=[{topic:t('teacher.demo_topic_limits'),attempts:18,avg_reasoning:1.4,solve_rate:.32,gaming_rate:.18},{topic:t('teacher.demo_topic_derivatives'),attempts:15,avg_reasoning:2.1,solve_rate:.58,gaming_rate:.08},{topic:t('teacher.demo_topic_chain_rule'),attempts:11,avg_reasoning:2.8,solve_rate:.74,gaming_rate:.04}]
 const chartRows=[...(rows.length?rows:demo)].sort((a,b)=>a.solve_rate-b.solve_rate)
 return <Panel><div id="teacher-topic-health"/><Header icon="🎯" title={t('teacher.topic_health')} sub={t('teacher.topic_health_sub')}/>{!rows.length&&<><Empty>{t(untied?'teacher.only_free_chat_data':'teacher.no_topic_data',{n:untied})}</Empty><p className="legacy-caption">{t('teacher.topic_health_demo_note')}</p></>}
 <Chart height={Math.max(150,52*chartRows.length)} option={{animation:false,grid:{left:10,right:45,top:20,bottom:40,containLabel:true},tooltip:{trigger:'axis',valueFormatter:v=>pct(v)},xAxis:{type:'value',max:1,name:t('teacher.axis_solve'),nameLocation:'middle',nameGap:25,axisLabel:{formatter:v=>pct(v)}},yAxis:{type:'category',inverse:true,data:chartRows.map(x=>label(x.topic))},series:[{type:'bar',barWidth:22,showBackground:true,backgroundStyle:{color:'#EEF3FE'},label:{show:true,position:'right',formatter:x=>pct(x.value)},data:chartRows.map(x=>({value:x.solve_rate,itemStyle:{color:x.solve_rate<.55?'#E76F51':x.solve_rate<.75?'#E9C46A':'#2A9D55',borderRadius:6}}))}]}}/>
 {!!rows.length&&<>{!!untied&&<p className="legacy-caption">{t('teacher.free_chat_note',{n:untied})}</p>}<details><summary>{t('teacher.full_table')}</summary><div className="legacy-table-scroll"><table className="tbl"><thead><tr>{['topic','attempts','solve','reasoning','gaming'].map(k=><th key={k}>{t('teacher.axis_'+k)}</th>)}</tr></thead><tbody>{rows.map(x=><tr key={x.topic}><td>{label(x.topic)}</td><td>{x.attempts}</td><td>{Math.round(x.solve_rate*100)}</td><td>{x.avg_reasoning}</td><td>{Math.round(x.gaming_rate*100)}</td></tr>)}</tbody></table></div></details></>}
 </Panel>
}
function Reasoning({data}) {
 const {t}=useCopy();const real=Object.values(data.reasoning_distribution||{}).reduce((a,b)=>a+b,0)>0
 const dist=real?data.reasoning_distribution:{none:.32,weak:.28,partial:.22,adequate:.13,strong:.05}
 return <Panel><div id="teacher-reasoning"/><Header icon="💬" title={t('teacher.reasoning_dist')} sub={t('teacher.reasoning_sub')}/>{!real&&<><div className="legacy-info">{t('teacher.no_reasoning_data')}</div><p className="legacy-caption">{t('teacher.reasoning_demo_note')}</p></>}
 <Chart height={280} option={{animation:false,tooltip:{trigger:'axis',valueFormatter:v=>pct(v)},xAxis:{type:'category',name:t('teacher.axis_level'),nameLocation:'middle',nameGap:30,data:levels},yAxis:{type:'value',axisLabel:{formatter:v=>pct(v)},name:t('teacher.axis_share')},series:[{type:'bar',barMaxWidth:46,data:levels.map((k,i)=>({value:dist[k]||0,itemStyle:{color:['#DC2626','#F97316','#F59E0B','#65A30D','#16A34A'][i],borderRadius:[0,6,6,0]}}))}]}}/>
 {real&&<><p className="legacy-caption">{t('teacher.reasoning_dist_caption')}</p>{data.explanation_response_rate!=null&&<Metric label={t('teacher.explain_rate')} value={pct(data.explanation_response_rate)}/>}</>}</Panel>
}
function Assignments({topics,data,classId}) {
 const {t,label,lang}=useCopy();const list=useAsync(()=>api.teacherAssignments(classId),[classId])
 const [items,setItems]=useState(()=>[block(topics[0])]);const [title,setTitle]=useState('');const [note,setNote]=useState('');const [prefill,setPrefill]=useState(null);const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [success,setSuccess]=useState(false)
 const setTemplate=(kind,topic=items[0]?.topic||topics[0])=>setItems(templates[kind].map(([q,d,c])=>block(topic,q,d,c)))
 const apply=row=>{const kind=row.solve_rate==null||row.solve_rate<.4?'foundation':row.solve_rate<=.7?'mixed':'challenge';setTemplate(kind,row.topic);setTitle(t('teacher.assign_title_suggest',{topic:label(row.topic)}));setPrefill(kind)}
 const reset=()=>{setPrefill(null);setItems([block(topics[0])]);setTitle('');setNote('')}
 const submit=async()=>{setError('');setSuccess(false);if(!title.trim()){setError(t('teacher.assign_need_title'));return}if(!items.length){setError(t('teacher.assign_need_items'));return}if(items.some(x=>!Number.isInteger(x.count)||x.count<1||x.count>10))return;setBusy(true);try{await api.teacherCreate({title:title.trim(),note:note.trim(),items:items.map(({topic,qtype,difficulty,count})=>({topic,qtype,difficulty,count})),class_id:classId});reset();list.reload();setSuccess(true)}catch(e){setError(e.message)}finally{setBusy(false)}}
 const remove=async id=>{try{await api.teacherDelete(id);list.reload()}catch(e){setError(e.message)}}
 const titleLabel=value=>lang==='en'?({'「导数」巩固练习':'Derivatives practice set','极限复习综合':'Limits review set'}[value]||value):value
 const countText=values=>t('teacher.assign_total',{n:total(values),m:minutes(values)})
 const update=(id,key,value)=>setItems(items.map(x=>x.id===id?{...x,[key]:value}:x))
 return <div className="legacy-cols assign"><Panel><div id="teacher-new-assignment"/><Header icon="✏️" title={t('teacher.assign_new')} sub={t('teacher.assign_caption')}/>
 {!!tied(data.by_topic).length&&<><p className="legacy-caption">{t('teacher.assign_quick')}</p><div className="legacy-cols three">{[...tied(data.by_topic)].sort((a,b)=>a.solve_rate-b.solve_rate).slice(0,3).map(x=><button className="btn" key={x.topic} disabled={!topics.includes(x.topic)} onClick={()=>apply(x)}>{label(x.topic)}</button>)}</div></>}
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
 const {t,label,lang}=useCopy();const {setLang}=useLang();const query=new URLSearchParams(window.location.search)
 const [classId,setClassId]=useState(()=>['calc1-a','calc1-b'].includes(query.get('class_id'))?query.get('class_id'):'calc1-a');const [topic,setTopic]=useState('')
 const result=useAsync(()=>Promise.all([api.teacherData(classId),api.teacherTopics(),api.teacherCatalog()]).then(([data,topics,catalog])=>({data,topics,catalog})),[classId])
 useEffect(()=>{if(['zh','en'].includes(query.get('lang')))setLang(query.get('lang'));if(['light','dark'].includes(query.get('theme')))setTheme(query.get('theme'))},[])
 const s=result.data
 const links=[['teacher-summary','teacher.flat_brief_title'],['teacher-overview','teacher.sec_overview',['teacher-class-status','teacher.sec_overview_title'],['teacher-practice-results','teacher.practice_overview'],['teacher-learning-attitude','teacher.insights']],['teacher-diagnose','teacher.sec_diagnose',['teacher-topic-health','teacher.topic_health'],['teacher-reasoning','teacher.reasoning_dist']],['teacher-act','teacher.sec_act',['teacher-new-assignment','teacher.assign_new'],['teacher-current-assignments','teacher.current_assignments']]]
 return <div className={'teacher-legacy '+(theme==='dark'?'legacy-dark':'')}>
 <style>{snapshot.css.replace(/<\/?style>/g,'')}</style>
 {theme==='dark'&&<style>{darkCss.replace(/<\/?style>/g,'')}</style>}
 <nav className="teacher-toc" aria-label={t('teacher.toc')}><div className="teacher-toc-title">{t('teacher.toc')}</div>{links.map(([id,key,...children],i)=><div className={i?'teacher-toc-group':''} key={id}><a href={'#'+id} className={i?'teacher-toc-step':'teacher-toc-standalone'}>{i>0&&<span>{String(i).padStart(2,'0')}</span>}{t(key)}</a>{children.map(([child,text])=><a key={child} className="teacher-toc-child" href={'#'+child}>{t(text)}</a>)}</div>)}</nav>
 <main className="legacy-main"><header className="sw-header"><button className="sw-brand"><span>∫</span><div>{t('teacher.shell_brand')}<small>{t('teacher.shell_sub')}</small></div></button><div className="sw-account"><input className="inp" aria-label={lang==='zh'?'填写教师账号':'Enter teacher account'} placeholder={lang==='zh'?'填写教师账号':'Enter teacher account'}/><select className="inp" aria-label={t('teacher.class_label')} value={classId} onChange={e=>{setClassId(e.target.value);setTopic('')}}>{['calc1-a','calc1-b'].map((id,i)=><option key={id} value={id}>{label(`微积分 I · ${i?'B':'A'} 班`)}</option>)}</select><details className="sw-preferences"><summary>{t('teacher.settings')}</summary><div className="teacher-settings-panel"><div className="teacher-settings-divider"/><div className="teacher-role-switch"><span className="teacher-setting-pill active">{t('teacher.role_teacher')}</span><button className="teacher-setting-pill" onClick={onStudent}>{t('teacher.role_student')}</button></div><button className="teacher-theme-row" onClick={()=>setTheme(theme==='dark'?'light':'dark')}>{t('teacher.theme_'+theme)}<span className={'teacher-switch '+(theme==='dark'?'on':'')}><span/></span></button><div className="teacher-lang-row">{['zh','en'].map(l=><button key={l} className={'teacher-lang-pill '+(l===lang?'active':'')} onClick={()=>setLang(l)}>{l==='zh'?'中文':'EN'}</button>)}</div></div></details></div></header>
 <div className="sw-main-spacer"/>{result.loading?<p>…</p>:result.error?<div role="alert" className="legacy-warning">{t('common.backend_error')} {result.error.message}</div>:<div className="legacy-content" key={classId}>
 <div id="teacher-overview"/><Brief data={s.data}/><Section step={t('teacher.sec_overview')} title={t('teacher.sec_overview_title')}/><KPIs data={s.data}/>
 <Panel><Practice practice={s.data.practice} catalog={s.catalog} onTopic={setTopic}/><hr/><Attitude data={s.data}/></Panel>
 <Section id="teacher-diagnose" step={t('teacher.sec_diagnose')} title={t('teacher.sec_diagnose_title')} sub={t('teacher.sec_diagnose_sub')}/><div className="legacy-cols diagnosis"><TopicHealth data={s.data}/><Reasoning data={s.data}/></div>
 {!!s.data.by_condition?.length&&<details><summary>{t('teacher.research_view')}</summary><Panel><Header icon="🧪" title={t('teacher.condition_heading')} sub={t('teacher.condition_sub')}/><div className="legacy-cols two">{s.data.by_condition.map(row=><div className="mini-card" key={row.condition}><div className="mini-head">{t('teacher.condition_'+(row.condition==='explain'?'explain':'control'))}</div>{[['kpi_sessions',row.n_sessions],['kpi_solve',pct(row.solve_rate)],['kpi_reasoning',`${row.avg_reasoning}/4`],['kpi_turns',row.avg_turns_per_session]].map(([key,value])=><div className="mini-row" key={key}><span>{t('teacher.'+key)}</span><span>{value}</span></div>)}</div>)}</div><p className="legacy-caption">{t('teacher.condition_note')}</p></Panel></details>}
 <Section id="teacher-act" step={t('teacher.sec_act')} title={t('teacher.sec_act_title')} sub={t('teacher.sec_act_sub')}/>{s.topics.length>0&&<Assignments topics={s.topics} data={s.data} classId={classId}/>}</div>}
 </main><Assistant classId={classId} topic={topic}/></div>
}
