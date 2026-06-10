from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yfinance as yf
import threading
import sqlite3
import time
import logging
import os
import requests
import traceback
import io
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "stockers.db")

app = FastAPI(title="Stockers")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

# ── STOCK & INDEX METADATA ────────────────────────────────────────────────────

STOCK_META = [
    # Banking
    {"sym":"HDFCBANK",    "yf":"HDFCBANK.NS",    "name":"HDFC Bank",                 "mcap":12.4, "sector":"Banking",    "idx":["n50","bnk","n100","n200"]},
    {"sym":"ICICIBANK",   "yf":"ICICIBANK.NS",    "name":"ICICI Bank",                "mcap":7.7,  "sector":"Banking",    "idx":["n50","bnk","n100","n200"]},
    {"sym":"KOTAKBANK",   "yf":"KOTAKBANK.NS",    "name":"Kotak Mahindra Bank",       "mcap":3.7,  "sector":"Banking",    "idx":["n50","bnk","n100","n200"]},
    {"sym":"SBIN",        "yf":"SBIN.NS",         "name":"State Bank of India",       "mcap":3.7,  "sector":"Banking",    "idx":["n50","bnk","n100","n200"]},
    {"sym":"AXISBANK",    "yf":"AXISBANK.NS",     "name":"Axis Bank",                 "mcap":3.5,  "sector":"Banking",    "idx":["n50","bnk","n100","n200"]},
    {"sym":"INDUSINDBK",  "yf":"INDUSINDBK.NS",   "name":"IndusInd Bank",             "mcap":0.96, "sector":"Banking",    "idx":["n50","bnk","n100","n200"]},
    {"sym":"BANDHANBNK",  "yf":"BANDHANBNK.NS",   "name":"Bandhan Bank",              "mcap":0.30, "sector":"Banking",    "idx":["bnk","nxt50","n100","n200"]},
    {"sym":"FEDERALBNK",  "yf":"FEDERALBNK.NS",   "name":"Federal Bank",              "mcap":0.42, "sector":"Banking",    "idx":["bnk","nxt50","n100","n200"]},
    {"sym":"IDFCFIRSTB",  "yf":"IDFCFIRSTB.NS",   "name":"IDFC First Bank",           "mcap":0.55, "sector":"Banking",    "idx":["bnk","nxt50","n100","n200"]},
    {"sym":"AUBANK",      "yf":"AUBANK.NS",        "name":"AU Small Finance Bank",     "mcap":0.50, "sector":"Banking",    "idx":["bnk","nxt50","n100","n200"]},
    {"sym":"PNB",         "yf":"PNB.NS",           "name":"Punjab National Bank",      "mcap":1.2,  "sector":"Banking",    "idx":["bnk","nxt50","n100","n200"]},
    {"sym":"CANARABANK",  "yf":"CANARABANK.NS",    "name":"Canara Bank",               "mcap":0.89, "sector":"Banking",    "idx":["bnk","nxt50","n100","n200"]},
    {"sym":"BANKBARODA",  "yf":"BANKBARODA.NS",    "name":"Bank of Baroda",            "mcap":1.1,  "sector":"Banking",    "idx":["bnk","nxt50","n100","n200"]},
    {"sym":"RBLBANK",     "yf":"RBLBANK.NS",       "name":"RBL Bank",                  "mcap":0.18, "sector":"Banking",    "idx":["bnk","mid","n200"]},
    {"sym":"YESBANK",     "yf":"YESBANK.NS",       "name":"Yes Bank",                  "mcap":0.62, "sector":"Banking",    "idx":["bnk","mid","n200"]},
    # IT
    {"sym":"TCS",         "yf":"TCS.NS",           "name":"Tata Consultancy Services", "mcap":12.9, "sector":"IT",         "idx":["n50","nit","n100","n200"]},
    {"sym":"INFY",        "yf":"INFY.NS",          "name":"Infosys",                   "mcap":6.6,  "sector":"IT",         "idx":["n50","nit","n100","n200"]},
    {"sym":"HCLTECH",     "yf":"HCLTECH.NS",       "name":"HCL Technologies",          "mcap":3.9,  "sector":"IT",         "idx":["n50","nit","n100","n200"]},
    {"sym":"WIPRO",       "yf":"WIPRO.NS",         "name":"Wipro",                     "mcap":2.4,  "sector":"IT",         "idx":["n50","nit","n100","n200"]},
    {"sym":"LTIM",        "yf":"LTIM.NS",          "name":"LTIMindtree",               "mcap":1.7,  "sector":"IT",         "idx":["n50","nit","n100","n200"]},
    {"sym":"TECHM",       "yf":"TECHM.NS",         "name":"Tech Mahindra",             "mcap":1.2,  "sector":"IT",         "idx":["n50","nit","n100","n200"]},
    {"sym":"MPHASIS",     "yf":"MPHASIS.NS",       "name":"Mphasis",                   "mcap":0.46, "sector":"IT",         "idx":["nxt50","nit","n100","n200"]},
    {"sym":"PERSISTENT",  "yf":"PERSISTENT.NS",    "name":"Persistent Systems",        "mcap":0.70, "sector":"IT",         "idx":["nxt50","nit","n100","n200"]},
    {"sym":"COFORGE",     "yf":"COFORGE.NS",       "name":"Coforge",                   "mcap":0.35, "sector":"IT",         "idx":["mid","nit","n200"]},
    {"sym":"KPIT",        "yf":"KPIT.NS",          "name":"KPIT Technologies",         "mcap":0.34, "sector":"IT",         "idx":["mid","nit","n200"]},
    {"sym":"HAPPYMNDS",   "yf":"HAPPYMNDS.NS",     "name":"Happiest Minds Tech",       "mcap":0.11, "sector":"IT",         "idx":["sml","nit"]},
    {"sym":"MASTEK",      "yf":"MASTEK.NS",        "name":"Mastek",                    "mcap":0.09, "sector":"IT",         "idx":["sml","nit"]},
    {"sym":"BSOFT",       "yf":"BSOFT.NS",         "name":"Birlasoft",                 "mcap":0.16, "sector":"IT",         "idx":["mid","nit","n200"]},
    {"sym":"ZENSARTECH",  "yf":"ZENSARTECH.NS",    "name":"Zensar Technologies",       "mcap":0.08, "sector":"IT",         "idx":["sml","nit"]},
    {"sym":"NAUKRI",      "yf":"NAUKRI.NS",        "name":"Info Edge (Naukri)",         "mcap":0.87, "sector":"IT",         "idx":["nxt50","nit","n100","n200"]},
    # Energy
    {"sym":"RELIANCE",    "yf":"RELIANCE.NS",      "name":"Reliance Industries",       "mcap":19.2, "sector":"Energy",     "idx":["n50","n100","n200"]},
    {"sym":"ONGC",        "yf":"ONGC.NS",          "name":"ONGC",                      "mcap":3.4,  "sector":"Energy",     "idx":["n50","n100","n200"]},
    {"sym":"BPCL",        "yf":"BPCL.NS",          "name":"Bharat Petroleum",          "mcap":1.5,  "sector":"Energy",     "idx":["n50","n100","n200"]},
    {"sym":"IOC",         "yf":"IOC.NS",           "name":"Indian Oil Corp",            "mcap":2.4,  "sector":"Energy",     "idx":["nxt50","n100","n200"]},
    {"sym":"GAIL",        "yf":"GAIL.NS",          "name":"GAIL India",                "mcap":1.5,  "sector":"Energy",     "idx":["nxt50","n100","n200"]},
    {"sym":"PETRONET",    "yf":"PETRONET.NS",      "name":"Petronet LNG",              "mcap":0.40, "sector":"Energy",     "idx":["nxt50","n100","n200"]},
    {"sym":"OIL",         "yf":"OIL.NS",           "name":"Oil India",                 "mcap":0.50, "sector":"Energy",     "idx":["mid","n200"]},
    {"sym":"MRPL",        "yf":"MRPL.NS",          "name":"MRPL",                      "mcap":0.31, "sector":"Energy",     "idx":["mid","n200"]},
    # FMCG
    {"sym":"HINDUNILVR",  "yf":"HINDUNILVR.NS",    "name":"Hindustan Unilever",        "mcap":5.8,  "sector":"FMCG",       "idx":["n50","n100","n200"]},
    {"sym":"ITC",         "yf":"ITC.NS",           "name":"ITC Ltd",                   "mcap":5.7,  "sector":"FMCG",       "idx":["n50","n100","n200"]},
    {"sym":"NESTLEIND",   "yf":"NESTLEIND.NS",     "name":"Nestle India",              "mcap":2.4,  "sector":"FMCG",       "idx":["n50","n100","n200"]},
    {"sym":"BRITANNIA",   "yf":"BRITANNIA.NS",     "name":"Britannia Industries",      "mcap":1.1,  "sector":"FMCG",       "idx":["n50","n100","n200"]},
    {"sym":"TATACONSUM",  "yf":"TATACONSUM.NS",    "name":"Tata Consumer Products",    "mcap":0.9,  "sector":"FMCG",       "idx":["n50","n100","n200"]},
    {"sym":"DABUR",       "yf":"DABUR.NS",         "name":"Dabur India",               "mcap":1.0,  "sector":"FMCG",       "idx":["nxt50","n100","n200"]},
    {"sym":"MARICO",      "yf":"MARICO.NS",        "name":"Marico",                    "mcap":0.73, "sector":"FMCG",       "idx":["nxt50","n100","n200"]},
    {"sym":"COLPAL",      "yf":"COLPAL.NS",        "name":"Colgate-Palmolive India",   "mcap":0.64, "sector":"FMCG",       "idx":["nxt50","n100","n200"]},
    {"sym":"GODREJCP",    "yf":"GODREJCP.NS",      "name":"Godrej Consumer Products",  "mcap":1.3,  "sector":"FMCG",       "idx":["nxt50","n100","n200"]},
    {"sym":"EMAMILTD",    "yf":"EMAMILTD.NS",      "name":"Emami",                     "mcap":0.24, "sector":"FMCG",       "idx":["mid","n200"]},
    {"sym":"VBL",         "yf":"VBL.NS",           "name":"Varun Beverages",           "mcap":0.73, "sector":"FMCG",       "idx":["nxt50","n100","n200"]},
    # Auto
    {"sym":"MARUTI",      "yf":"MARUTI.NS",        "name":"Maruti Suzuki",             "mcap":3.8,  "sector":"Auto",       "idx":["n50","n100","n200"]},
    {"sym":"TATAMOTORS",  "yf":"TATAMOTORS.NS",    "name":"Tata Motors",               "mcap":3.6,  "sector":"Auto",       "idx":["n50","n100","n200"]},
    {"sym":"M&M",         "yf":"M&M.NS",           "name":"Mahindra & Mahindra",       "mcap":2.9,  "sector":"Auto",       "idx":["n50","n100","n200"]},
    {"sym":"BAJAJ-AUTO",  "yf":"BAJAJ-AUTO.NS",    "name":"Bajaj Auto",                "mcap":2.6,  "sector":"Auto",       "idx":["n50","n100","n200"]},
    {"sym":"EICHERMOT",   "yf":"EICHERMOT.NS",     "name":"Eicher Motors",             "mcap":1.2,  "sector":"Auto",       "idx":["n50","n100","n200"]},
    {"sym":"HEROMOTOCO",  "yf":"HEROMOTOCO.NS",    "name":"Hero MotoCorp",             "mcap":0.9,  "sector":"Auto",       "idx":["n50","n100","n200"]},
    {"sym":"TVSMOTOR",    "yf":"TVSMOTOR.NS",      "name":"TVS Motor Company",         "mcap":1.1,  "sector":"Auto",       "idx":["nxt50","n100","n200"]},
    {"sym":"ASHOKLEY",    "yf":"ASHOKLEY.NS",      "name":"Ashok Leyland",             "mcap":0.69, "sector":"Auto",       "idx":["nxt50","n100","n200"]},
    {"sym":"MRF",         "yf":"MRF.NS",           "name":"MRF",                       "mcap":0.62, "sector":"Auto",       "idx":["nxt50","n100","n200"]},
    {"sym":"BOSCHLTD",    "yf":"BOSCHLTD.NS",      "name":"Bosch India",               "mcap":0.40, "sector":"Auto",       "idx":["mid","n200"]},
    {"sym":"EXIDEIND",    "yf":"EXIDEIND.NS",      "name":"Exide Industries",          "mcap":0.39, "sector":"Auto",       "idx":["mid","n200"]},
    {"sym":"BALKRISIND",  "yf":"BALKRISIND.NS",    "name":"Balkrishna Industries",     "mcap":0.48, "sector":"Auto",       "idx":["nxt50","n100","n200"]},
    # Finance
    {"sym":"BAJFINANCE",  "yf":"BAJFINANCE.NS",    "name":"Bajaj Finance",             "mcap":4.4,  "sector":"Finance",    "idx":["n50","n100","n200"]},
    {"sym":"BAJAJFINSV",  "yf":"BAJAJFINSV.NS",    "name":"Bajaj Finserv",             "mcap":2.7,  "sector":"Finance",    "idx":["n50","n100","n200"]},
    {"sym":"HDFCLIFE",    "yf":"HDFCLIFE.NS",      "name":"HDFC Life Insurance",       "mcap":1.4,  "sector":"Finance",    "idx":["n50","n100","n200"]},
    {"sym":"SBILIFE",     "yf":"SBILIFE.NS",       "name":"SBI Life Insurance",        "mcap":1.6,  "sector":"Finance",    "idx":["n50","n100","n200"]},
    {"sym":"SHRIRAMFIN",  "yf":"SHRIRAMFIN.NS",    "name":"Shriram Finance",           "mcap":0.97, "sector":"Finance",    "idx":["n50","n100","n200"]},
    {"sym":"CHOLAFIN",    "yf":"CHOLAFIN.NS",      "name":"Cholamandalam Finance",     "mcap":0.81, "sector":"Finance",    "idx":["nxt50","n100","n200"]},
    {"sym":"MUTHOOTFIN",  "yf":"MUTHOOTFIN.NS",    "name":"Muthoot Finance",           "mcap":0.79, "sector":"Finance",    "idx":["nxt50","n100","n200"]},
    {"sym":"PFC",         "yf":"PFC.NS",           "name":"Power Finance Corp",        "mcap":1.5,  "sector":"Finance",    "idx":["nxt50","n100","n200"]},
    {"sym":"RECLTD",      "yf":"RECLTD.NS",        "name":"REC Limited",               "mcap":1.5,  "sector":"Finance",    "idx":["nxt50","n100","n200"]},
    {"sym":"PAYTM",       "yf":"PAYTM.NS",         "name":"One97 Comm (Paytm)",        "mcap":0.29, "sector":"Finance",    "idx":["mid","n200"]},
    {"sym":"LICHSGFIN",   "yf":"LICHSGFIN.NS",     "name":"LIC Housing Finance",       "mcap":0.34, "sector":"Finance",    "idx":["mid","n200"]},
    # Pharma
    {"sym":"SUNPHARMA",   "yf":"SUNPHARMA.NS",     "name":"Sun Pharmaceutical",        "mcap":3.8,  "sector":"Pharma",     "idx":["n50","n100","n200"]},
    {"sym":"DRREDDY",     "yf":"DRREDDY.NS",       "name":"Dr. Reddy's Labs",          "mcap":2.4,  "sector":"Pharma",     "idx":["n50","n100","n200"]},
    {"sym":"CIPLA",       "yf":"CIPLA.NS",         "name":"Cipla",                     "mcap":1.3,  "sector":"Pharma",     "idx":["n50","n100","n200"]},
    {"sym":"DIVISLAB",    "yf":"DIVISLAB.NS",      "name":"Divi's Laboratories",       "mcap":1.2,  "sector":"Pharma",     "idx":["n50","n100","n200"]},
    {"sym":"TORNTPHARM",  "yf":"TORNTPHARM.NS",    "name":"Torrent Pharma",            "mcap":0.79, "sector":"Pharma",     "idx":["nxt50","n100","n200"]},
    {"sym":"ALKEM",       "yf":"ALKEM.NS",         "name":"Alkem Laboratories",        "mcap":0.55, "sector":"Pharma",     "idx":["nxt50","n100","n200"]},
    {"sym":"LUPIN",       "yf":"LUPIN.NS",         "name":"Lupin",                     "mcap":0.90, "sector":"Pharma",     "idx":["nxt50","n100","n200"]},
    {"sym":"ABBOTINDIA",  "yf":"ABBOTINDIA.NS",    "name":"Abbott India",              "mcap":0.50, "sector":"Pharma",     "idx":["mid","n200"]},
    {"sym":"BIOCON",      "yf":"BIOCON.NS",        "name":"Biocon",                    "mcap":0.42, "sector":"Pharma",     "idx":["nxt50","n100","n200"]},
    {"sym":"GLAXO",       "yf":"GLAXO.NS",         "name":"GSK Pharma India",          "mcap":0.34, "sector":"Pharma",     "idx":["mid","n200"]},
    {"sym":"PFIZER",      "yf":"PFIZER.NS",        "name":"Pfizer India",              "mcap":0.21, "sector":"Pharma",     "idx":["mid","n200"]},
    # Infra
    {"sym":"LT",          "yf":"LT.NS",            "name":"Larsen & Toubro",           "mcap":4.9,  "sector":"Infra",      "idx":["n50","n100","n200"]},
    {"sym":"ADANIENT",    "yf":"ADANIENT.NS",      "name":"Adani Enterprises",         "mcap":2.8,  "sector":"Infra",      "idx":["n50","n100","n200"]},
    {"sym":"ADANIPORTS",  "yf":"ADANIPORTS.NS",    "name":"Adani Ports & SEZ",         "mcap":2.7,  "sector":"Infra",      "idx":["n50","n100","n200"]},
    {"sym":"GMRAIRPORT",  "yf":"GMRINFRA.NS",      "name":"GMR Airports Infra",        "mcap":0.53, "sector":"Infra",      "idx":["mid","n200"]},
    {"sym":"IRCON",       "yf":"IRCON.NS",         "name":"IRCON International",       "mcap":0.22, "sector":"Infra",      "idx":["mid","n200"]},
    {"sym":"RVNL",        "yf":"RVNL.NS",          "name":"Rail Vikas Nigam",          "mcap":0.95, "sector":"Infra",      "idx":["nxt50","n100","n200"]},
    {"sym":"NBCC",        "yf":"NBCC.NS",          "name":"NBCC India",                "mcap":0.16, "sector":"Infra",      "idx":["sml"]},
    {"sym":"IRB",         "yf":"IRB.NS",           "name":"IRB Infrastructure",        "mcap":0.20, "sector":"Infra",      "idx":["mid","n200"]},
    # Power
    {"sym":"NTPC",        "yf":"NTPC.NS",          "name":"NTPC",                      "mcap":3.4,  "sector":"Power",      "idx":["n50","n100","n200"]},
    {"sym":"POWERGRID",   "yf":"POWERGRID.NS",     "name":"Power Grid Corp",           "mcap":2.2,  "sector":"Power",      "idx":["n50","n100","n200"]},
    {"sym":"COALINDIA",   "yf":"COALINDIA.NS",     "name":"Coal India",                "mcap":2.8,  "sector":"Power",      "idx":["n50","n100","n200"]},
    {"sym":"ADANIPOWER",  "yf":"ADANIPOWER.NS",    "name":"Adani Power",               "mcap":2.2,  "sector":"Power",      "idx":["nxt50","n100","n200"]},
    {"sym":"TATAPOWER",   "yf":"TATAPOWER.NS",     "name":"Tata Power Company",        "mcap":1.5,  "sector":"Power",      "idx":["nxt50","n100","n200"]},
    {"sym":"TORNTPOWER",  "yf":"TORNTPOWER.NS",    "name":"Torrent Power",             "mcap":0.59, "sector":"Power",      "idx":["mid","n200"]},
    {"sym":"CESC",        "yf":"CESC.NS",          "name":"CESC",                      "mcap":0.25, "sector":"Power",      "idx":["mid","n200"]},
    {"sym":"NHPC",        "yf":"NHPC.NS",          "name":"NHPC",                      "mcap":0.90, "sector":"Power",      "idx":["nxt50","n100","n200"]},
    # Defence
    {"sym":"BEL",         "yf":"BEL.NS",           "name":"Bharat Electronics",        "mcap":1.8,  "sector":"Defence",    "idx":["n50","n100","n200"]},
    {"sym":"HAL",         "yf":"HAL.NS",           "name":"Hindustan Aeronautics",     "mcap":1.5,  "sector":"Defence",    "idx":["nxt50","n100","n200"]},
    {"sym":"BEML",        "yf":"BEML.NS",          "name":"BEML",                      "mcap":0.14, "sector":"Defence",    "idx":["mid","n200"]},
    {"sym":"BHEL",        "yf":"BHEL.NS",          "name":"Bharat Heavy Electricals",  "mcap":0.94, "sector":"Defence",    "idx":["nxt50","n100","n200"]},
    {"sym":"COCHINSHIP",  "yf":"COCHINSHIP.NS",    "name":"Cochin Shipyard",           "mcap":0.22, "sector":"Defence",    "idx":["mid","n200"]},
    {"sym":"MAZDOCK",     "yf":"MAZDOCK.NS",       "name":"Mazagon Dock",              "mcap":0.46, "sector":"Defence",    "idx":["mid","n200"]},
    # Consumer
    {"sym":"TITAN",       "yf":"TITAN.NS",         "name":"Titan Company",             "mcap":3.1,  "sector":"Consumer",   "idx":["n50","n100","n200"]},
    {"sym":"ASIANPAINT",  "yf":"ASIANPAINT.NS",    "name":"Asian Paints",              "mcap":2.6,  "sector":"Consumer",   "idx":["n50","n100","n200"]},
    {"sym":"ZOMATO",      "yf":"ZOMATO.NS",        "name":"Zomato",                    "mcap":2.1,  "sector":"Consumer",   "idx":["n50","n100","n200"]},
    {"sym":"NYKAA",       "yf":"NYKAA.NS",         "name":"Nykaa (FSN E-Comm)",        "mcap":0.51, "sector":"Consumer",   "idx":["mid","n200"]},
    {"sym":"HAVELLS",     "yf":"HAVELLS.NS",        "name":"Havells India",             "mcap":1.1,  "sector":"Consumer",   "idx":["nxt50","n100","n200"]},
    {"sym":"VOLTAS",      "yf":"VOLTAS.NS",        "name":"Voltas",                    "mcap":0.48, "sector":"Consumer",   "idx":["nxt50","n100","n200"]},
    {"sym":"CROMPTON",    "yf":"CROMPTON.NS",      "name":"Crompton Greaves Consumer", "mcap":0.22, "sector":"Consumer",   "idx":["mid","n200"]},
    {"sym":"VGUARD",      "yf":"VGUARD.NS",        "name":"V-Guard Industries",        "mcap":0.15, "sector":"Consumer",   "idx":["sml"]},
    # Healthcare
    {"sym":"APOLLOHOSP",  "yf":"APOLLOHOSP.NS",    "name":"Apollo Hospitals",          "mcap":0.98, "sector":"Healthcare", "idx":["n50","n100","n200"]},
    {"sym":"MAXHEALTH",   "yf":"MAXHEALTH.NS",     "name":"Max Healthcare",            "mcap":0.97, "sector":"Healthcare", "idx":["nxt50","n100","n200"]},
    {"sym":"FORTIS",      "yf":"FORTIS.NS",        "name":"Fortis Healthcare",         "mcap":0.43, "sector":"Healthcare", "idx":["nxt50","n100","n200"]},
    {"sym":"ASTER",       "yf":"ASTERDM.NS",       "name":"Aster DM Healthcare",       "mcap":0.19, "sector":"Healthcare", "idx":["mid","n200"]},
    {"sym":"NARAYNAHLT",  "yf":"NH.NS",            "name":"Narayana Hrudayalaya",      "mcap":0.25, "sector":"Healthcare", "idx":["mid","n200"]},
    # Cement
    {"sym":"ULTRACEMCO",  "yf":"ULTRACEMCO.NS",    "name":"UltraTech Cement",          "mcap":3.0,  "sector":"Cement",     "idx":["n50","n100","n200"]},
    {"sym":"GRASIM",      "yf":"GRASIM.NS",        "name":"Grasim Industries",         "mcap":1.5,  "sector":"Cement",     "idx":["n50","n100","n200"]},
    {"sym":"AMBUJACEMENT","yf":"AMBUJACEM.NS",      "name":"Ambuja Cements",            "mcap":1.1,  "sector":"Cement",     "idx":["nxt50","n100","n200"]},
    {"sym":"ACC",         "yf":"ACC.NS",           "name":"ACC",                       "mcap":0.37, "sector":"Cement",     "idx":["nxt50","n100","n200"]},
    {"sym":"SHREECEM",    "yf":"SHREECEM.NS",      "name":"Shree Cement",              "mcap":0.85, "sector":"Cement",     "idx":["nxt50","n100","n200"]},
    {"sym":"RAMCOCEM",    "yf":"RAMCOCEM.NS",      "name":"Ramco Cements",             "mcap":0.19, "sector":"Cement",     "idx":["mid","n200"]},
    {"sym":"DALMIACEM",   "yf":"DALMIACEM.NS",     "name":"Dalmia Bharat",             "mcap":0.38, "sector":"Cement",     "idx":["nxt50","n100","n200"]},
    # Metals
    {"sym":"JSWSTEEL",    "yf":"JSWSTEEL.NS",      "name":"JSW Steel",                 "mcap":2.1,  "sector":"Metals",     "idx":["n50","n100","n200"]},
    {"sym":"TATASTEEL",   "yf":"TATASTEEL.NS",     "name":"Tata Steel",                "mcap":2.1,  "sector":"Metals",     "idx":["n50","n100","n200"]},
    {"sym":"HINDALCO",    "yf":"HINDALCO.NS",      "name":"Hindalco Industries",       "mcap":1.5,  "sector":"Metals",     "idx":["n50","n100","n200"]},
    {"sym":"SAIL",        "yf":"SAIL.NS",          "name":"SAIL",                      "mcap":0.56, "sector":"Metals",     "idx":["nxt50","n100","n200"]},
    {"sym":"VEDL",        "yf":"VEDL.NS",          "name":"Vedanta",                   "mcap":1.7,  "sector":"Metals",     "idx":["nxt50","n100","n200"]},
    {"sym":"NMDC",        "yf":"NMDC.NS",          "name":"NMDC",                      "mcap":0.69, "sector":"Metals",     "idx":["nxt50","n100","n200"]},
    {"sym":"NATIONALUM",  "yf":"NATIONALUM.NS",    "name":"National Aluminium Co",     "mcap":0.33, "sector":"Metals",     "idx":["mid","n200"]},
    {"sym":"APLAPOLLO",   "yf":"APLAPOLLO.NS",     "name":"APL Apollo Tubes",          "mcap":0.22, "sector":"Metals",     "idx":["mid","n200"]},
]

INDEX_META = [
    {"id":"n50",   "yf":"^NSEI",       "label":"NIFTY 50",       "tags":["n50"]},
    {"id":"bnk",   "yf":"^NSEBANK",    "label":"BANK NIFTY",     "tags":["bnk"]},
    {"id":"nxt50", "yf":"^NSMIDCP50",  "label":"NIFTY NEXT 50",  "tags":["nxt50"]},
    {"id":"n100",  "yf":"^CNX100",     "label":"NIFTY 100",      "tags":["n50","nxt50"]},
    {"id":"n200",  "yf":"^CNX200",     "label":"NIFTY 200",      "tags":["n50","nxt50","mid"]},
    {"id":"mid",   "yf":"^NSEMDCP50",  "label":"NIFTY MIDCAP",   "tags":["mid"]},
    {"id":"sml",   "yf":"^CNXSC",      "label":"NIFTY SMALLCAP", "tags":["sml"]},
    {"id":"nit",   "yf":"^CNXIT",      "label":"NIFTY IT",       "tags":["nit"]},
]

# ── SQLITE ────────────────────────────────────────────────────────────────────

def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS prices (
                sym        TEXT PRIMARY KEY,
                price      REAL DEFAULT 0,
                chg        REAL DEFAULT 0,
                prev_close REAL DEFAULT 0,
                high52     REAL DEFAULT 0,
                low52      REAL DEFAULT 0,
                ts         REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS idx_prices (
                id    TEXT PRIMARY KEY,
                val   REAL DEFAULT 0,
                chg   REAL DEFAULT 0,
                ts    REAL DEFAULT 0
            );
        """)

def db_save_stocks(stocks: dict, ts: float):
    with _db() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO prices (sym,price,chg,prev_close,high52,low52,ts) VALUES (?,?,?,?,?,?,?)",
            [(sym, d["price"], d["chg"], d["prev_close"], d["high52"], d["low52"], ts)
             for sym, d in stocks.items()]
        )

def db_save_indices(indices: list, ts: float):
    with _db() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO idx_prices (id,val,chg,ts) VALUES (?,?,?,?)",
            [(i["id"], i["val"], i["chg"], ts) for i in indices if i.get("val", 0) > 0]
        )

def db_load_stocks() -> dict:
    with _db() as conn:
        rows = conn.execute("SELECT sym,price,chg,prev_close,high52,low52 FROM prices").fetchall()
    return {r["sym"]: dict(r) for r in rows if r["price"] > 0}

def db_load_indices() -> list:
    with _db() as conn:
        rows = conn.execute("SELECT id,val,chg FROM idx_prices").fetchall()
    by_id = {r["id"]: dict(r) for r in rows}
    return [{**m, **by_id.get(m["id"], {"val": 0, "chg": 0})} for m in INDEX_META]

# ── IN-MEMORY CACHE ───────────────────────────────────────────────────────────

_stock_cache: dict = {}
_index_cache: list = []
_last_refresh: float = 0
_fetch_count: int = 0
_cache_lock = threading.Lock()
_is_fetching = False
FETCH_INTERVAL = 15  # seconds between refreshes

# ── YFINANCE FETCH ────────────────────────────────────────────────────────────

def _download(syms: list, period: str, interval: str) -> object:
    return yf.download(
        tickers=syms,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=True,
        progress=False,
        threads=True,
    )

def _parse_stocks(data, syms: list, prev_closes: dict) -> dict:
    """Extract price, chg, high52, low52 from a yfinance DataFrame."""
    result = {}
    for stock in STOCK_META:
        try:
            df = data if len(syms) == 1 else data.get(stock["yf"])
            if df is None or df.empty:
                continue
            close = df["Close"].dropna()
            if len(close) < 1:
                continue
            cur = float(close.iloc[-1])
            if cur <= 0:
                continue
            # Use stored prev_close for accurate daily % change
            prev = prev_closes.get(stock["sym"], 0)
            if prev <= 0:
                # Fallback: use second-to-last bar if available
                prev = float(close.iloc[-2]) if len(close) >= 2 else cur
            result[stock["sym"]] = {
                "price":      round(cur, 2),
                "chg":        round((cur - prev) / prev * 100, 2) if prev > 0 else 0.0,
                "prev_close": round(prev, 2),
                "high52":     round(float(df["High"].dropna().max()), 2),
                "low52":      round(float(df["Low"].dropna().min()), 2),
            }
        except Exception as e:
            logger.debug(f"Skip {stock['sym']}: {e}")
    return result

def _parse_indices(data, syms: list) -> list:
    result = []
    for idx in INDEX_META:
        try:
            df = data if len(syms) == 1 else data.get(idx["yf"])
            if df is None or df.empty:
                result.append({**idx, "val": 0, "chg": 0})
                continue
            close = df["Close"].dropna()
            if len(close) >= 2:
                val  = float(close.iloc[-1])
                prev = float(close.iloc[-2])
                result.append({**idx, "val": round(val, 2), "chg": round((val - prev) / prev * 100, 2)})
            else:
                result.append({**idx, "val": 0, "chg": 0})
        except Exception as e:
            logger.debug(f"Skip index {idx['id']}: {e}")
            result.append({**idx, "val": 0, "chg": 0})
    return result

def _refresh_cache():
    global _stock_cache, _index_cache, _last_refresh, _fetch_count

    stock_syms = [s["yf"] for s in STOCK_META]
    idx_syms   = [i["yf"] for i in INDEX_META]

    # Read stored prev_close values from current cache
    with _cache_lock:
        prev_closes = {sym: d.get("prev_close", 0) for sym, d in _stock_cache.items()}

    t0 = time.time()

    # ── Intraday fetch (1-minute bars, 15-min delayed NSE data) ──────────────
    stocks, indices = {}, []
    try:
        data = _download(stock_syms, period="1d", interval="1m")
        if data is not None and not data.empty:
            stocks = _parse_stocks(data, stock_syms, prev_closes)
            logger.info(f"Intraday: got {len(stocks)} stocks in {time.time()-t0:.1f}s")
    except Exception as e:
        logger.warning(f"Intraday fetch failed: {e}")

    # ── Daily fallback (also used to set prev_close accurately) ──────────────
    # Always run daily fetch so we have correct prev_close from yesterday's close
    try:
        daily = _download(stock_syms, period="5d", interval="1d")
        if daily is not None and not daily.empty:
            daily_stocks = _parse_stocks(daily, stock_syms, {})  # {} → uses iloc[-2] as prev
            if not stocks:
                stocks = daily_stocks
                logger.info(f"Daily fallback: got {len(stocks)} stocks")
            else:
                # Merge: take prev_close from daily data for accuracy
                for sym, dd in daily_stocks.items():
                    if sym in stocks:
                        stocks[sym]["prev_close"] = dd["prev_close"]
                        stocks[sym]["high52"]     = dd["high52"]
                        stocks[sym]["low52"]      = dd["low52"]
                        # Recompute chg with accurate prev_close
                        p = dd["prev_close"]
                        if p > 0:
                            stocks[sym]["chg"] = round((stocks[sym]["price"] - p) / p * 100, 2)
    except Exception as e:
        logger.warning(f"Daily fetch failed: {e}")

    # ── Indices ───────────────────────────────────────────────────────────────
    try:
        idx_data = _download(idx_syms, period="5d", interval="1d")
        if idx_data is not None and not idx_data.empty:
            indices = _parse_indices(idx_data, idx_syms)
    except Exception as e:
        logger.warning(f"Index fetch failed: {e}")

    ts = time.time()

    # ── Persist to SQLite ─────────────────────────────────────────────────────
    if stocks:
        try:
            db_save_stocks(stocks, ts)
        except Exception as e:
            logger.error(f"DB write error: {e}")
    if indices:
        try:
            db_save_indices(indices, ts)
        except Exception as e:
            logger.error(f"DB index write error: {e}")

    # ── Update in-memory cache ────────────────────────────────────────────────
    with _cache_lock:
        if stocks:
            _stock_cache = stocks
        if indices:
            _index_cache = indices
        _last_refresh = ts
        _fetch_count += 1

    logger.info(f"Cache #{_fetch_count}: {len(stocks)} stocks, {len(indices)} indices — {ts - t0:.1f}s total")


def _background_loop():
    global _is_fetching
    while True:
        if not _is_fetching:
            _is_fetching = True
            try:
                _refresh_cache()
            except Exception as e:
                logger.error(f"Refresh error: {e}")
            finally:
                _is_fetching = False
        time.sleep(FETCH_INTERVAL)


# ── STARTUP ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    global _stock_cache, _index_cache, _last_refresh
    init_db()

    # Restore last known prices from SQLite immediately (zero wait for first user)
    saved_stocks  = db_load_stocks()
    saved_indices = db_load_indices()
    with _cache_lock:
        if saved_stocks:
            _stock_cache = saved_stocks
            logger.info(f"Restored {len(saved_stocks)} stocks from DB")
        if any(i.get("val", 0) > 0 for i in saved_indices):
            _index_cache = saved_indices
            logger.info(f"Restored {len(saved_indices)} indices from DB")

    # Start background refresh thread
    t = threading.Thread(target=_background_loop, daemon=True)
    t.start()
    logger.info(f"Background thread started — refresh every {FETCH_INTERVAL}s")


# ── API ENDPOINTS ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    with _cache_lock:
        age = round(time.time() - _last_refresh, 1) if _last_refresh else None
        live_count = sum(1 for d in _stock_cache.values() if d.get("price", 0) > 0)
        return {
            "status":         "ok",
            "fetching":       _is_fetching,
            "fetch_count":    _fetch_count,
            "cached_stocks":  live_count,
            "cached_indices": len(_index_cache),
            "cache_age_sec":  age,
            "last_refresh":   _last_refresh,
            "fetch_interval": FETCH_INTERVAL,
        }


@app.get("/api/stocks")
def get_stocks():
    with _cache_lock:
        ts = _last_refresh
        result = []
        for stock in STOCK_META:
            d = _stock_cache.get(stock["sym"], {})
            result.append({
                "sym":    stock["sym"],
                "name":   stock["name"],
                "sector": stock["sector"],
                "mcap":   stock["mcap"],
                "idx":    stock["idx"],
                "price":  d.get("price", 0),
                "chg":    d.get("chg", 0),
                "high52": d.get("high52", 0),
                "low52":  d.get("low52", 0),
                "live":   d.get("price", 0) > 0,
            })
    return {"stocks": result, "last_refresh": ts}


@app.get("/api/indices")
def get_indices():
    with _cache_lock:
        ts = _last_refresh
        if _index_cache:
            return {"indices": _index_cache, "last_refresh": ts}
        return {"indices": [{**i, "val": 0, "chg": 0} for i in INDEX_META], "last_refresh": ts}


@app.get("/api/status")
def status():
    """Shows what's in SQLite right now."""
    with _db() as conn:
        stock_rows = conn.execute(
            "SELECT sym, price, chg, ts FROM prices WHERE price > 0 ORDER BY sym LIMIT 10"
        ).fetchall()
        idx_rows = conn.execute("SELECT * FROM idx_prices").fetchall()
    return {
        "db_path":      DB_PATH,
        "sample_stocks": [dict(r) for r in stock_rows],
        "indices":       [dict(r) for r in idx_rows],
    }


# ── DIAGNOSTICS ──────────────────────────────────────────────────────────────

@app.get("/api/diagnose")
def diagnose():
    results = {}

    # Test 1 & 2: raw HTTP to Yahoo Finance
    for label, url in [
        ("1_yahoo_finance_homepage", "https://finance.yahoo.com"),
        ("2_yahoo_query1",           "https://query1.finance.yahoo.com"),
    ]:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            results[label] = {
                "status_code": r.status_code,
                "headers":     dict(r.headers),
                "body_snippet": r.text[:500],
            }
        except Exception as e:
            results[label] = {"error": str(e), "traceback": traceback.format_exc()}

    # Test 3 & 4: yf.Ticker.history
    for label, sym in [
        ("3_yf_ticker_AAPL",        "AAPL"),
        ("4_yf_ticker_RELIANCE_NS", "RELIANCE.NS"),
    ]:
        try:
            old_stderr = sys.stderr
            sys.stderr = buf = io.StringIO()
            df = yf.Ticker(sym).history(period="1d")
            sys.stderr = old_stderr
            results[label] = {
                "rows":    len(df),
                "columns": list(df.columns),
                "sample":  df.tail(2).to_dict() if not df.empty else {},
                "stderr":  buf.getvalue()[:500],
            }
        except Exception as e:
            sys.stderr = old_stderr if 'old_stderr' in dir() else sys.stderr
            results[label] = {"error": str(e), "traceback": traceback.format_exc()}

    # Test 5 & 6: yf.download
    for label, sym in [
        ("5_yf_download_AAPL",        "AAPL"),
        ("6_yf_download_RELIANCE_NS", "RELIANCE.NS"),
    ]:
        try:
            old_stderr = sys.stderr
            sys.stderr = buf = io.StringIO()
            df = yf.download(sym, period="1d", progress=False)
            sys.stderr = old_stderr
            results[label] = {
                "rows":    len(df),
                "columns": list(df.columns),
                "sample":  df.tail(2).to_dict() if not df.empty else {},
                "stderr":  buf.getvalue()[:500],
            }
        except Exception as e:
            sys.stderr = old_stderr if 'old_stderr' in dir() else sys.stderr
            results[label] = {"error": str(e), "traceback": traceback.format_exc()}

    return results


# ── FRONTEND ──────────────────────────────────────────────────────────────────

@app.get("/")
def serve_root():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    return FileResponse(os.path.join(BASE_DIR, "index.html"))
