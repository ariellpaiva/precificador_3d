"""
Precificador 3D - servidor local.

Uso:
    python server.py            # só neste computador: http://precificador.local/
    python server.py --lan      # também para outros aparelhos da rede: http://<ip-do-pc>:8000
    python server.py --port 9000
    python server.py --lan --nome precificador --port 80   # http://precificador.local
"""
import argparse
import json
import re
import secrets
import socket
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response

BASE = Path(__file__).parent
DATA = BASE / "data"
BLOBS = DATA / "blobs"
DB_PATH = DATA / "precificador.db"
INDEX = BASE / "static" / "index.html"

SEG = re.compile(r"^[A-Za-z0-9_\-.~:@+]{1,200}$")
MAX_DOC = 256 * 1024
MAX_BLOB = 20 * 1024 * 1024
IMG_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

DATA.mkdir(exist_ok=True)
BLOBS.mkdir(exist_ok=True)


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


with closing(conn()) as c, c:
    c.execute("CREATE TABLE IF NOT EXISTS docs (col TEXT, id TEXT, data TEXT NOT NULL, updated TEXT, PRIMARY KEY (col, id))")
    c.execute("CREATE TABLE IF NOT EXISTS blobs (id TEXT PRIMARY KEY, ctype TEXT, size INTEGER, created TEXT)")


def now():
    return datetime.now(timezone.utc).isoformat()


def check(*segs):
    for s in segs:
        if not SEG.match(s) or s in (".", ".."):
            raise HTTPException(400, f"segmento inválido: {s!r}")


app = FastAPI(title="Precificador 3D", docs_url=None, redoc_url=None)


@app.get("/")
def index():
    return FileResponse(INDEX, headers={"Cache-Control": "no-cache"})


# ---------- documentos ----------
@app.get("/api/docs/{col}")
def list_docs(col: str):
    check(col)
    with closing(conn()) as c:
        rows = c.execute("SELECT id, data FROM docs WHERE col=? ORDER BY id", (col,)).fetchall()
    return [{"id": r["id"], "data": json.loads(r["data"])} for r in rows]


@app.get("/api/docs/{col}/{doc_id}")
def get_doc(col: str, doc_id: str):
    check(col, doc_id)
    with closing(conn()) as c:
        r = c.execute("SELECT data FROM docs WHERE col=? AND id=?", (col, doc_id)).fetchone()
    return {"exists": bool(r), "data": json.loads(r["data"]) if r else None}


def _validate(body):
    if not isinstance(body, dict):
        raise HTTPException(400, "o documento precisa ser um objeto JSON")
    raw = json.dumps(body, ensure_ascii=False)
    if len(raw.encode()) > MAX_DOC:
        raise HTTPException(413, "documento maior que 256 KB")
    return raw


@app.put("/api/docs/{col}/{doc_id}")
def set_doc(col: str, doc_id: str, body: dict):
    check(col, doc_id)
    raw = _validate(body)
    with closing(conn()) as c, c:
        c.execute("INSERT OR REPLACE INTO docs (col, id, data, updated) VALUES (?,?,?,?)", (col, doc_id, raw, now()))
    return {"ok": True}


@app.patch("/api/docs/{col}/{doc_id}")
def update_doc(col: str, doc_id: str, body: dict):
    check(col, doc_id)
    with closing(conn()) as c, c:
        r = c.execute("SELECT data FROM docs WHERE col=? AND id=?", (col, doc_id)).fetchone()
        if not r:
            raise HTTPException(404, "documento não existe")
        merged = {**json.loads(r["data"]), **body}
        c.execute("UPDATE docs SET data=?, updated=? WHERE col=? AND id=?", (_validate(merged), now(), col, doc_id))
    return {"ok": True}


@app.delete("/api/docs/{col}/{doc_id}")
def delete_doc(col: str, doc_id: str):
    check(col, doc_id)
    with closing(conn()) as c, c:
        c.execute("DELETE FROM docs WHERE col=? AND id=?", (col, doc_id))
    return {"ok": True}


# ---------- imagens ----------
@app.post("/api/assets")
async def upload(file: UploadFile = File(...)):
    ctype = (file.content_type or "").split(";")[0].strip()
    if ctype not in IMG_TYPES:
        raise HTTPException(415, "tipo de arquivo não suportado")
    data = await file.read()
    if len(data) > MAX_BLOB:
        raise HTTPException(413, "imagem maior que 20 MB")
    blob_id = secrets.token_hex(16)
    (BLOBS / blob_id).write_bytes(data)
    with closing(conn()) as c, c:
        c.execute("INSERT INTO blobs VALUES (?,?,?,?)", (blob_id, ctype, len(data), now()))
    return {"id": blob_id, "url": f"/_blob/{blob_id}", "sizeBytes": len(data), "contentType": ctype}


@app.get("/_blob/{blob_id}")
def get_blob(blob_id: str):
    check(blob_id)
    with closing(conn()) as c:
        r = c.execute("SELECT ctype FROM blobs WHERE id=?", (blob_id,)).fetchone()
    path = BLOBS / blob_id
    if not r or not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type=r["ctype"], headers={"Cache-Control": "public, max-age=31536000, immutable"})


@app.delete("/api/assets/{blob_id}")
def delete_blob(blob_id: str):
    check(blob_id)
    (BLOBS / blob_id).unlink(missing_ok=True)
    with closing(conn()) as c, c:
        c.execute("DELETE FROM blobs WHERE id=?", (blob_id,))
    return {"ok": True}


# ---------- backup ----------
@app.get("/api/export")
def export():
    with closing(conn()) as c:
        rows = c.execute("SELECT col, id, data FROM docs ORDER BY col, id").fetchall()
    out = {}
    for r in rows:
        out.setdefault(r["col"], {})[r["id"]] = json.loads(r["data"])
    name = f"precificador-backup-{datetime.now():%Y%m%d-%H%M}.json"
    return JSONResponse(out, headers={"Content-Disposition": f'attachment; filename="{name}"'})


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


def lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "SEU-IP"


def anunciar_mdns(nome, ip, port):
    """Publica <nome>.local na rede (mDNS/Bonjour). Retorna o objeto para desligar ao sair."""
    try:
        from zeroconf import ServiceInfo, Zeroconf
    except ImportError:
        print("  [aviso] instale 'zeroconf' (pip install zeroconf) para usar --nome")
        return None
    zc = Zeroconf()
    info = ServiceInfo(
        "_http._tcp.local.",
        f"Precificador 3D._http._tcp.local.",
        addresses=[socket.inet_aton(ip)],
        port=port,
        server=f"{nome}.local.",
        properties={"path": "/"},
    )
    zc.register_service(info)
    return zc, info


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lan", action="store_true", help="aceita conexões de outros aparelhos da rede local")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--nome", help="nome na rede, ex.: precificador -> http://precificador.local (requer --lan)")
    a = ap.parse_args()
    host = "0.0.0.0" if a.lan else "127.0.0.1"
    porta = "" if a.port == 80 else f":{a.port}"
    ip = lan_ip()
    print(f"\n  Precificador rodando em http://localhost{porta}")
    mdns = None
    if a.lan:
        if a.nome:
            nome = re.sub(r"[^a-z0-9-]", "", a.nome.lower()) or "precificador"
            mdns = anunciar_mdns(nome, ip, a.port)
        if mdns:
            print(f"  Na rede local:          http://{nome}.local{porta}/")
            print(f"  Ou pelo IP:             http://{ip}{porta}/")
        else:
            print(f"  Na rede local:          http://{ip}{porta}/")
    print(f"  Dados em: {DATA.resolve()}\n")
    import threading, webbrowser
    threading.Timer(1.5, webbrowser.open, [f"http://localhost{porta}"]).start()
    try:
        uvicorn.run(app, host=host, port=a.port, log_level="warning")
    finally:
        if mdns:
            zc, info = mdns
            zc.unregister_service(info)
            zc.close()
