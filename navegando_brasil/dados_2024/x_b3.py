import pandas as pd, zipfile, glob
rows=[]
for z in sorted(glob.glob('/home/user/raw/b3/COTAHIST_A*.ZIP')):
    zf=zipfile.ZipFile(z)
    for n in zf.namelist():
        for line in zf.open(n):
            if line[:2]!=b'01' or line[24:27]!=b'010': continue
            d=line[2:10].decode()
            if d<'20231101': continue
            rows.append((line[12:24].decode('latin1').strip(),d,int(line[108:121])/100/int(line[210:217]),line[27:39].decode('latin1').strip()))
b=pd.DataFrame(rows,columns=['tk','dt','close','nome'])
b.to_pickle('/home/user/work/b3_daily.pkl'); print(len(b),b.dt.max())
