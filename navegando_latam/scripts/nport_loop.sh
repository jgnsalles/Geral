cd /home/user/raw/latam/us
for q in 2026q3 2026q1 2025q4 2025q3 2025q2 2025q1 2024q4 2024q3; do
  [ -s /home/user/work/latam/np/$q.pkl ] && continue
  for i in 1 2 3; do curl -sf -A 'Navegando-Research/1.0 research@example.org' -o $q.zip https://www.sec.gov/files/dera/data/form-n-port-data-sets/${q}_nport.zip && break; sleep 10; done
  python3 -I /home/user/work/latam/scripts/nport.py $q.zip /home/user/work/latam/np/$q.pkl >> /home/user/work/latam/np/log.txt 2>&1
  rm -f $q.zip
done
echo done >> /home/user/work/latam/np/log.txt
