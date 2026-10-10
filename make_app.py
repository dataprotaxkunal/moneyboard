#!/usr/bin/env python3
"""Moneyboard -> phone app (PWA). Usage:  python make_app.py index.html
Creates ./moneyboard-app/ with index.html, manifest, service worker and icons.
Nothing in your original file is removed; every web feature keeps working."""
import sys, os, re, zlib, struct, json

src = sys.argv[1] if len(sys.argv) > 1 else "index.html"
html = open(src, encoding="utf-8").read()
out = "moneyboard-app"; os.makedirs(out, exist_ok=True)

# ---------- icons (pure python PNG: teal gradient, white coin) ----------
def png(size, path):
    rows = []
    c = size / 2
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            t = (x + y) / (2 * size)
            r, g, b = int(20 + 0 * t), int(184 - 27 * t), int(166 + 59 * t)  # #14b8a6 -> #0ea5e9
            d = ((x - c) ** 2 + (y - c) ** 2) ** .5
            if size * .27 < d < size * .34 or (abs(x - c) < size * .035 and d < size * .27) or \
               (abs(y - c * .86) < size * .03 and abs(x - c) < size * .14) or (abs(y - c * 1.12) < size * .03 and abs(x - c) < size * .14):
                r = g = b = 255
            row += bytes((r, g, b))
        rows.append(bytes(row))
    raw = b"".join(rows)
    def ch(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b""))
for s in (192, 512): png(s, f"{out}/icon-{s}.png")

json.dump({
    "name": "Moneyboard", "short_name": "Moneyboard", "description": "Personal finance",
    "start_url": "./index.html", "scope": "./", "display": "standalone", "orientation": "portrait",
    "background_color": "#0c111d", "theme_color": "#0f766e",
    "icons": [{"src": f"icon-{s}.png", "sizes": f"{s}x{s}", "type": "image/png", "purpose": "any maskable"} for s in (192, 512)]
}, open(f"{out}/manifest.webmanifest", "w"), indent=2)

# ---------- service worker: app shell works offline, Firebase calls always go to network ----------
open(f"{out}/sw.js", "w").write("""const V='moneyboard-v1',SHELL=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(e.request.method!=='GET'||/firestore|identitytoolkit|securetoken|googleapis\\.com\\/(?!css)/.test(u.href))return;
  if(e.request.mode==='navigate'){e.respondWith(fetch(e.request).then(r=>{const c=r.clone();caches.open(V).then(x=>x.put('./index.html',c));return r}).catch(()=>caches.match('./index.html')));return}
  e.respondWith(caches.match(e.request).then(h=>h||fetch(e.request).then(r=>{if(r.ok){const c=r.clone();caches.open(V).then(x=>x.put(e.request,c))}return r})));
});""")

# ---------- head additions ----------
HEAD = """
  <link rel="manifest" href="manifest.webmanifest">
  <meta name="theme-color" content="#0f766e">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="Moneyboard">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="icon-192.png">
  <style id="mobile-css">
    html{-webkit-text-size-adjust:100%;-webkit-tap-highlight-color:transparent}
    body{overscroll-behavior-y:none}
    #bnav{display:none}
    @media(max-width:820px){
      body{font-size:14px}
      input,select,textarea,.input,.select,.textarea,.csel,.rl-in,.cell-in{font-size:16px!important}
      .input,.select{height:42px}.btn{height:40px}.btn-sm{height:34px}.icon-btn{width:38px;height:38px}
      .topbar{padding:env(safe-area-inset-top) 12px 0;height:calc(54px + env(safe-area-inset-top));gap:8px}
      .page-head h1{font-size:16px}
      .top-actions .btn-secondary{padding:0 10px}
      .top-actions .btn-secondary{font-size:0}.top-actions .btn-secondary svg{width:20px;height:20px}
      .content{padding:12px 12px calc(86px + env(safe-area-inset-bottom))}
      .sidebar{width:82%;max-width:300px;padding-top:env(safe-area-inset-top)}
      .stats{grid-template-columns:1fr 1fr;gap:10px}.stat-val{font-size:18px}
      .stat{padding:12px}
      .kstrip{grid-template-columns:1fr 1fr!important}
      .kstrip .k{padding:12px 14px}.k .kv{font-size:17px}
      .yoy-head{padding:10px}.tabs{width:100%;overflow-x:auto}.tabs button{flex:1;padding:0 10px 0 6px;white-space:nowrap;height:38px}
      .ovset{margin-left:0!important;width:100%}
      .ov3,.ov2,.grid-main{grid-template-columns:1fr!important}
      .summary{grid-template-columns:1fr 1fr;gap:10px}
      .acct-grid{grid-template-columns:1fr}
      .toolbar{padding:10px}.toolbar .select,.toolbar .tsearch{max-width:none;flex:1 1 140px;height:40px}
      .toolbar .right{margin-left:0}
      .card-head{padding:10px 12px}
      .table-wrap,.yt-wrap,.yr-wrap,.lt-wrap{-webkit-overflow-scrolling:touch}
      .t td.first{min-width:170px}
      .t td,.t th{padding:9px 10px}
      .yr-wrap .cf td{padding:8px 8px}
      .cf .lead,.yt th:first-child,.yt td:first-child{min-width:130px!important}
      .ytb{gap:6px}.ytb .leg{display:none}
      .drawer,.drawer.wide{width:100%;max-width:100%}
      .drawer-head{padding:calc(12px + env(safe-area-inset-top)) 16px 12px}
      .dform-body{grid-template-columns:1fr;padding:14px 16px}
      .dform-foot{padding:12px 16px calc(12px + env(safe-area-inset-bottom))}
      .dform-foot .btn{flex:1;justify-content:center}
      .map-grid{grid-template-columns:1fr 1fr}
      .menu{position:fixed;left:12px;right:12px;top:calc(60px + env(safe-area-inset-top));width:auto}
      .toast{bottom:calc(86px + env(safe-area-inset-bottom))}
      #login{display:block}.login-form{min-height:100vh;padding:calc(24px + env(safe-area-inset-top)) 20px}
      #bnav{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:35;background:rgba(255,255,255,.96);backdrop-filter:blur(12px);
        border-top:1px solid var(--border);padding:6px 4px calc(6px + env(safe-area-inset-bottom))}
      #bnav button{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;font-size:10.5px;font-weight:600;color:var(--muted);padding:4px 0;border-radius:10px;position:relative}
      #bnav button.on{color:var(--brand)}
      #bnav button.on::before{content:"";position:absolute;top:-7px;width:26px;height:3px;border-radius:3px;background:var(--brand)}
      #bnav .bdg{position:absolute;top:0;right:22%;min-width:16px;height:16px;border-radius:9px;background:var(--red);color:#fff;font-size:10px;display:grid;place-items:center;padding:0 4px}
    }
  </style>
"""
html = html.replace('<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                    '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">', 1)
html = html.replace("</head>", HEAD + "</head>", 1)

# offline data cache for Firestore (works offline, syncs when back online)
html = html.replace("const db = firebase.firestore();",
    "const db = firebase.firestore();\ntry{db.enablePersistence({synchronizeTabs:true}).catch(()=>{})}catch(e){}", 1)

# ---------- body additions: bottom tab bar, back-button, install, SW ----------
BODY = """
<nav id="bnav">
  <button data-v="overview" onclick="go('overview')"><span data-ic="grid"></span>Home</button>
  <button data-v="accounts" onclick="go('accounts')"><span data-ic="bank"></span>Accounts</button>
  <button data-v="txns" onclick="go('txns')"><span data-ic="list"></span>Txns<i class="bdg hidden" id="bTx"></i></button>
  <button data-v="year" onclick="go('year')"><span data-ic="table"></span>I&amp;E</button>
  <button data-v="more" onclick="openSidebar()"><span data-ic="menu"></span>More</button>
</nav>
<script>
(function(){
  document.querySelectorAll('#bnav [data-ic]').forEach(e=>e.innerHTML=ic(e.dataset.ic,22));
  function sync(){
    document.querySelectorAll('#bnav button').forEach(b=>b.classList.toggle('on',b.dataset.v===view));
    const n=txns.filter(t=>groupOf(t.category)==='none').length, b=document.getElementById('bTx');
    b.textContent=n>99?'99+':n; b.classList.toggle('hidden',!n);
    document.getElementById('bnav').style.display = currentUser ? '' : 'none';
  }
  const _go=window.go; window.go=function(v){ _go(v); sync(); };
  const _rv=window.renderView; window.renderView=function(){ _rv(); sync(); };
  // Android back button / iOS swipe-back closes the drawer or menu instead of leaving the app
  const _od=window.openDrawer, _cd=window.closeDrawer;
  window.openDrawer=function(a,b,c){ _od(a,b,c); if(!(history.state&&history.state.mb)) history.pushState({mb:1},''); };
  window.closeDrawer=function(){ _cd(); if(history.state&&history.state.mb) history.back(); };
  window.addEventListener('popstate',()=>{ _cd(); if(typeof closeSidebar==='function') closeSidebar(); });
  // service worker + install prompt
  if('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js').catch(()=>{});
  let ev; window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();ev=e;
    const b=document.createElement('button'); b.className='btn btn-primary btn-sm'; b.textContent='Install app';
    b.onclick=()=>{ev.prompt();b.remove()}; const ta=document.querySelector('.top-actions'); if(ta) ta.prepend(b);});
})();
</script>
"""
html = html.replace("</body>", BODY + "</body>", 1)
open(f"{out}/index.html", "w", encoding="utf-8").write(html)
print(f"Done -> {out}/  ({len(html)//1024} KB). Host it over HTTPS, then 'Add to Home screen'.")
