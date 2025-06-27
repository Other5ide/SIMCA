import requests
import time
import random

URL = "http://3.221.0.222:8081/data"

def generar_dato():
    opciones = [
        {"device": "rak", "type": "temperature", "value": round(random.uniform(20, 30), 2)},
        {"device": "mobile", "type": "decibels", "value": round(random.uniform(50, 100), 2)}
    ]
    return random.choice(opciones)

if __name__ == "__main__":
    while True:
        data = generar_dato()
        try:
            r = requests.post(URL, json=data)
            print("Enviado:", data, "Status:", r.status_code)
        except Exception as e:
            print("Error al enviar:", e)
        time.sleep(1)
