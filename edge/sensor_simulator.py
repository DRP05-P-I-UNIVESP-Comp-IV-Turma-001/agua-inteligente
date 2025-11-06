# edge/sensor_simulator.py
import time
import random
import requests
from datetime import datetime, timezone

API_URL = "http://127.0.0.1:8000/readings"

METER_CODES = ["SETOR-A-01", "SETOR-A-02", "SETOR-B-01"]


def gen_flow_lpm():
    # base 12–30 L/min, com pequenas variações
    base = random.uniform(12.0, 30.0)
    # pico eventual para simular anomalia
    if random.random() < 0.05:
        base *= random.uniform(1.8, 2.5)
    return round(base, 3)


def gen_pressure_bar():
    return round(random.uniform(1.5, 3.5), 3)


def gen_temp_c():
    return round(random.uniform(18.0, 30.0), 2)


def main():
    print("Iniciando simulador de sensor. Ctrl+C para parar.")
    while True:
        meter = random.choice(METER_CODES)
        payload = {
            "meter_code": meter,
            "flow_lpm": gen_flow_lpm(),
            "pressure_bar": gen_pressure_bar(),
            "temperature_c": gen_temp_c(),
            "ts": datetime.now(timezone.utc).isoformat()
        }
        try:
            r = requests.post(API_URL, json=payload, timeout=5)
            r.raise_for_status()
            data = r.json()
            print(
                f"[OK] {data['ts']} {data['meter_code']} flow={data['flow_lpm']} L/min")
        except Exception as e:
            print(f"[ERRO] Falha ao enviar leitura: {e}")
        time.sleep(5)


if __name__ == "__main__":
    main()
