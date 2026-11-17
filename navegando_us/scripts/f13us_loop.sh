mkdir -p /home/user/work/us/f13 /home/user/raw/us13f && cd /home/user/raw/us13f
head -42 /home/user/raw/latam/13f/urls.txt | while read u; do
  n=$(basename "$u" .zip); o=/home/user/work/us/f13/$n.pkl
  [ -s $o ] && continue
  for i in 1 2 3; do curl -sf -A 'Navegando-Research/1.0 research@example.org' -o z.zip "https://www.sec.gov$u" && break; sleep 15; done
  python3 -I /home/user/work/us/scripts/f13us.py z.zip $o >> /home/user/work/us/f13/log.txt 2>&1
  rm -f z.zip
done
echo done >> /home/user/work/us/f13/log.txt
