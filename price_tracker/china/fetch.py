"""China (acoes A): fundamentos anuais em lote do Eastmoney (via AkShare, com data de divulgacao) e precos do Yahoo (.SS/.SZ).
Uso: python3 china/fetch.py"""
import pathlib, time
import pandas as pd
import akshare as ak
D = pathlib.Path(__file__).parent / 'data'

def main():
    for fn in ('stock_yjbb_em', 'stock_zcfz_em', 'stock_lrb_em'):
        for y in range(2008, 2026):
            f = D / f'{fn}_{y}.csv'
            if f.exists(): continue
            for a in range(4):
                try:
                    getattr(ak, fn)(date=f'{y}1231').to_csv(f, index=False); break
                except Exception as e:
                    print(fn, y, 'erro', repr(e)[:80], flush=True); time.sleep(30 * (a + 1))
            print(fn, y, flush=True); time.sleep(2)
    codes = set()
    for f in D.glob('stock_yjbb_em_*.csv'):
        codes |= set(pd.read_csv(f, dtype={'股票代码': str})['股票代码'].str.zfill(6))
    yt = sorted({c + ('.SS' if c[0] == '6' else '.SZ') for c in codes if c[0] in '603'})
    import yfinance as yf
    parts = {k: [] for k in ('Close', 'Adj Close', 'Volume', 'Stock Splits')}
    for i in range(0, len(yt), 400):
        px = yf.download(yt[i:i + 400], start='2009-06-01', auto_adjust=False, actions=True, progress=False, threads=True)
        for k in parts:
            if k in px.columns.get_level_values(0): parts[k].append(px[k])
        print('yahoo', i, len(yt), flush=True)
    bm = yf.download(['000300.SS', '000905.SS', '000001.SS'], start='2009-06-01', auto_adjust=False, progress=False)['Close']
    bm.to_csv(D / 'indices.csv')
    for k, n in (('Close', 'close'), ('Adj Close', 'adj_close'), ('Volume', 'volume'), ('Stock Splits', 'splits')):
        pd.concat(parts[k], axis=1).to_csv(D / f'prices_{n}.csv.gz')
    print('ok', len(yt))

if __name__ == '__main__':
    main()
