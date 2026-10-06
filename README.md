# StockSetu

*Setu* means "bridge" — this app is a bridge between raw NSE/BSE market data
and a clear, numeric answer about a company: a **Fundamental Score**, a
**Quantitative Score**, and one combined **Overall Score**.

## What it does

1. Sign up / log in (with "Forgot password" via a real emailed reset link).
2. Search any NSE or BSE company symbol (e.g. `TCS`, `RELIANCE`, `INFY`).
3. The backend fetches real data from Yahoo Finance and computes:
   - **Fundamental Score** — P/E ratio, Return on Equity, Debt-to-Equity,
     Profit Margin, Revenue Growth
   - **Quantitative Score** — 6-month momentum, volatility, 14-day RSI,
     position vs. 50/200-day moving averages
   - **Overall Score** (average of the two) with a Strong Buy / Buy / Hold /
     Sell / Strong Sell label
4. See the result on a gauge, with a breakdown of every sub-metric, plus a
   1-year price chart with moving averages.
5. **Admins** get a separate panel to view all users and enable/disable
   accounts or promote/demote admins.

## Project structure

```
stocksetu/
  public/              Frontend - plain HTML/CSS/JS, no framework, no build step
    login.html, signup.html, forgot.html, reset.html
    dashboard.html, admin.html
    style.css, common.js, dashboard.js, admin.js
  api/
    app.py             The ENTIRE backend - one Flask file, every route
  core/
    db.py               All SQL (Postgres) - tables, admin seeding
    scoring.py           The two scoring formulas (pure Python, no DB/network)
    yahoo.py             Fetches data from Yahoo Finance
    mailer.py            Sends the password-reset email (Gmail SMTP)
  requirements.txt
  vercel.json
  push.bat             One-click "commit + push" for quick redeploys
```

## How to explain the code (viva walkthrough order)

1. **`core/scoring.py`** — start here, it has no dependencies on Flask,
   the database, or the internet. Each metric (P/E, ROE, RSI, etc.) is
   turned into a 0-100 "band score" using simple thresholds (explained in
   the comments above each function), then averaged. This is the part
   worth explaining in most depth — it's the actual "analysis" in the
   project.

2. **`core/yahoo.py`** — fetches real price history and company
   fundamentals via the `yfinance` library. `build_yahoo_symbol()` shows
   how a plain symbol like `TCS` + exchange `NSE` becomes `TCS.NS` for
   Yahoo Finance.

3. **`core/db.py`** — every SQL query the app uses, in one place, in
   plain readable SQL (no ORM). `init_db()` creates the two tables
   (`users`, `score_cache`) and seeds the first admin account.

4. **`core/mailer.py`** — sends the password-reset email via Gmail's
   SMTP server.

5. **`api/app.py`** — the whole backend, organized into five clearly
   labelled sections (read the comment at the top of the file). Each
   route is short: get input -> call a `core/` function -> return JSON.

6. **`public/dashboard.js`** — the main frontend logic: calls
   `/api/analyze`, then fills in the gauge, the two score bars, the
   breakdown lists, and the chart.

## Setting it up (do this once, before deploying)

### 1. Create a Vercel Postgres database

1. In your Vercel project (after importing from GitHub), go to the
   **Storage** tab -> **Create Database** -> **Postgres** (powered by Neon).
2. Once created, Vercel automatically adds a `DATABASE_URL` environment
   variable to your project. You don't need to copy/paste anything.

### 2. Set the admin account

In your Vercel project -> **Settings** -> **Environment Variables**, add:

| Name | Value |
|---|---|
| `ADMIN_EMAIL` | the email you want to log in as admin with |
| `ADMIN_PASSWORD` | a password for that admin account |
| `ADMIN_NAME` | (optional) your name |
| `SECRET_KEY` | any long random string (used to sign login sessions) |

### 3. Set up email sending (for "Forgot Password")

You need a Gmail account and an **App Password** (not your normal Gmail
password — Google blocks that for security):

1. Go to your Google Account -> **Security**.
2. Turn on **2-Step Verification** if it isn't already on (required for
   App Passwords to be available).
3. Go to **myaccount.google.com/apppasswords**.
4. Create a new App Password (name it "StockSetu" or similar), choose
   "Mail" as the app. Google gives you a 16-character password.
5. In Vercel's Environment Variables, add:

| Name | Value |
|---|---|
| `SMTP_EMAIL` | your Gmail address |
| `SMTP_APP_PASSWORD` | the 16-character App Password (no spaces) |

### 4. Deploy

Push this project to GitHub, import it into Vercel, click Deploy.
`vercel.json` handles the rest automatically. See the separate deployment
walkthrough for exact click-by-click steps.

### 5. Redeploying after changes

Just run `push.bat` (double-click it, or run it from cmd). It commits and
pushes your changes to GitHub, and Vercel automatically redeploys.

## Why these two scores (for the viva)

The obvious way to judge a stock is "is the business good?" (fundamentals)
and "has the price been behaving well?" (quantitative/technical). This
project keeps both, computed from the same data source (Yahoo Finance), with
transparent, explainable band-based scoring rather than an opaque model —
every number on screen can be traced back to one line of code.

## Future scope

- Add a third pillar: simple technical indicators (MACD, Bollinger Bands).
- Let users save a personal watchlist (small new table, same database).
- Compare two companies side-by-side.
- Add the Line Segment Intersection (sweep-line) crossover detector from
  the earlier version of this project as a bonus "Technical Signals" tab.
- Batch-score an entire index (e.g. NIFTY 50) overnight via a scheduled job,
  instead of only on-demand per search.
