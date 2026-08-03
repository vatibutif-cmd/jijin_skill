import requests, json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
proxies = {'http': None, 'https': None}

print('=== 1. Testing Index Realtime Spot ===')
url_idx = 'http://push2.eastmoney.com/api/qt/clist/get'
params_idx = {
    'pn': 1, 'pz': 30, 'po': 1, 'np': 1,
    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
    'fltt': 2, 'invt': 2, 'fid': 'f3',
    'fs': 'm:1 t:1,m:0 t:5',
    'fields': 'f12,f14,f2,f3,f4,f6',
}
r = requests.get(url_idx, params=params_idx, headers=headers, proxies=proxies, timeout=5)
data = r.json().get('data', {}).get('diff', [])
print(f"Total indices found: {len(data)}")
for item in data[:5]:
    print(f"  [{item.get('f12')}] {item.get('f14')}: 现价={item.get('f2')}, 涨跌幅={item.get('f3')}%, 成交额={item.get('f6')}")

print('\n=== 2. Testing ETF Realtime Spot ===')
url_etf = 'http://push2.eastmoney.com/api/qt/clist/get'
params_etf = {
    'pn': 1, 'pz': 20, 'po': 1, 'np': 1,
    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
    'fltt': 2, 'invt': 2, 'fid': 'f6',
    'fs': 'b:MK0021+b:MK0022+b:MK0023',
    'fields': 'f12,f14,f2,f3,f4,f5,f6,f8,f15,f16,f17,f18,f23',
}
r = requests.get(url_etf, params=params_etf, headers=headers, proxies=proxies, timeout=5)
data_etf = r.json().get('data', {}).get('diff', [])
print(f"Total ETFs found: {len(data_etf)}")
for item in data_etf[:5]:
    print(f"  [{item.get('f12')}] {item.get('f14')}: 现价={item.get('f2')}, 涨跌幅={item.get('f3')}%, 换手={item.get('f8')}%, 成交额={item.get('f6')}")

print('\n=== 3. Testing Sector Capital Flow ===')
url_sec = 'http://push2.eastmoney.com/api/qt/clist/get'
params_sec = {
    'pn': 1, 'pz': 15, 'po': 1, 'np': 1,
    'ut': 'b2884c39002816ce865ee8f47db4f2b9',
    'fltt': 2, 'invt': 2, 'fid': 'f62',
    'fs': 'm:90 t:2',
    'fields': 'f12,f14,f2,f3,f62,f184',
}
r = requests.get(url_sec, params=params_sec, headers=headers, proxies=proxies, timeout=5)
data_sec = r.json().get('data', {}).get('diff', [])
print(f"Total sector flows found: {len(data_sec)}")
for item in data_sec[:5]:
    flow_yi = round((item.get('f62') or 0) / 100000000.0, 2)
    print(f"  {item.get('f14')}: 行业涨跌={item.get('f3')}%, 主力净流入={flow_yi}亿元, 占比={item.get('f184')}%")

print('\n=== 4. Testing Northbound Flow ===')
url_kamt = 'http://push2.eastmoney.com/api/qt/kamt/get'
params_kamt = {'fields1': 'f1,f2,f3,f4', 'fields2': 'f51,f52,f53,f54,f55,f56'}
r = requests.get(url_kamt, params=params_kamt, headers=headers, proxies=proxies, timeout=5)
data_kamt = r.json().get('data', {})
hk2sh = data_kamt.get('hk2sh', {})
hk2sz = data_kamt.get('hk2sz', {})
print(f"  沪股通余额={hk2sh.get('dayNetAmtIn')}万元, 深股通余额={hk2sz.get('dayNetAmtIn')}万元")
