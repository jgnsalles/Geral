"""Setores e subsetores das derrotas na OoL e na GCGR (sem zROIC, universo point-in-time, ROIC oficial corrigido).
Le backtest/atributos.csv. Setor GICS do universo atual; empresas que sairam do S&P 500 classificadas a mao (abaixo).
Saidas: backtest/setores_derrotas.md, backtest/setores_derrotas.png
Uso: python3 backtest/setores_derrotas.py"""
import pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).parent; D = ROOT / 'data'
OOL, GCGR = 'Opportunity of Lifetime', 'Good Companies, Great Returns'
CD, CS, MT, EN, IN, IT, FN, CM, HC = ('Consumer Discretionary', 'Consumer Staples', 'Materials', 'Energy', 'Industrials',
                                      'Information Technology', 'Financials', 'Communication Services', 'Health Care')
# empresas fora do S&P 500 atual: setor e subsetor GICS atribuidos a mao
MANUAL = {
    'CAG': (CS, 'Packaged Foods & Meats'), 'LW': (CS, 'Packaged Foods & Meats'),
    'CLF': (MT, 'Steel'), 'ATI': (MT, 'Steel'), 'EMN': (MT, 'Diversified Chemicals'), 'CE': (MT, 'Diversified Chemicals'),
    'FMC': (MT, 'Fertilizers & Agricultural Chemicals'),
    'NOV': (EN, 'Oil & Gas Equipment & Services'), 'HP': (EN, 'Oil & Gas Drilling'),
    'GME': (CD, 'Computer & Electronics Retail'), 'KSS': (CD, 'Broadline Retail (lojas de departamento)'), 'M': (CD, 'Broadline Retail (lojas de departamento)'),
    'MAT': (CD, 'Leisure Products'), 'GAP': (CD, 'Apparel Retail'), 'URBN': (CD, 'Apparel Retail'),
    'VFC': (CD, 'Apparel, Accessories & Luxury Goods'), 'FOSL': (CD, 'Apparel, Accessories & Luxury Goods'), 'CPRI': (CD, 'Apparel, Accessories & Luxury Goods'),
    'UA': (CD, 'Apparel, Accessories & Luxury Goods'), 'UAA': (CD, 'Apparel, Accessories & Luxury Goods'),
    'BWA': (CD, 'Automotive Parts & Equipment'), 'GT': (CD, 'Automotive Parts & Equipment'), 'HOG': (CD, 'Motorcycle Manufacturers'),
    'AN': (CD, 'Automotive Retail'), 'AAP': (CD, 'Automotive Retail'), 'SIG': (CD, 'Other Specialty Retail'),
    'WHR': (CD, 'Household Appliances'), 'MHK': (CD, 'Home Furnishings'), 'HRB': (CD, 'Specialized Consumer Services'), 'ETSY': (CD, 'Broadline Retail'),
    'FLR': (IN, 'Construction & Engineering'), 'RHI': (IN, 'Human Resource & Employment Services'), 'FLS': (IN, 'Industrial Machinery'),
    'ALK': (IN, 'Passenger Airlines'), 'AYI': (IN, 'Electrical Components & Equipment'), 'FBIN': (IN, 'Building Products'),
    'TDC': (IT, 'Application Software'), 'PAYC': (IT, 'Application Software'), 'IPGP': (IT, 'Electronic Manufacturing Services'),
    'EPAM': (IT, 'IT Consulting & Other Services'), 'TTD': (IT, 'Application Software'),
    'WU': (FN, 'Transaction & Payment Processing Services'), 'SLM': (FN, 'Consumer Finance'), 'AMG': (FN, 'Asset Management & Custody Banks'),
    'ZION': (FN, 'Regional Banks'),
    'TRIP': (CM, 'Interactive Media & Services'), 'GOOGL': (CM, 'Interactive Media & Services'), 'MTCH': (CM, 'Interactive Media & Services'),
    'BIO': (HC, 'Life Sciences Tools & Services'),
}
pc = lambda x: '—' if pd.isna(x) else f'{x:.0%}'
sg = lambda x: '—' if pd.isna(x) else f'{x:+.1%}'.replace('.', ',')
sp = lambda x: '—' if pd.isna(x) else f'{x * 100:+.2f}'.replace('.', ',')


def main():
    c = pd.read_csv(ROOT / 'atributos.csv', parse_dates=['date'])
    u = pd.read_csv(D / 'universe.csv').drop_duplicates('ticker').set_index('ticker')
    x_ = pd.read_csv(D / 'universe_pit_extra.csv').drop_duplicates('ticker').set_index('ticker')
    sec = lambda t: MANUAL[t][0] if t in MANUAL else (u.sector.get(t) if t in u.index else 'Sem classificação')
    ind = lambda t: MANUAL[t][1] if t in MANUAL else (u.industry.get(t) if t in u.index else 'Sem classificação')
    name = lambda t: u.name.get(t) if t in u.index else (x_.sec_name.get(t, t) if t in x_.index else t)
    c['sector'] = c.ticker.map(sec); c['industry'] = c.ticker.map(ind)
    c['n'] = c.groupby(['cat', 'date']).ticker.transform('size'); c['exc'] = c.ex / c.n
    Y = c.date.nunique() / 4
    out = ['# Setores das derrotas na OoL e na GCGR (EUA, point-in-time, sem zROIC)\n',
           '> ⚠️ **ROIC:** ROIC oficial (corrigido em 2026-11-10). A presença de cada setor na OoL e na GCGR depende do ROIC; setores leves em ativos '
           '(software, marcas) tendem a ter ROIC alto, e o ROIC acima de 100% em empresas leves em ativos ainda está em aberto.\n',
           'Unidade: empresa dentro da classe. **Derrota** = empresa entre os 20% piores pelo excesso médio sobre o universo (mín. 4 trimestres na classe). '
           '**Concentração** = % das derrotas ÷ % das empresas (1,0 = proporcional; 2,0 = o dobro do esperado). **Contribuição** = soma do excesso de cada posição '
           '÷ nº de ações da classe no trimestre, por ano (p.p. a.a. no excesso da classe). Setor GICS; 49 empresas que saíram do S&P 500 foram classificadas a mão.\n']
    figdata = {}
    for cat in (OOL, GCGR):
        x = c[c.cat == cat]
        e = x.groupby('ticker').agg(ex=('ex', 'mean'), q=('ex', 'size'), ctr=('exc', 'sum'), sector=('sector', 'first'), industry=('industry', 'first'))
        e['ex'] *= 4; e['ctr'] /= Y
        el = e[e.q >= 4].copy(); cut = el.ex.quantile(.2); el['loser'] = el.ex <= cut
        s = el.groupby('sector').agg(emp=('ex', 'size'), derrotas=('loser', 'sum'), med=('ex', 'median'), pos=('ex', lambda v: (v > 0).mean()))
        s['conc'] = (s.derrotas / s.derrotas.sum()) / (s.emp / s.emp.sum())
        w = x.groupby('sector').size() / len(x)
        ctr = e.groupby('sector').ctr.agg(total='sum', neg=lambda v: v[v < 0].sum(), posit=lambda v: v[v > 0].sum())
        s = s.join(w.rename('peso')).join(ctr).sort_values('neg')
        figdata[cat] = s
        out += [f'## {cat}\n', f'{len(el)} empresas com ≥ 4 trimestres; derrota = excesso médio ≤ {sg(cut)} a.a. ({int(el.loser.sum())} empresas).\n',
                '| Setor | Peso nas posições | Empresas | Derrotas | **Concentração** | Excesso mediano | % empresas > universo | Contribuição negativa | Contribuição positiva | **Saldo** |',
                '|---|---|---|---|---|---|---|---|---|---|']
        for k, r in s.iterrows():
            cc = f'**{r.conc:.1f}**' if r.conc >= 1.5 and r.derrotas >= 3 else f'{r.conc:.1f}'
            out.append(f'| {k} | {pc(r.peso)} | {r.emp:.0f} | {r.derrotas:.0f} | {cc.replace(".", ",")} | {sg(r.med)} | {pc(r.pos)} | {sp(r.neg)} | {sp(r.posit)} | **{sp(r.total)}** |')
        # subsetores
        i = el.groupby('industry').agg(emp=('ex', 'size'), derrotas=('loser', 'sum'), med=('ex', 'median'), sector=('sector', 'first'))
        ic = e.groupby('industry').ctr.agg(total='sum', neg=lambda v: v[v < 0].sum())
        i = i.join(ic)
        losers = el[el.loser].sort_values('ex')
        i['nomes'] = [', '.join(f'{t} ({name(t)})' for t in losers[losers.industry == k].index) for k in i.index]
        i = i[i.derrotas >= 2].sort_values(['derrotas', 'neg'], ascending=[False, True])
        out += ['', '### Subsetores com 2 ou mais derrotas\n', '| Subsetor | Setor | Empresas | Derrotas | Excesso mediano | Saldo da contribuição | Derrotas (nomes) |',
                '|---|---|---|---|---|---|---|']
        for k, r in i.iterrows():
            out.append(f'| {k} | {r.sector} | {r.emp:.0f} | {r.derrotas:.0f} | {sg(r.med)} | {sp(r.total)} | {r.nomes} |')
        out.append('')
    (ROOT / 'setores_derrotas.md').write_text('\n'.join(out))
    print('\n'.join(out))
    fig, axs = plt.subplots(1, 2, figsize=(17, 6.5), dpi=130)
    for ax, cat in zip(axs, (OOL, GCGR)):
        s = figdata[cat].sort_values('total')
        y = np.arange(len(s))
        ax.barh(y, s.neg * 100, color='#cf222e', alpha=.8, label='Contribuição negativa')
        ax.barh(y, s.posit * 100, color='#2da44e', alpha=.8, label='Contribuição positiva')
        ax.scatter(s.total * 100, y, color='black', zorder=3, s=25, label='Saldo')
        ax.set_yticks(y); ax.set_yticklabels([f'{k} ({r.derrotas:.0f}/{r.emp:.0f})' for k, r in s.iterrows()], fontsize=8)
        ax.axvline(0, color='black', lw=.8); ax.grid(alpha=.3, axis='x'); ax.set_xlabel('p.p. a.a. no excesso da classe')
        ax.set_title(f'{"OoL" if cat == OOL else "GCGR"}: contribuição por setor (derrotas/empresas)', fontsize=10); ax.legend(fontsize=8, loc='lower right')
    fig.suptitle('Setores: quem gera as derrotas e quem compensa — sem zROIC, universo point-in-time', fontsize=11)
    fig.tight_layout(); fig.savefig(ROOT / 'setores_derrotas.png'); plt.close(fig)


if __name__ == '__main__':
    main()
