import requests
base = 'http://127.0.0.1:8000'
r = requests.post(base+'/api/predict', json={'product':'Wonka Bar - Milk Chocolate','region':'Pacific','factory':"Lot's O' Nuts",'ship_mode':'Standard Class'})
print('predict:', r.json())
r = requests.get(base+'/')
print('dashboard:', r.status_code, 'html' if 'html' in r.headers.get('content-type','') else 'other')