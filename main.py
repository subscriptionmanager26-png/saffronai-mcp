from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import csv
from io import StringIO
from typing import List, Dict

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def fetch_etf_data() -> List[Dict]:
    """Fetch ETF data from SaffronAI API"""
    url = "https://www.saffronai.in/api/etf-data"
    headers = {
        'accept': '*/*',
        'referer': 'https://www.saffronai.in/etf-tracker',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data)
    etfs = list(reader)
    
    for etf in etfs:
        try:
            ltp = float(etf.get('lastPrice', 0))
            inav = float(etf.get('inav', 0))
            if inav > 0:
                premium_discount = ((ltp - inav) / inav) * 100
                etf['premium_discount_pct'] = round(premium_discount, 2)
        except:
            etf['premium_discount_pct'] = None
    
    return etfs

@app.get("/")
async def root():
    return {"status": "SaffronAI MCP Server", "version": "1.0"}

@app.get("/api/etf/all")
async def get_all_etfs():
    return {"result": fetch_etf_data()}

@app.get("/api/etf/{symbol}")
async def get_etf(symbol: str):
    all_etfs = fetch_etf_data()
    for etf in all_etfs:
        if etf.get("symbol", "").upper() == symbol.upper():
            return {"result": etf}
    return {"error": "Not found"}

@app.get("/api/etf/search/{query}")
async def search_etfs(query: str):
    all_etfs = fetch_etf_data()
    results = [
        etf for etf in all_etfs 
        if query.lower() in etf.get("symbol", "").lower() 
        or query.lower() in etf.get("companyName", "").lower()
        or query.lower() in etf.get("assets", "").lower()
    ]
    return {"result": results}

@app.get("/api/etf/premium")
async def get_premium_etfs():
    all_etfs = fetch_etf_data()
    premium_etfs = [
        etf for etf in all_etfs 
        if etf.get('premium_discount_pct') and etf['premium_discount_pct'] > 0
    ]
    premium_etfs.sort(key=lambda x: x.get('premium_discount_pct', 0), reverse=True)
    return {"result": premium_etfs}

@app.get("/api/etf/discount")
async def get_discount_etfs():
    all_etfs = fetch_etf_data()
    discount_etfs = [
        etf for etf in all_etfs 
        if etf.get('premium_discount_pct') and etf['premium_discount_pct'] < 0
    ]
    discount_etfs.sort(key=lambda x: x.get('premium_discount_pct', 0))
    return {"result": discount_etfs}
```

**File 2: `requirements.txt`**
```
fastapi==0.104.1
uvicorn==0.24.0
requests==2.31.0
```

**File 3: `Procfile`** (for Railway)
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
