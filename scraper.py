"""
Mercado Público Scraper - Async Version
Para usar con FastAPI async
"""
from playwright.async_api import async_playwright
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
    
    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        context = await self.browser.new_context(
            locale='es-CL',
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await context.new_page()
        await self.page.add_init_script(
            'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
        )
        return self
    
    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def build_url(self, params: dict) -> str:
        from urllib.parse import urlencode
        return f"{BASE_URL}?{urlencode(params)}"
    
    async def search(
        self,
        keyword: str = None,
        codigo: str = None,
        estado: str = "publicada",
        fecha_desde: str = None,
        fecha_hasta: str = None,
        region: str = None,
        order_by: str = "reciente",
        pagina: int = 1
    ) -> dict:
        
        estado_map = {"publicada": "2", "cerrada": "3", "oc_emitida": "4", "todos": "1"}
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
        
        url = self.build_url(params)
        logger.info(f"Buscando: {url}")
        
        try:
            response = await self.page.goto(url, wait_until="networkidle", timeout=30000)
            logger.info(f"Status: {response.status}")
            
            # Esperar resultados
            try:
                await self.page.wait_for_selector("text=resultados", timeout=10000)
            except:
                pass
            
            html = await self.page.content()
            
            # Extraer total
            total = 0
            total_match = re.search(r'(\d+)\s+resultados', html)
            if total_match:
                total = int(total_match.group(1))
            
            # Extraer compras
            compras = self._extract_compras(html)
            
            return {
                "success": True,
                "data": compras,
                "total": total,
                "pagination": {
                    "total": total,
                    "pagina": pagina
                }
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_compras(self, html: str) -> List[dict]:
        soup = BeautifulSoup(html, 'html.parser')
        compras = []
        
        codigos = re.findall(r'(\d{4,5}-\d{1,3}-COT\d{2})', html)
        titulos = [h.get_text().strip() for h in soup.find_all('h4')]
        presupuestos = re.findall(r'\$\s*([\d.]+)', html)
        
        org_keywords = ['MUNICIPALIDAD', 'HOSPITAL', 'UNIVERSIDAD', 'DEFENSORIA', 
                       'INSTITUTO', 'EJERCITO', 'FUERZAS', 'DIRECCIÓN', 'CORP', 'SERVICIO']
        organismos = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if any(kw in text.upper() for kw in org_keywords):
                org = text.split('\n')[0].strip()
                if org and len(org) > 5:
                    organismos.append(org[:120])
        
        fechas_pub = re.findall(r'Publicada el\s*(\d{2}/\d{2}/\d{4})', html)
        fechas_cierre = re.findall(r'Finaliza el\s*(\d{2}/\d{2}/\d{4})', html)
        
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


async def buscar(**kwargs) -> dict:
    scraper = await MercadoPublicoScraper().start()
    try:
        result = await scraper.search(**kwargs)
        return result
    finally:
        await scraper.close()


if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== Mercado Público Scraper (Async) ===")
        result = await buscar(estado="publicada", pagina=1)
        print(f"Total: {result.get('total', 0)}")
        print(f"Compras: {len(result.get('data', []))}")
        if result.get('data'):
            print(f"Ejemplo: {result['data'][0]}")
    
    asyncio.run(test())
