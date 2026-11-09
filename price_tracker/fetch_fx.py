"""Congela as cotacoes de cambio necessarias (moeda do EPS -> moeda do preco) em data/raw/yahoo/<data>/_fx.json."""
import sys, json, glob, pathlib
import yfinance as yf

def main(day):
    pairs = set()
    for f in glob.glob(f'data/raw/yahoo/{day}/*.json'):
        if f.endswith('_fx.json'): continue
        d = json.load(open(f))
        pc = (d.get('info') or {}).get('currency')
        ec = ((d.get('earnings_estimate') or {}).get('0y') or {}).get('currency')
        if pc and ec and pc != ec:
            pairs.add((ec, pc))
    fx = {}
    for ec, pc in sorted(pairs):
        h = yf.Ticker(f'{ec}{pc}=X').history(period='5d')
        fx[f'{ec}{pc}'] = float(h['Close'].iloc[-1]) if len(h) else None
        print(ec, pc, fx[f'{ec}{pc}'])
    pathlib.Path(f'data/raw/yahoo/{day}/_fx.json').write_text(json.dumps(fx, indent=1))

if __name__ == '__main__':
    main(sys.argv[1])
