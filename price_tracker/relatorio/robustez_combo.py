import sys, json; sys.path[:0]=['/home/user/Geral/price_tracker/relatorio','/home/user/Geral/price_tracker/backtest','/home/user/Geral/price_tracker']
import robustez3 as r3, robustez as rz, robustez2 as r2, backtest_8 as b8, backtest_bear as bb, benchmarks as bm
from validation_factors import factors; from ciclicos import cyclical_industries
rf=factors()['RF']; c,adj,dates=b8.build(bm.ROIC_FILE,cyclical_industries()); c=bb.add_bear(c); c['esc']=r2.escadinha(c); c=r3.nota(c)
spy=adj['SPY'].loc[dates[0]:dates[-1]]; spy=spy/spy.iloc[0]; F=rz.fwd4(c,adj,dates)
cw=c.copy(); cw['mcap']=cw.mcap*cw.nota**2
out={}
for k,W in {'Top 20 · ≥ US$ 20 bi + N3 peso': rz.top20(cw, c.mcap>=20e9)}.items():
    m,nav=rz.metr(W,adj,dates,spy,rf,F); out[k]=m; print(k,{a:round(m[a],3) for a in ('cagr','maxdd','w3','w5','w10','w3min','sev')})
json.dump(out,open('/home/user/Geral/price_tracker/relatorio/dados_robustez_combo.json','w'),default=float)
