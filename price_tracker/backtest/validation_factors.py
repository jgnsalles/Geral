"""Fase 3 do protocolo: alfa das candidatas (universo point-in-time, ROIC oficial) contra Fama-French 5 + momentum + QMJ.
Regressoes mensais com erros de Newey-West (6 defasagens). Duas versoes: (i) retorno - taxa livre; (ii) retorno - universo EW.
Uso: python3 backtest/validation_factors.py"""
import pathlib
import numpy as np, pandas as pd
import statsmodels.api as sm

ROOT = pathlib.Path(__file__).parent
D = ROOT / 'data'
F = D / 'factors'
pc = lambda x: '—' if pd.isna(x) else f'{x:.1%}'.replace('.', ',')
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
n2 = lambda x: '—' if pd.isna(x) else f'{x:.2f}'.replace('.', ',')


def french(path):
    lines = path.read_text(errors='ignore').splitlines()
    i0 = next(i for i, l in enumerate(lines) if l.strip().startswith(',')) if path.name.startswith('F-F_Research') else \
        next(i for i, l in enumerate(lines) if l.strip().startswith(',Mom'))
    rows = []
    for l in lines[i0 + 1:]:
        p = l.split(',')
        if len(p) < 2 or not p[0].strip().isdigit() or len(p[0].strip()) != 6: break
        rows.append(p)
    df = pd.DataFrame(rows).set_index(0)
    df.columns = [c.strip() for c in lines[i0].split(',')[1:]]
    df.index = pd.to_datetime(df.index.str.strip(), format='%Y%m') + pd.offsets.MonthEnd(0)
    return df.astype(float) / 100


def factors():
    ff = french(F / 'F-F_Research_Data_5_Factors_2x3.csv')
    mom = french(F / 'F-F_Momentum_Factor.csv'); mom.columns = ['UMD']
    q = pd.read_excel(F / 'qmj.xlsx', 'QMJ Factors', skiprows=18)[['DATE', 'USA']].dropna()
    q.index = pd.to_datetime(q.DATE) + pd.offsets.MonthEnd(0); q = q[['USA']].rename(columns={'USA': 'QMJ'})
    return ff.join(mom).join(q)


def reg(y, X):
    d = pd.concat([y.rename('y'), X], axis=1).dropna()
    m = sm.OLS(d.y, sm.add_constant(d.drop(columns='y'))).fit(cov_type='HAC', cov_kwds={'maxlags': 6})
    return m, len(d)


def main():
    m = pd.read_csv(D / 'val_monthly.csv', index_col=0, parse_dates=True)
    m.index = m.index + pd.offsets.MonthEnd(0)
    fac = factors()
    cols = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'UMD', 'QMJ']
    cands = [c for c in m.columns if c.startswith('PIT|')]
    out = ['# Fase 3: alfa contra fatores conhecidos (universo point-in-time, ROIC oficial)\n',
           '> ⚠️ **ROIC:** carteiras com o ROIC oficial (B com reserva em A).\n',
           f'Regressões mensais {m.dropna(how="all").index.min():%m/%Y}–{fac.dropna().index.max():%m/%Y}, erros de Newey-West (6 defasagens). '
           'Fatores: Fama-French 5 (mercado, tamanho, valor, rentabilidade, investimento), momentum (Kenneth French) e Quality Minus Junk (AQR, EUA).\n',
           '## 1. Retorno da carteira − taxa livre de risco\n',
           '| Carteira | Alfa a.a. | t | Mkt | SMB | HML | RMW | CMA | UMD | QMJ | R² |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for c in cands:
        y = m[c] - fac.RF
        mod, n = reg(y, fac[cols])
        b = mod.params
        out.append(f"| {c.split('|')[1]} | **{sg(b['const'] * 12)}** | {n2(mod.tvalues['const'])} | " + ' | '.join(n2(b[k]) for k in cols) + f' | {n2(mod.rsquared)} |')
    out += ['', '## 2. Retorno da carteira − universo EW (long-short contra a contraprova)\n',
            '| Carteira | Alfa a.a. | t | Mkt | SMB | HML | RMW | CMA | UMD | QMJ | R² |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for c in cands:
        if 'Universo' in c: continue
        y = m[c] - m['PIT|Universo EW']
        mod, n = reg(y, fac[cols])
        b = mod.params
        out.append(f"| {c.split('|')[1]} | **{sg(b['const'] * 12)}** | {n2(mod.tvalues['const'])} | " + ' | '.join(n2(b[k]) for k in cols) + f' | {n2(mod.rsquared)} |')
    out += ['', 'Leitura dos betas: RMW e QMJ positivos = exposição a qualidade/rentabilidade; UMD = momentum; HML negativo = viés de crescimento; '
            'SMB = tamanho. O alfa é o que sobra depois desses fatores.']
    (ROOT / 'validation_phase3.md').write_text('\n'.join(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
