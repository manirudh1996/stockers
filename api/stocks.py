from http.server import BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, time, urllib.parse, threading

try:
    import requests as _req
    HAS_REQ = True
except ImportError:
    HAS_REQ = False

STOCKS = [
    ("HDFCBANK","HDFCBANK.NS","HDFC Bank",12.4,"Banking",["n50","bnk","n100","n200"]),
    ("ICICIBANK","ICICIBANK.NS","ICICI Bank",7.7,"Banking",["n50","bnk","n100","n200"]),
    ("KOTAKBANK","KOTAKBANK.NS","Kotak Mahindra Bank",3.7,"Banking",["n50","bnk","n100","n200"]),
    ("SBIN","SBIN.NS","State Bank of India",3.7,"Banking",["n50","bnk","n100","n200"]),
    ("AXISBANK","AXISBANK.NS","Axis Bank",3.5,"Banking",["n50","bnk","n100","n200"]),
    ("INDUSINDBK","INDUSINDBK.NS","IndusInd Bank",0.96,"Banking",["n50","bnk","n100","n200"]),
    ("BANDHANBNK","BANDHANBNK.NS","Bandhan Bank",0.30,"Banking",["bnk","nxt50","n100","n200"]),
    ("FEDERALBNK","FEDERALBNK.NS","Federal Bank",0.42,"Banking",["bnk","nxt50","n100","n200"]),
    ("IDFCFIRSTB","IDFCFIRSTB.NS","IDFC First Bank",0.55,"Banking",["bnk","nxt50","n100","n200"]),
    ("AUBANK","AUBANK.NS","AU Small Finance Bank",0.50,"Banking",["bnk","nxt50","n100","n200"]),
    ("PNB","PNB.NS","Punjab National Bank",1.2,"Banking",["bnk","nxt50","n100","n200"]),
    ("CANARABANK","CANARABANK.NS","Canara Bank",0.89,"Banking",["bnk","nxt50","n100","n200"]),
    ("BANKBARODA","BANKBARODA.NS","Bank of Baroda",1.1,"Banking",["bnk","nxt50","n100","n200"]),
    ("RBLBANK","RBLBANK.NS","RBL Bank",0.18,"Banking",["bnk","mid","n200"]),
    ("YESBANK","YESBANK.NS","Yes Bank",0.62,"Banking",["bnk","mid","n200"]),
    ("TCS","TCS.NS","Tata Consultancy Services",12.9,"IT",["n50","nit","n100","n200"]),
    ("INFY","INFY.NS","Infosys",6.6,"IT",["n50","nit","n100","n200"]),
    ("HCLTECH","HCLTECH.NS","HCL Technologies",3.9,"IT",["n50","nit","n100","n200"]),
    ("WIPRO","WIPRO.NS","Wipro",2.4,"IT",["n50","nit","n100","n200"]),
    ("LTIM","LTIM.NS","LTIMindtree",1.7,"IT",["n50","nit","n100","n200"]),
    ("TECHM","TECHM.NS","Tech Mahindra",1.2,"IT",["n50","nit","n100","n200"]),
    ("MPHASIS","MPHASIS.NS","Mphasis",0.46,"IT",["nxt50","nit","n100","n200"]),
    ("PERSISTENT","PERSISTENT.NS","Persistent Systems",0.70,"IT",["nxt50","nit","n100","n200"]),
    ("COFORGE","COFORGE.NS","Coforge",0.35,"IT",["mid","nit","n200"]),
    ("KPIT","KPIT.NS","KPIT Technologies",0.34,"IT",["mid","nit","n200"]),
    ("HAPPYMNDS","HAPPYMNDS.NS","Happiest Minds Tech",0.11,"IT",["sml","nit"]),
    ("MASTEK","MASTEK.NS","Mastek",0.09,"IT",["sml","nit"]),
    ("BSOFT","BSOFT.NS","Birlasoft",0.16,"IT",["mid","nit","n200"]),
    ("ZENSARTECH","ZENSARTECH.NS","Zensar Technologies",0.08,"IT",["sml","nit"]),
    ("NAUKRI","NAUKRI.NS","Info Edge (Naukri)",0.87,"IT",["nxt50","nit","n100","n200"]),
    ("RELIANCE","RELIANCE.NS","Reliance Industries",19.2,"Energy",["n50","n100","n200"]),
    ("ONGC","ONGC.NS","ONGC",3.4,"Energy",["n50","n100","n200"]),
    ("BPCL","BPCL.NS","Bharat Petroleum",1.5,"Energy",["n50","n100","n200"]),
    ("IOC","IOC.NS","Indian Oil Corp",2.4,"Energy",["nxt50","n100","n200"]),
    ("GAIL","GAIL.NS","GAIL India",1.5,"Energy",["nxt50","n100","n200"]),
    ("PETRONET","PETRONET.NS","Petronet LNG",0.40,"Energy",["nxt50","n100","n200"]),
    ("OIL","OIL.NS","Oil India",0.50,"Energy",["mid","n200"]),
    ("MRPL","MRPL.NS","MRPL",0.31,"Energy",["mid","n200"]),
    ("HINDUNILVR","HINDUNILVR.NS","Hindustan Unilever",5.8,"FMCG",["n50","n100","n200"]),
    ("ITC","ITC.NS","ITC Ltd",5.7,"FMCG",["n50","n100","n200"]),
    ("NESTLEIND","NESTLEIND.NS","Nestle India",2.4,"FMCG",["n50","n100","n200"]),
    ("BRITANNIA","BRITANNIA.NS","Britannia Industries",1.1,"FMCG",["n50","n100","n200"]),
    ("TATACONSUM","TATACONSUM.NS","Tata Consumer Products",0.9,"FMCG",["n50","n100","n200"]),
    ("DABUR","DABUR.NS","Dabur India",1.0,"FMCG",["nxt50","n100","n200"]),
    ("MARICO","MARICO.NS","Marico",0.73,"FMCG",["nxt50","n100","n200"]),
    ("COLPAL","COLPAL.NS","Colgate-Palmolive India",0.64,"FMCG",["nxt50","n100","n200"]),
    ("GODREJCP","GODREJCP.NS","Godrej Consumer Products",1.3,"FMCG",["nxt50","n100","n200"]),
    ("EMAMILTD","EMAMILTD.NS","Emami",0.24,"FMCG",["mid","n200"]),
    ("VBL","VBL.NS","Varun Beverages",0.73,"FMCG",["nxt50","n100","n200"]),
    ("MARUTI","MARUTI.NS","Maruti Suzuki",3.8,"Auto",["n50","n100","n200"]),
    ("TATAMOTORS","TATAMOTORS.NS","Tata Motors",3.6,"Auto",["n50","n100","n200"]),
    ("M&M","M&M.NS","Mahindra & Mahindra",2.9,"Auto",["n50","n100","n200"]),
    ("BAJAJ-AUTO","BAJAJ-AUTO.NS","Bajaj Auto",2.6,"Auto",["n50","n100","n200"]),
    ("EICHERMOT","EICHERMOT.NS","Eicher Motors",1.2,"Auto",["n50","n100","n200"]),
    ("HEROMOTOCO","HEROMOTOCO.NS","Hero MotoCorp",0.9,"Auto",["n50","n100","n200"]),
    ("TVSMOTOR","TVSMOTOR.NS","TVS Motor Company",1.1,"Auto",["nxt50","n100","n200"]),
    ("ASHOKLEY","ASHOKLEY.NS","Ashok Leyland",0.69,"Auto",["nxt50","n100","n200"]),
    ("MRF","MRF.NS","MRF",0.62,"Auto",["nxt50","n100","n200"]),
    ("BOSCHLTD","BOSCHLTD.NS","Bosch India",0.40,"Auto",["mid","n200"]),
    ("EXIDEIND","EXIDEIND.NS","Exide Industries",0.39,"Auto",["mid","n200"]),
    ("BALKRISIND","BALKRISIND.NS","Balkrishna Industries",0.48,"Auto",["nxt50","n100","n200"]),
    ("BAJFINANCE","BAJFINANCE.NS","Bajaj Finance",4.4,"Finance",["n50","n100","n200"]),
    ("BAJAJFINSV","BAJAJFINSV.NS","Bajaj Finserv",2.7,"Finance",["n50","n100","n200"]),
    ("HDFCLIFE","HDFCLIFE.NS","HDFC Life Insurance",1.4,"Finance",["n50","n100","n200"]),
    ("SBILIFE","SBILIFE.NS","SBI Life Insurance",1.6,"Finance",["n50","n100","n200"]),
    ("SHRIRAMFIN","SHRIRAMFIN.NS","Shriram Finance",0.97,"Finance",["n50","n100","n200"]),
    ("CHOLAFIN","CHOLAFIN.NS","Cholamandalam Finance",0.81,"Finance",["nxt50","n100","n200"]),
    ("MUTHOOTFIN","MUTHOOTFIN.NS","Muthoot Finance",0.79,"Finance",["nxt50","n100","n200"]),
    ("PFC","PFC.NS","Power Finance Corp",1.5,"Finance",["nxt50","n100","n200"]),
    ("RECLTD","RECLTD.NS","REC Limited",1.5,"Finance",["nxt50","n100","n200"]),
    ("PAYTM","PAYTM.NS","One97 Comm (Paytm)",0.29,"Finance",["mid","n200"]),
    ("LICHSGFIN","LICHSGFIN.NS","LIC Housing Finance",0.34,"Finance",["mid","n200"]),
    ("SUNPHARMA","SUNPHARMA.NS","Sun Pharmaceutical",3.8,"Pharma",["n50","n100","n200"]),
    ("DRREDDY","DRREDDY.NS","Dr. Reddy's Labs",2.4,"Pharma",["n50","n100","n200"]),
    ("CIPLA","CIPLA.NS","Cipla",1.3,"Pharma",["n50","n100","n200"]),
    ("DIVISLAB","DIVISLAB.NS","Divi's Laboratories",1.2,"Pharma",["n50","n100","n200"]),
    ("TORNTPHARM","TORNTPHARM.NS","Torrent Pharma",0.79,"Pharma",["nxt50","n100","n200"]),
    ("ALKEM","ALKEM.NS","Alkem Laboratories",0.55,"Pharma",["nxt50","n100","n200"]),
    ("LUPIN","LUPIN.NS","Lupin",0.90,"Pharma",["nxt50","n100","n200"]),
    ("ABBOTINDIA","ABBOTINDIA.NS","Abbott India",0.50,"Pharma",["mid","n200"]),
    ("BIOCON","BIOCON.NS","Biocon",0.42,"Pharma",["nxt50","n100","n200"]),
    ("GLAXO","GLAXO.NS","GSK Pharma India",0.34,"Pharma",["mid","n200"]),
    ("PFIZER","PFIZER.NS","Pfizer India",0.21,"Pharma",["mid","n200"]),
    ("LT","LT.NS","Larsen & Toubro",4.9,"Infra",["n50","n100","n200"]),
    ("ADANIENT","ADANIENT.NS","Adani Enterprises",2.8,"Infra",["n50","n100","n200"]),
    ("ADANIPORTS","ADANIPORTS.NS","Adani Ports & SEZ",2.7,"Infra",["n50","n100","n200"]),
    ("GMRAIRPORT","GMRINFRA.NS","GMR Airports Infra",0.53,"Infra",["mid","n200"]),
    ("IRCON","IRCON.NS","IRCON International",0.22,"Infra",["mid","n200"]),
    ("RVNL","RVNL.NS","Rail Vikas Nigam",0.95,"Infra",["nxt50","n100","n200"]),
    ("NBCC","NBCC.NS","NBCC India",0.16,"Infra",["sml"]),
    ("IRB","IRB.NS","IRB Infrastructure",0.20,"Infra",["mid","n200"]),
    ("NTPC","NTPC.NS","NTPC",3.4,"Power",["n50","n100","n200"]),
    ("POWERGRID","POWERGRID.NS","Power Grid Corp",2.2,"Power",["n50","n100","n200"]),
    ("COALINDIA","COALINDIA.NS","Coal India",2.8,"Power",["n50","n100","n200"]),
    ("ADANIPOWER","ADANIPOWER.NS","Adani Power",2.2,"Power",["nxt50","n100","n200"]),
    ("TATAPOWER","TATAPOWER.NS","Tata Power Company",1.5,"Power",["nxt50","n100","n200"]),
    ("TORNTPOWER","TORNTPOWER.NS","Torrent Power",0.59,"Power",["mid","n200"]),
    ("CESC","CESC.NS","CESC",0.25,"Power",["mid","n200"]),
    ("NHPC","NHPC.NS","NHPC",0.90,"Power",["nxt50","n100","n200"]),
    ("BEL","BEL.NS","Bharat Electronics",1.8,"Defence",["n50","n100","n200"]),
    ("HAL","HAL.NS","Hindustan Aeronautics",1.5,"Defence",["nxt50","n100","n200"]),
    ("BEML","BEML.NS","BEML",0.14,"Defence",["mid","n200"]),
    ("BHEL","BHEL.NS","Bharat Heavy Electricals",0.94,"Defence",["nxt50","n100","n200"]),
    ("COCHINSHIP","COCHINSHIP.NS","Cochin Shipyard",0.22,"Defence",["mid","n200"]),
    ("MAZDOCK","MAZDOCK.NS","Mazagon Dock",0.46,"Defence",["mid","n200"]),
    ("TITAN","TITAN.NS","Titan Company",3.1,"Consumer",["n50","n100","n200"]),
    ("ASIANPAINT","ASIANPAINT.NS","Asian Paints",2.6,"Consumer",["n50","n100","n200"]),
    ("ZOMATO","ZOMATO.NS","Zomato",2.1,"Consumer",["n50","n100","n200"]),
    ("NYKAA","NYKAA.NS","Nykaa (FSN E-Comm)",0.51,"Consumer",["mid","n200"]),
    ("HAVELLS","HAVELLS.NS","Havells India",1.1,"Consumer",["nxt50","n100","n200"]),
    ("VOLTAS","VOLTAS.NS","Voltas",0.48,"Consumer",["nxt50","n100","n200"]),
    ("CROMPTON","CROMPTON.NS","Crompton Greaves Consumer",0.22,"Consumer",["mid","n200"]),
    ("VGUARD","VGUARD.NS","V-Guard Industries",0.15,"Consumer",["sml"]),
    ("APOLLOHOSP","APOLLOHOSP.NS","Apollo Hospitals",0.98,"Healthcare",["n50","n100","n200"]),
    ("MAXHEALTH","MAXHEALTH.NS","Max Healthcare",0.97,"Healthcare",["nxt50","n100","n200"]),
    ("FORTIS","FORTIS.NS","Fortis Healthcare",0.43,"Healthcare",["nxt50","n100","n200"]),
    ("ASTER","ASTERDM.NS","Aster DM Healthcare",0.19,"Healthcare",["mid","n200"]),
    ("NARAYNAHLT","NH.NS","Narayana Hrudayalaya",0.25,"Healthcare",["mid","n200"]),
    ("ULTRACEMCO","ULTRACEMCO.NS","UltraTech Cement",3.0,"Cement",["n50","n100","n200"]),
    ("GRASIM","GRASIM.NS","Grasim Industries",1.5,"Cement",["n50","n100","n200"]),
    ("AMBUJACEMENT","AMBUJACEM.NS","Ambuja Cements",1.1,"Cement",["nxt50","n100","n200"]),
    ("ACC","ACC.NS","ACC",0.37,"Cement",["nxt50","n100","n200"]),
    ("SHREECEM","SHREECEM.NS","Shree Cement",0.85,"Cement",["nxt50","n100","n200"]),
    ("RAMCOCEM","RAMCOCEM.NS","Ramco Cements",0.19,"Cement",["mid","n200"]),
    ("DALMIACEM","DALMIACEM.NS","Dalmia Bharat",0.38,"Cement",["nxt50","n100","n200"]),
    ("JSWSTEEL","JSWSTEEL.NS","JSW Steel",2.1,"Metals",["n50","n100","n200"]),
    ("TATASTEEL","TATASTEEL.NS","Tata Steel",2.1,"Metals",["n50","n100","n200"]),
    ("HINDALCO","HINDALCO.NS","Hindalco Industries",1.5,"Metals",["n50","n100","n200"]),
    ("SAIL","SAIL.NS","SAIL",0.56,"Metals",["nxt50","n100","n200"]),
    ("VEDL","VEDL.NS","Vedanta",1.7,"Metals",["nxt50","n100","n200"]),
    ("NMDC","NMDC.NS","NMDC",0.69,"Metals",["nxt50","n100","n200"]),
    ("NATIONALUM","NATIONALUM.NS","National Aluminium Co",0.33,"Metals",["mid","n200"]),
    ("APLAPOLLO","APLAPOLLO.NS","APL Apollo Tubes",0.22,"Metals",["mid","n200"]),
]

# NSE indices to fetch — covers all 139 stocks via parallel calls
NSE_IDX_LIST = [
    "NIFTY 50",
    "NIFTY NEXT 50",
    "NIFTY BANK",
    "NIFTY IT",
    "NIFTY PHARMA",
    "NIFTY AUTO",
    "NIFTY FMCG",
    "NIFTY METAL",
    "NIFTY MIDCAP 50",
    "NIFTY FINANCIAL SERVICES",
    "NIFTY REALTY",
    "NIFTY INFRASTRUCTURE",
    "NIFTY PSE",
    "NIFTY ENERGY",
    "NIFTY INDIA DEFENCE",
    "NIFTY HEALTHCARE INDEX",
    "NIFTY CONSUMER DURABLES",
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

_cache = {"stocks": [], "ts": 0}
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


def _fetch_one(session, idx_name):
    try:
        enc = urllib.parse.quote(idx_name)
        r = session.get(
            f"https://www.nseindia.com/api/equity-stockIndices?index={enc}",
            timeout=8,
        )
        if r.status_code != 200:
            return {}
        result = {}
        for item in r.json().get("data", []):
            sym = item.get("symbol", "")
            price = item.get("lastPrice") or 0
            pchg = item.get("pChange") or 0
            high52 = item.get("yearHigh") or 0
            low52 = item.get("yearLow") or 0
            if sym and float(price) > 0:
                result[sym] = {
                    "price": round(float(price), 2),
                    "chg": round(float(pchg), 2),
                    "high52": round(float(high52), 2),
                    "low52": round(float(low52), 2),
                }
        return result
    except Exception:
        return {}


def _fetch_prices():
    session = _get_sess()
    if not session:
        return {}
    price_map = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(_fetch_one, session, idx): idx for idx in NSE_IDX_LIST}
        for future in as_completed(futures, timeout=12):
            try:
                for sym, data in future.result().items():
                    if sym not in price_map:
                        price_map[sym] = data
            except Exception:
                pass
    return price_map


def _build():
    price_map = _fetch_prices()
    result = []
    for sym, yfsym, name, mcap, sector, idx in STOCKS:
        nse_sym = yfsym.replace(".NS", "")
        p = price_map.get(nse_sym, {})
        result.append({
            "sym": sym,
            "name": name,
            "sector": sector,
            "mcap": mcap,
            "idx": idx,
            "price": p.get("price", 0),
            "chg": p.get("chg", 0),
            "high52": p.get("high52", 0),
            "low52": p.get("low52", 0),
            "live": bool(p),
        })
    return result


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if time.time() - _cache["ts"] > CACHE_TTL or not _cache["stocks"]:
            try:
                _cache["stocks"] = _build()
                _cache["ts"] = time.time()
            except Exception:
                pass

        body = json.dumps({"stocks": _cache["stocks"], "last_refresh": _cache["ts"]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass
