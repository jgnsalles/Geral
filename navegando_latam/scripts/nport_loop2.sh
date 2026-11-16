cd /home/user/raw/latam/us
for y in 2026 2025 2024 2023 2022 2021 2020 2019; do for n in 4 3 2 1; do q=${y}q$n
  [ "$q" \> "2026q3" ] && continue; [ "$q" \< "2019q4" ] && continue
  [ -s /home/user/work/latam/nf/$q.pkl ] && [ -s /home/user/work/latam/np2/$q.pkl ] && continue
  [ -s $q.zip ] || for i in 1 2 3; do curl -sf -A 'Navegando-Research/1.0 research@example.org' -o $q.zip https://www.sec.gov/files/dera/data/form-n-port-data-sets/${q}_nport.zip && break; sleep 15; done
  python3 -I /home/user/work/latam/scripts/nport.py $q.zip /home/user/work/latam/np2/$q.pkl >> /home/user/work/latam/np2/log.txt 2>&1
  python3 -I /home/user/work/latam/scripts/nport_fundos.py $q.zip /home/user/work/latam/nf/$q.pkl >> /home/user/work/latam/nf/log.txt 2>&1
  rm -f $q.zip
done; done
echo done >> /home/user/work/latam/nf/log.txt
