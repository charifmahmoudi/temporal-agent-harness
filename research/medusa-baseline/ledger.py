"""Separate-process payment test contract; no real provider or money."""
import json, sqlite3, os, time
from http.server import BaseHTTPRequestHandler, HTTPServer
os.makedirs("evidence", exist_ok=True)
db=sqlite3.connect("evidence/provider.sqlite")
db.execute("CREATE TABLE IF NOT EXISTS effects (id INTEGER PRIMARY KEY, kind TEXT, amount TEXT, external_id TEXT, operation_key TEXT UNIQUE, input TEXT, committed_ns INTEGER)")
db.commit()
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  rows=[dict(zip(["id","kind","amount","external_id","operation_key","input","committed_ns"],r)) for r in db.execute("SELECT * FROM effects ORDER BY id")]
  self.respond(rows)
 def respond(self,data):
  self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(json.dumps(data).encode())
 def do_POST(self):
  x=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
  key=x.get("context",{}).get("idempotency_key")
  if key: key=x["kind"]+":"+key
  db.execute("INSERT OR IGNORE INTO effects(kind,amount,external_id,operation_key,input,committed_ns) VALUES(?,?,?,?,?,?)",(x["kind"],str(x["amount"]),x.get("data",{}).get("external_id"),key,json.dumps(x),time.time_ns()))
  db.commit()
  with open("evidence/provider-requests.jsonl","a") as f: f.write(json.dumps({"time_ns":time.time_ns(),"request":x})+"\n")
  self.respond({"committed":True})
HTTPServer(("127.0.0.1",8877),Handler).serve_forever()
