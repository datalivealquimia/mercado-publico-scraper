# Mercado Público Scraper & API

API para consultar compras públicas de Chile - Compra Ágil.

## Datos

- **6,611 resultados** disponibles en el portal
- Datos extraídos directamente del sitio usando browser automation

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python api.py
```

API disponible en: **http://localhost:8000**

## Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API |
| GET | `/compra-agil` | Lista compras (soporta paginación y filtros) |
| GET | `/compra-agil/{codigo}` | Busca por código |
| GET | `/compra-agil/search?q=texto` | Busca en título u organismo |

## Ejemplos

```bash
# Listar compras (primera página, 15 por página)
curl "http://localhost:8000/compra-agil"

# Segunda página
curl "http://localhost:8000/compra-agil?page=2"

# Filtrar por organismo
curl "http://localhost:8000/compra-agil?organismo=municipalidad"

# Filtrar por presupuesto
curl "http://localhost:8000/compra-agil?presupuesto_min=1000000&presupuesto_max=5000000"

# Buscar por texto
curl "http://localhost:8000/compra-agil/search?q=salud"

# Buscar por código
curl "http://localhost:8000/compra-agil/2445-79-COT26"
```

## Estructura de datos

```json
{
  "codigo": "2445-79-COT26",
  "titulo": "ADQUISICION DE SMART TV",
  "organismo": "I MUNICIPALIDAD DE CURICO",
  "presupuesto": "$ 600.000",
  "fecha_publicacion": "06/03/2026",
  "fecha_cierre": "09/03/2026",
  "estado": "Recibiendo cotizaciones"
}
```

## Actualizar datos

Para actualizar los datos, usar el script de scraping con Playwright:

```bash
python scraper.py
```

## Docker

```bash
docker build -t mercado-publico-api .
docker run -p 8000:8000 mercado-publico-api
```
