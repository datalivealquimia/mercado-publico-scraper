# Mercado Público Scraper & API

Scraper y API REST para consultas del portal ChileCompra - Compra Ágil.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso como API

```bash
python api.py
```

La API estará disponible en `http://localhost:8000`

### Endpoints

- `GET /` - Información de la API
- `GET /health` - Health check
- `GET /compra-agil` - Buscar compras (parámetros query)
- `GET /compra-agil/search` - Búsqueda avanzada
- `GET /compra-agil/url` - Generar URL

### Ejemplos

```bash
# Buscar compras publicadas
curl "http://localhost:8000/compra-agil?date_from=2026-02-01&date_to=2026-03-06"

# Buscar por región
curl "http://localhost:8000/compra-agil?region=RM&page=1"

# Búsqueda avanzada
curl "http://localhost:8000/compra-agil/search?q=computadores&max_pages=5"
```

## Uso como scraper

```python
from scraper import scrape_page, scrape_all

# Una página
data = scrape_page(date_from="2026-02-01", date_to="2026-03-06")

# Múltiples páginas
results = scrape_all(date_from="2026-02-01", max_pages=10, delay=2.0)
```

## Docker (opcional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "api.py"]
```

## Notas

- Respetar delays entre requests para no bloquear el servidor
- Usar datos responsablemente según términos de ChileCompra
- Para uso productivo, considerar la API oficial o datos abiertos
