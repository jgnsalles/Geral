import sys, json; sys.path[:0]=['/home/user/Geral/price_tracker/relatorio','/home/user/Geral/price_tracker/backtest','/home/user/Geral/price_tracker']
import robustez as rz, backtest_8 as b8, backtest_bear as bb, benchmarks as bm
from validation_factors import factors; from ciclicos import cyclical_industries
rf=factors()['RF']; c,adj,dates=b8.build(bm.ROIC_FILE,cyclical_industries()); c=bb.add_bear(c)
spy=adj['SPY'].loc[dates[0]:dates[-1]]; spy=spy/spy.iloc[0]; F=rz.fwd4(c,adj,dates)
out={}
for nome, inds in (('Application Software',['Application Software']),('3 perigosas',['Application Software','Technology Hardware, Storage & Peripherals','Other Specialty Retail'])):
    cx=c.copy(); cx.loc[cx.industry.isin(inds),'excluded']=True
    for k,W in (('Top 20',rz.top20(cx)),('Especiais',rz.especiais(cx))):
        m,_=rz.metr(W,adj,dates,spy,rf,F); out[f'{k} sem {nome}']=m; print(k,nome,{a:round(m[a],3) for a in ('cagr','maxdd','w3','w3min','sev')},flush=True)
json.dump(out,open('/home/user/Geral/price_tracker/relatorio/dados_robustez_ind.json','w'),default=float)
