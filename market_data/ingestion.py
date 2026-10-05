"""
Módulo de ingestión asíncrona de datos de mercado (OHLCV).
Contiene la validación estricta de tipos con Pydantic y la optimización de pandas.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator


# ----------------------------------------------------------------------
# 1. Esquema de validación estricta con Pydantic
# ----------------------------------------------------------------------

class OHLCVRecord(BaseModel):
    """Define y valida la estructura exacta de un solo dato/vela de mercado."""
    timestamp: datetime
    open: float = Field(gt=0, description="El precio de apertura debe ser mayor a 0")
    high: float = Field(gt=0, description="El precio máximo debe ser mayor a 0")
    low: float = Field(gt=0, description="El precio mínimo debe ser mayor a 0")
    close: float = Field(gt=0, description="El precio de cierre debe ser mayor a 0")
    volume: float = Field(ge=0, description="El volumen no puede ser negativo")

    @field_validator("high")
    @classmethod
    def validate_high(cls, v: float, info) -> float:
        if "open" in info.data and v < info.data["open"]:
            raise ValueError("El precio 'high' no puede ser menor que 'open'.")
        if "low" in info.data and v < info.data["low"]:
            raise ValueError("El precio 'high' no puede ser menor que 'low'.")
        return v

    @field_validator("low")
    @classmethod
    def validate_low(cls, v: float, info) -> float:
        if "open" in info.data and v > info.data["open"]:
            raise ValueError("El precio 'low' no puede ser mayor que 'open'.")
        return v


# ----------------------------------------------------------------------
# 2. Clase Principal de Ingestión Asíncrona
# ----------------------------------------------------------------------

class MarketDataIngestor:
    """Ingestor asíncrono de series temporales financieras."""

    def __init__(self, max_workers: int = 5):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def fetch_ohlcv(
        self,
        symbol: str,
        period: Optional[str] = "1mo",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Descarga datos OHLCV. Acepta 'period' o un rango explícito 'start'/'end' (YYYY-MM-DD).
        """
        loop = asyncio.get_running_loop()

        raw_df = await loop.run_in_executor(
            self._executor,
            self._download_yfinance,
            symbol,
            period,
            interval,
            start,
            end
        )

        validated_df = self._process_and_validate(raw_df)
        optimized_df = self._optimize_dataframe(validated_df)

        return optimized_df

    async def fetch_multiple_ohlcv(
        self,
        symbols: List[str],
        period: Optional[str] = "1mo",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """Descarga múltiples activos de forma concurrente con opción de fechas inicio/fin."""
        tasks = [
            self.fetch_ohlcv(symbol, period=period, interval=interval, start=start, end=end)
            for symbol in symbols
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data_dict = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                print(f"❌ Error descargando {symbol}: {result}")
            else:
                data_dict[symbol] = result

        return data_dict

    @staticmethod
    def _download_yfinance(
        symbol: str,
        period: Optional[str],
        interval: str,
        start: Optional[str],
        end: Optional[str]
    ) -> pd.DataFrame:
        """Descarga directa desde Yahoo Finance usando period o start/end."""
        import yfinance as yf
        ticker = yf.Ticker(symbol)

        if start and end:
            df = ticker.history(start=start, end=end, interval=interval, auto_adjust=True)
        else:
            df = ticker.history(period=period, interval=interval, auto_adjust=True)

        if df.empty:
            raise ValueError(f"No se obtuvieron datos para '{symbol}'. Revisa las fechas o el símbolo.")

        return df

    def _process_and_validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia nombres de columnas y aplica la validación estricta de Pydantic."""
        df = df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        })

        cols = ["open", "high", "low", "close", "volume"]
        df = df[cols].copy().reset_index()

        time_col = "Date" if "Date" in df.columns else "Datetime"
        df = df.rename(columns={time_col: "timestamp"})

        records = df.to_dict(orient="records")
        validated_records = [OHLCVRecord(**rec).model_dump() for rec in records]

        clean_df = pd.DataFrame(validated_records)
        clean_df.set_index("timestamp", inplace=True)
        return clean_df

    @staticmethod
    def _optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Reduce el uso de memoria a float32 y asegura fechas en zona UTC."""
        float_cols = ["open", "high", "low", "close"]
        df[float_cols] = df[float_cols].astype(np.float32)
        df["volume"] = df["volume"].astype(np.float64)

        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")

        return df

    def close(self):
        """Cierra el pool de hilos para liberar memoria."""
        self._executor.shutdown(wait=True)

