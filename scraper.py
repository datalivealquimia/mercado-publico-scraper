"""
Mercado Público Scraper - Compra Ágil
Scraping con headers seguros para evitar bloqueos
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

BASE_URL = "https://buscador.mercadopublico.cl/compra-agil"


def build_url(
    date_from: str = None,
    date_to: str = None,
    status: str = "2",
    region: str = "all",
    page: int = 1,
    order_by: str = "recent"
) -> str:
    """Construye URL con parámetros"""
    params = {
        "order_by": order_by,
        "page_number": page,
        "region": region,
        "status": status,
    }
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    
    from urllib.parse import urlencode
    return f"{BASE_URL}?{urlencode(params)}"


def scrape_page(
    date_from: str = None,
    date_to: str = None,
    status: str = "2",
    region: str = "all",
    page: int = 1,
    order_by: str = "recent"
) -> dict:
    """
    Scraper una página de resultados de Compra Ágil
    
    Args:
        date_from: Fecha inicio (YYYY-MM-DD)
        date_to: Fecha fin (YYYY-MM-DD)
        status: Estado (2 = Publicada)
        region: Región (all = todas)
        page: Número de página
        order_by: Orden (recent, old, low_price, high_price)
    
    Returns:
        dict con 'results' (lista de compras) y 'total' (total de resultados)
    """
    url = build_url(date_from, date_to, status, region, page, order_by)
    logger.info(f"Scraping: {url}")
    
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extraer total de resultados
    total_text = soup.find("p", string=lambda t: t and "resultados" in t.lower())
    total = 0
    if total_text:
        import re
        match = re.search(r'(\d+)', total_text.text)
        if match:
            total = int(match.group(1))
    
    # Extraer compras
    compras = []
    
    # Buscar items de compra en el HTML
    items = soup.find_all("div", class_=lambda x: x and "resultado" in x.lower() if x else False)
    
    # También buscar por estructura conocida
    if not items:
        items = soup.find_all("div", {"data-id": True})
    
    for item in items:
        try:
            compra = extract_compra(item)
            if compra:
                compras.append(compra)
        except Exception as e:
            logger.warning(f"Error extrayendo item: {e}")
            continue
    
    # Si no encontramos por clase, buscar por estructura
    if not compras:
        compras = extract_from_structure(soup)
    
    return {
        "results": compras,
        "total": total,
        "page": page,
        "url": url,
        "timestamp": datetime.now().isoformat()
    }


def extract_compra(item) -> Optional[dict]:
    """Extrae datos de un item de compra"""
    # Implementar según estructura específica
    return None


def extract_from_structure(soup) -> List[dict]:
    """Extrae compras desde la estructura del HTML"""
    compras = []
    
    # Buscar todos los headings con códigos de compra
    codigos = soup.find_all(string=lambda t: t and "COT" in t)
    
    for codigo in codigos:
        try:
            parent = codigo.find_parent()
            if parent:
                compra = parse_compra_element(parent)
                if compra:
                    compras.append(compra)
        except Exception:
            continue
    
    return compras


def parse_compra_element(element) -> Optional[dict]:
    """Parsea un elemento de compra individual"""
    # Implementar según estructura específica
    return None


def scrape_all(
    date_from: str = None,
    date_to: str = None,
    status: str = "2",
    region: str = "all",
    max_pages: int = 10,
    delay: float = 2.0
) -> List[dict]:
    """
    Scraper múltiples páginas con delay entre requests
    
    Args:
        date_from: Fecha inicio
        date_to: Fecha fin  
        status: Estado
        region: Región
        max_pages: Máximo de páginas a scrapear
        delay: Segundos entre requests
    
    Returns:
        Lista de todas las compras encontradas
    """
    import time
    
    all_results = []
    page = 1
    
    while page <= max_pages:
        try:
            data = scrape_page(date_from, date_to, status, region, page)
            results = data.get("results", [])
            
            if not results:
                break
                
            all_results.extend(results)
            logger.info(f"Página {page}: {len(results)} resultados")
            
            if len(results) < 15:  # Última página
                break
                
            page += 1
            time.sleep(delay)  # Respetar delay para no bloquear
            
        except Exception as e:
            logger.error(f"Error en página {page}: {e}")
            break
    
    return all_results


if __name__ == "__main__":
    # Ejemplo de uso
    print("Ejecutando scraping de prueba...")
    data = scrape_page()
    print(f"Total: {data['total']}")
    print(f"Resultados en página 1: {len(data['results'])}")
