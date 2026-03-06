"""
Mercado Público Scraper - Compra Ágil
Usa Playwright para evitar bloqueos de CloudFront + BeautifulSoup para parseo
"""
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
import logging
import re
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://buscador.mercadopublico.cl/compra-agil"


def create_browser():
    """Crea un browser stealth para evitar detección"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
    )
    context = browser.new_context(
        locale='es-CL',
        timezone_id='America/Santiago',
        permissions=['geolocation'],
        viewport={'width': 1920, 'height': 1080}
    )
    page = context.new_page()
    
    # Ocultar webdriver
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    return playwright, browser, page


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
    Scraper una página usando Playwright + BeautifulSoup
    """
    url = build_url(date_from, date_to, status, region, page, order_by)
    logger.info(f"Scraping: {url}")
    
    playwright, browser, page = create_browser()
    
    try:
        response = page.goto(url, wait_until="networkidle", timeout=30000)
        logger.info(f"Status: {response.status}")
        
        # Esperar a que carguen los resultados
        page.wait_for_selector("text=resultados", timeout=10000)
        
        # Obtener el HTML
        html = page.content()
        
        # Parsear con BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extraer total
        total_text = soup.find(string=re.compile(r'resultados'))
        total = 0
        if total_text:
            match = re.search(r'(\d+)', total_text)
            if match:
                total = int(match.group(1))
        
        # Extraer compras del HTML
        compras = extract_compras(soup)
        
        return {
            "results": compras,
            "total": total,
            "page": page,
            "url": url,
            "timestamp": datetime.now().isoformat()
        }
        
    finally:
        browser.close()
        playwright.stop()


def extract_compras(soup) -> List[dict]:
    """Extrae compras del HTML parseado"""
    compras = []
    
    # Buscar todos los elementos que contengan códigos COT
    texto_html = str(soup)
    
    # Patrón para encontrar bloques de compras
    # El código viene como: XXXX-XXX-COT26
    patrones = re.findall(
        r'(\d{4,5}-\d{1,3}-COT\d{2})\s*</.*?heading\s*"([^"]+)"[^>]*>.*?>([^<]+)<.*?'
        r'(\d{2}/\d{2}/\d{4}).*?(\d{2}/\d{2}/\d{4})',
        texto_html,
        re.DOTALL
    )
    
    # Buscar de otra forma - por bloques
    # Encontrar todos los códigos
    codigos = re.findall(r'(\d{4,5}-\d{1,3}-COT\d{2})', texto_html)
    
    # Buscar títulos (h4)
    titulos = soup.find_all('h4')
    
    # Buscar presupuestos
    presupuestos = re.findall(r'\$\s*([\d.]+)', texto_html)
    
    # Buscar organismos - párrafos que contengan palabras clave
    org_keywords = ['MUNICIPALIDAD', 'HOSPITAL', 'UNIVERSIDAD', 'DEFENSORIA', 'INSTITUTO', 'EJERCITO', 'FUERZAS']
    organismos = []
    for p in soup.find_all('p'):
        text = p.get_text()
        if any(kw in text.upper() for kw in org_keywords):
            # Limpiar el texto
            org = text.strip().split('\n')[0]
            if org and len(org) > 5:
                organismos.append(org[:100])
    
    # Buscar fechas de publicación y cierre
    fechas_pub = re.findall(r'Publicada el\s*(\d{2}/\d{2}/\d{4})', texto_html)
    fechas_cierre = re.findall(r'Finaliza el\s*(\d{2}/\d{2}/\d{4})', texto_html)
    
    # Armar las compras
    for i in range(min(len(codigos), 15)):
        try:
            compra = {
                "codigo": codigos[i] if i < len(codigos) else None,
                "titulo": titulos[i].get_text().strip() if i < len(titulos) else None,
                "organismo": organismos[i] if i < len(organismos) else None,
                "presupuesto": f"$ {presupuestos[i]}" if i < len(presupuestos) else None,
                "fecha_publicacion": fechas_pub[i] if i < len(fechas_pub) else None,
                "fecha_cierre": fechas_cierre[i] if i < len(fechas_cierre) else None,
                "estado": "Recibiendo cotizaciones"
            }
            if compra["codigo"]:
                compras.append(compra)
        except Exception as e:
            logger.warning(f"Error armando compra {i}: {e}")
            continue
    
    return compras


def scrape_all(
    date_from: str = None,
    date_to: str = None,
    status: str = "2",
    region: str = "all",
    max_pages: int = 5,
    delay: float = 2.0
) -> List[dict]:
    """
    Scraper múltiples páginas con delay entre requests
    """
    import time
    all_results = []
    
    for page_num in range(1, max_pages + 1):
        try:
            data = scrape_page(
                date_from=date_from,
                date_to=date_to,
                status=status,
                region=region,
                page=page_num
            )
            results = data.get("results", [])
            
            if not results:
                break
                
            all_results.extend(results)
            logger.info(f"Página {page_num}: {len(results)} resultados")
            
            if len(results) < 15:
                break
                
            time.sleep(delay)
            
        except Exception as e:
            logger.error(f"Error en página {page_num}: {e}")
            break
    
    return all_results


if __name__ == "__main__":
    print("Ejecutando scraping de prueba...")
    data = scrape_page()
    print(f"Total: {data['total']}")
    print(f"Resultados: {len(data['results'])}")
    if data['results']:
        print(f"\nPrimer resultado:")
        print(json.dumps(data['results'][0], indent=2, ensure_ascii=False))
