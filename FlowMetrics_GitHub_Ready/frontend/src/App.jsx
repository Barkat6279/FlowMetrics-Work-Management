import React, { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowUpRight, CheckCircle2, ClipboardList, Clock3, LogOut, Plus, Search, ShieldCheck, Users, X } from 'lucide-react';

const API = `${(import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')}/api`;
const demo = [
  ['Admin','admin@flowmetrics.local'], ['Team Leader','lead@flowmetrics.local'], ['Employee','employee@flowmetrics.local']
];

export default function App() {
  const [token,setToken] = useState(localStorage.getItem('fm_token') || '');
  const [user,setUser] = useState(JSON.parse(localStorage.getItem('fm_user') || 'null'));
  const [email,setEmail] = useState('lead@flowmetrics.local');
  const [password,setPassword] = useState('FlowMetrics@123');
  const [tasks,setTasks] = useState([]);
  const [people,setPeople] = useState([]);
  const [loading,setLoading] = useState(false);
  const [error,setError] = useState('');
  const [query,setQuery] = useState('');
  const [showCreate,setShowCreate] = useState(false);
  const [form,setForm] = useState({title:'',description:'',assignee_id:'',priority:'Medium',due_date:''});
  const [editing,setEditing] = useState(null);

  async function request(path, options={}) {
    const res = await fetch(API+path,{...options,headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{}) ,...(options.headers||{})}});
    const data = await res.json().catch(()=>({detail:'Unexpected server response'}));
    if(!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
  }
  async function load() {
    if(!token) return;
    setLoading(true); setError('');
    try {
      const [t,p] = await Promise.all([request('/tasks'), user?.role !== 'Employee' ? request('/users') : Promise.resolve([])]);
      setTasks(t); setPeople(p);
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }
  useEffect(()=>{ if(token && user) load(); },[token]);
  async function login(e) {
    e.preventDefault(); setError('');
    try {
      const data=await request('/login',{method:'POST',body:JSON.stringify({email,password})});
      localStorage.setItem('fm_token',data.token); localStorage.setItem('fm_user',JSON.stringify(data.user));
      setToken(data.token); setUser(data.user);
    } catch(e){setError(e.message);}
  }
  async function logout() {
    try { await request('/logout',{method:'POST'}); } catch {}
    localStorage.removeItem('fm_token'); localStorage.removeItem('fm_user');
    setToken(''); setUser(null); setTasks([]); setPeople([]);
  }
  async function createTask(e) {
    e.preventDefault(); setError('');
    try {
      await request('/tasks',{method:'POST',body:JSON.stringify({...form,assignee_id:Number(form.assignee_id)})});
      setShowCreate(false); setForm({title:'',description:'',assignee_id:'',priority:'Medium',due_date:''}); await load();
    } catch(e){setError(e.message);}
  }
  async function updateTask(id,status,employee_update) {
    try { await request(`/tasks/${id}/update`,{method:'PATCH',body:JSON.stringify({status,employee_update})}); setEditing(null); await load(); }
    catch(e){setError(e.message);}
  }
  async function reviewTask(id,status,review_note) {
    try { await request(`/tasks/${id}/review`,{method:'PATCH',body:JSON.stringify({status,review_note})}); setEditing(null); await load(); }
    catch(e){setError(e.message);}
  }
  async function deleteTask(id) {
    if(!confirm('Delete this task permanently?')) return;
    try { await request(`/tasks/${id}`,{method:'DELETE'}); await load(); } catch(e){setError(e.message);}
  }
  const filtered=useMemo(()=>tasks.filter(t=>`${t.title} ${t.assignee_name} ${t.status}`.toLowerCase().includes(query.toLowerCase())),[tasks,query]);
  const counts={total:tasks.length,active:tasks.filter(t=>['Assigned','In Progress'].includes(t.status)).length,submitted:tasks.filter(t=>t.status==='Submitted').length,reviewed:tasks.filter(t=>t.status==='Reviewed').length};

  if(!token || !user) return <div className="login-shell"><div className="login-card"><div className="brand"><div className="brand-mark"><Activity/></div><div><b>flowmetrics</b><small>WORK MANAGEMENT</small></div></div><div className="login-copy"><span className="eyebrow">TEAM WORKSPACE</span><h1>Work that moves<br/><em>forward.</em></h1><p>Assign clearly. Track progress. Close the loop.</p></div><form onSubmit={login} className="login-form"><label>Email address<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required/></label>{error&&<div className="error">{error}</div>}<button className="primary full">Sign in <ArrowUpRight size={17}/></button></form><div className="demo"><b>Demo access</b>{demo.map(([r,m])=><button key={r} onClick={()=>setEmail(m)}>{r}<span>{m}</span></button>)}<small>Password for all: FlowMetrics@123</small></div></div><div className="login-side"><div className="side-orb orb-one"/><div className="side-orb orb-two"/><div className="side-message"><span>FLOWMETRICS / 01</span><h2>One place for<br/>every moving part.</h2><p>A simple operating rhythm for teams that need visibility, ownership, and momentum.</p><div className="side-stat"><b>01</b><span>Assign work<br/>with clear ownership</span><b>02</b><span>Track progress<br/>without chasing</span></div></div><small className="side-foot">BUILT FOR TEAMS THAT GET THINGS DONE</small></div></div>;

  return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-mark"><Activity/></div><div><b>flowmetrics</b><small>WORK MANAGEMENT</small></div></div><div className="workspace-label">WORKSPACE</div><div className="nav-item active"><ClipboardList size={18}/> Tasks <span>{tasks.length}</span></div><div className="sidebar-bottom"><div className="profile"><div className="avatar">{user.name.split(' ').map(x=>x[0]).join('').slice(0,2)}</div><div><b>{user.name}</b><small>{user.role}</small></div><button className="icon-btn" onClick={logout} title="Sign out"><LogOut size={17}/></button></div></div></aside><main className="main"><header className="topbar"><div><span className="eyebrow">OVERVIEW / TASKS</span><h1>Good work starts with clarity.</h1></div><div className="top-actions"><span className="role-pill"><ShieldCheck size={14}/>{user.role}</span><button className="refresh" onClick={load}>Refresh</button>{user.role!=='Employee'&&<button className="primary" onClick={()=>setShowCreate(true)}><Plus size={17}/> Create task</button>}</div></header>
    {error&&<div className="error banner">{error}<button onClick={()=>setError('')}><X size={16}/></button></div>}
    <section className="welcome"><div><span className="eyebrow">YOUR WORKSPACE</span><h2>{user.role==='Employee'?'Your tasks, in one place':user.role==='Team Leader'?'Your team’s work, in view':'Organization overview'}</h2><p>{user.role==='Employee'?'See what needs attention and keep your team updated.':'Create assignments, follow progress, and review submitted work.'}</p></div><div className="welcome-icon"><Activity size={30}/></div></section>
    <section className="stats"><Stat icon={<ClipboardList/>} label="Total tasks" value={counts.total}/><Stat icon={<Clock3/>} label="In progress" value={counts.active}/><Stat icon={<Activity/>} label="Submitted" value={counts.submitted}/><Stat icon={<CheckCircle2/>} label="Reviewed" value={counts.reviewed}/></section>
    <section className="task-section"><div className="section-head"><div><span className="eyebrow">TASK REGISTER</span><h2>{user.role==='Employee'?'My tasks':'Team tasks'}</h2></div><div className="search"><Search size={17}/><input placeholder="Search tasks..." value={query} onChange={e=>setQuery(e.target.value)}/></div></div>
    {loading?<div className="empty">Loading tasks…</div>:filtered.length===0?<div className="empty"><ClipboardList size={28}/><b>No tasks found</b><span>{query?'Try another search.':'New assignments will appear here.'}</span></div>:<div className="task-list">{filtered.map(t=><article className="task-card" key={t.id}><div className="task-main"><div className="task-top"><span className={`status status-${t.status.toLowerCase().replaceAll(' ','-')}`}>{t.status}</span><span className={`priority priority-${t.priority.toLowerCase()}`}>{t.priority} priority</span><span className="task-id">FM-{String(t.id).padStart(4,'0')}</span></div><h3>{t.title}</h3><p>{t.description||'No description provided.'}</p><div className="task-meta"><span><Users size={14}/>{user.role==='Employee'?`Assigned by ${t.leader_name}`:`${t.assignee_name}`}</span><span><Clock3 size={14}/>{t.due_date||'No due date'}</span></div>{t.employee_update&&<div className="update-box"><b>Employee update</b><p>{t.employee_update}</p></div>}{t.review_note&&<div className="review-box"><b>Review note</b><p>{t.review_note}</p></div>}</div><div className="task-actions">{user.role==='Employee'?<button className="outline" onClick={()=>setEditing({task:t,mode:'update'})}>Update task</button>:<><button className="outline" onClick={()=>setEditing({task:t,mode:'review'})}>{t.status==='Submitted'?'Review submission':'Review'}</button><button className="quiet danger" onClick={()=>deleteTask(t.id)}>Delete</button></>}</div></article>)}</div>}</section>
    <footer>FLOWMETRICS <span>·</span> KEEP WORK MOVING</footer></main>
    {showCreate&&<Modal title="Create a task" close={()=>setShowCreate(false)}><form className="modal-form" onSubmit={createTask}><label>Task title<input value={form.title} onChange={e=>setForm({...form,title:e.target.value})} required minLength="3" placeholder="e.g. Prepare weekly sales report"/></label><label>Description<textarea value={form.description} onChange={e=>setForm({...form,description:e.target.value})} placeholder="Describe the expected outcome…"/></label><div className="two"><label>Assign to<select value={form.assignee_id} onChange={e=>setForm({...form,assignee_id:e.target.value})} required><option value="">Select employee</option>{people.map(p=><option value={p.id} key={p.id}>{p.name}</option>)}</select></label><label>Priority<select value={form.priority} onChange={e=>setForm({...form,priority:e.target.value})}><option>Low</option><option>Medium</option><option>High</option></select></label></div><label>Due date<input type="date" value={form.due_date} onChange={e=>setForm({...form,due_date:e.target.value})}/></label><button className="primary full">Create assignment <ArrowUpRight size={17}/></button></form></Modal>}
    {editing&&<Modal title={editing.mode==='update'?'Update your task':'Review employee submission'} close={()=>setEditing(null)}><div className="edit-summary"><span className="eyebrow">FM-{String(editing.task.id).padStart(4,'0')}</span><h3>{editing.task.title}</h3><p>{editing.task.description}</p></div>{editing.mode==='update'?<UpdateForm task={editing.task} save={updateTask}/>:<ReviewForm task={editing.task} save={reviewTask}/>}</Modal>}
  </div>;
}
function Stat({icon,label,value}){return <div className="stat"><div className="stat-icon">{icon}</div><div><span>{label}</span><b>{value}</b></div></div>}
function Modal({title,close,children}){return <div className="modal-backdrop" onMouseDown={e=>e.target===e.currentTarget&&close()}><div className="modal"><div className="modal-head"><h2>{title}</h2><button className="icon-btn" onClick={close}><X/></button></div>{children}</div></div>}
function UpdateForm({task,save}){const [status,setStatus]=useState(task.status==='Assigned'?'In Progress':task.status);const [note,setNote]=useState(task.employee_update||'');return <form className="modal-form" onSubmit={e=>{e.preventDefault();save(task.id,status,note)}}><label>Status<select value={status} onChange={e=>setStatus(e.target.value)}><option>In Progress</option><option>Submitted</option></select></label><label>Progress update<textarea value={note} onChange={e=>setNote(e.target.value)} placeholder="What have you completed? Any blockers?"/></label><button className="primary full">Save update</button></form>}
function ReviewForm({task,save}){const [status,setStatus]=useState(task.status==='Submitted'?'Reviewed':task.status);const [note,setNote]=useState(task.review_note||'');return <form className="modal-form" onSubmit={e=>{e.preventDefault();save(task.id,status,note)}}><label>Review decision<select value={status} onChange={e=>setStatus(e.target.value)}><option>Reviewed</option><option>In Progress</option><option>Assigned</option></select></label><label>Feedback to employee<textarea value={note} onChange={e=>setNote(e.target.value)} placeholder="Add feedback or next steps…"/></label><button className="primary full">Save review</button></form>}
