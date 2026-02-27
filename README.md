# 📈 SMA Crossover Backtesting Engine (Python)

## Overview
This project is a Python-based backtesting system that evaluates a simple moving average (SMA) crossover trading strategy on historical stock price data. The strategy is compared against a Buy & Hold benchmark using performance metrics and equity curve visualization.

The system downloads historical market data for multiple tickers (SPY, QQQ), computes indicators, generates trading signals, simulates trades, and reports results.
---

## Tickers Backtested

SPY (S&P 500 ETF)
QQQ (Nasdaq 100 ETF)

## Strategy Logic

The strategy uses two moving averages:

- 20-day Simple Moving Average (SMA_20)
- 50-day Simple Moving Average (SMA_50)

Trading Rules:

- If SMA_20 > SMA_50 → Hold a long position
- If SMA_20 ≤ SMA_50 → Stay in cash

Signals are shifted forward by one day to avoid lookahead bias.

---

## Features

- Automatic market data download using yfinance  
- Multi-ticker support (SPY, QQQ)
- Daily return calculation  
- Moving average indicator generation  
- Signal and position creation  
- Strategy return calculation  
- Equity curve generation  
- Performance metrics:
  - CAGR (Compound Annual Growth Rate)
  - Volatility
  - Sharpe Ratio
  - Max Drawdown
- Equity curve visualization using matplotlib

---

## Folder Structure


## Install required libraries:

pip install yfinance pandas numpy matplotlib

## How to Run

From the project folder: python3 backtest.py


## Output

The script prints:

- Strategy CAGR  
- Strategy Volatility  
- Sharpe Ratio  
- Max Drawdown  
- Buy & Hold CAGR  

It also displays a chart comparing:

- Strategy Equity Curve  
- Buy & Hold Equity Curve  

---

## Example Metrics

CAGR: 9.4%
Volatility: 13.2%
Sharpe Ratio: 0.71
Max Drawdown: -18.5%
Buy & Hold CAGR: 10.8%


## Why This Project Matters

This project demonstrates:

- Financial data handling  
- Time-series analysis  
- Trading logic implementation  
- Risk-adjusted performance evaluation  
- Python proficiency for finance  

It mirrors the structure of professional quantitative research pipelines.

---

## Possible Enhancements

- Add transaction costs & slippage  
- Add short-selling  
- Add RSI or MACD strategies  
- Multi-asset portfolios  
- Parameter optimization  
- Walk-forward testing  

---

## Author

TJ  
Finance Major (FinTech Concentration)  
Python • Quantitative Finance • Trading Systems
