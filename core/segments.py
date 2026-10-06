"""
segments.py
------------
Turns real stock price data into the line segments that sweep_line.py
needs, and fetches that data from Yahoo Finance.

Coordinate system used everywhere in this project:
  x = day index (0, 1, 2, ... in order), y = price.
Using a plain day index instead of real calendar dates keeps the geometry
simple -- we convert back to real dates only when sending the answer to
the frontend.
"""

from __future__ import annotations
from typing import List, Dict
import pandas as pd
import yfinance as yf

from core.sweep_line import Segment, Point


def load_prices_from_yahoo(ticker: str, period: str = "2y") -> pd.DataFrame:
    """Fetch real daily price history for a stock ticker.

    Examples of valid tickers:
      "AAPL"      -> Apple (US market)
      "TCS.NS"    -> TCS (India, NSE)
      "RELIANCE.NS" -> Reliance Industries (India, NSE)
    """
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"No data found for ticker '{ticker}'")

    df = df.reset_index()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def add_moving_averages(df: pd.DataFrame, windows=(50, 200)) -> pd.DataFrame:
    """SMA = Simple Moving Average = average of the last N closing prices."""
    for w in windows:
        df[f"SMA{w}"] = df["Close"].rolling(window=w, min_periods=w).mean()
    return df


def series_to_segments(y_values, label: str) -> List[Segment]:
    """Turn one line (a list of prices, one per day) into a chain of
    small straight segments, skipping over any missing values (e.g. the
    first 50 days have no SMA50 yet)."""
    segs = []
    prev_x, prev_y = None, None
    for x, y in enumerate(y_values):
        if pd.isna(y):
            prev_x, prev_y = None, None
            continue
        if prev_x is not None:
            segs.append(Segment(Point(prev_x, prev_y), Point(x, y), label=label))
        prev_x, prev_y = x, y
    return segs


def build_segment_set(df: pd.DataFrame, lines: Dict[str, str]) -> List[Segment]:
    """lines: e.g. {"Close": "Close", "SMA50": "SMA50", "SMA200": "SMA200"}"""
    all_segments: List[Segment] = []
    for label, column in lines.items():
        all_segments.extend(series_to_segments(df[column].values, label=label))
    return all_segments
