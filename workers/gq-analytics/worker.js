/**
 * GQ Analytics Dashboard Worker
 *
 * Serves the dashboard HTML at / and proxies API requests to the
 * Render backend at /api/* — adding permissive CORS headers so the
 * browser can fetch data cross-origin without Render config changes.
 */

const RENDER_API = 'https://gentlequest.onrender.com';

// Dashboard HTML (inline so we don't need a separate KV or binding)
const DASHBOARD_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GentleQuest Analytics</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0a;color:#e0e0e0;padding:40px 20px;min-height:100vh}
.container{max-width:1000px;margin:0 auto}
h1{font-size:24px;font-weight:600;margin-bottom:4px}
h2{font-size:15px;font-weight:600;color:#ccc;margin-bottom:16px}
.subtitle{color:#888;font-size:13px;margin-bottom:32px}
.filter-badge{display:inline-block;padding:2px 8px;background:#1a3a1a;color:#4a4;border-radius:4px;font-size:11px;margin-left:8px}
.section{margin-bottom:40px}
.funnel-stages{display:flex;flex-direction:column;gap:8px}
.stage{display:flex;align-items:center;gap:16px;padding:20px 24px;background:#141414;border-radius:12px;border:1px solid #222;transition:border-color .2s}
.stage:hover{border-color:#333}
.stage-number{font-size:11px;color:#666;width:24px;text-align:right}
.stage-name{font-size:15px;flex:1}
.stage-value{font-size:28px;font-weight:700;color:#fff;font-variant-numeric:tabular-nums}
.stage-detail{font-size:12px;color:#888;margin-left:8px}
.stage-bar{height:4px;background:#4a8;border-radius:2px;margin-top:8px;transition:width .5s}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.stat-card{padding:16px 20px;background:#141414;border-radius:10px;border:1px solid #222}
.stat-label{font-size:11px;color:#666;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.stat-value{font-size:22px;font-weight:600;font-variant-numeric:tabular-nums}
.stat-sub{font-size:11px;color:#666;margin-top:2px}
.chart-container{background:#141414;border-radius:12px;border:1px solid #222;padding:24px}
.chart-title{font-size:14px;font-weight:600;margin-bottom:16px;color:#ccc}
canvas{width:100%!important;height:200px!important}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:700px){.two-col{grid-template-columns:1fr}}
.events-list{background:#141414;border-radius:12px;border:1px solid #222;padding:16px 20px;max-height:300px;overflow-y:auto}
.event-row{display:flex;gap:12px;padding:8px 0;border-bottom:1px solid #1a1a1a;font-size:13px}
.event-row:last-child{border-bottom:none}
.event-time{color:#666;font-variant-numeric:tabular-nums;white-space:nowrap;min-width:140px}
.event-type{color:#aaa;font-family:monospace;font-size:12px}
.event-meta{color:#555;font-size:12px;margin-left:auto;text-align:right}
.trend-bars{display:flex;gap:4px;align-items:flex-end;height:60px;margin-top:12px}
.trend-bar{flex:1;background:#333;border-radius:3px 3px 0 0;min-height:2px;position:relative;transition:background .2s}
.trend-bar.active{background:#4a8}
.trend-bar:hover{background:#5b9}
.trend-bar-label{position:absolute;bottom:-18px;left:50%;transform:translateX(-50%);font-size:9px;color:#555}
.intervention-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}
.intervention-card{padding:16px 20px;background:#141414;border-radius:10px;border:1px solid #222}
.intervention-card .name{font-size:14px;font-weight:600;margin-bottom:8px}
.intervention-card .stat{font-size:12px;color:#888;margin-top:4px}
.intervention-card .value{font-size:20px;font-weight:600;color:#4a8}
.footer{margin-top:40px;padding-top:20px;border-top:1px solid #222;font-size:12px;color:#555;display:flex;justify-content:space-between}
.loading{opacity:.5}
.error{padding:16px;background:#2a1414;border:1px solid #5a2222;border-radius:8px;color:#e88;font-size:13px;margin-bottom:20px}
.empty{color:#555;font-size:13px;padding:20px 0}
.refresh-btn{padding:6px 14px;background:#222;color:#ccc;border:1px solid #333;border-radius:6px;cursor:pointer;font-size:13px;transition:background .2s}
.refresh-btn:hover{background:#2a2a2a}
</style>
</head>
<body>
<div class="container">
<div style="display:flex;justify-content:space-between;align-items:center">
<h1>GentleQuest Analytics <span class="filter-badge">real devices only</span></h1>
<button class="refresh-btn" onclick="refresh()">🔄 Refresh</button>
</div>
<p class="subtitle" id="subtitle">Loading...</p>
<div id="error" style="display:none" class="error"></div>
<div class="section"><h2>Funnel (last 90 days)</h2><div class="funnel-stages" id="funnel"></div></div>
<div class="section"><h2>Key metrics</h2><div class="stats-grid" id="stats"></div></div>
<div class="two-col section">
<div class="chart-container"><div class="chart-title">Installs trend (30 snapshots)</div><canvas id="chart-installs"></canvas></div>
<div class="chart-container"><div class="chart-title">First chat sent (7-day)</div><div class="trend-bars" id="trend-bars"></div><div style="margin-top:24px;font-size:12px;color:#666" id="trend-summary"></div></div>
</div>
<div class="two-col section">
<div><h2>Interventions (30 days)</h2><div class="stats-grid" id="intervention-stats" style="margin-bottom:16px"></div><div class="intervention-grid" id="interventions-grid"></div></div>
<div><h2>Recent events</h2><div class="events-list" id="events-list"></div></div>
</div>
<div class="footer"><span id="last-fetch">—</span><span>Auto-refresh: 60 seconds</span></div>
</div>
<script>
const API=window.location.origin;
async function fetchAll(){
  const[f,h,o,t,r]=await Promise.all([
    fetch(API+'/api/metrics/funnel'),
    fetch(API+'/api/metrics/funnel/history?limit=30'),
    fetch(API+'/api/analytics/overview?days=30'),
    fetch(API+'/api/metrics/true'),
    fetch(API+'/api/analytics/recent?limit=15')
  ]);
  return{funnel:await f.json(),history:await h.json(),overview:await o.json(),trueMetrics:await t.json(),recent:await r.json()}
}
function render(d){
  const{funnel,history,overview,trueMetrics,recent}=d;
  document.getElementById('subtitle').textContent='Last 90 days · simulator-filtered · '+funnel.blocked_test_sessions+' test sessions excluded';
  const s=funnel.funnel,inst=s.stage_2_installs||{},ti=(inst.iOS||0)+(inst.Android||0),wv=s.stage_1_web_visits,ao=s.stage_3_app_opens||0,fc=s.stage_4_first_chat||0;
  const fs=[{num:1,name:'Web visits',value:wv===null?'—':wv,detail:'gentlequest.app + /blog'},{num:2,name:'App installs',value:ti,detail:'iOS '+(inst.iOS||0)+' · Android '+(inst.Android||0)},{num:3,name:'App opens',value:ao,detail:'last 90 days'},{num:4,name:'First chat sent',value:fc,detail:'real users (test excluded)'}];
  const mv=Math.max(...fs.map(s=>typeof s.value==='number'?s.value:0),1);
  document.getElementById('funnel').innerHTML=fs.map(s=>{const p=typeof s.value==='number'?(s.value/mv*100):0;return '<div class="stage"><div class="stage-number">'+s.num+'</div><div class="stage-name">'+s.name+'<span class="stage-detail">'+s.detail+'</span><div class="stage-bar" style="width:'+p+'%"></div></div><div class="stage-value">'+s.value+'</div></div>'}).join('');
  const at=funnel.all_time||{},ai=at.installs||{},at2=at.total_users||{},ac=funnel.active_users_90d||{},att=(ai.iOS||0)+(ai.Android||0),act=(ac.iOS||0)+(ac.Android||0);
  const st=[{label:'All-time installs',value:att,sub:'iOS '+(ai.iOS||0)+' · Android '+(ai.Android||0)},{label:'All-time users',value:(at2.iOS||0)+(at2.Android||0),sub:'iOS '+(at2.iOS||0)+' · Android '+(at2.Android||0)},{label:'Active (90d)',value:act,sub:'iOS '+(ac.iOS||0)+' · Android '+(ac.Android||0)},{label:'First chat (all-time)',value:trueMetrics.all_time,sub:(trueMetrics.yesterday)+' yesterday'}];
  document.getElementById('stats').innerHTML=st.map(s=>'<div class="stat-card"><div class="stat-label">'+s.label+'</div><div class="stat-value">'+s.value+'</div><div class="stat-sub">'+s.sub+'</div></div>').join('');
  const t7=trueMetrics.trend_7d||[],mt=Math.max(...t7.map(d=>d.count),1);
  document.getElementById('trend-bars').innerHTML=t7.map(d=>{const h=(d.count/mt*100);return '<div class="trend-bar '+(d.count>0?'active':'')+'" style="height:'+Math.max(h,3)+'%" title="'+d.date+': '+d.count+'"><div class="trend-bar-label">'+d.date.slice(5)+'</div></div>'}).join('');
  document.getElementById('trend-summary').textContent=t7.reduce((a,d)=>a+d.count,0)+' first chats in last 7 days';
  const ov=overview.overall||{},is=[{label:'Total interventions',value:ov.total_interventions||0,sub:'last 30 days'},{label:'Completion rate',value:(ov.completion_rate*100).toFixed(0)+'%',sub:(ov.total_completed||0)+' completed'},{label:'Avg mood improvement',value:(ov.avg_mood_improvement||0).toFixed(1),sub:'1-10 scale'},{label:'Avg time spent',value:Math.round(ov.avg_time_spent||0)+'s',sub:'per exercise'}];
  document.getElementById('intervention-stats').innerHTML=is.map(s=>'<div class="stat-card"><div class="stat-label">'+s.label+'</div><div class="stat-value">'+s.value+'</div><div class="stat-sub">'+s.sub+'</div></div>').join('');
  const bt=overview.by_type||{},ic={breathing:'🌬️',grounding:'🌿',journaling:'📝'};
  if(Object.keys(bt).length===0){document.getElementById('interventions-grid').innerHTML='<div class="empty">No intervention data yet.</div>'}else{document.getElementById('interventions-grid').innerHTML=Object.entries(bt).map(([t,s])=>{const r=(s.completion_rate*100).toFixed(0),m=s.avg_mood_improvement?.toFixed(1)||'N/A';return '<div class="intervention-card"><div class="name">'+(ic[t]||'📋')+' '+t+'</div><div class="value">'+r+'%</div><div class="stat">completion · '+(s.total_interventions||0)+' total</div><div class="stat">mood delta: '+m+'</div></div>'}).join('')}
  const evts=recent.events||[];
  if(evts.length===0){document.getElementById('events-list').innerHTML='<div class="empty">No recent events.</div>'}else{document.getElementById('events-list').innerHTML=evts.map(e=>{const ts=e.timestamp?new Date(e.timestamp).toLocaleString('en-US',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'—';const m=e.metadata||{},ms=Object.entries(m).slice(0,2).map(([k,v])=>k+'='+v).join(', ');return '<div class="event-row"><span class="event-time">'+ts+'</span><span class="event-type">'+e.event_type+'</span><span class="event-meta">'+ms+'</span></div>'}).join('')}
  renderChart(history);
  document.getElementById('last-fetch').textContent='Updated '+new Date(funnel.timestamp).toLocaleString();
}
function renderChart(h){
  const c=document.getElementById('chart-installs'),ctx=c.getContext('2d'),sn=(h.snapshots||[]).reverse();
  if(sn.length<2){ctx.fillStyle='#555';ctx.font='13px sans-serif';ctx.textAlign='center';ctx.fillText('Not enough snapshots yet',c.offsetWidth/2,100);return}
  const dpr=window.devicePixelRatio||1,w=c.offsetWidth,hh=200;c.width=w*dpr;c.height=hh*dpr;ctx.scale(dpr,dpr);
  const p={top:20,right:20,bottom:30,left:40},cw=w-p.left-p.right,ch=hh-p.top-p.bottom;
  const pts=sn.map(s=>{const d=s.data||{},i=d.installs_90d||{};return{date:(s.created_at||'').slice(0,10),ios:i.iOS||0,android:i.Android||0,total:(i.iOS||0)+(i.Android||0)}}),mv=Math.max(...pts.map(p=>p.total),1),sx=cw/Math.max(pts.length-1,1);
  ctx.strokeStyle='#1a1a1a';ctx.lineWidth=1;for(let i=0;i<=4;i++){const y=p.top+(ch/4)*i;ctx.beginPath();ctx.moveTo(p.left,y);ctx.lineTo(p.left+cw,y);ctx.stroke()}
  ctx.fillStyle='#555';ctx.font='10px sans-serif';ctx.textAlign='right';for(let i=0;i<=4;i++){ctx.fillText(Math.round(mv-(mv/4)*i),p.left-6,p.top+(ch/4)*i+3)}
  ctx.strokeStyle='#6a9';ctx.lineWidth=2;ctx.beginPath();pts.forEach((p,i)=>{const x=p.left+sx*i,y=p.top+ch-(p.ios/mv)*ch;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke();
  ctx.strokeStyle='#e95';ctx.lineWidth=2;ctx.beginPath();pts.forEach((p,i)=>{const x=p.left+sx*i,y=p.top+ch-(p.android/mv)*ch;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke();
  ctx.strokeStyle='#4a8';ctx.lineWidth=2;ctx.beginPath();pts.forEach((p,i)=>{const x=p.left+sx*i,y=p.top+ch-(p.total/mv)*ch;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke();
  ctx.fillStyle='#4a8';pts.forEach((p,i)=>{const x=p.left+sx*i,y=p.top+ch-(p.total/mv)*ch;ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fill()});
  ctx.fillStyle='#555';ctx.textAlign='center';[0,Math.floor(pts.length/2),pts.length-1].forEach(i=>{if(pts[i]){ctx.fillText(pts[i].date,p.left+sx*i,hh-10)}});
  ctx.font='11px sans-serif';ctx.textAlign='left';ctx.fillStyle='#6a9';ctx.fillText('● iOS',p.left+10,p.top+12);ctx.fillStyle='#e95';ctx.fillText('● Android',p.left+60,p.top+12);ctx.fillStyle='#4a8';ctx.fillText('● Total',p.left+130,p.top+12);
}
async function refresh(){try{document.getElementById('error').style.display='none';const d=await fetchAll();render(d)}catch(err){document.getElementById('error').textContent='Failed to load: '+err.message;document.getElementById('error').style.display='block'}}
refresh();setInterval(refresh,60000);
</script>
</body>
</html>`;

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // Serve dashboard HTML at root
    if (url.pathname === '/' || url.pathname === '/index.html') {
      return new Response(DASHBOARD_HTML, {
        headers: { 'Content-Type': 'text/html; charset=utf-8' },
      });
    }

    // Proxy /api/* to Render backend
    if (url.pathname.startsWith('/api/')) {
      const targetUrl = RENDER_API + url.pathname + url.search;
      try {
        const resp = await fetch(targetUrl, {
          method: request.method,
          headers: { 'Accept': 'application/json' },
        });
        const body = await resp.text();
        return new Response(body, {
          status: resp.status,
          headers: {
            'Content-Type': resp.headers.get('Content-Type') || 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': '*',
            'Cache-Control': 'no-cache',
          },
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: 'Proxy failed: ' + err.message }), {
          status: 502,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        });
      }
    }

    // 404 for everything else
    return new Response('Not found', { status: 404 });
  },
};
