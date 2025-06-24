# =========================
#   P-RAF: Python Benchmark Worker (Queue/Concurrent Version)
# =========================

import socket
import json
import random
import time
import threading
import queue

ORCHESTRATOR_HOST = '127.0.0.1'
ORCHESTRATOR_PORT = 9000
LANGUAGE_NAME = "Python"
ALGORITHMS = [
    "array_sort", "fibonacci", "game_of_life",
    "matrix_multiplication", "prime_factors", "is_leap_year"
]

result_queue = queue.Queue(maxsize=1000)

def array_sort():
    a = [random.randint(0, 99) for _ in range(40)]
    a.sort()

def fibonacci():
    a, b = 0, 1
    for _ in range(random.randint(20, 35)):
        a, b = b, a + b

def game_of_life():
    w, h, g = 35, 35, 5
    grid = [[random.randint(0, 1) for _ in range(h)] for _ in range(w)]
    for _ in range(g):
        next_grid = [[0] * h for _ in range(w)]
        for x in range(w):
            for y in range(h):
                ln = sum(
                    grid[(x + i) % w][(y + j) % h]
                    for i in (-1, 0, 1) for j in (-1, 0, 1)
                    if not (i == 0 and j == 0)
                )
                il = grid[x][y] == 1
                next_grid[x][y] = 1 if (il and (ln == 2 or ln == 3)) or (not il and ln == 3) else 0
        grid = next_grid

def matrix_multiplication():
    d = 50
    a = [[random.randint(0, 9) for _ in range(d)] for _ in range(d)]
    b = [[random.randint(0, 9) for _ in range(d)] for _ in range(d)]
    res = [[0] * d for _ in range(d)]
    for i in range(d):
        for j in range(d):
            for k in range(d):
                res[i][j] += a[i][k] * b[k][j]

def prime_factors():
    n = random.randint(100000, 500000)
    d = 2
    fac = []
    while d * d <= n:
        if n % d == 0:
            fac.append(d)
            n //= d
        else:
            d += 1
    if n > 1:
        fac.append(n)

def is_leap_year():
    y = random.randint(1, 9999)
    _ = (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0))

# Each algo thread: run forever, push result to queue
def algo_worker(name, algo_func):
    while True:
        start = time.time()
        algo_func()
        duration = time.time() - start
        result_queue.put({
            "lang": LANGUAGE_NAME,
            "algo": name,
            "duration": duration
        })

# Sender thread: keep one socket, send all results, reconnect if needed
def sender():
    while True:
        try:
            with socket.create_connection((ORCHESTRATOR_HOST, ORCHESTRATOR_PORT)) as sock:
                sock_file = sock.makefile("w", encoding="utf-8", newline="\n")
                print(f"✅ Python sender connected to orchestrator.")
                while True:
                    result = result_queue.get()
                    try:
                        sock_file.write(json.dumps(result) + "\n")
                        sock_file.flush()
                    except Exception as e:
                        print(f"⚠️  Python sender write error: {e}. Reconnecting...")
                        break  # Will reconnect outer loop
        except Exception as e:
            print(f"⚠️  Python sender connect error: {e}. Retrying in 2s...")
            time.sleep(2)

if __name__ == "__main__":
    print("✅ Starting P-RAF Python worker (queue version)...")
    algo_funcs = [
        array_sort, fibonacci, game_of_life,
        matrix_multiplication, prime_factors, is_leap_year
    ]
    # Algo threads
    threads = []
    for name, func in zip(ALGORITHMS, algo_funcs):
        t = threading.Thread(target=algo_worker, args=(name, func), daemon=True)
        t.start()
        threads.append(t)
    # Sender thread
    s = threading.Thread(target=sender, daemon=True)
    s.start()
    for t in threads:
        t.join()
