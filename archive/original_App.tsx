import React, { useMemo, useState } from "react";

type Item = {
  type: "event" | "club" | "suggestion";
  title: string;
  url: string;
  score?: number;
  reason?: string;
};

const ALL_TAGS = [
  "basketball","sports","fitness","yoga","wellness","outdoor",
  "hiking","frisbee","music","creative","photography","boardgames",
  "strategy","tech","ai","coding","career","study","volunteer",
  "community","food","culture","social","chill","performance","research"
];

export default function App() {
  const [selected, setSelected] = useState<string[]>([]);
  const [filter, setFilter] = useState("");
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|undefined>();

  const shownTags = useMemo(() => {
    const f = filter.trim().toLowerCase();
    return ALL_TAGS.filter(t => !f || t.includes(f));
  }, [filter]);

  function toggleTag(tag: string) {
    setSelected(prev => prev.includes(tag) ? prev.filter(t => t!==tag) : [...prev, tag]);
  }

  async function recommend() {
    setLoading(true); setError(undefined);
    try {
      const res = await fetch("http://localhost:5000/recommend", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ interests: selected.length ? selected : [filter].filter(Boolean), top_k: 12 })
      });
      const data = await res.json();
      setItems(data.items || []);
    } catch (e:any) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  const liquidHeight = Math.min((selected.length / ALL_TAGS.length) * 200, 180); // Adjust to fit glass height

  return (
    <div style={{height: "1200px", width: "1200px", margin: "0 auto", position: "relative", overflow: "auto"}}>
      <style>{`
        @keyframes stir {
          0% { transform: rotate(0deg); }
          25% { transform: rotate(5deg); }
          50% { transform: rotate(0deg); }
          75% { transform: rotate(-5deg); }
          100% { transform: rotate(0deg); }
        }
        .stirring {
          animation: stir 1s ease-in-out infinite;
        }
        .liquid {
          background: linear-gradient(to bottom, #87ceeb, #4682b4);
          border-bottom-left-radius: 20px;
          border-bottom-right-radius: 20px;
          transition: height 0.5s ease;
        }
      `}</style>
      {/* Background scene */}
      <img src="/assets/background.png" alt="Desk scene with eagle and plant" style={{position: "absolute", top: 0, left: 0, width: "100%", height: "auto", zIndex: -1}} />

      {/* Title banner */}
      <img src="/assets/blendin-title.png" alt="BLEND IN - Mix your interests. Find your place" style={{position: "absolute", top: -150, left: 10, width: 600}} />

      <div style={{margin: "0 auto", padding: "0px 24px 24px", display: "flex", justifyContent: "space-between", alignItems: "flex-start"}}>
        {/* Left side: Glass positioned on the doily in the scene */}
        <div style={{flex: 1, position: "relative", top: 550, height: 400, display: "flex", justifyContent: "center", alignItems: "flex-end"}}>
          {/* Empty glass as base */}
          <div style={{position: "relative", left:-20, top:-220,width: 200, height: 300, overflow: "hidden", className: loading ? "stirring" : ""}}>
            <img src="/assets/empty-glass.png" alt="Empty glass" style={{position: "relative", top:-200, left:-100, width: "300%", height: "150%"}} />
            {/* Liquid overlay */}
            <div className="liquid" style={{position: "absolute", bottom: 115, left: 65, width: "calc(100% - 120px)", height: `${liquidHeight}px`, zIndex: -1}}></div>
          </div>
        </div>

        {/* Right side: Ingredients panel */}
        <div style={{width: 400, position: "relative", marginLeft: -50}}>
          <img src="/assets/ingredients-panel.png" alt="Ingredients panel" style={{position:"absolute", right: 5,  width: "150%",  height: "auto"}} />
          <div style={{position: "absolute", top: 120, left: -10, bottom: 20, width:"400px"}}>
            
            <input value={filter} onChange={e=>setFilter(e.target.value)}
                   placeholder="e.g., basketball / AI / music"
                   style={{width: "70%", padding:"8px 10px", borderRadius:10, border:"none", background:"#fff5e1", color:"#4a2c2a", marginBottom: 12}}/>
            
            <div style={{display:"flex", flexWrap:"wrap", gap:8, maxHeight: 500, position: "absolute", width: "300px", overflowY: "auto"}}>
              {shownTags.map(tag=>{
                const on = selected.includes(tag);
                return (
                  <button key={tag}
                    onClick={()=>toggleTag(tag)}
                    style={{
                      borderRadius: 999, padding:"6px 10px", border:"1px solid #8b4513",
                      background: on? "#cd853f":"#fff5e1", color: on ? "#fff5e1" : "#4a2c2a", cursor:"pointer"
                    }}
                  >{tag}</button>
                );
              })}
            </div>

            <div style={{marginTop:12, display:"flex", gap:8, justifyContent: "center"}}>
              <button onClick={()=>{ setSelected([]); setFilter(""); setItems([]);}}
                      style={{position:"absolute", top:350, left:10, padding:"8px 10px", borderRadius:10, border:"1px solid #8b4513", background:"#fff5e1", color:"#4a2c2a"}}>Clear</button>
              <img src="/assets/mix-button.png" alt="Mix" onClick={recommend} style={{position:"absolute", left:30, top:260, width:"80%", cursor: "pointer"}} />
            </div>
            <div style={{textAlign: "center", opacity:0, marginTop: 8, color: "#fff5e1"}}>Selected {selected.length}</div>
          </div>
        </div>
      </div>

      {/* Recommendations below */}
      <div style={{position:"relative", top:200, margin:"0 auto", padding: "0 24px 24px"}}>
        <div style={{background:"#d2b48c", border:"4px solid #8b4513", borderRadius: 20, padding:16}}>
          <div style={{display:"flex", alignItems:"center", justifyContent:"space-between", color: "#fff5e1"}}>
            <div style={{fontWeight:700}}>Recommendations</div>
            <div style={{opacity:0.7, fontSize:12}}>{items.length} result(s)</div>
          </div>
          {error && <div style={{marginTop:10, padding:10, borderRadius:10, background:"rgba(255,0,0,0.2)", border:"1px solid rgba(255,0,0,0.5)", color: "#fff5e1"}}>{error}</div>}
          <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:12, marginTop:12}}>
            {items.map((it, idx)=> (
              <div key={idx} style={{border:"1px solid #8b4513", background:"#fff5e1", borderRadius:12, padding:12, color: "#4a2c2a"}}>
                <div style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
                  <div>
                    <div style={{fontWeight:700}}>{it.type.toUpperCase()}</div>
                    <a href={it.url} target="_blank" rel="noreferrer" style={{color:"#cd853f", textDecoration:"underline"}}>{it.title}</a>
                  </div>
                  {typeof it.score === "number" && <div style={{opacity:0.8}}>score: {it.score?.toFixed?.(2)}</div>}
                </div>
                {it.reason && <div style={{marginTop:6, opacity:0.85, fontSize:12}}>{it.reason}</div>}
              </div>
            ))}
            {items.length === 0 && <div style={{opacity:0.75, color: "#fff5e1", textAlign: "center"}}>No results yet. Add some keywords and click “Mix”.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}