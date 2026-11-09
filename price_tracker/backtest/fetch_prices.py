"""Precos diarios (Yahoo) desde 2005: Close (ajustado so por desdobramento), Adj Close (retorno total),
Dividends e Stock Splits. Saida: backtest/data/prices_<campo>.csv.gz"""
import pathlib
import pandas as pd, yfinance as yf

D = pathlib.Path(__file__).parent / 'data'
BENCH = ['SPY', 'QQQ', 'RSP']

def main():
    tk = pd.read_csv(D / 'universe.csv').ticker.tolist() + BENCH
    frames = []
    for i in range(0, len(tk), 100):
        frames.append(yf.download(tk[i:i + 100], start='2005-01-01', end='2026-11-08', auto_adjust=False,
                                  actions=True, progress=False, threads=True))
    df = pd.concat(frames, axis=1)
    for field in ('Close', 'Adj Close', 'Dividends', 'Stock Splits'):
        x = df[field]
        x = x.loc[:, ~x.columns.duplicated()]
        x.to_csv(D / f"prices_{field.replace(' ', '_').lower()}.csv.gz")
        print(field, x.shape, 'sem dado:', int(x.notna().sum().eq(0).sum()))

if __name__ == '__main__':
    main()
