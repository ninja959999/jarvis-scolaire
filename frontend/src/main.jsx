import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? "/backend" : "http://127.0.0.1:8000");
const formatTime = (value) => new Date(value).toLocaleTimeString("fr-FR", {hour:"2-digit", minute:"2-digit"});
const formatDate = (value) => new Date(value).toLocaleDateString("fr-FR", {day:"2-digit", month:"short"});

function Card({title, action, children}) { return <section className="card"><div className="card-head"><h2>{title}</h2>{action}</div>{children}</section> }

function App() {
  const [data, setData] = useState(null); const [log, setLog] = useState(null); const [error, setError] = useState(""); const [showReminder, setShowReminder] = useState(false); const [saving, setSaving] = useState(false);
  const load = async () => { try { const [d,l] = await Promise.all([fetch(`${API}/api/dashboard`), fetch(`${API}/api/logs/today`)]); if(!d.ok) throw Error("API indisponible"); setData(await d.json()); setLog(await l.json()); } catch(e) { setError("L’API n’est pas démarrée. Lance d’abord le backend FastAPI."); } };
  useEffect(() => { load(); }, []);
  const complete = async (kind, id) => { await fetch(`${API}/api/${kind}/${id}/complete`, {method:"PATCH"}); load(); };
  const toggleLog = async (field) => { const next = {...log, [field]: !log[field]}; setLog(next); await fetch(`${API}/api/logs/today`, {method:"PATCH", headers:{"Content-Type":"application/json"}, body:JSON.stringify({[field]:next[field]})}); };
  const addReminder = async (event) => { event.preventDefault(); setSaving(true); const form = new FormData(event.currentTarget); const response = await fetch(`${API}/api/reminders`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({title:form.get("title"), trigger_time:new Date(form.get("trigger_time")).toISOString(), category:form.get("category")})}); setSaving(false); if (!response.ok) { setError("Impossible de créer le rappel."); return; } setShowReminder(false); event.currentTarget.reset(); load(); };
  if(error) return <main className="shell"><header><div className="logo">J</div><div><h1>JARVIS</h1><p>Ton deuxième cerveau</p></div></header><div className="error">{error}<br/><small>API attendue : {API}</small></div></main>;
  if(!data || !log) return <main className="shell"><div className="loading">Initialisation de JARVIS…</div></main>;
  return <main className="shell">
    <header><div className="logo">J</div><div><h1>Bonjour, {data.user.name}</h1><p>{new Date().toLocaleDateString("fr-FR", {weekday:"long", day:"numeric", month:"long"})}</p></div><button className="refresh" onClick={load}>↻</button></header>
    <div className="hero"><div><span className="eyebrow">BRIEFING DU JOUR</span><h2>On garde le cap.</h2><p>{data.homeworks.length} devoir{data.homeworks.length > 1 ? "s" : ""} à traiter et {data.timetable.length} cours prévu{data.timetable.length > 1 ? "s" : ""} aujourd’hui.</p></div><div className="sun">☀️</div></div>
    <div className="grid">
      <Card title="Emploi du temps"><div className="timeline">{data.timetable.length ? data.timetable.map(x=><div className={`timeline-item ${x.is_cancelled?"cancelled":""}`} key={x.id}><b>{formatTime(x.start_time)}</b><span><strong>{x.subject}</strong><small>{x.room || "Salle à confirmer"}</small></span>{x.is_cancelled && <em>Annulé</em>}</div>) : <p className="muted">Aucun cours aujourd’hui.</p>}</div></Card>
      <Card title="Priorités" action={<span className="count">{data.homeworks.length}</span>}><div className="tasks">{data.homeworks.length ? data.homeworks.map(x=><label className="task" key={x.id}><input type="checkbox" onChange={()=>complete("homeworks",x.id)}/><span><strong>{x.subject}</strong><small>{x.description}</small></span><em>{formatDate(x.due_date)}</em></label>) : <p className="muted">Tout est terminé 🎉</p>}</div></Card>
      <Card title="Checklist du soir"><label className="check"><input type="checkbox" checked={!!log.bag_prepared} onChange={()=>toggleLog("bag_prepared")}/><span>Préparer le sac</span></label><label className="check"><input type="checkbox" checked={!!log.clothes_prepared} onChange={()=>toggleLog("clothes_prepared")}/><span>Préparer les vêtements</span></label><label className="check"><input type="checkbox" checked={!!log.sport_done} onChange={()=>toggleLog("sport_done")}/><span>Séance de sport</span></label></Card>
      <Card title="Rappels" action={<button className="add" onClick={()=>setShowReminder(true)}>+</button>}>{data.reminders.length ? data.reminders.map(x=><label className="task" key={x.id}><input type="checkbox" onChange={()=>complete("reminders",x.id)}/><span><strong>{x.title}</strong><small>{formatTime(x.trigger_time)} · {x.category}</small></span></label>) : <p className="muted">Aucun rappel en attente.</p>}</Card>
    </div>
    <footer>JARVIS v0.2 · Données synchronisées · <a href={`${API}/docs`} target="_blank">API</a></footer>
    {showReminder && <div className="modal-backdrop" onClick={()=>setShowReminder(false)}><form className="modal card" onSubmit={addReminder} onClick={e=>e.stopPropagation()}><div className="card-head"><h2>Nouveau rappel</h2><button type="button" className="add" onClick={()=>setShowReminder(false)}>×</button></div><label className="field">Titre<input name="title" required maxLength="255" placeholder="Ex. Réviser les maths" /></label><label className="field">Date et heure<input name="trigger_time" required type="datetime-local" /></label><label className="field">Catégorie<select name="category"><option>PERSO</option><option>ÉCOLE</option><option>SPORT</option></select></label><button className="primary" disabled={saving}>{saving ? "Enregistrement…" : "Ajouter le rappel"}</button></form></div>}
  </main>;
}
createRoot(document.getElementById("root")).render(<App/>);
