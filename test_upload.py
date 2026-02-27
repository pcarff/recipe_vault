import urllib.request
import urllib.parse
import json
import base64

with open('/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/mz2_work/LCB2_export.mx2', 'rb') as f:
    content = f.read()

payload = {
    "filename": "LCB2_export.mx2",
    "content": base64.b64encode(content).decode('ascii')
}
data = json.dumps(payload).encode('utf-8')

req = urllib.request.Request("http://localhost:8080/api/import_mz2", data=data, method="POST")
req.add_header('Content-Type', 'application/json')
try:
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print("Body:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code)
