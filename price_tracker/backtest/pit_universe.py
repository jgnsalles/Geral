"""Universo point-in-time: membros do S&P 500 em cada data, mapeados para os tickers com dados.
Mudancas de ticker conhecidas sao mapeadas para o ticker atual (mesma empresa)."""
import pathlib
import pandas as pd

D = pathlib.Path(__file__).parent / 'data'
RENAMES = {'FB': 'META', 'ABC': 'COR', 'ANTM': 'ELV', 'BLL': 'BALL', 'FLT': 'CPAY', 'HRS': 'LHX', 'JEC': 'J', 'ARNC': 'HWM',
           'BHGE': 'BKR', 'HFC': 'DINO', 'CTL': 'LUMN', 'FBHS': 'FBIN', 'WLTW': 'WTW', 'PKI': 'RVTY', 'RE': 'EG', 'DWDP': 'DD',
           'GPS': 'GAP', 'COG': 'CTRA', 'CDAY': 'DAY', 'FISV': 'FI', 'FI': 'FISV', 'CHK': 'EXE', 'TMK': 'GL', 'HCP': 'DOC',
           'DISCA': 'WBD', 'DISCK': 'WBD', 'CBS': 'PARA', 'VIAC': 'PARA', 'GOOGL': 'GOOG', 'BRK.B': 'BRK-B', 'BF.B': 'BF-B',
           'KORS': 'CPRI', 'LLL': 'LHX', 'SYMC': 'GEN', 'NLOK': 'GEN', 'TSO': 'ANDV', 'WYN': 'WH', 'SNI': 'WBD', 'COL': 'RTX',
           'UTX': 'RTX', 'RTN': 'RTX', 'MON': 'BAYRY', 'PCLN': 'BKNG', 'ESV': 'VAL', 'GGP': 'BPYU', 'CA': 'AVGO', 'FDO': 'DLTR',
           'TWC': 'CHTR', 'BRCM': 'AVGO', 'CELG': 'BMY', 'KRFT': 'KHC', 'HNZ': 'KHC', 'COV': 'MDT', 'CFN': 'BDX', 'BCR': 'BDX',
           'FRX': 'ABBV', 'ALXN': 'AZN', 'AGN': 'ABBV', 'XLNX': 'AMD', 'LLTC': 'ADI', 'MXIM': 'ADI', 'ATVI': 'MSFT', 'CERN': 'ORCL',
           'CTXS': 'CTXS', 'ANSS': 'SNPS', 'JNPR': 'HPE', 'DFS': 'COF', 'IPG': 'OMC', 'HES': 'CVX', 'CXO': 'COP', 'APC': 'OXY',
           'PXD': 'XOM', 'XEC': 'CTRA', 'MRO': 'COP', 'DNR': 'DNR', 'WFM': 'AMZN', 'ESRX': 'CI', 'AET': 'CVS', 'TWX': 'T',
           'INFO': 'SPGI', 'KSU': 'CP', 'CPGX': 'TRP', 'STJ': 'ABT', 'EMC': 'DELL', 'XL': 'AXAHY', 'LM': 'BEN', 'ETFC': 'MS',
           'RHT': 'IBM', 'TSS': 'GPN', 'GAS': 'SO', 'SCG': 'D', 'WYND': 'WH', 'DTV': 'T', 'HOT': 'MAR', 'HAR': 'SSNLF', 'DPS': 'KDP'}
# fusoes acima (empresa absorvida) NAO devem herdar o preco da compradora: so mudancas de nome/ticker da mesma empresa
SAME_COMPANY = {'FB', 'ABC', 'ANTM', 'BLL', 'FLT', 'HRS', 'JEC', 'ARNC', 'BHGE', 'HFC', 'CTL', 'FBHS', 'WLTW', 'PKI', 'RE', 'GPS',
                'COG', 'CDAY', 'FISV', 'FI', 'CHK', 'TMK', 'HCP', 'GOOGL', 'BRK.B', 'BF.B', 'KORS', 'SYMC', 'NLOK', 'PCLN', 'ESV', 'WYN',
                'DISCA', 'CBS', 'VIAC', 'DWDP', 'LLL'}


def membership(have):
    """{data: [tickers com dados]} e {data: n_membros_sem_dados}, para cada data da base historica."""
    h = pd.read_csv(D / 'pit_membership/sp500_hist.csv', parse_dates=['date'])
    h = h[h.date >= '2011-06-01']
    mem, miss, miss_list = {}, {}, {}
    for d, tks in zip(h.date, h.tickers.str.split(',')):
        got, lost = [], []
        for t in tks:
            c = t.replace('.', '-')
            if c in have: got.append(c); continue
            if t in SAME_COMPANY and RENAMES.get(t, '').replace('.', '-') in have: got.append(RENAMES[t].replace('.', '-')); continue
            lost.append(t)
        mem[d] = sorted(set(got)); miss[d] = len(lost); miss_list[d] = lost
    return mem, miss, miss_list


def at(dates_map, d):
    """Composicao vigente na data d (ultima linha da base ate d)."""
    keys = [k for k in dates_map if k <= d]
    return dates_map[max(keys)] if keys else []
