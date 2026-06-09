from http.server import BaseHTTPRequestHandler
import json, time
import yfinance as yf

INDICES = [
    {"id":"n50",   "yf":"^NSEI",      "label":"NIFTY 50",       "tags":["n50"]},
    {"id":"bnk",   "yf":"^NSEBANK",   "label":"BANK NIFTY",     "tags":["bnk"]},
    {"id":"nxt50", "yf":"^NSMIDCP50", "label":"NIFTY NEXT 50",  "tags":["nxt50"]},
    {"id":"n100",  "yf":"^CNX100",    "label":"NIFTY 100",      "tags":["n50","nxt50"]},
    {"id":"n200",  "yf":"^CNX200",    "label":"NIFTY 200",      "tags":["n50","nxt50","mid"]},
    {"id":"mid",   "yf":"^NSEMDCP50", "label":"NIFTY MIDCAP",   "tags":["mid"]},
    {"id":"sml",   "yf":"^CNXSC",     "label":"NIFTY SMALLCAP", "tags":["sml"]},
    {"id":"nit",   "yf":"^CNXIT",     "label":"NIFTY IT",       "tags":["nit"]},
]

_cache = {"indices": [], "ts": 0}
CACHE_TTL = 120


def _build():
    yf_syms = [i["yf"] for i in INDICES]
    data = yf.download(
        tickers=yf_syms, period="2d", interval="1d",
        group_by="ticker", auto_adjust=True, progress=False, threads=True,
    )
    result = []
    for idx in INDICES:
        entry = {**idx, "val": 0, "chg": 0}
        try:
            df = data[idx["yf"]] if len(yf_syms) > 1 else data
            close = df["Close"].dropna()
            if len(close) >= 2:
                val, prev = float(close.iloc[-1]), float(close.iloc[-2])
                entry["val"] = round(val, 2)
                entry["chg"] = round((val - prev) / prev * 100, 2)
        except Exception:
            pass
        result.append(entry)
    return result


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if time.time() - _cache["ts"] > CACHE_TTL or not _cache["indices"]:
            try:
                _cache["indices"] = _build()
                _cache["ts"] = time.time()
            except Exception:
                pass

        body = json.dumps({
            "indices": _cache["indices"] or [{**i, "val": 0, "chg": 0} for i in INDICES],
            "last_refresh": _cache["ts"],
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass
