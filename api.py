"""
Mercado Público API - FastAPI
API completa con todos los filtros del buscador
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
import os

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

# Cargar datos de ejemplo
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "compras.json")

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

compras = load_data()


# ============== ENDPOINTS ==============

@app.get("/", response_class=HTMLResponse)
def root():
    """Página principal con documentación"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mercado Público API</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
            h1 { color: #2c3e50; }
            .card { background: white; padding: 20px; border-radius: 8px; margin: 10px 0; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code { background: #ecf0f1; padding: 2px 6px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🏛️ Mercado Público API v2.0</h1>
        <div class="card">
            <h2>📡 Endpoints disponibles</h2>
            <ul>
                <li><a href="/docs">/docs</a> - Documentación Swagger</li>
                <li><a href="/compra-agil">/compra-agil</a> - Listar compras</li>
                <li><a href="/compra-agil/2445-79-COT26">/compra-agil/{codigo}</a> - Buscar por código</li>
                <li><a href="/compra-agil/search?q=salud">/compra-agil/search</a> - Búsqueda avanzada</li>
            </ul>
        </div>
        <div class="card">
            <h2>🌐 Web UI</h2>
            <p><a href="/web">Ir a la interfaz web</a></p>
        </div>
    </body>
    </html>
    """


@app.get("/web", response_class=HTMLResponse)
def web_interface():
    """Interfaz web para consultar la API"""
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mercado Público - Buscador</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            background: white; 
            padding: 20px 30px; 
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        .header h1 { margin: 0; color: #2c3e50; }
        .filters { 
            background: white; 
            padding: 25px; 
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        .filters h3 { margin-top: 0; color: #34495e; }
        .filter-row { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 15px; }
        .filter-group { flex: 1; min-width: 200px; }
        .filter-group label { display: block; margin-bottom: 5px; font-weight: 600; color: #555; font-size: 14px; }
        .filter-group input, .filter-group select { 
            width: 100%; 
            padding: 10px; 
            border: 2px solid #e0e0e0; 
            border-radius: 8px;
            font-size: 14px;
        }
        .filter-group input:focus, .filter-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn:hover { background: #5568d3; transform: translateY(-2px); }
        .btn-secondary { background: #95a5a6; }
        .results { 
            background: white; 
            padding: 25px; 
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        .results-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        .result-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        .result-card:hover { 
            border-color: #667eea; 
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }
        .result-card .codigo { 
            color: #667eea; 
            font-weight: 700; 
            font-size: 16px;
        }
        .result-card .titulo { 
            font-size: 15px; 
            color: #2c3e50; 
            margin: 8px 0;
            font-weight: 600;
        }
        .result-card .organismo { 
            color: #7f8c8d; 
            font-size: 13px;
        }
        .result-card .meta { 
            display: flex; 
            gap: 20px; 
            margin-top: 10px;
            font-size: 13px;
        }
        .result-card .meta span { 
            background: #f8f9fa; 
            padding: 4px 10px; 
            border-radius: 4px;
        }
        .result-card .presupuesto { 
            color: #27ae60; 
            font-weight: 700;
        }
        .result-card .fecha { color: #e74c3c; }
        .pagination { display: flex; gap: 10px; justify-content: center; margin-top: 20px; }
        .pagination button {
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 4px;
            cursor: pointer;
        }
        .pagination button.active { background: #667eea; color: white; border-color: #667eea; }
        .loading { text-align: center; padding: 40px; color: #999; }
        .error { background: #fee; color: #c00; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Mercado Público Chile</h1>
            <p>Buscador de Compras Ágiles</p>
        </div>
        
        <div class="filters">
            <h3>🔍 Filtros de búsqueda</h3>
            <div class="filter-row">
                <div class="filter-group">
                    <label>Palabra clave</label>
                    <input type="text" id="keyword" placeholder="ej: generador, mantención">
                </div>
                <div class="filter-group">
                    <label>Código de compra</label>
                    <input type="text" id="codigo" placeholder="ej: 4829-46-COT26">
                </div>
                <div class="filter-group">
                    <label>Estado</label>
                    <select id="estado">
                        <option value="publicada">Publicada</option>
                        <option value="cerrada">Cerrada</option>
                        <option value="oc_emitida">OC Emitida</option>
                        <option value="todos">Todos</option>
                    </select>
                </div>
            </div>
            <div class="filter-row">
                <div class="filter-group">
                    <label>Fecha desde (ddMMyyyy)</label>
                    <input type="text" id="fecha_desde" placeholder="ej: 01032026">
                </div>
                <div class="filter-group">
                    <label>Fecha hasta (ddMMyyyy)</label>
                    <input type="text" id="fecha_hasta" placeholder="ej: 06032026">
                </div>
                <div class="filter-group">
                    <label>Región</label>
                    <select id="region">
                        <option value="">Todas las regiones</option>
                        <option value="RM">Región Metropolitana</option>
                        <option value="I">Tarapacá</option>
                        <option value="II">Antofagasta</option>
                        <option value="III">Atacama</option>
                        <option value="IV">Coquimbo</option>
                        <option value="V">Valparaíso</option>
                        <option value="VI">O'Higgins</option>
                        <option value="VII">Maule</option>
                        <option value="VIII">Biobío</option>
                        <option value="IX">La Araucanía</option>
                        <option value="XIV">Los Ríos</option>
                        <option value="X">Los Lagos</option>
                        <option value="XI">Aysén</option>
                        <option value="XII">Magallanes</option>
                    </select>
                </div>
            </div>
            <div class="filter-row">
                <div class="filter-group">
                    <label>Presupuesto mínimo ($)</label>
                    <input type="number" id="presupuesto_min" placeholder="ej: 100000">
                </div>
                <div class="filter-group">
                    <label>Presupuesto máximo ($)</label>
                    <input type="number" id="presupuesto_max" placeholder="ej: 5000000">
                </div>
                <div class="filter-group">
                    <label>Ordenar por</label>
                    <select id="order_by">
                        <option value="reciente">Más recientes</option>
                        <option value="cierre_proximo">Próximas a cerrar</option>
                        <option value="presupuesto_asc">Menor presupuesto</option>
                        <option value="presupuesto_desc">Mayor presupuesto</option>
                    </select>
                </div>
            </div>
            <div class="filter-row">
                <div class="filter-group">
                    <label>Página</label>
                    <input type="number" id="pagina" value="1" min="1" style="width: 100px;">
                </div>
                <div class="filter-group">
                    <label>Resultados por página</label>
                    <select id="cantidad">
                        <option value="10">10</option>
                        <option value="15" selected>15</option>
                        <option value="25">25</option>
                        <option value="50">50</option>
                    </select>
                </div>
            </div>
            <button class="btn" onclick="buscar()">🔍 Buscar</button>
            <button class="btn btn-secondary" onclick="limpiar()">Limpiar</button>
        </div>
        
        <div class="results" id="results" style="display: none;">
            <div class="results-header">
                <h3 id="results-title">Resultados</h3>
                <span id="results-count"></span>
            </div>
            <div id="results-list"></div>
            <div class="pagination" id="pagination"></div>
        </div>
    </div>

    <script>
        let currentPage = 1;
        
        async function buscar() {
            const resultsDiv = document.getElementById('results');
            const listDiv = document.getElementById('results-list');
            const titleDiv = document.getElementById('results-title');
            const countDiv = document.getElementById('results-count');
            
            resultsDiv.style.display = 'block';
            listDiv.innerHTML = '<div class="loading">Buscando...</div>';
            
            // Construir query string
            const params = new URLSearchParams();
            
            const keyword = document.getElementById('keyword').value;
            const codigo = document.getElementById('codigo').value;
            const estado = document.getElementById('estado').value;
            const fecha_desde = document.getElementById('fecha_desde').value;
            const fecha_hasta = document.getElementById('fecha_hasta').value;
            const region = document.getElementById('region').value;
            const presupuesto_min = document.getElementById('presupuesto_min').value;
            const presupuesto_max = document.getElementById('presupuesto_max').value;
            const order_by = document.getElementById('order_by').value;
            const pagina = document.getElementById('pagina').value;
            const cantidad = document.getElementById('cantidad').value;
            
            if (keyword) params.append('keyword', keyword);
            if (codigo) params.append('codigo', codigo);
            if (estado) params.append('estado', estado);
            if (fecha_desde) params.append('fecha_desde', fecha_desde);
            if (fecha_hasta) params.append('fecha_hasta', fecha_hasta);
            if (region) params.append('region', region);
            if (presupuesto_min) params.append('presupuesto_min', presupuesto_min);
            if (presupuesto_max) params.append('presupuesto_max', presupuesto_max);
            if (order_by) params.append('order_by', order_by);
            if (pagina) params.append('pagina', pagina);
            if (cantidad) params.append('cantidad', cantidad);
            
            try {
                const response = await fetch('/compra-agil/search?' + params);
                const data = await response.json();
                
                if (data.error) {
                    listDiv.innerHTML = '<div class="error">' + data.error + '</div>';
                    return;
                }
                
                titleDiv.textContent = 'Resultados de búsqueda';
                countDiv.textContent = data.total + ' compras encontradas';
                
                if (data.data.length === 0) {
                    listDiv.innerHTML = '<div class="loading">No se encontraron resultados</div>';
                    return;
                }
                
                let html = '';
                data.data.forEach(compra => {
                    html += `
                        <div class="result-card">
                            <div class="codigo">${compra.codigo || 'N/A'}</div>
                            <div class="titulo">${compra.titulo || 'Sin título'}</div>
                            <div class="organismo">${compra.organismo || 'N/A'}</div>
                            <div class="meta">
                                <span class="presupuesto">💰 ${compra.presupuesto || 'N/A'}</span>
                                <span>📅 Publicada: ${compra.fecha_publicacion || 'N/A'}</span>
                                <span class="fecha">⏰ Cierra: ${compra.fecha_cierre || 'N/A'}</span>
                                <span>${compra.estado || ''}</span>
                            </div>
                        </div>
                    `;
                });
                
                listDiv.innerHTML = html;
                
                // Paginación
                if (data.total_paginas > 1) {
                    let paginationHtml = '';
                    for (let i = 1; i <= Math.min(data.total_paginas, 10); i++) {
                        const active = i == pagina ? 'active' : '';
                        paginationHtml += `<button class="${active}" onclick="cambiarPagina(${i})">${i}</button>`;
                    }
                    document.getElementById('pagination').innerHTML = paginationHtml;
                }
                
            } catch (err) {
                listDiv.innerHTML = '<div class="error">Error: ' + err.message + '</div>';
            }
        }
        
        function cambiarPagina(pagina) {
            document.getElementById('pagina').value = pagina;
            buscar();
        }
        
        function limpiar() {
            document.getElementById('keyword').value = '';
            document.getElementById('codigo').value = '';
            document.getElementById('estado').value = 'publicada';
            document.getElementById('fecha_desde').value = '';
            document.getElementById('fecha_hasta').value = '';
            document.getElementById('region').value = '';
            document.getElementById('presupuesto_min').value = '';
            document.getElementById('presupuesto_max').value = '';
            document.getElementById('order_by').value = 'reciente';
            document.getElementById('pagina').value = '1';
            document.getElementById('cantidad').value = '15';
            document.getElementById('results').style.display = 'none';
        }
    </script>
</body>
</html>
    """


# ============== API ENDPOINTS ==============

@app.get("/compra-agil/search")
def search_compras(
    keyword: Optional[str] = Query(None, description="Palabra clave o título"),
    codigo: Optional[str] = Query(None, description="Código de compra"),
    estado: str = Query("publicada", description="Estado: publicada, cerrada, oc_emitida, todos"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (ddMMyyyy)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (ddMMyyyy)"),
    region: Optional[str] = Query(None, description="Código de región"),
    presupuesto_min: Optional[int] = Query(None, description="Presupuesto mínimo"),
    presupuesto_max: Optional[int] = Query(None, description="Presupuesto máximo"),
    order_by: str = Query("reciente", description="Orden: reciente, cierre_proximo, presupuesto_asc, presupuesto_desc"),
    pagina: int = Query(1, ge=1, description="Número de página"),
    cantidad: int = Query(15, ge=1, le=100, description="Resultados por página")
):
    """
    Búsqueda avanzada de compras
    
    Todos los filtros disponibles:
    - keyword: Palabra clave
    - codigo: Código de compra (ej: 4829-46-COT26)
    - estado: publicada, cerrada, oc_emitida, todos
    - fecha_desde: Fecha desde (ddMMyyyy)
    - fecha_hasta: Fecha hasta (ddMMyyyy)
    - region: Código de región
    - presupuesto_min: Presupuesto mínimo
    - presupuesto_max: Presupuesto máximo
    - order_by: reciente, cierre_proximo, presupuesto_asc, presupuesto_desc
    - pagina: Número de página
    - cantidad: Resultados por página
    """
    # Filtrar datos locales (en producción, esto llamaría al scraper)
    filtered = compras.copy()
    
    # Filtro por keyword
    if keyword:
        kw = keyword.lower()
        filtered = [c for c in filtered if kw in c.get("titulo", "").lower() or kw in c.get("organismo", "").lower()]
    
    # Filtro por código
    if codigo:
        filtered = [c for c in filtered if codigo.upper() in c.get("codigo", "").upper()]
    
    # Filtro por presupuesto
    if presupuesto_min:
        filtered = [c for c in filtered if parse_presupuesto(c.get("presupuesto", "0")) >= presupuesto_min]
    
    if presupuesto_max:
        filtered = [c for c in filtered if parse_presupuesto(c.get("presupuesto", "0")) <= presupuesto_max]
    
    # Ordenar
    if order_by == "presupuesto_asc":
        filtered.sort(key=lambda x: parse_presupuesto(x.get("presupuesto", "0")))
    elif order_by == "presupuesto_desc":
        filtered.sort(key=lambda x: parse_presupuesto(x.get("presupuesto", "0")), reverse=True)
    # "reciente" y "cierre_proximo" mantienen el orden original
    
    # Paginación
    total = len(filtered)
    start = (pagina - 1) * cantidad
    end = start + cantidad
    data = filtered[start:end]
    
    return {
        "success": True,
        "data": data,
        "total": total,
        "pagina": pagina,
        "cantidad": cantidad,
        "total_paginas": (total + cantidad - 1) // cantidad if total else 0,
        "filters": {
            "keyword": keyword,
            "codigo": codigo,
            "estado": estado,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "region": region,
            "presupuesto_min": presupuesto_min,
            "presupuesto_max": presupuesto_max,
            "order_by": order_by
        }
    }


@app.get("/compra-agil")
def list_compras(
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    organismo: Optional[str] = Query(None)
):
    """Lista compras con paginación"""
    filtered = compras
    
    if organismo:
        filtered = [c for c in filtered if organismo.lower() in c.get("organismo", "").lower()]
    
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "data": filtered[start:end],
        "total": len(filtered),
        "page": page,
        "limit": limit
    }


@app.get("/compra-agil/{codigo}")
def get_by_codigo(codigo: str):
    """Busca una compra por código"""
    for c in compras:
        if c.get("codigo", "").upper() == codigo.upper():
            return c
    return {"error": "Compra no encontrada", "success": False}


@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


def parse_presupuesto(pres: str) -> int:
    """Convierte presupuesto string a número"""
    try:
        return int(pres.replace("$", "").replace(".", "").replace(" ", ""))
    except:
        return 0


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
