# market-data-ingestor
# 📈 Market Data Ingestor

Un motor asíncrono y optimizado en Python para la ingesta, validación estricta y visualización interactiva de series temporales financieras (datos OHLCV) desde Yahoo Finance.

---

## 🚀 Características Principales

- **Ingesta Asíncrona:** Descarga concurrente de múltiples activos financieros usando `asyncio` y `ThreadPoolExecutor` para evitar bloqueos de red.
- **Validación Estricta con Pydantic:** Control de calidad de datos fila por fila (`OHLCVRecord`), asegurando incoherencias cero (precios mayores a 0, valores altos/bajos coherentes y volumen no negativo).
- **Optimización de Memoria:** Reducción del uso de RAM convirtiendo las columnas de precios a `float32` y estandarizando las marcas de tiempo a zona horaria **UTC**.
- **Dashboard Interactivo con Plotly:** Gráficos profesionales de velas japonesas (*Candlestick*), promedios móviles (*SMA 20* y *SMA 50*) y volumen de negociación coloreado por tendencia (alcista/bajista).
- **Menú Interactivo de Selección:** Interfaz de consola que permite seleccionar y visualizar de forma individual la gráfica del activo deseado.
- **Rango de Fechas Personalizable:** Filtrado exacto de periodos históricos usando parámetros `start` y `end`.

---

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.10+
- **Descarga de datos:** `yfinance`
- **Manipulación de datos:** `pandas`, `numpy`
- **Validación de tipos:** `pydantic`
- **Visualización:** `plotly`

---

## 📂 Estructura del Proyecto

```text
market-data-ingestor/
│
├── market_data/
│   ├── __init__.py         # Exportación limpia de MarketDataIngestor y OHLCVRecord
│   └── ingestion.py        # Validador Pydantic e Ingestor Asíncrono
│
├── .venv/                  # Entorno virtual de Python
├── main.py                 # Script principal con menú y visualización
├── requirements.txt        # Dependencias del proyecto
├── README.md               # Documentación del proyecto
└── .gitignore              # Archivos excluidos de Git