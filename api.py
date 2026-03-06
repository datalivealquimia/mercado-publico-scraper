"""
Mercado Público API - FastAPI
API simple que sirve datos extraídos del browser
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
import os

app = FastAPI(
    title="Mercado Público API",
    description="API para consultar compras públicas de Chile - Compra Ágil",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar datos
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "compras.json")

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

compras = load_data()


@app.get("/")
def root():
    return {
        "name": "Mercado Público API",
        "version": "1.0.0",
        "total_compras": len(compras),
        "endpoints": {
            "/compra-agil": "Lista todas las compras",
            "/compra-agil/{codigo}": "Busca por código",
            "/compra-agil/search?q=texto": "Busca en título u organismo"
        }
    }


@app.get("/compra-agil")
def list_compras(
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    organismo: Optional[str] = Query(None, description="Filtrar por organismo"),
    presupuesto_min: Optional[int] = Query(None, description="Presupuesto mínimo"),
    presupuesto_max: Optional[int] = Query(None, description="Presupuesto máximo")
):
    """Lista compras con filtros opcionales"""
    filtered = compras
    
    # Filtro por organismo
    if organismo:
        filtered = [c for c in filtered if organismo.lower() in c.get("organismo", "").lower()]
    
    # Filtro por presupuesto
    if presupuesto_min:
        filtered = [c for c in filtered if parse_presupuesto(c.get("presupuesto", "0")) >= presupuesto_min]
    
    if presupuesto_max:
        filtered = [c for c in filtered if parse_presupuesto(c.get("presupuesto", "0")) <= presupuesto_max]
    
    # Paginación
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "data": filtered[start:end],
        "total": len(filtered),
        "page": page,
        "limit": limit,
        "total_pages": (len(filtered) + limit - 1) // limit
    }


@app.get("/compra-agil/{codigo}")
def get_by_codigo(codigo: str):
    """Busca una compra por código"""
    for c in compras:
        if c.get("codigo", "").upper() == codigo.upper():
            return c
    return {"error": "Compra no encontrada"}


@app.get("/compra-agil/search")
def search(
    q: str = Query(..., description="Texto a buscar"),
    limit: int = Query(10, ge=1, le=50)
):
    """Busca en título y organismo"""
    q = q.lower()
    results = []
    for c in compras:
        if q in c.get("titulo", "").lower() or q in c.get("organismo", "").lower():
            results.append(c)
    return {
        "query": q,
        "results": results[:limit],
        "total": len(results)
    }


def parse_presupuesto(pres: str) -> int:
    """Convierte presupuesto string a número"""
    try:
        return int(pres.replace("$", "").replace(".", "").replace(" ", ""))
    except:
        return 0


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
