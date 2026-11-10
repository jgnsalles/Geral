"""Top N por retorno esperado + filtros do usuario (2026-11-10): fora se alguma taxa anual de crescimento do lucro nos 5 anos > 150%
ou se P/L < 6. Saidas: backtest/top_ret_filtro.md, backtest/top_ret_filtro.png. Uso: python3 backtest/top_ret_filtro.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import top_n, top_ret  # noqa: E402  (top_ret troca a ordenacao para retorno esperado)

GMAX, PEMIN = 1.5, 6.0


def us(el):
    g = el[[f'gy{i}' for i in range(1, 6)]].max(axis=1)
    pe = el.price / el.eps.where(el.eps > 0)
    return ~(g > GMAX) & ~(pe < PEMIN)


def br(elb, fund, cvm):
    keep = []
    for r in elb.itertuples():
        f = fund[(fund.CD_CVM == cvm.get(r.ticker)) & (fund.DT_RECEB <= r.date)]
        f = f.sort_values(['DT_RECEB']).groupby('fy').tail(1).set_index('fy').ni
        rates = [f.get(y) / f.get(y - 1) - 1 for y in range(int(r.last_fy) - 4, int(r.last_fy) + 1)
                 if pd.notna(f.get(y)) and pd.notna(f.get(y - 1)) and f.get(y - 1) > 0]
        pe = r.price / r.eps if r.eps and r.eps > 0 else np.nan
        keep.append(not (rates and max(rates) > GMAX) and not (pe < PEMIN))
    return np.array(keep, dtype=bool)


top_n.EXTRA_US, top_n.EXTRA_BR = us, br

if __name__ == '__main__':
    bak = {p: (ROOT / p).read_bytes() for p in ('top_ret.md', 'top_ret.png') if (ROOT / p).exists()}
    top_ret.main()
    src = (ROOT / 'top_ret.md').read_text().replace('# Carteira de tamanho fixo: as 20 de maior retorno esperado entre as de qualidade (EUA e Brasil)',
        '# Top 20 por retorno esperado + filtros: fora crescimento anual > 150% e P/L < 6 (EUA e Brasil)')
    src = src.replace('sem o corte de 20%; ficam as N maiores.', 'sem o corte de 20%; ficam as N maiores. **Fora:** alguma taxa anual de crescimento do lucro > 150% nos 5 anos, ou P/L < 6.')
    (ROOT / 'top_ret_filtro.md').write_text(src); (ROOT / 'top_ret.png').replace(ROOT / 'top_ret_filtro.png')
    for p, b in bak.items(): (ROOT / p).write_bytes(b)
