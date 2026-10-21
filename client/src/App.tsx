import { useMemo, useRef, useState } from 'react';
import './style.css';
type Item = {type:'club'|'event';title:string;url:string;reason:string;source:string};
type Result = {items:Item[];warnings:string[];directory_note:string;mode:string;calendars:{title:string;url:string}[]};
const TAGS=['basketball','sports','fitness','yoga','outdoor','hiking','frisbee','music','creative','photography','boardgames','tech','ai','coding','career','study','volunteer','community','food','culture','social','performance','research'];
export default function App(){
 const [started,setStarted]=useState(false);
 const [selected,setSelected]=useState<string[]>([]);
 const [query,setQuery]=useState('');
 const [live,setLive]=useState(false);
 const [loading,setLoading]=useState(false);
 const [error,setError]=useState('');
 const [result,setResult]=useState<Result|null>(null);
 const request=useRef<AbortController|null>(null);
 const visible=useMemo(()=>TAGS.filter(tag=>tag.includes(query.trim().toLowerCase())),[query]);
 const toggle=(tag:string)=>{setSelected(values=>values.includes(tag)?values.filter(v=>v!==tag):values.length<20?[...values,tag]:values);setResult(null);setError('');};
 async function mix(){
  const interests=selected.length?selected:[query.trim()].filter(Boolean);
  if(!interests.length){setError('Choose an interest or type one to start your blend.');return;}
  const controller=new AbortController();request.current?.abort();request.current=controller;
  setLoading(true);setError('');setResult(null);
  const timeout=setTimeout(()=>controller.abort(),12000);
  try{
   const response=await fetch('/api/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({interests,top_k:12,live_events:live}),signal:controller.signal});
   if(!response.ok)throw new Error(response.status===422?'Please use 1–20 interests, each under 60 characters.':'The server could not complete your blend. Please try again.');
   const data:Result=await response.json();
   if(request.current===controller)setResult(data);
  }catch(err){if(request.current===controller)setError(err instanceof Error&&err.name==='AbortError'?'The request timed out. Try again with live calendars turned off.':err instanceof Error?err.message:'Unable to connect to Blendin.');}
  finally{clearTimeout(timeout);if(request.current===controller)setLoading(false);}
 }
 function clear(){request.current?.abort();request.current=null;setSelected([]);setQuery('');setResult(null);setError('');setLoading(false);}
 if(!started)return <main className="welcome"><div className="welcome-card"><p className="eyebrow">A LITTLE CURIOSITY. A NEW CONNECTION.</p><img className="brand" src="/assets/blendin-title.png" alt="Blendin — Mix your interests. Find your place."/><p>Turn the things you love into somewhere to belong.<br/>A campus club, a local event, your next good afternoon.</p><button className="primary" onClick={()=>setStarted(true)}>Begin your blend <span aria-hidden="true">↗</span></button><p className="small">Made for William & Mary · A team hackathon project</p></div></main>;
 return <main className="workspace"><header><button className="wordmark" onClick={()=>{clear();setStarted(false)}}>Blendin<span>✳</span></button><span>Mix your interests. Find your place.</span><a href="https://devpost.com/software/project-5rayh1" target="_blank" rel="noreferrer">Our story ↗</a></header>
 <div className="builder"><section className="drink-scene" aria-label="Your interest blend"><div className="scene-copy"><p className="eyebrow">YOUR NEXT CONNECTION STARTS HERE</p><h1>A little of you.<br/>A whole new mix.</h1><p>Pick a few interests. We’ll find campus clubs<br/>and help you explore local events.</p></div><div className={`drink ${loading?'stirring':''}`} aria-label={`${selected.length} interests in your drink`}><div className="straw"/><div className="glass"><div className="liquid" style={{height:`${20+Math.min(selected.length,10)*6}%`}}/><div className="boba">● ● ●<br/> ● ● ●</div></div></div><div className="recipe">{selected.length?`${selected.length} ingredients, one unique blend`:'Your blend is waiting'}</div></section>
 <section className="ingredients"><p className="eyebrow">01 / CHOOSE YOUR INGREDIENTS</p><h2>What’s your flavor?</h2><p>Choose up to 20 interests, or type your own.</p><label htmlFor="interest">Find an interest</label><input id="interest" value={query} disabled={loading} maxLength={60} onChange={e=>setQuery(e.target.value)} placeholder="Try music, coding, hiking…"/>
 <div className="chips">{visible.map(tag=><button key={tag} disabled={loading} aria-pressed={selected.includes(tag)} onClick={()=>toggle(tag)}>{selected.includes(tag)?'✓ ': '+ '}{tag}</button>)}</div>
 {query.trim()&&!TAGS.includes(query.trim().toLowerCase())&&<button className="add" disabled={loading||selected.length>=20||selected.includes(query.trim().toLowerCase())} onClick={()=>{toggle(query.trim().toLowerCase());setQuery('')}}>+ Add “{query.trim()}”</button>}
 <div className="selected" aria-live="polite">{selected.length?`Your mix: ${selected.join(' · ')}`:'No ingredients selected yet.'}</div>
 <label className="check"><input type="checkbox" checked={live} disabled={loading} onChange={e=>{setLive(e.target.checked);setResult(null)}}/>Also check live event calendars</label><p className="hint">Club matching works offline. Live calendars need internet and may not return matches.</p>
 <div className="actions"><button className="primary" disabled={loading} onClick={mix}>{loading?'Mixing your interests…':'Mix my interests ↗'}</button><button className="clear" onClick={clear}>Clear</button></div>{error&&<p role="alert" className="notice error">{error}</p>}</section></div>
 <section className="results" aria-live="polite" aria-busy={loading}><div className="results-heading"><div><p className="eyebrow">02 / FIND YOUR PLACE</p><h2>Your discoveries</h2></div><span>{result?`${result.items.length} matches`:'A fresh mix of possibilities'}</span></div>
 {loading?<p className="empty">Blending your interests{live?' and checking live calendars':''}…</p>:!result?<p className="empty">Your next favorite place could start with one ingredient. Choose an interest above.</p>:<><p className="hint">{result.directory_note}</p>{result.warnings.map(w=><p className="notice" key={w}>{w}</p>)}{!result.items.length&&<p className="empty">No matches for this blend yet. Try a broader interest such as music, sports or coding.</p>}<div className="cards">{result.items.map(item=><article key={item.url}><span className="type">{item.type==='club'?'CAMPUS CLUB':'EVENT LISTING'}</span><h3><a href={item.url} target="_blank" rel="noopener noreferrer">{item.title} ↗</a></h3><p>{item.reason}</p><small>{item.source}</small></article>)}</div><div className="calendars">Explore the calendars directly: {result.calendars.map(c=><a key={c.url} href={c.url} target="_blank" rel="noreferrer">{c.title} ↗</a>)}</div></>}
 </section><footer>Made with curiosity, boba & a little teamwork. <span>Blendin · &hacks XI, 2025</span></footer></main>;
}
