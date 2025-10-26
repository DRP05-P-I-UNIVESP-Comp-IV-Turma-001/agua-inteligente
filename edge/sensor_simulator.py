import random
import time


def simulate_sensor():
    while True:
        vazao = round(random.uniform(0.5, 2.5), 2)
        print(f"Vazão simulada: {vazao} L/s")
        time.sleep(2)


if __name__ == "__main__":
    simulate_sensor()
