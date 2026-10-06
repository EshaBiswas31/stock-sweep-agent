"""
app.py
------
The whole backend. This is a Flask app (the simplest Python web
framework) with just two routes:

  GET /api/health            -> simple "is the server alive" check
  GET /api/analyze?ticker=X  -> the main endpoint: fetches the stock's
                                 real price history, runs the algorithm,
                                 and returns the results as JSON for the
                                 frontend to draw.

This single file is the entire backend "API layer" -- there is no
database and no user accounts, so there is nothing else to explain here
beyond these two routes.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify, send_from_directory
import pandas as pd

from core.segments import load_prices_from_yahoo, add_moving_averages, build_segment_set
from core.sweep_line import find_intersections
from core.agent import generate_signals
from core.backtest import backtest

PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "public")
app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path="")


@app.route("/")
def home():
    return send_from_directory(PUBLIC_DIR, "index.html")

MIN_DAYS_NEEDED = 210  # need at least ~210 trading days for SMA200 to exist


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/analyze")
def analyze():
    ticker = request.args.get("ticker", "").strip().upper()
    if not ticker:
        return jsonify({"error": "Please enter a stock ticker, e.g. AAPL or TCS.NS"}), 400

    # ---- Step 1: get real price history ----
    try:
        df = load_prices_from_yahoo(ticker)
    except Exception:
        return jsonify({"error": f"Couldn't fetch data for '{ticker}'. Check the symbol and try again."}), 400

    if len(df) < MIN_DAYS_NEEDED:
        return jsonify({
            "error": f"Not enough price history for '{ticker}' "
                     f"(found {len(df)} days, need at least {MIN_DAYS_NEEDED})."
        }), 400

    # ---- Step 2: compute the moving averages ----
    df = add_moving_averages(df, windows=(50, 200))

    # ---- Step 3: turn Price / SMA50 / SMA200 into line segments ----
    segments = build_segment_set(df, {"Close": "Close", "SMA50": "SMA50", "SMA200": "SMA200"})

    # ---- Step 4: run the sweep-line algorithm to find every crossing ----
    intersections = find_intersections(segments)

    # ---- Step 5: agent turns crossings into BUY/SELL signals ----
    signals = generate_signals(intersections, segments)

    # ---- Step 6: backtest the signals against real history ----
    result = backtest(df, signals)

    # ---- Step 7: package everything for the frontend ----
    def clean(series):
        return [None if pd.isna(v) else round(float(v), 2) for v in series]

    response = {
        "ticker": ticker,
        "dates": df["Date"].dt.strftime("%Y-%m-%d").tolist(),
        "close": clean(df["Close"]),
        "sma50": clean(df["SMA50"]),
        "sma200": clean(df["SMA200"]),
        "signals": [
            {
                "day": int(round(s.day_index)),
                "price": round(s.price_at_signal, 2),
                "action": s.action,
                "reason": s.reason,
            }
            for s in signals if 0 <= int(round(s.day_index)) < len(df)
        ],
        "backtest": {
            "starting_cash": result.starting_cash,
            "final_equity": round(result.final_equity, 2),
            "strategy_return_pct": round(result.strategy_return_pct, 2),
            "buy_hold_return_pct": round(result.buy_hold_return_pct, 2),
            "num_trades": len(result.trades),
        },
        "algorithm_stats": {
            "num_segments": len(segments),
            "num_crossings_found": len(intersections),
            "num_tradeable_signals": len(signals),
        },
    }
    return jsonify(response)


# Local testing: `python api/app.py` runs this on http://localhost:5000
if __name__ == "__main__":
    app.run(debug=True, port=5000)
