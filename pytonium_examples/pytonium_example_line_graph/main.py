"""Pytonium Line Graph Example — Real-Time Data Visualization

Demonstrates real-time Python-to-JavaScript data streaming using state
management. A Geometric Brownian Motion simulation pushes stock price
data every 0.5 seconds, and a D3.js line chart in the browser updates
live.

Features:
- State management (set_state from Python, DOM events in JavaScript)
- Real-time data visualization with D3.js
- Mathematical simulation in Python (Brownian motion)
"""

import math
import os
import time
import random
from datetime import datetime

from Pytonium import Pytonium


def main():
    pytonium = Pytonium()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")

    pytonium.initialize(f"file:///{html_path}", 1920, 1080)

    labels = []
    data = []

    # Brownian motion parameters
    mu = 0.001       # drift
    sigma = 0.01     # volatility
    S0 = 100          # initial price

    last_update_time = time.time()

    while pytonium.is_running():
        pytonium.update_message_loop()
        time.sleep(0.01)

        # Push new data point every 0.5 seconds
        current_time = time.time()
        if current_time - last_update_time >= 0.5:
            last_update_time = current_time

            now = datetime.now()
            date_time = now.strftime("%d.%m.%Y, %H:%M:%S")
            labels.append(date_time)

            # Geometric Brownian Motion step
            Wt = random.gauss(0, 1)
            new_stock_price = S0 * math.exp((mu - 0.5 * sigma ** 2) + sigma * Wt)
            data.append(new_stock_price)

            pytonium.set_state("app-general", "stock_data", {"data": data, "labels": labels})


if __name__ == "__main__":
    main()
