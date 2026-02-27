import yfinance as yf
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import os


# Settings

tickers = ["SPY","QQQ"]
start_date = "2015-01-01"
end_date = "2025-01-01"
# Whether to display plots interactively (requires a GUI-capable backend)
SHOW_PLOTS = True


# Download + process each ticker


all_data = {}

for ticker in tickers:
    df = yf.download(
        ticker,
        start=start_date,
        end=end_date
    )

    df = df.reset_index()
    # yfinance may return MultiIndex columns (Price, Ticker). Normalize to single-level
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    df["Return"] = df["Close"].pct_change()
    all_data[ticker] = df


# Prepare outputs directory
os.makedirs("outputs", exist_ok=True)
# Prepare data directory (user-requested location)
os.makedirs("data", exist_ok=True)

# Prepare Excel writer and a summary
output_file = "outputs/backtest_results.xlsx"
summary_rows = []
processed_data = {}

for ticker, df in all_data.items():
    # Process dataframe
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    # Compute returns and indicators before dropping rows so we don't remove
    # the rows needed to calculate moving averages. Later we drop rows where
    # the indicators are not yet available.
    df["Return"] = df["Close"].pct_change()

    # Moving averages
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()

    # Drop rows where indicators are NaN (first ~50 rows while SMA_50 warms up)
    df = df.dropna(subset=["SMA_20", "SMA_50", "Return"]).reset_index(drop=True)

    # Signals / positions
    df["Signal"] = 0
    df.loc[df["SMA_20"] > df["SMA_50"], "Signal"] = 1
    df["Position"] = df["Signal"].shift(1).fillna(0)

    # Strategy returns / equity
    df["Strategy_Return"] = df["Position"] * df["Return"]
    df["BuyHold_Equity"] = (1 + df["Return"]).cumprod()
    df["Strategy_Equity"] = (1 + df["Strategy_Return"]).cumprod()

    # Performance metrics
    trading_days = 251
    years = len(df) / trading_days if len(df) > 0 else 1
    strategy_cagr = (df["Strategy_Equity"].iloc[-1]) ** (1 / years) - 1 if len(df) > 0 else 0
    buyhold_cagr = (df["BuyHold_Equity"].iloc[-1]) ** (1 / years) - 1 if len(df) > 0 else 0
    strategy_vol = df["Strategy_Return"].std() * (trading_days ** 0.5) if df["Strategy_Return"].notna().any() else 0
    strategy_sharpe = (strategy_cagr / strategy_vol) if strategy_vol != 0 else 0
    rolling_max = df["Strategy_Equity"].cummax()
    drawdown = df["Strategy_Equity"] / rolling_max - 1
    max_drawdown = drawdown.min()

    summary_rows.append({
        "Ticker": ticker,
        "Strategy_CAGR": strategy_cagr,
        "BuyHold_CAGR": buyhold_cagr,
        "Volatility": strategy_vol,
        "Sharpe": strategy_sharpe,
        "Max_Drawdown": max_drawdown,
        "Rows": len(df),
    })
    # Flatten MultiIndex columns (some data sources produce MultiIndex cols)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join([str(c) for c in col]).strip("_") for col in df.columns]

    # store processed df to write once
    # convert Date to date-only (remove time component) so Excel displays clean dates
    try:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
    except Exception:
        # fallback: cast to string in YYYY-MM-DD format
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    processed_data[ticker] = df

    # Save per-ticker equity plot to outputs/
    try:
        plt.figure(figsize=(10,6))
        plt.plot(df['Date'], df['BuyHold_Equity'], label='Buy & Hold')
        plt.plot(df['Date'], df['Strategy_Equity'], label='Strategy')
        plt.xlabel('Date')
        plt.ylabel('Equity (Growth of $1)')
        plt.title(f'{ticker} Equity Curve')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        out_png = f"outputs/{ticker}_equity.png"
        plt.savefig(out_png)

        # If SHOW_PLOTS is True and a GUI-capable backend is active, show the plot.
        try:
            backend = matplotlib.get_backend().lower()
            if SHOW_PLOTS and backend not in ("agg", "pdf", "svg", "ps"):
                # non-blocking show where supported
                try:
                    plt.show(block=False)
                    # small pause to let window appear when run locally
                    plt.pause(0.1)
                except Exception:
                    # fallback to blocking show if non-blocking not supported
                    try:
                        plt.show()
                    except Exception:
                        pass
        except Exception:
            pass

        plt.close()
    except Exception as e:
        print(f"Failed to save/ show plot for {ticker}: {e}")

# Write all sheets (overwrite output file)
try:
    with pd.ExcelWriter(output_file, engine="openpyxl", mode="w") as writer:
        for ticker, df in processed_data.items():
            sheet_name = ticker if len(ticker) <= 31 else ticker[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        summary_df = pd.DataFrame(summary_rows)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
    # Also save individual per-ticker workbooks and a summary workbook in data/
    for ticker, df in processed_data.items():
        try:
            out_path = f"data/{ticker}_backtest_results.xlsx"
            df.to_excel(out_path, index=False)
        except Exception as e:
            print(f"Failed to write per-ticker file for {ticker}: {e}")

    try:
        summary_out = "data/backtest_summary.xlsx"
        summary_df.to_excel(summary_out, index=False)
    except Exception as e:
        print("Failed to write summary workbook to data/:", e)
    print(f"Wrote results to {output_file}")
    # Create summary plots and save to outputs/
    try:
        # Ensure numeric types
        plot_df = summary_df.copy()
        for col in ["Strategy_CAGR", "BuyHold_CAGR", "Sharpe", "Max_Drawdown"]:
            if col in plot_df.columns:
                plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")

        if not plot_df.empty:
            # CAGR comparison
            try:
                ax = plot_df.set_index("Ticker")[ ["Strategy_CAGR", "BuyHold_CAGR"] ].plot(kind="bar", figsize=(8,5))
                ax.set_ylabel("CAGR")
                ax.set_title("Strategy vs Buy & Hold CAGR")
                plt.tight_layout()
                plt.savefig("outputs/summary_cagr.png")
                plt.close()
            except Exception as e:
                print("Failed to create CAGR summary plot:", e)

            # Sharpe and Max Drawdown
            try:
                cols = [c for c in ["Sharpe", "Max_Drawdown"] if c in plot_df.columns]
                if cols:
                    ax2 = plot_df.set_index("Ticker")[cols].plot(kind="bar", figsize=(8,5))
                    ax2.set_ylabel("Value")
                    ax2.set_title("Sharpe Ratio and Max Drawdown")
                    plt.tight_layout()
                    plt.savefig("outputs/summary_metrics.png")
                    plt.close()
            except Exception as e:
                print("Failed to create metrics summary plot:", e)
    except Exception as e:
        print("Failed to create summary plots:", e)
except Exception as e:
    print("Failed to write Excel workbook:", e)
