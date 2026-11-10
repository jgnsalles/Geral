import requests, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
O='/home/user/raw/yahoo'; tks=sys.argv[1].split(',')
S=requests.Session(); S.headers['User-Agent']='Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
P1=1698796800  # 2023-11-01
def get(t):
    f=f'{O}/{t}.json'
    if os.path.exists(f) and '"timestamp"' in open(f).read(): return t,'cached'
    sym=t if t.startswith('^') else t+'.SA'
    for i in range(4):
        r=S.get(f'https://query2.finance.yahoo.com/v8/finance/chart/{sym}',params=dict(period1=P1,period2=int(time.time()),interval='1d',events='div,splits'),timeout=30)
        if r.status_code==429: time.sleep(5*(i+1)); continue
        break
    open(f,'w').write(r.text); return t,('ok' if '"timestamp"' in r.text else r.status_code)
with ThreadPoolExecutor(4) as ex: res=list(ex.map(get,tks))
from collections import Counter; print(Counter(x[1] for x in res)); print('falhou',[t for t,s in res if s not in('ok','cached')])
