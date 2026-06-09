from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = {"status": "unknown", "error": None, "data": None}
        try:
            ticker = yf.Ticker("RELIANCE.NS")
            hist = ticker.history(period="2d")
            if not hist.empty and len(hist) >= 2:
                cur = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2])
                result = {
                    "status": "ok",
                    "price": round(cur, 2),
                    "chg": round((cur - prev) / prev * 100, 2),
                    "rows": len(hist),
                }
            else:
                result = {"status": "empty", "rows": len(hist), "cols": list(hist.columns)}
        except Exception as e:
            result = {"status": "error", "error": str(e)}

        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass
