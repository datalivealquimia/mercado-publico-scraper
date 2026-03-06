"""
Mercado Público API - FastAPI
Con datos de ejemplo (funciona inmediatamente)
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Optional
from datetime import datetime

app = FastAPI(
    title="Mercado Público API",
    description="API para consultar compras públicas de Chile - Compra Ágil",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datos de ejemplo - 15 compras reales
COMPRAS = [
    {"codigo": "2445-79-COT26", "titulo": "ADQUISICION DE SMART TV Y LICENCIA MICROSOFT SP/449", "organismo": "I MUNICIPALIDAD DE CURICO", "presupuesto": "$ 600.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "09/03/2026", "estado": "Publicada"},
    {"codigo": "5504-45-COT26", "titulo": "COMPRA DE MATERIALES", "organismo": "UNIVERSIDAD DE CHILE", "presupuesto": "$ 250.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "09/03/2026", "estado": "Publicada"},
    {"codigo": "815-13-COT26", "titulo": "Adquisición de cuatro (4) neumáticos para vehículo Nissan Navarra", "organismo": "DIRECCIÓN REGIONAL ADUANA DE PUERTO MONTT", "presupuesto": "$ 1.500.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "10/03/2026", "estado": "Publicada"},
    {"codigo": "188-162-COT26", "titulo": "SERVICIO DE DESINSECTACIÓN PARA ESTABLECIMIENTOS ADMINISTRADOS POR COMUDEF", "organismo": "CORP MUNICIPAL DE EDUC SALUD CULTURA Y RECREACION DE LA FLORIDA", "presupuesto": "$ 6.961.100", "fecha_publicacion": "06/03/2026", "fecha_cierre": "09/03/2026", "estado": "Publicada"},
    {"codigo": "2462-38-COT26", "titulo": "STAND DE HIDRATACIÓN Y ALIMENTACIÓN SALUDABLE", "organismo": "I MUNICIPALIDAD DE PROVIDENCIA", "presupuesto": "$ 1.500.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "12/03/2026", "estado": "Publicada"},
    {"codigo": "2481-12-COT26", "titulo": "CORTINAS ROLLER", "organismo": "I MUNICIPALIDAD DE CHILLAN", "presupuesto": "$ 3.826.148", "fecha_publicacion": "06/03/2026", "fecha_cierre": "16/03/2026", "estado": "Publicada"},
    {"codigo": "2013-255-COT26", "titulo": "40 colaciones 10/03", "organismo": "UNIVERSIDAD ARTURO PRAT", "presupuesto": "$ 100.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "09/03/2026", "estado": "Publicada"},
    {"codigo": "1976-25-COT26", "titulo": "REPARACION SUV MARCA TOYOTA, MODELO RAV4", "organismo": "DELEGACIÓN PRESIDENCIAL PROVINCIAL DEL BIOBÍO", "presupuesto": "$ 1.150.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "09/03/2026", "estado": "Publicada"},
    {"codigo": "1411-162-COT26", "titulo": "CDP STGO SUR - ALIMENTOS MES MARZO 2026 HOSPITAL Y SSEE", "organismo": "Dirección Regional de Gendarmeria - Metropolitana", "presupuesto": "$ 4.000.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "09/03/2026", "estado": "Publicada"},
    {"codigo": "4305-36-COT26", "titulo": "Adquisición de material y útiles quirúrgicos para el funcionamiento de la BAE", "organismo": "Ejercito de Chile", "presupuesto": "$ 1.500.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "09/03/2026", "estado": "Publicada"},
    {"codigo": "3753-70-COT26", "titulo": "SERVICIO DE TRANSPORTE ESCOLAR POR EL MES DE MARZO DE 2026", "organismo": "I MUNICIPALIDAD DE CANELA", "presupuesto": "$ 1.700.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "07/03/2026", "estado": "Publicada"},
    {"codigo": "1057501-877-COT26", "titulo": "ESTANTE REPISA METALICO 200X150X50CM 400KG", "organismo": "COMPLEJO ASISTENCIAL DR. SOTERO DEL RIO", "presupuesto": "$ 2.300.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "09/03/2026", "estado": "Publicada"},
    {"codigo": "3797-117-COT26", "titulo": "META INFLABLE PARA ACTIVIDADES MUNICIPALES", "organismo": "I MUNICIPALIDAD DE COCHRANE", "presupuesto": "$ 3.400.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "07/03/2026", "estado": "Publicada"},
    {"codigo": "2294-171-COT26", "titulo": "MANTENCION BUSES DAEM", "organismo": "I MUNICIPALIDAD DE TALCA", "presupuesto": "$ 180.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "09/03/2026", "estado": "Publicada"},
    {"codigo": "4475-122-COT26", "titulo": "Textos de apoyo para el aprendizaje para Escuela Ramón Freire", "organismo": "I.MUNICIPALIDAD DE ROMERAL", "presupuesto": "$ 3.000.000", "fecha_publicacion": "06/03/2026", "fecha_cierre": "07/03/2026", "estado": "Publicada"},
]


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mercado Público API</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
            h1 { color: #2c3e50; }
            .card { background: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            a { color: #3498db; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>🏛️ Mercado Público API v2.0</h1>
        <div class="card">
            <h2>📡 Endpoints</h2>
            <ul>
                <li><a href="/web">/web</a> - Interfaz Web (BUSCAR)</li>
                <li><a href="/compra-agil">/compra-agil</a> - API JSON</li>
            </ul>
        </div>
    </body>
    </html>
    """


@app.get("/web", response_class=HTMLResponse)
def web_interface():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mercado Público - Buscador</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px 30px; border-radius: 12px; margin-bottom: 20px; text-align: center; }
        .filters { background: white; padding: 25px; border-radius: 12px; margin-bottom: 20px; }
        .filter-row { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 15px; }
        .filter-group { flex: 1; min-width: 200px; }
        .filter-group label { display: block; margin-bottom: 5px; font-weight: 600; color: #555; font-size: 14px; }
        .filter-group input, .filter-group select { width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        .btn { background: #667eea; color: white; border: none; padding: 12px 30px; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; }
        .results { background: white; padding: 25px; border-radius: 12px; }
        .result-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
        .result-card .codigo { color: #667eea; font-weight: 700; font-size: 16px; }
        .result-card .titulo { font-size: 15px; color: #2c3e50; margin: 8px 0; font-weight: 600; }
        .result-card .organismo { color: #7f8c8d; font-size: 13px; }
        .result-card .meta { display: flex; gap: 20px; margin-top: 10px; font-size: 13px; flex-wrap: wrap; }
        .result-card .meta span { background: #f8f9fa; padding: 4px 10px; border-radius: 4px; }
        .result-card .presupuesto { color: #27ae60; font-weight: 700; }
        .result-card .fecha { color: #e74c3c; }
        .loading { text-align: center; padding: 40px; color: #999; }
        .info { background: #e8f4fd; color: #0066cc; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Mercado Público Chile</h1>
            <p>Buscador de Compras Ágiles</p>
        </div>
        
        <div class="filters">
            <h3>🔍 Buscar en compras</h3>
            <div class="filter-row">
                <div class="filter-group">
                    <label>Palabra clave</label>
                    <input type="text" id="keyword" placeholder="ej: agua, mantención, smart tv">
                </div>
            </div>
            <button class="btn" onclick="buscar()">🔍 Buscar</button>
        </div>
        
        <div class="results" id="results" style="display: none;">
            <h3 id="results-title">Resultados</h3>
            <div id="results-list"></div>
        </div>
    </div>

    <script>
        const compras = """ + json.dumps(COMPRAS) + """;
        
        async function buscar() {
            const keyword = document.getElementById('keyword').value.toLowerCase();
            const resultsDiv = document.getElementById('results');
            const listDiv = document.getElementById('results-list');
            
            resultsDiv.style.display = 'block';
            
            // Filtrar
            const filtered = compras.filter(c => 
                !keyword || 
                c.titulo.toLowerCase().includes(keyword) || 
                c.organismo.toLowerCase().includes(keyword) ||
                c.codigo.toLowerCase().includes(keyword)
            );
            
            if (filtered.length === 0) {
                listDiv.innerHTML = '<div class="loading">No se encontraron resultados. Intenta con: agua, smart tv, муниципаidad</div>';
                return;
            }
            
            let html = '';
            filtered.forEach(compra => {
                html += `
                    <div class="result-card">
                        <div class="codigo">${compra.codigo}</div>
                        <div class="titulo">${compra.titulo}</div>
                        <div class="organismo">${compra.organismo}</div>
                        <div class="meta">
                            <span class="presupuesto">💰 ${compra.presupuesto}</span>
                            <span>📅 ${compra.fecha_publicacion}</span>
                            <span class="fecha">⏰ Cierra: ${compra.fecha_cierre}</span>
                        </div>
                    </div>
                `;
            });
            
            listDiv.innerHTML = html;
        }
    </script>
</body>
</html>
    """


@app.get("/compra-agil")
def list_compras(
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100)
):
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": COMPRAS[start:end],
        "total": len(COMPRAS),
        "page": page,
        "limit": limit
    }


@app.get("/compra-agil/{codigo}")
def get_by_codigo(codigo: str):
    for c in COMPRAS:
        if c["codigo"].upper() == codigo.upper():
            return c
    return {"error": "Compra no encontrada"}


@app.get("/compra-agil/search")
def search(
    q: str = Query(..., description="Texto a buscar")
):
    q = q.lower()
    results = [c for c in COMPRAS if q in c["titulo"].lower() or q in c["organismo"].lower() or q in c["codigo"].lower()]
    return {"data": results, "total": len(results)}


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


import json
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
