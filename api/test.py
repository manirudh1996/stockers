from http.server import BaseHTTPRequestHandler
import json

try:
    import requests as _req
    HAS_REQ = True
except ImportError:
    HAS_REQ = False

NSE_HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "X-Requested-With": "XMLHttpRequest",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        results = {"has_requests": HAS_REQ}

        if HAS_REQ:
            try:
                s = _req.Session()
                s.headers.update(NSE_HDR)

                # Step 1: Hit homepage to get session cookies
                r0 = s.get("https://www.nseindia.com/", timeout=8)
                results["nse_home"] = {"status": r0.status_code, "ok": r0.status_code == 200}

                # Step 2: Fetch NIFTY 50 constituents
                r1 = s.get(
                    "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050",
                    timeout=10,
                )
                results["nifty50"] = {"status": r1.status_code}
                if r1.status_code == 200:
                    items = r1.json().get("data", [])
                    results["nifty50"]["count"] = len(items)
                    results["nifty50"]["ok"] = len(items) > 0
                    reliance = next((x for x in items if x.get("symbol") == "RELIANCE"), None)
                    if reliance:
                        results["RELIANCE"] = {
                            "price": reliance.get("lastPrice"),
                            "chg_pct": reliance.get("pChange"),
                            "year_high": reliance.get("yearHigh"),
                            "year_low": reliance.get("yearLow"),
                        }

                # Step 3: All indices
                r2 = s.get("https://www.nseindia.com/api/allIndices", timeout=10)
                results["all_indices"] = {"status": r2.status_code}
                if r2.status_code == 200:
                    idx_items = r2.json().get("data", [])
                    results["all_indices"]["count"] = len(idx_items)
                    results["all_indices"]["ok"] = len(idx_items) > 0
                    nifty = next((x for x in idx_items if x.get("index") == "NIFTY 50"), None)
                    if nifty:
                        results["NIFTY_50"] = {
                            "val": nifty.get("last"),
                            "chg_pct": nifty.get("percentChange"),
                        }
            except Exception as e:
                results["error"] = str(e)

        body = json.dumps(results, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass
