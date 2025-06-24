import random
import time
import threading
import os
import yaml
import numpy as np
from numba import njit
from scipy.signal import convolve2d

# --- Configuration ---
PYTHON_STATS_FILE = 'python_stats.yaml'
RUBY_STATS_FILE = 'ruby_stats.yaml'
ALGORITHMS = ['array_sort', 'fibonacci', 'game_of_life', 'matrix_multiplication', 'prime_factors', 'is_leap_year']
STATS = {name: {'runs': 0, 'total_time': 0.0, 'min_time': float('inf'), 'max_time': 0.0} for name in ALGORITHMS}
LOCK = threading.Lock()

# Seeds muss halt doppelt wegen numpy und random
random.seed(123)
np.random.seed(123)



def array_sort():
    """Uses NumPy for potentially faster sorting."""
    arr = np.random.rand(40) * 100
    np.sort(arr)


@njit
def fibonacci_numba():
    a, b = 0, 1

    for _ in range(random.randint(20, 35)):
        a, b = b, a + b
    return a

def fibonacci():
    fibonacci_numba()

def game_of_life():
    """Optimized with NumPy and SciPy's convolution for neighbor counting."""
    w, h, g = 35, 35, 5
    grid = np.random.randint(0, 2, size=(w, h), dtype=np.int8)
    kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int8)
    
    for _ in range(g):
        live_neighbors = convolve2d(grid, kernel, mode='same', boundary='wrap')
        grid = ((grid == 1) & ((live_neighbors == 2) | (live_neighbors == 3))) | \
               ((grid == 0) & (live_neighbors == 3))
        grid = grid.astype(np.int8)

def matrix_multiplication():
    """Drastically accelerated using NumPy's optimized dot product."""
    dim = 50
    a = np.random.rand(dim, dim)
    b = np.random.rand(dim, dim)
    np.dot(a, b)

@njit
def prime_factors_numba(n):
    factors = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            factors.append(d)
            n //= d
        else:
            d += 1
    if n > 1:
        factors.append(n)
    return factors

def prime_factors():
    num = random.randint(100000, 500000)
    prime_factors_numba(num)

def is_leap_year():
    """This function is already extremely fast; optimization is not necessary."""
    y = random.randint(1, 9999)
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)

# --- Core Application Logic ---

ALGO_FUNCTIONS = dict(zip(ALGORITHMS, [array_sort, fibonacci, game_of_life, matrix_multiplication, prime_factors, is_leap_year]))

def worker(name, func):
    """Benchmark worker thread."""
    while True:
        start = time.perf_counter()
        func()
        duration = time.perf_counter() - start
        
        with LOCK:
            s = STATS[name]
            s['runs'] += 1
            s['total_time'] += duration
            s['min_time'] = min(s['min_time'], duration)
            s['max_time'] = max(s['max_time'], duration)
            
        # time.sleep(0.05)

def yaml_writer():
    """Periodically writes stats to a YAML file."""
    tmp_file = PYTHON_STATS_FILE + '.tmp'
    while True:
        time.sleep(10)
        stats_copy = {}
        with LOCK:
            # Deep copy and reset the stats dictionary atomically
            stats_copy = {k: v.copy() for k, v in STATS.items()}
            for name in STATS:
                STATS[name] = {'runs': 0, 'total_time': 0.0, 'min_time': float('inf'), 'max_time': 0.0}
        
        with open(tmp_file, 'w') as f:
            yaml.dump(stats_copy, f)
        os.replace(tmp_file, PYTHON_STATS_FILE)

def reporter():
    """Periodically reads all YAML files and prints a combined dashboard."""
    while True:
        time.sleep(10)
        
        # --- Load Data ---
        try:
            with open(PYTHON_STATS_FILE, 'r') as f: python_data = yaml.safe_load(f) or {}
        except FileNotFoundError: python_data = {}
        
        try:
            with open(RUBY_STATS_FILE, 'r') as f: ruby_data = yaml.safe_load(f) or {}
        except FileNotFoundError: ruby_data = {}

        try:
            with open('java_stats.yaml', 'r') as f: java_data = yaml.safe_load(f) or {}
        except FileNotFoundError: java_data = {}
            
        try:
            with open('rust_stats.yaml', 'r') as f: rust_data = yaml.safe_load(f) or {}
        except FileNotFoundError: rust_data = {}
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print("--- Cross-Language Performance Dashboard (10s Intervals) ---")
        header = f"{'Algorithm':<25} {'Python':>12} {'Ruby':>12} {'Java':>12} {'Rust':>12}"
        print(header)
        print("-" * len(header))
        
        for name in ALGORITHMS:
            py_runs = python_data.get(name, {}).get('runs', 0)
            java_runs = java_data.get(name, {}).get('runs', 0)
            rust_runs = rust_data.get(name, {}).get('runs', 0)
            rb_runs = ruby_data.get(name, {}).get(':runs', 0)

            print(f"{name:<25} {py_runs:>12} {rb_runs:>12} {java_runs:>12} {rust_runs:>12}")

def main():
    """Initializes and starts all threads."""
    for f in [PYTHON_STATS_FILE, RUBY_STATS_FILE, PYTHON_STATS_FILE + '.tmp', RUBY_STATS_FILE + '.tmp']:
        if os.path.exists(f):
            os.remove(f)
            
    # Create threads for each algorithm and the reporter
    threads = [threading.Thread(target=reporter), threading.Thread(target=yaml_writer)]
    threads += [threading.Thread(target=worker, args=(name, func)) for name, func in ALGO_FUNCTIONS.items()]


    print("starting python multitask benchmark v0.1")
    print("starting dahsboard reporter in 10 seconds")
    print("written by: ThomasTannenberg")
    print("Python multitask workers initialized for algorithms: " + ", ".join(ALGORITHMS))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()