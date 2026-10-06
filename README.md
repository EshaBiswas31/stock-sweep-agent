# Stock Market Analysis Agent (Mini Project)

A one-page web app: type a stock ticker, click Analyze, see its price chart
with Buy/Sell signals marked at every point where the price crossed its
moving averages — found using the **Line Segment Intersection (sweep line)
algorithm**.

## Project structure

```
mini_project/
  public/              <- Frontend (plain HTML/CSS/JS, no framework)
    index.html
    style.css
    script.js
  api/
    app.py             <- Backend (one Flask file, this is the whole API)
  core/                <- The algorithm, kept separate from the web code
    sweep_line.py       The sweep-line algorithm itself
    segments.py          Fetches real stock data, builds line segments
    agent.py             Turns crossings into BUY/SELL decisions
    backtest.py           Simulates the decisions on real history
  requirements.txt     <- Python packages needed (flask, pandas, yfinance)
  vercel.json          <- Tells Vercel how to deploy this
```

## How to explain the code (walkthrough order)

1. **`core/sweep_line.py`** — start here. This is the actual algorithm from
   class. Read the big docstring at the top first: it explains the idea
   (every line is a chain of segments, a crossover is an intersection),
   then explains the sweep (event queue + status structure), then explains
   why it's faster than brute force. `find_intersections()` is the main
   function — it's a direct implementation of `FindIntersections` /
   `HandleEventPoint` / `FindNewEvent` from the slides, using Python's
   built-in `heapq` for the event queue (a min-heap is a simple, well-known
   way to always process the next event first) and a plain sorted list for
   the "status structure" (segments currently crossing the sweep line).

2. **`core/segments.py`** — turns a stock's price data into segments.
   `load_prices_from_yahoo()` fetches real daily prices using `yfinance`.
   `add_moving_averages()` computes SMA50 and SMA200 (just rolling
   averages, using pandas' built-in `.rolling().mean()`). `series_to_segments()`
   converts one line (a list of prices) into the small Segment objects the
   algorithm needs — one segment per day, connecting yesterday's value to
   today's.

3. **`core/agent.py`** — the decision rules. `generate_signals()` looks at
   each crossing found by the algorithm and classifies it: if Price crossed
   above SMA50 → BUY; if SMA50 crossed below SMA200 → SELL (Death Cross),
   etc. This is deliberately simple — the algorithmic contribution is
   *finding* the crossings efficiently, not the trading rule itself.

4. **`core/backtest.py`** — replays the signals on real price history.
   Starts with a pretend ₹1,00,000, goes all-in on a BUY, goes back to cash
   on a SELL, and compares the result to simply buying and holding.

5. **`api/app.py`** — the backend web server (Flask). Has exactly two
   routes: `/api/health` (just confirms the server is alive) and
   `/api/analyze?ticker=XYZ` (runs steps 2-4 above in order and returns
   everything as JSON). Read this top to bottom — it's commented
   Step 1 through Step 7 and mirrors the pipeline exactly.

6. **`public/script.js`** — the frontend logic. Calls `/api/analyze`,
   then draws the chart using Chart.js (a well-known charting library,
   loaded from a CDN link in `index.html`) and fills the signals table.
   No build step, no framework — it's a single `fetch()` call and some
   DOM updates.

## Running it locally

```bash
pip install -r requirements.txt
python api/app.py
```

Then open `http://localhost:5000` in a browser.

## Deploying it (Vercel)

1. Push this folder to a GitHub repository.
2. Go to vercel.com, "New Project", import that repository.
3. Vercel reads `vercel.json` automatically: it builds `api/app.py` as a
   Python serverless function and serves everything in `public/` as static
   files. No extra configuration needed.
4. Click Deploy. You get a live link (e.g. `yourproject.vercel.app`).

## Why the algorithm matters here (for the viva)

The obvious way to find crossings is to compare every line against every
other line, point by point — with n segments that's roughly n² comparisons.
The sweep-line algorithm only compares segments that are near each other at
any given moment as it scans top to bottom, so it runs in about
**(n + k) log n** time, where k is the number of crossings actually found.
This is called an **output-sensitive algorithm** — it only does more work
when there's actually more to find. The `algorithm_stats` field returned by
`/api/analyze` (number of segments, number of crossings found) is there
specifically so this can be pointed out and discussed live during a demo.

## Future scope

- Add more lines to watch (trendlines, Bollinger Bands) — same algorithm,
  just add more segments to the same list.
- Add a simple watchlist / saved history (would need a small database —
  the natural next phase after this one).
- Compare two different stocks against each other on the same chart.
- Replace the simple crossover rule with a smarter one (volume, volatility).
