"""Gera backtest/data/roic_series.csv: ROIC oficial anual (historico completo, dados mais recentes da SEC) de todas as empresas do universo.
Uso: python3 backtest/roic_series.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from trajetorias import annual  # noqa: E402
from validation_core import load_prices, universe_table  # noqa: E402
from backtest import D  # noqa: E402

t = universe_table().set_index('ticker'); spl = load_prices()['stock_splits']; rows = []
for tk, r in t.iterrows():
    try:
        s = spl[tk][spl[tk] > 0] if tk in spl else pd.Series(dtype=float)
        a = annual(tk, bool(r.fin), s)
    except Exception:
        continue
    for y, v in a.roic.replace([np.inf, -np.inf], np.nan).dropna().items():
        if y >= 2005: rows.append((tk, int(y), float(v)))
pd.DataFrame(rows, columns=['ticker', 'fy', 'roic']).to_csv(D / 'roic_series.csv', index=False)
print(len(rows))
