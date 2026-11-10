# Extrai CDA (BLC_2/4/8, PL) e Informe Diário para o universo dos 30 fundos, dez/2023 em diante.
# Segue extract.py / extract8.py / quotas.py do repo gestoras.
import pandas as pd, zipfile, glob, json, sys, os
R='/home/user/raw/cvm'; W='/home/user/work'
REN={'CNPJ_FUNDO_CLASSE':'CNPJ_FUNDO','CNPJ_FUNDO_CLASSE_COTA':'CNPJ_FUNDO_COTA','TP_FUNDO_CLASSE':'TP_FUNDO'}
M=set(json.load(open(W+'/seed.json')))
def read(zf,key,**kw):
    kw.setdefault('quoting',3); kw.setdefault('on_bad_lines','skip')
    out=[]
    for n in [n for n in zf.namelist() if key in n]:
        for c in pd.read_csv(zf.open(n),sep=';',encoding='latin1',dtype=str,chunksize=400000,**kw):
            out.append(c.rename(columns=REN))
    return pd.concat(out) if out else pd.DataFrame()
pos,pls,cot,p8=[],[],[],[]
for z in sorted(glob.glob(R+'/cda_fi_20*.zip')):
    zf=zipfile.ZipFile(z)
    b2=read(zf,'BLC_2'); b2=b2[b2.CNPJ_FUNDO_COTA.notna()]
    b2['v']=pd.to_numeric(b2.VL_MERC_POS_FINAL,errors='coerce')
    for _ in range(3): M|=set(b2[b2.CNPJ_FUNDO.isin(M)].CNPJ_FUNDO_COTA)
    cot.append(b2[b2.CNPJ_FUNDO.isin(M)][['CNPJ_FUNDO','DT_COMPTC','CNPJ_FUNDO_COTA','v']])
    b4=read(zf,'BLC_4'); b4=b4[b4.CNPJ_FUNDO.isin(M)]
    pos.append(b4[['CNPJ_FUNDO','DT_COMPTC','TP_APLIC','TP_ATIVO','CD_ATIVO','DS_ATIVO','CD_ISIN','QT_POS_FINAL','VL_MERC_POS_FINAL','QT_AQUIS_NEGOC','VL_AQUIS_NEGOC','QT_VENDA_NEGOC','VL_VENDA_NEGOC','DT_CONFID_APLIC']])
    b8=read(zf,'BLC_8',quoting=3,on_bad_lines='skip'); b8=b8[b8.CNPJ_FUNDO.isin(M)]
    p8.append(b8[['CNPJ_FUNDO','DT_COMPTC','TP_APLIC','TP_ATIVO','DS_ATIVO','QT_POS_FINAL','VL_MERC_POS_FINAL','QT_AQUIS_NEGOC','VL_AQUIS_NEGOC','QT_VENDA_NEGOC','VL_VENDA_NEGOC']])
    pl=read(zf,'_PL_'); pls.append(pl[pl.CNPJ_FUNDO.isin(M)][['CNPJ_FUNDO','DT_COMPTC','VL_PATRIM_LIQ']])
    print(os.path.basename(z),len(M),len(pos[-1]),len(p8[-1]),len(pls[-1]),flush=True)
d8=pd.concat(p8); d8['CD_ATIVO']=d8.DS_ATIVO.str.upper().str.extract(r'\b([A-Z]{4}\d{1,2}[A-Z]?)\b',expand=False); d8['CD_ISIN']=None
pd.concat(pos).to_pickle(W+'/hist_pos.pkl'); d8.to_pickle(W+'/hist_pos8.pkl'); pd.concat(pls).to_pickle(W+'/hist_pl.pkl'); pd.concat(cot).to_pickle(W+'/hist_cot.pkl')
json.dump(sorted(M),open(W+'/allfunds.json','w'))
# cotas (Informe Diário)
out=[]
for z in sorted(glob.glob(R+'/inf_diario_fi_20*.zip')):
    zf=zipfile.ZipFile(z)
    for n in zf.namelist():
        d=pd.read_csv(zf.open(n),sep=';',dtype=str).rename(columns=REN)
        if 'ID_SUBCLASSE' in d: d=d[d.ID_SUBCLASSE.isna()]
        out.append(d[d.CNPJ_FUNDO.isin(M)][['CNPJ_FUNDO','DT_COMPTC','VL_QUOTA','VL_PATRIM_LIQ']])
q=pd.concat(out); q['VL_QUOTA']=pd.to_numeric(q.VL_QUOTA,errors='coerce'); q['VL_PATRIM_LIQ']=pd.to_numeric(q.VL_PATRIM_LIQ,errors='coerce')
q['ym']=q.DT_COMPTC.str[:7]; q=q.sort_values('DT_COMPTC').groupby(['CNPJ_FUNDO','ym']).tail(1)
q.to_pickle(W+'/quotas.pkl'); print(len(q),q.ym.min(),q.ym.max())
