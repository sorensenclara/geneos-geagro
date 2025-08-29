import requests

def obtener_precios_fob(fecha):
    print(f"Fetching FOB prices for date: {fecha}")
    url = f"https://monitorsiogranos.magyp.gob.ar/ws/ssma/precios_fob.php?Fecha={fecha}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f"Response JSON: {response.json()}")
        return response.json()
    return None

def obtener_cotizaciones_bcr():
    url = "https://api.bcr.com.ar/gix/v1.0/Cotizacion"
    headers = {
        "accept": "application/json",
        # "Authorization": "Bearer TU_TOKEN_AQUI"  # Si la API requiere autenticación
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None