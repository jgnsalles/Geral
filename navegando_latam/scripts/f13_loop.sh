cd /home/user/raw/latam/13f
head -42 urls.txt | while read u; do
  n=$(basename "$u" .zip); o=/home/user/work/latam/f13/$n.pkl
  [ -s $o ] && continue
  for i in 1 2 3; do curl -sf -A 'Navegando-Research/1.0 research@example.org' -o z.zip "https://www.sec.gov$u" && break; sleep 15; done
  python3 -I /home/user/work/latam/scripts/f13.py z.zip $o /home/user/work/latam/latam_cusips.txt >> /home/user/work/latam/f13/log.txt 2>&1
  rm -f z.zip
done
echo done >> /home/user/work/latam/f13/log.txt
