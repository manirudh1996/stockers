from http.server import BaseHTTPRequestHandler
import json, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from _data import STOCK_META
import yfinance as yf

_cache = {"stocks": [], "time": 0}
CACHE_TTL = 120


def _fetch():
    yf_syms = [s["yf"] for s in STOCK_META]
    data = yf.download(
        tickers=yf_syms, period="5d", interval="1d",
        group_by="ticker", auto_adjust=True, progress=False, threads=True,
    )
    result = []
    for stock in STOCK_META:
        entry = {
            "sym": stock["sym"], "name": stock["name"],
            "sector": stock["sector"], "mcap": stock["mcap"],
            "idx": stock["idx"], "price": 0, "chg": 0,
            "high52": 0, "low52": 0, "live": False,
        }
        try:
            sym_yf = stock["yf"]
            df = data[sym_yf] if len(yf_syms) > 1 else data
            close = df["Close"].dropna()
            if len(close) >= 2:
                cur = float(close.iloc[-1])
                prev = float(close.iloc[-2])
                entry["price"] = round(cur, 2)
                entry["chg"] = round((cur - prev) / prev * 100, 2)
                entry["high52"] = round(float(df["High"].dropna().max()), 2)
                entry["low52"] = round(float(df["Low"].dropna().min()), 2)
                entry["live"] = True
        except Exception:
            pass
        result.append(entry)
    return result


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _cache
        if time.time() - _cache["time"] > CACHE_TTL or not _cache["stocks"]:
            try:
                _cache["stocks"] = _fetch()
                _cache["time"] = time.time()
            except Exception as e:
                pass

        body = json.dumps({
            "stocks": _cache["stocks"],
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
