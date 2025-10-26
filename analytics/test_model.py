import random

def detect_anomaly(vazao):
    if vazao > 2.0:
        return "Possível vazamento detectado!"
    return "Fluxo normal"

print(detect_anomaly(random.uniform(0.5, 2.5)))
