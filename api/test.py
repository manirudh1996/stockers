from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        results = {}

        # Test 1: NSE stock with 5d period
        try:
            h = yf.Ticker("RELIANCE.NS").history(period="5d")
            results["RELIANCE_5d"] = {"rows": len(h), "ok": len(h) >= 2}
            if len(h) >= 2:
                results["RELIANCE_5d"]["price"] = round(float(h["Close"].iloc[-1]), 2)
                results["RELIANCE_5d"]["chg"] = round(
                    (float(h["Close"].iloc[-1]) - float(h["Close"].iloc[-2]))
                    / float(h["Close"].iloc[-2]) * 100, 2)
        except Exception as e:
            results["RELIANCE_5d"] = {"error": str(e)}

        # Test 2: US stock to verify yfinance works at all
        try:
            h2 = yf.Ticker("AAPL").history(period="5d")
            results["AAPL_5d"] = {"rows": len(h2), "ok": len(h2) >= 2}
            if len(h2) >= 2:
                results["AAPL_5d"]["price"] = round(float(h2["Close"].iloc[-1]), 2)
        except Exception as e:
            results["AAPL_5d"] = {"error": str(e)}

        # Test 3: NSE with 1mo period
        try:
            h3 = yf.Ticker("TCS.NS").history(period="1mo")
            results["TCS_1mo"] = {"rows": len(h3), "ok": len(h3) >= 2}
            if len(h3) >= 2:
                results["TCS_1mo"]["price"] = round(float(h3["Close"].iloc[-1]), 2)
        except Exception as e:
            results["TCS_1mo"] = {"error": str(e)}

        body = json.dumps(results, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass
