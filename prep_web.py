"""Downloads every CDN script into www/lib so the APK works offline, and tidies index.html for the app."""
import re, os, urllib.request, hashlib
p = "www/index.html"
h = open(p, encoding="utf-8").read()
os.makedirs("www/lib", exist_ok=True)
def local(url):
    name = hashlib.md5(url.encode()).hexdigest()[:8] + "-" + url.split("?")[0].rstrip("/").split("/")[-1]
    path = "www/lib/" + name
    if not os.path.exists(path):
        print("downloading", url)
        urllib.request.urlretrieve(url, path)
    return "lib/" + name
for u in set(re.findall(r'<script[^>]+src="(https://[^"]+)"', h)):
    h = h.replace(u, local(u))
h = re.sub(r'const PDF_WORKER = "[^"]+";', 'const PDF_WORKER = "' + local("https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js") + '";', h)
h = h.replace("if('serviceWorker' in navigator &&", "if(false &&")   # not needed inside the APK
open(p, "w", encoding="utf-8").write(h)
print("ready")
