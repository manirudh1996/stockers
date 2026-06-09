from http.server import BaseHTTPRequestHandler
import json, time

try:
    import requests as _req
    HAS_REQ = True
except ImportError:
    HAS_REQ = False

# nse field must match exact index name from NSE allIndices API
INDICES = [
    {"id":"n50",   "label":"NIFTY 50",       "nse":"NIFTY 50",         "tags":["n50"]},
    {"id":"bnk",   "label":"BANK NIFTY",     "nse":"NIFTY BANK",       "tags":["bnk"]},
    {"id":"nxt50", "label":"NIFTY NEXT 50",  "nse":"NIFTY NEXT 50",    "tags":["nxt50"]},
    {"id":"n100",  "label":"NIFTY 100",      "nse":"NIFTY 100",        "tags":["n50","nxt50"]},
    {"id":"n200",  "label":"NIFTY 200",      "nse":"NIFTY 200",        "tags":["n50","nxt50","mid"]},
    {"id":"mid",   "label":"NIFTY MIDCAP",   "nse":"NIFTY MIDCAP 50",  "tags":["mid"]},
    {"id":"sml",   "label":"NIFTY SMALLCAP", "nse":"NIFTY SMLCAP 50",  "tags":["sml"]},
    {"id":"nit",   "label":"NIFTY IT",       "nse":"NIFTY IT",         "tags":["nit"]},
]

NSE_HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
    "X-Requested-With": "XMLHttpRequest",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

_cache = {"indices": [], "ts": 0}
_sess = {"s": None, "ts": 0}
CACHE_TTL = 120
SESSION_TTL = 270


def _get_sess():
    if not HAS_REQ:
        return None
    now = time.time()
    if _sess["s"] is None or now - _sess["ts"] > SESSION_TTL:
        s = _req.Session()
        s.headers.update(NSE_HDR)
        try:
            s.get("https://www.nseindia.com/", timeout=8)
        except Exception:
            pass
        _sess["s"] = s
        _sess["ts"] = now
    return _sess["s"]


def _build():
    session = _get_sess()
    if not session:
        return [{k: v for k, v in i.items() if k != "nse"} | {"val": 0, "chg": 0} for i in INDICES]

    try:
        r = session.get("https://www.nseindia.com/api/allIndices", timeout=10)
        if r.status_code == 200:
            idx_map = {}
            for item in r.json().get("data", []):
                name = item.get("index", "")
                last = item.get("last") or 0
                pchg = item.get("percentChange") or 0
                if name and float(last) > 0:
                    idx_map[name] = {
                        "val": round(float(last), 2),
                        "chg": round(float(pchg), 2),
                    }
            result = []
            for idx in INDICES:
                p = idx_map.get(idx["nse"], {})
                result.append({
                    "id": idx["id"],
                    "label": idx["label"],
                    "tags": idx["tags"],
                    "val": p.get("val", 0),
                    "chg": p.get("chg", 0),
                })
            return result
    except Exception:
        pass

    return [{k: v for k, v in i.items() if k != "nse"} | {"val": 0, "chg": 0} for i in INDICES]


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if time.time() - _cache["ts"] > CACHE_TTL or not _cache["indices"]:
            try:
                _cache["indices"] = _build()
                _cache["ts"] = time.time()
            except Exception:
                pass

        data = _cache["indices"] or [
            {k: v for k, v in i.items() if k != "nse"} | {"val": 0, "chg": 0}
            for i in INDICES
        ]
        body = json.dumps({"indices": data, "last_refresh": _cache["ts"]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass
