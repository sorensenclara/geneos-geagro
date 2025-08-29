import requests

API_KEY = "F871B3E5-3346-F011-9445-00155D09E201"
SECRET = "7803e9d213c4f8df1ce2573b28927b270e802fe51f0d393d8b3ec3a1ce10deba"

def obtener_token_bcr():
    url = "https://api.bcr.com.ar/gix/v1.0/Login"
    payload = {
    }
    
    headers = { 
                "accept": "application/json",
                "api_key": API_KEY,
                "secret": SECRET
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        # El token viene como "Bearer <token>", úsalo tal cual
        return data["data"]["token"]
    else:
        print("Error autenticando:", response.status_code, response.text)
        return None

def get_quotes_bcr():
    token = obtener_token_bcr()
    if not token:
        return []
    url = "https://api.bcr.com.ar/gix/v1.0/PreciosCamara"
    headers = {
        "accept": "application/json",
        "Authorization": token
    }
    params = {
        "fechaConcertacionDesde": "2025-07-01", 
        "fechaConcertacionHasta": "2025-07-08", 
        "idGrano": "21"  
    }


    response = requests.get(url,params=params, headers=headers)
    print(response.status_code)
    print(response.text)
    if response.status_code == 200:
        return response.json()
    return []