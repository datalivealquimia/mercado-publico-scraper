"""
Mercado Público Scraper - Completo
Soporta todos los filtros del buscador
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


class MercadoPublicoScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
    
    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        context = self.browser.new_context(
            locale='es-CL',
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = context.new_page()
        self.page.add_init_script(
            'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
        )
        return self
    
    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def build_url(self, params: dict) -> str:
        """Construye URL con parámetros"""
        from urllib.parse import urlencode
        return f"{BASE_URL}?{urlencode(params)}"
    
    def search(
        self,
        keyword: str = None,
        codigo: str = None,
        estado: str = "publicada",
        fecha_desde: str = None,
        fecha_hasta: str = None,
        region: str = None,
        rubro: int = None,
        codigo_organismo: int = None,
        presupuesto_min: int = None,
        presupuesto_max: int = None,
        order_by: str = "reciente",
        pagina: int = 1,
        cantidad: int = 15
    ) -> dict:
        """
        Realiza búsqueda con todos los filtros
        
        Args:
            keyword: Palabra clave o título
            codigo: Número de compra (ej: 4829-46-COT26)
            estado: publicada, cerrada, oc_emitida, todos
            fecha_desde: Fecha desde (ddMMyyyy)
            fecha_hasta: Fecha hasta (ddMMyyyy)
            region: Código de región (1-16)
            rubro: Código de rubro
            codigo_organismo: Código del organismo
            presupuesto_min: Presupuesto mínimo (CLP)
            presupuesto_max: Presupuesto máximo (CLP)
            order_by: reciente, cierre_proximo, presupuesto_asc, presupuesto_desc
            pagina: Número de página
            cantidad: Resultados por página
        """
        # Mapear estado
        estado_map = {
            "publicada": "2",
            "cerrada": "3", 
            "oc_emitida": "4",
            "todos": "1"
        }
        
        # Mapear orden
        order_map = {
            "reciente": "recent",
            "cierre_proximo": "closing",
            "presupuesto_asc": "low_price",
            "presupuesto_desc": "high_price"
        }
        
        params = {
            "status": estado_map.get(estado, "2"),
            "order_by": order_map.get(order_by, "recent"),
            "page_number": pagina,
            "region": region if region else "all"
        }
        
        if keyword:
            params["keyword"] = keyword
        
        if codigo:
            params["codigo"] = codigo
        
        if fecha_desde:
            # Convertir ddMMyyyy a dd/mm/yyyy
            if len(fecha_desde) == 8:
                params["date_from"] = f"{fecha_desde[0:2]}/{fecha_desde[2:4]}/{fecha_desde[4:8]}"
        
        if fecha_hasta:
            if len(fecha_hasta) == 8:
                params["date_to"] = f"{fecha_hasta[0:2]}/{fecha_hasta[2:4]}/{fecha_hasta[4:8]}"
        
        url = self.build_url(params)
        logger.info(f"Buscando: {url}")
        
        try:
            response = self.page.goto(url, wait_until="networkidle", timeout=30000)
            logger.info(f"Status: {response.status}")
            
            # Esperar resultados
            self.page.wait_for_selector("text=resultados", timeout=10000)
            
            # Obtener HTML
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extraer total
            total_text = soup.find(string=re.compile(r'resultados'))
            total = 0
            if total_text:
                match = re.search(r'(\d+)', total_text)
                if match:
                    total = int(match.group(1))
            
            # Extraer compras
            compras = self._extract_compras(soup)
            
            return {
                "success": True,
                "data": compras,
                "pagination": {
                    "total": total,
                    "pagina": pagina,
                    "cantidad": cantidad,
                    "total_paginas": (total + cantidad - 1) // cantidad if total else 0
                },
                "filters": {
                    "keyword": keyword,
                    "codigo": codigo,
                    "estado": estado,
                    "fecha_desde": fecha_desde,
                    "fecha_hasta": fecha_hasta,
                    "region": region,
                    "order_by": order_by
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_compras(self, soup) -> List[dict]:
        """Extrae compras del HTML"""
        compras = []
        html = str(soup)
        
        # Buscar códigos
        codigos = re.findall(r'(\d{4,5}-\d{1,3}-COT\d{2})', html)
        
        # Buscar títulos
        titulos = [h.get_text().strip() for h in soup.find_all('h4')]
        
        # Buscar presupuestos
        presupuestos = re.findall(r'\$\s*([\d.]+)', html)
        
        # Buscar organismos
        org_keywords = ['MUNICIPALIDAD', 'HOSPITAL', 'UNIVERSIDAD', 'DEFENSORIA', 
                       'INSTITUTO', 'EJERCITO', 'FUERZAS', 'DIRECCIÓN', 'CORP', 'SERVICIO']
        organismos = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if any(kw in text.upper() for kw in org_keywords):
                org = text.split('\n')[0].strip()
                if org and len(org) > 5:
                    organismos.append(org[:120])
        
        # Fechas
        fechas_pub = re.findall(r'Publicada el\s*(\d{2}/\d{2}/\d{4})', html)
        fechas_cierre = re.findall(r'Finaliza el\s*(\d{2}/\d{2}/\d{4})', html)
        
        # Armar resultados
        for i in range(min(len(codigos), 20)):
            compra = {
                "codigo": codigos[i] if i < len(codigos) else None,
                "titulo": titulos[i] if i < len(titulos) else None,
                "organismo": organismos[i] if i < len(organismos) else None,
                "presupuesto": f"$ {presupuestos[i]}" if i < len(presupuestos) else None,
                "fecha_publicacion": fechas_pub[i] if i < len(fechas_pub) else None,
                "fecha_cierre": fechas_cierre[i] if i < len(fechas_cierre) else None,
                "estado": "Recibiendo cotizaciones"
            }
            if compra["codigo"]:
                compras.append(compra)
        
        return compras


def buscar(**kwargs) -> dict:
    """Función helper para usar desde Python"""
    scraper = MercadoPublicoScraper().start()
    try:
        result = scraper.search(**kwargs)
        return result
    finally:
        scraper.close()


if __name__ == "__main__":
    print("=== Mercado Público Scraper ===")
    print("Buscando compras...")
    
    scraper = MercadoPublicoScraper().start()
    try:
        result = scraper.search(
            estado="publicada",
            order_by="reciente",
            pagina=1
        )
        
        print(f"\nTotal resultados: {result['pagination']['total']}")
        print(f"Compras encontradas: {len(result['data'])}")
        
        if result['data']:
            print("\nEjemplo:")
            print(json.dumps(result['data'][0], indent=2, ensure_ascii=False))
        
    finally:
        scraper.close()
