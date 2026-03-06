"""
Mercado Público API - FastAPI
API REST para consultar compras públicas
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

from scraper import scrape_page, scrape_all, build_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mercado Público API",
    description="API para consultar compras públicas de Chile - Compra Ágil",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class Compra(BaseModel):
    codigo: str
    titulo: str
    organismo: str
    region: str
    presupuesto: Optional[str] = None
    fecha_publicacion: Optional[str] = None
    fecha_cierre: Optional[str] = None
    estado: str


class ScrapedData(BaseModel):
    results: List[dict]
    total: int
    page: int
    url: str
    timestamp: str


@app.get("/")
def root():
    """Endpoint raíz"""
    return {
        "name": "Mercado Público API",
        "version": "1.0.0",
        "endpoints": {
            "/compra-agil": "Buscar compras ágiles (parámetros de query)",
            "/compra-agil/search": "Busqueda avanzada",
            "/health": "Health check"
        }
    }


@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/compra-agil", response_model=ScrapedData)
def buscar_compra_agil(
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    status: str = Query("2", description="Estado (2=Publicada, 3=Cerrada, etc.)"),
    region: str = Query("all", description="Región (all, RM, V, etc.)"),
    page: int = Query(1, ge=1, description="Número de página"),
    order_by: str = Query("recent", description="Orden (recent, old, low_price, high_price)")
):
    """
    Busca compras en Compra Ágil
    
    Ejemplos:
    - /compra-agil?date_from=2026-02-01&date_to=2026-03-06
    - /compra-agil?status=2&region=RM&page=1
    """
    try:
        data = scrape_page(
            date_from=date_from,
            date_to=date_to,
            status=status,
            region=region,
            page=page,
            order_by=order_by
        )
        return data
    except Exception as e:
        logger.error(f"Error scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/compra-agil/search")
def busqueda_avanzada(
    q: str = Query(..., description="Palabra clave o código"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    max_pages: int = Query(5, ge=1, le=50, description="Máximo de páginas"),
    delay: float = Query(2.0, ge=0.5, description="Delay entre requests (segundos)")
):
    """
    Búsqueda avanzada con múltiples páginas
    """
    try:
        results = scrape_all(
            date_from=date_from,
            date_to=date_to,
            max_pages=max_pages,
            delay=delay
        )
        return {
            "query": q,
            "results": results,
            "total_encontrados": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error búsqueda: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/compra-agil/url")
def generar_url(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    status: str = "2",
    region: str = "all",
    page: int = 1,
    order_by: str = "recent"
):
    """Genera URL de búsqueda"""
    return {
        "url": build_url(date_from, date_to, status, region, page, order_by)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
