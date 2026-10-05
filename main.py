import asyncio
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from market_data.ingestion import MarketDataIngestor


def plot_market_data(symbol: str, df):
    """Genera el gráfico interactivo ÚNICAMENTE para el activo seleccionado."""
    df["SMA20"] = df["close"].rolling(window=20).mean()
    df["SMA50"] = df["close"].rolling(window=50).mean()

    # Asignamos color verde para días alcistas y rojo para bajistas
    colors = ['#26a69a' if row['close'] >= row['open'] else '#ef5350' for _, row in df.iterrows()]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f"Análisis Técnico de Precios: {symbol}", "Volumen de Negociación"),
        row_width=[0.30, 0.70]
    )

    # 1. Velas Japonesas
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            name="Precio (OHLC)"
        ),
        row=1, col=1
    )

    # 2. Promedios Móviles
    fig.add_trace(
        go.Scatter(x=df.index, y=df["SMA20"], mode="lines", name="SMA 20 Días", line=dict(color="orange", width=1.5)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["SMA50"], mode="lines", name="SMA 50 Días", line=dict(color="#1f77b4", width=1.5)),
        row=1, col=1
    )

    # 3. Barras de Volumen
    fig.add_trace(
        go.Bar(
            x=df.index, 
            y=df["volume"], 
            name="Volumen", 
            marker_color=colors,
            opacity=0.85
        ),
        row=2, col=1
    )

    fig.update_layout(
        title=f"📊 Dashboard Financiero Interactivo — {symbol}",
        yaxis_title="Precio (USD)",
        yaxis2_title="Volumen",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=750
    )

    fig.update_yaxes(autorange=True, row=2, col=1)

    # Muestra únicamente la figura del activo seleccionado
    fig.show()


async def main():
    # 🗓️ Configuración de Rango de Fechas
    FECHA_INICIO = "2026-01-01"
    FECHA_FIN    = "2026-06-30"
    symbols      = ["BTC-USD", "AAPL", "NVDA", "MSFT"]

    ingestor = MarketDataIngestor(max_workers=4)

    print(f"📥 Descargando datos desde {FECHA_INICIO} hasta {FECHA_FIN} para: {symbols}...\n")

    data = await ingestor.fetch_multiple_ohlcv(
        symbols=symbols,
        interval="1d",
        start=FECHA_INICIO,
        end=FECHA_FIN
    )

    loop = asyncio.get_running_loop()

    while True:
        print("\n" + "=" * 60)
        print(f" 📈 RANGO SELECCIONADO: {FECHA_INICIO} ➔ {FECHA_FIN}")
        print("=" * 60)

        for i, symbol in enumerate(symbols, 1):
            if symbol in data:
                precio_actual = data[symbol]["close"].iloc[-1]
                rendimiento = ((precio_actual - data[symbol]["close"].iloc[0]) / data[symbol]["close"].iloc[0]) * 100
                print(f"  {i}. {symbol:10s} | Último Precio: ${precio_actual:10,.2f} | Rendimiento: {rendimiento:+.2f}%")

        print("  0. Salir")
        print("=" * 60)

        opcion = await loop.run_in_executor(None, input, "\nIngresa el número del activo a graficar (0 para salir): ")
        opcion = opcion.strip()

        if opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break

        if opcion.isdigit():
            idx = int(opcion) - 1
            if 0 <= idx < len(symbols):
                symbol_elegido = symbols[idx]
                if symbol_elegido in data:
                    print(f"\n🌐 Abriendo ÚNICAMENTE el gráfico para {symbol_elegido}...")
                    # Se llama a la función pasando SOLO el DataFrame del activo elegido
                    plot_market_data(symbol_elegido, data[symbol_elegido])
                else:
                    print(f"\n❌ No hay datos disponibles para {symbol_elegido}.")
            else:
                print("\n❌ Número fuera de rango.")
        else:
            print("\n❌ Por favor, ingresa solo un número.")

    ingestor.close()


if __name__ == "__main__":
    asyncio.run(main())
