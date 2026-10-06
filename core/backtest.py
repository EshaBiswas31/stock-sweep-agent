"""
backtest.py
-----------
Takes the agent's BUY/SELL signals and "replays" them on the real
historical prices, to answer: "if a person had actually followed these
signals, how much money would they have, compared to simply buying the
stock on day 1 and holding it?"

This is a simple long-only simulation: start with cash, go all-in on a
BUY, go back to cash on a SELL. No shorting, no partial positions --
kept simple on purpose so it's easy to explain and check by hand.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List
import pandas as pd
from core.agent import Signal


@dataclass
class Trade:
    action: str
    day_index: int
    price: float


@dataclass
class BacktestResult:
    trades: List[Trade]
    final_equity: float
    strategy_return_pct: float
    buy_hold_return_pct: float
    starting_cash: float


def backtest(df: pd.DataFrame, signals: List[Signal], starting_cash: float = 100_000.0) -> BacktestResult:
    cash = starting_cash
    shares = 0.0
    holding = False
    trades: List[Trade] = []

    n = len(df)
    for sig in signals:
        day = int(round(sig.day_index))
        if day < 0 or day >= n:
            continue
        price = float(df["Close"].iloc[day])

        if sig.action == "BUY" and not holding:
            shares = cash / price
            cash = 0.0
            holding = True
            trades.append(Trade("BUY", day, price))
        elif sig.action == "SELL" and holding:
            cash = shares * price
            shares = 0.0
            holding = False
            trades.append(Trade("SELL", day, price))

    last_price = float(df["Close"].iloc[-1])
    final_equity = cash + shares * last_price

    first_price = float(df["Close"].iloc[0])
    buy_hold_final = (starting_cash / first_price) * last_price

    return BacktestResult(
        trades=trades,
        final_equity=final_equity,
        strategy_return_pct=(final_equity / starting_cash - 1) * 100,
        buy_hold_return_pct=(buy_hold_final / starting_cash - 1) * 100,
        starting_cash=starting_cash,
    )
