"""Top N por RETORNO ESPERADO entre as elegiveis de qualidade (pre-registro de 2026-11-10, sugestao do usuario).
Reaproveita backtest/top_n.py trocando so a ordenacao. Saida: backtest/top_ret.md, backtest/top_ret.png. Uso: python3 backtest/top_ret.py"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
import top_n  # noqa: E402


def pick_ret(x, n):
    return x.sort_values(['ret', 'roic'], ascending=False).head(n)


top_n.pick = pick_ret
_main = top_n.main


def main():
    # no Brasil o retorno esperado precisa do P/E justo com ROIC limitado a 100% (regra congelada): recalcula no proprio classes_pit em memoria
    BD = ROOT.parent / 'brasil' / 'data'
    orig_read = pd.read_csv
    def read_csv(p, *a, **k):
        df = orig_read(p, *a, **k)
        if str(p).endswith('classes_pit.csv') and 'brasil' in str(p):
            r = df.roic.clip(upper=1.0); df['fair_pe'] = np.where(r > 0, (1 - df.g / r) / (0.12 - df.g), np.nan)
            base = df.fair_pe * df.eps * (1 + df.growth) ** 2 / df.price
            df['ret_fair'] = np.where(base > 0, np.sqrt(base.clip(lower=0)) - 1, np.nan) + df.dy; df['ret_const'] = df.growth + df.dy
            both = df.ret_fair.notna() & df.ret_const.notna(); df['ret'] = np.where(both, (df.ret_fair + df.ret_const) / 2, df.growth)
        return df
    pd.read_csv = read_csv
    try:
        _main()
    finally:
        pd.read_csv = orig_read
    src = (ROOT / 'top_n.md').read_text()
    src = src.replace('# Carteira de tamanho fixo pré-registrada: as 20 melhores por ROIC + crescimento (EUA e Brasil)',
                      '# Carteira de tamanho fixo: as 20 de maior retorno esperado entre as de qualidade (EUA e Brasil)')
    src = src.replace('Nota = percentil do ROIC + percentil do crescimento; ficam as N maiores.',
                      'Ordenação = **retorno esperado do modelo** (P/E justo + múltiplo constante + dividendos), sem o corte de 20%; ficam as N maiores.')
    (ROOT / 'top_ret.md').write_text(src)
    (ROOT / 'top_n.png').replace(ROOT / 'top_ret.png')


if __name__ == '__main__':
    main()
