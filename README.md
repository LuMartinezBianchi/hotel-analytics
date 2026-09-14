# Hotel Booking Analytics — Hotel Aurora Bay (proyecto ficticio)

Pipeline de datos SQL + Python y dashboard interactivo en Power BI para analizar
ocupación, ADR (tarifa promedio diaria), RevPAR y satisfacción de huéspedes de
un hotel ficticio de 60 habitaciones.

## Stack

- **SQL (SQLite)** — esquema normalizado (huéspedes, habitaciones, tarifas, reservas, reseñas) y consultas de KPIs con CTE recursiva.
- **Python** (`Faker`, `pandas`) — generación de datos sintéticos realistas y cálculo de KPIs.
- **Power BI Desktop** — modelo de datos y dashboard interactivo.

## KPIs calculados

- **Tasa de ocupación** — noches vendidas / noches disponibles
- **ADR** (Average Daily Rate) — ingresos por habitación / noches vendidas
- **RevPAR** (Revenue per Available Room) — ingresos por habitación / noches disponibles
- **Satisfacción de huéspedes** — rating promedio (1-5) por tipo de habitación

## Estructura del proyecto

```
hotel-analytics-project/
├── sql/
│   ├── schema.sql          # esquema normalizado de la base
│   └── kpi_queries.sql     # consultas SQL de referencia para los KPIs
├── python/
│   ├── generate_data.py    # genera datos sintéticos y crea data/hotel.db
│   └── calculate_kpis.py   # calcula KPIs y exporta CSVs para Power BI
├── data/                   # generado localmente (no versionado, ver .gitignore)
├── powerbi/
│   └── hotel_dashboard.pbix
├── requirements.txt
└── README.md
```

## Cómo correrlo

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python python/generate_data.py
python python/calculate_kpis.py
```

Esto crea `data/hotel.db` y los CSVs (`dim_*`, `fact_*`, `kpi_*`) listos para
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
