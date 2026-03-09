"""
Mercado Público API - Con Notificaciones SMTP
"""
from fastapi import FastAPI, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, RedirectResponse
import re
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = FastAPI(title="Mercado Público API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Configuración SMTP
SMTP_EMAIL = "cvergarach@gmail.com"
SMTP_PASSWORD = "iosdcyucvncioibj"  # App password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Archivos
DATA_FILE = "/Users/einstein/.openclaw/workspace/mercado-publico-scraper/alertas.json"

def cargar_alertas():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"alertas": []}

def guardar_alertas(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def enviar_email(destinatario, asunto, mensaje):
    """Envía email por SMTP"""
    try:
        msg = MIMEText(mensaje, 'html', 'utf-8')
        msg['Subject'] = asunto
        msg['From'] = SMTP_EMAIL
        msg['To'] = destinatario
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False

# Browser
browser = None
playwright = None

def get_browser():
    global browser, playwright
    if not browser:
        from playwright.sync_api import sync_playwright
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=False)
    return browser

def buscar_en_mercado():
    br = get_browser()
    page = br.new_page()
    url = "https://buscador.mercadopublico.cl/compra-agil?status=2&order_by=recent&page_number=1&region=all"
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(4000)
    html = page.content()
    page.close()
    return html

def parsear_resultados(html):
    resultados = []
    ui_texts = ['Buscar Compra', 'Filtrar por', 'Estado', 'Región', 'Presupuesto', 'Organismo']
    codigos = re.findall(r'(\d{4,5}-\d{1,3}-COT\d{2})', html)
    presupuestos = re.findall(r'\$\s*([\d.]+)', html)
    blocks = re.findall(r'<h4[^>]*>([^<]+)</h4>', html)
    titulos_limpios = [t.strip()[:100] for t in blocks if t.strip() and len(t.strip()) > 5 and not any(ui in t for ui in ui_texts)]
    orgs = []
    for match in re.findall(r'<p[^>]*>([^<]{15,150})</p>', html):
        text = match.strip()
        if any(ui in text for ui in ui_texts):
            continue
        if any(k in text.upper() for k in ['MUNICIPALIDAD', 'HOSPITAL', 'UNIVERSIDAD', 'DEFENSORIA', 'INSTITUTO', 'EJERCITO', 'FUERZAS', 'DIRECCION', 'CORP', 'SERVICIO', 'CENTRO', 'ABASTECIMIENTO', 'MINISTERIO']):
            orgs.append(text[:100])
    fechas_pub = re.findall(r'Publicada el\s*(\d{2}/\d{2}/\d{4})', html)
    fechas_cierre = re.findall(r'Finaliza el\s*(\d{2}/\d{2}/\d{4})', html)
    
    for i in range(min(len(codigos), 20)):
        resultados.append({
            "codigo": codigos[i] if i < len(codigos) else "",
            "titulo": titulos_limpios[i] if i < len(titulos_limpios) else "",
            "organismo": orgs[i] if i < len(orgs) else "",
            "presupuesto": presupuestos[i] if i < len(presupuestos) else "0",
            "fecha_pub": fechas_pub[i] if i < len(fechas_pub) else "",
            "fecha_cierre": fechas_cierre[i] if i < len(fechas_cierre) else ""
        })
    return resultados

# ============== RUTAS ==============

@app.get("/")
def root():
    return Response(content="""<h1>🏛️ Mercado Público API</h1>
<p><a href="/web">Buscador</a> | <a href="/admin">Admin</a></p>""", media_type="text/html")

@app.get("/web")
def web():
    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Mercado Público Chile</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body{background:linear-gradient(135deg,#1e3c72,#2a5298);min-height:100vh;font-family:'Segoe UI',sans-serif}
.navbar{background:rgba(255,255,255,0.95)}
.card{background:white;border:none;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.1)}
.search-box{background:white;border-radius:16px;padding:25px;margin-top:20px}
.form-control{border-radius:10px;padding:12px}
.btn-search{background:linear-gradient(135deg,#1e3c72,#2a5298);color:white;border:none;padding:12px 30px;border-radius:10px}
.result-card{border-radius:12px;margin-bottom:15px}
.codigo{color:#2a5298;font-weight:700}
.titulo{color:#333;margin:8px 0}
.organismo{color:#666;font-size:13px}
.presupuesto{color:#27ae60;font-weight:700}
.stat-card{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border-radius:12px;padding:20px}
</style>
</head>
<body>
<nav class="navbar">
<div class="container">
<a class="navbar-brand" href="/web">Mercado Público</a>
<a href="/admin" class="btn btn-outline-primary btn-sm">Admin</a>
</div>
</nav>
<div class="container pb-5">
<div class="search-box">
<div class="row">
<div class="col-md-9">
<input type="text" id="q" class="form-control" placeholder="Buscar: hormigon, agua, medicamentos..." onkeyup="if(event.key=='Enter')buscar()">
</div>
<div class="col-md-3">
<button class="btn btn-search w-100" onclick="buscar()">Buscar</button>
</div>
</div>
</div>
<div class="row mt-4" id="stats" style="display:none;">
<div class="col-md-4"><div class="stat-card"><div class="fs-1" id="totalCount">0</div><div>Resultados</div></div>
</div>
<div class="mt-4" id="results" style="display:none;">
<h5>Resultados</h5>
<div id="list"></div>
</div>
<div class="mt-4 text-center" id="loading" style="display:none;">
<div class="spinner-border text-primary"></div>
<p>Buscando...</p>
</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
function fmt(n){return new Intl.NumberFormat('es-CL').format(n);}
async function buscar(){
let q=document.getElementById('q').value.trim().toLowerCase();
document.getElementById('loading').style.display='block';
document.getElementById('results').style.display='none';
document.getElementById('stats').style.display='none';
try{
let data=await (await fetch('/buscar?q='+encodeURIComponent(q))).json();
document.getElementById('loading').style.display='none';
document.getElementById('results').style.display='block';
document.getElementById('stats').style.display='block';
let f=data.results;
if(q){f=data.results.filter(x=>(x.titulo||'').toLowerCase().includes(q)||(x.organismo||'').toLowerCase().includes(q));}
document.getElementById('totalCount').textContent=f.length;
if(f.length==0){document.getElementById('list').innerHTML='<p>No hay resultados</p>';return;}
document.getElementById('list').innerHTML=f.slice(0,30).map(x=>'
<div class="card result-card p-3">
<div class="d-flex justify-content-between"><span class="codigo">'+x.codigo+'</span><span class="presupuesto">$'+fmt(x.presupuesto)+'</span></div>
<div class="titulo">'+x.titulo+'</div>
<div class="organismo">'+x.organismo+'</div>
</div>').join('');
}catch(e){document.getElementById('list').innerHTML='<div class="alert alert-danger">Error: '+e.message+'</div>';}}
window.onload=buscar;
</script>
</body>
</html>"""
    return Response(content=html, media_type="text/html")

@app.get("/admin")
def admin():
    alertas = cargar_alertas()
    html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Admin</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>body{background:#f5f5f5}.card{background:white;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1)}</style>
</head>
<body><div class="container py-5">
<h2>Admin - Alertas de Mercado Público</h2><hr>
<div class="card p-4 mb-4">
<h4>Nueva Alerta</h4>
<form action="/admin/agregar" method="post">
<div class="row">
<div class="col-md-4"><input type="text" name="palabra" class="form-control" placeholder="Palabra (ej: hormigon)" required></div>
<div class="col-md-4"><input type="email" name="email" class="form-control" placeholder="Email" required></div>
<div class="col-md-4"><button type="submit" class="btn btn-primary w-100">Agregar</button></div>
</div></form></div>
<div class="card p-4">
<h4>Alertas Activas</h4>
<table class="table"><tr><th>Palabra</th><th>Email</th><th></th></tr>"""
    for a in alertas.get("alertas", []):
        html += f"<tr><td><strong>{a['palabra']}</strong></td><td>{a['email']}</td><td><a href='/admin/eliminar?palabra={a['palabra']}' class='btn btn-danger btn-sm'>Eliminar</a></td></tr>"
    html += """</table></div>
<div class="card p-4 mt-4">
<h4>Ejecutar Ahora</h4>
<p>Busca y envía notificaciones por email</p>
<form action="/admin/enviar" method="post">
<div class="row">
<div class="col-md-8"><input type="text" name="busqueda" class="form-control" placeholder="Buscar y notificar"></div>
<div class="col-md-4"><button type="submit" class="btn btn-success w-100">Ejecutar</button></div>
</div></form>
</div></div></body></html>"""
    return Response(content=html, media_type="text/html")

@app.post("/admin/agregar")
def agregar(palabra: str = Form(...), email: str = Form(...)):
    data = cargar_alertas()
    for a in data["alertas"]:
        if a["palabra"].lower() == palabra.lower():
            a["email"] = email
            break
    else:
        data["alertas"].append({"palabra": palabra.lower(), "email": email})
    guardar_alertas(data)
    return RedirectResponse("/admin?msg=ok", status_code=302)

@app.get("/admin/eliminar")
def eliminar(palabra: str):
    data = cargar_alertas()
    data["alertas"] = [a for a in data["alertas"] if a["palabra"].lower() != palabra.lower()]
    guardar_alertas(data)
    return RedirectResponse("/admin?msg=eliminado", status_code=302)

@app.post("/admin/enviar")
def enviar(busqueda: str = Form(...)):
    html = buscar_en_mercado()
    resultados = parsear_resultados(html)
    
    data = cargar_alertas()
    # Filtrar alertas que coinciden con la búsqueda
    coincidencias = [a for a in data["alertas"] if a["palabra"].lower() in busqueda.lower()]
    
    # Enviar emails
    emails_enviados = []
    for alerta in coincidencias:
        # Crear email HTML
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1e3c72;">🔔 Nueva alerta de Mercado Público</h2>
            <p>Se encontraron <strong>{len(resultados)}</strong> compras que coinciden con: <strong>{busqueda}</strong></p>
            <hr>
        """
        for r in resultados[:10]:
            mensaje_html += f"""
            <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px;">
                <strong style="color: #2a5298;">{r['codigo']}</strong> - <span style="color: #27ae60; font-weight: bold;">${r['presupuesto']}</span>
                <br><strong>{r['titulo']}</strong>
                <br><small>{r['organismo']}</small>
            </div>
            """
        mensaje_html += """
            <hr>
            <p style="color: #666; font-size: 12px;">
                Este email fue enviado automáticamente por Mercado Público API<br>
                Si no deseas recibir más alertas, elimina la alerta desde el admin.
            </p>
        </body>
        </html>
        """
        
        if enviar_email(alerta["email"], f"🔔 Alerta Mercado Público: {busqueda}", mensaje_html):
            emails_enviados.append(f"✓ {alerta['email']}")
        else:
            emails_enviados.append(f"✗ {alerta['email']} (error)")
    
    html_resp = f"""<!DOCTYPE html><head>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body class="p-5"><div class="card p-4">
<h3>✅ Ejecución Completada</h3>
<p>Búsqueda: <strong>{busqueda}</strong></p>
<p>Resultados encontrados: {len(resultados)}</p>
<hr><h4>Estado de Emails:</h4><ul>"""
    for e in emails_enviados:
        html_resp += f"<li>{e}</li>"
    html_resp += f"""</ul>
<p>Total: {len(emails_enviados)} emails enviados</p>
<a href="/admin" class="btn btn-primary">Volver</a>
</div></body></html>"""
    return Response(content=html_resp, media_type="text/html")

@app.get("/buscar")
def buscar(q: str = Query("")):
    html = buscar_en_mercado()
    resultados = parsear_resultados(html)
    return {"results": resultados, "total": len(resultados)}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
