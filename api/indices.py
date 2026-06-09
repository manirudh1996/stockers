from http.server import BaseHTTPRequestHandler
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from _data import INDEX_META
import yfinance as yf

_cache = {"indices": [], "time": 0}
CACHE_TTL = 120


def _fetch():
    yf_syms = [i["yf"] for i in INDEX_META]
    data = yf.download(
        tickers=yf_syms, period="5d", interval="1d",
        group_by="ticker", auto_adjust=True, progress=False, threads=True,
    )
    result = []
    for idx in INDEX_META:
        entry = {**idx, "val": 0, "chg": 0}
        try:
            sym_yf = idx["yf"]
            df = data[sym_yf] if len(yf_syms) > 1 else data
            close = df["Close"].dropna()
            if len(close) >= 2:
                val = float(close.iloc[-1])
                prev = float(close.iloc[-2])
                entry["val"] = round(val, 2)
                entry["chg"] = round((val - prev) / prev * 100, 2)
        except Exception:
            pass
        result.append(entry)
    return result


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _cache
        if time.time() - _cache["time"] > CACHE_TTL or not _cache["indices"]:
            try:
                _cache["indices"] = _fetch()
                _cache["time"] = time.time()
            except Exception:
                pass

        body = json.dumps({
            "indices": _cache["indices"] or [{**i, "val": 0, "chg": 0} for i in INDEX_META],
            "last_refresh": _cache["time"],
        }).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, s-maxage=60")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass
