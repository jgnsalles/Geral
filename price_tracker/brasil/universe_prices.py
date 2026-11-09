"""Universo B3 (cadastro FCA da CVM) e precos do Yahoo: Close, Adj Close, Volume, Dividends, Stock Splits.
Escolhe, por empresa, o ticker mais liquido (mediana de volume financeiro nos ultimos 3 anos)."""
import io, zipfile, pathlib, requests
import pandas as pd, numpy as np, yfinance as yf

UA = {'User-Agent': 'PriceTracker-Research/1.0'}
D = pathlib.Path(__file__).parent / 'data'
FIN = {'Bancos', 'Intermediação Financeira', 'Seguradoras e Corretoras', 'Arrendamento Mercantil', 'Securitização de Recebíveis',
       'Bolsas de Valores/Mercadorias e Futuros', 'Crédito Imobiliário', 'Factoring', 'Previdência', 'Emp. Adm. Part. - Seguradoras e Corretoras',
       'Emp. Adm. Part. - Bancos', 'Emp. Adm. Part. - Intermediação Financeira'}

def main():
    r = requests.get('https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_2026.zip', headers=UA, timeout=120)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    rd = lambda n: pd.read_csv(z.open(n), sep=';', encoding='latin1', dtype=str)
    vm, ge = rd('fca_cia_aberta_valor_mobiliario_2026.csv'), rd('fca_cia_aberta_geral_2026.csv')
    vm = vm[(vm.Mercado == 'Bolsa') & vm.Codigo_Negociacao.notna() & vm.Data_Fim_Negociacao.isna()
            & vm.Valor_Mobiliario.isin(['Ações Ordinárias', 'Ações Preferenciais', 'Units'])]
    ge = ge.sort_values('Versao').drop_duplicates('CNPJ_Companhia', keep='last')
    u = vm.merge(ge[['CNPJ_Companhia', 'Codigo_CVM', 'Setor_Atividade', 'Nome_Empresarial']], on='CNPJ_Companhia', suffixes=('', '_g'))
    u['ticker'] = u.Codigo_Negociacao.str.strip().str.upper()
    u = u[u.ticker.str.match(r'^[A-Z0-9]{4}\d{1,2}$')].drop_duplicates('ticker')
    print('tickers', len(u), 'empresas', u.CNPJ_Companhia.nunique())
    print(sorted(u.Setor_Atividade.dropna().unique()))
    tk = [t + '.SA' for t in u.ticker]
    frames = []
    for i in range(0, len(tk), 100):
        frames.append(yf.download(tk[i:i + 100], start='2005-01-01', end='2026-11-08', auto_adjust=False, actions=True,
                                  progress=False, threads=True))
    df = pd.concat(frames, axis=1)
    bench = yf.download(['BOVA11.SA', 'SMAL11.SA', '^BVSP'], start='2005-01-01', end='2026-11-08', auto_adjust=False, progress=False)
    for f in ('Close', 'Adj Close', 'Volume', 'Dividends', 'Stock Splits'):
        x = df[f]; x = x.loc[:, ~x.columns.duplicated()]
        if f in ('Close', 'Adj Close'):
            x = pd.concat([x, bench[f]], axis=1)
        x.to_csv(D / f"prices_{f.replace(' ', '_').lower()}.csv.gz")
    close, vol = df['Close'], df['Volume']
    tv = (close * vol).loc['2023-11-01':].median()
    u['yf'] = u.ticker + '.SA'
    u['adtv'] = u.yf.map(tv)
    u = u[u.adtv.notna() & (u.adtv > 0)]
    best = u.sort_values('adtv', ascending=False).drop_duplicates('CNPJ_Companhia')
    best['fin'] = best.Setor_Atividade.isin(FIN)
    best[['yf', 'ticker', 'Codigo_CVM', 'CNPJ_Companhia', 'Nome_Empresarial', 'Setor_Atividade', 'Valor_Mobiliario', 'fin', 'adtv']].to_csv(D / 'universe.csv', index=False)
    print('empresas com preco', len(best), 'financeiras', int(best.fin.sum()))

if __name__ == '__main__':
    main()
