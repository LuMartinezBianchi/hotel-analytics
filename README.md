# Hotel Booking Analytics — Cuesta Blanca Hotel (proyecto ficticio)

Pipeline de datos SQL + Python y dashboard interactivo en Power BI para analizar
ocupación, ADR (tarifa promedio diaria), RevPAR y satisfacción de huéspedes de
un hotel ficticio de 60 habitaciones.

## Stack

- **SQL (SQLite)** — esquema normalizado (huéspedes, habitaciones, tarifas, reservas, reseñas).
- **Python** (`Faker`, `pandas`) — generación de datos sintéticos realistas y exportación a CSV.
- **Power BI Desktop** — modelo de datos, medidas DAX y dashboard interactivo.

## KPIs (calculados en Power BI con DAX)

- **Tasa de ocupación** — noches vendidas / noches disponibles
- **ADR** (Average Daily Rate) — ingresos por habitación / noches vendidas
- **RevPAR** (Revenue per Available Room) — ingresos por habitación / noches disponibles
- **Satisfacción de huéspedes** — rating promedio (1-5) por tipo de habitación

Ocupación, ADR y RevPAR se calculan en vivo dentro de Power BI (medidas DAX
sobre `fact_reservations`), no en Python — así el dashboard se recalcula solo
ante cualquier filtro de fecha o tipo de habitación. `sql/kpi_queries.sql`
queda como referencia de cómo se resolvería el mismo problema en SQL puro
(con una CTE recursiva).

## Estructura del proyecto
hotel-analytics-project/
├── sql/
│ ├── schema.sql # esquema normalizado de la base
│ └── kpi_queries.sql # referencia: los mismos KPIs resueltos en SQL puro
├── python/
│ ├── generate_data.py # genera datos sintéticos y crea data/hotel.db
│ └── export_data.py # exporta las tablas a CSV para Power BI
├── data/ # generado localmente (no versionado, ver .gitignore)
├── powerbi/
│ └── hotel_dashboard.pbix
├── requirements.txt
└── README.md

## Cómo correrlo

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python python/generate_data.py
python python/export_data.py
```

Esto crea `data/hotel.db` y los CSVs (`dim_*`, `fact_*`) listos para
importar en Power BI Desktop.

## Dashboard

El dashboard (`powerbi/hotel_dashboard.pbix`) incluye:

- Resumen general: ocupación, ADR y RevPAR con tendencia mensual
- Estacionalidad por temporada y tipo de habitación
- Satisfacción de huéspedes por tipo de habitación y canal de reserva

![Dashboard preview](powerbi/dashboard_preview.png)

## Datos

Todos los datos son sintéticos, generados con [Faker](https://faker.readthedocs.io/)
para un hotel ficticio. No representan huéspedes ni reservas reales.

## Autora

Lucía Martínez Bianchi
