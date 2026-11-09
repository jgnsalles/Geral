"""Extrai o snapshot (valores em cache do ultimo refresh do Wisesheets) da aba Formula."""
import sys, openpyxl, pandas as pd
from openpyxl.utils import column_index_from_string as ci

COLS = dict(ticker='B', name='E', sector='F', industry='G', pe27='M', pe28='N', fair_pe='O',
            g26='P', g27='Q', g28='R', g29='S', growth='T', g='U',
            roic2019='V', roic2021='W', roic2022='X', roic2023='Y', roic2024='Z', roic2025='AA', roic='AB',
            dy2024='AC', dy2025='AD', ret_fair='AE', ret_const='AF', ret='AG', zgrowth='AP', zroic_old='AR',
            category='AM')

def main(path, out):
    ws = openpyxl.load_workbook(path, data_only=True)['Formula']
    rows = []
    for r in list(range(6, 207)) + list(range(211, 234)):
        tk = ws.cell(r, 2).value
        if not isinstance(tk, str) or not tk.strip():
            continue
        d = {k: ws.cell(r, ci(c)).value for k, c in COLS.items()}
        d['row'] = r
        rows.append(d)
    df = pd.DataFrame(rows)
    df['fin'] = df['row'] >= 211  # bloco de financeiras (ranking de g proprio)
    df.to_csv(out, index=False)
    print(len(df), 'tickers ->', out)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
