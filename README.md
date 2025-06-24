 __      __        ___                                                                                                                                                  
|__) __ |__)  /\  |__                                                                                                                                                   
|       |  \ /~~\ |                                                                                                                                                     
                                                                                                                                                                        
 __   __   __   __   ___  __   __   __   __      __            ___          ___                             __     __      ___  __              ___       __   __       
|__) |__) /  \ /  ` |__  /__` /__` /  \ |__)    |__) |  | |\ |  |  |  |\/| |__      /\  |\ |  /\  |    \ / /__` | /__`    |__  |__)  /\   |\/| |__  |  | /  \ |__) |__/ 
|    |  \ \__/ \__, |___ .__/ .__/ \__/ |  \    |  \ \__/ | \|  |  |  |  | |___    /~~\ | \| /~~\ |___  |  .__/ | .__/    |    |  \ /~~\  |  | |___ |/\| \__/ |  \ |  \ 
                                                                                                                                                                                                                      
# P-RAF: Processor-Runtime Analysis Framework
Version: 1.0 
Date: 24 June 2025
Author: Thomas Tannenberg
Licence MIT (c) Thomas Tannenberg, 2025

Proof of concept on a modern, cross-language benchmarking suite—built for real concurrency and fair comparisons.
Compare algorithm speed and runtime performance across Python, Ruby, Java, and Rust in a single interactive dashboard.

---

1. Current Features
- Multi-language: Benchmarks the same algorithms in Python, Ruby, Java, and Rust workers.
- Real concurrency: Each algorithm is executed in its own thread/process, across all languages.
- Unified Orchestrator: All results stream live to a single Python orchestrator via TCP.
- Web Dashboard: curently a simplified Dashboard via HTML/JS.
- Auto-reconnect & Fault Tolerance: All workers and orchestrator recover from disconnects and crashes.

2. Architecture

       +-----------------+        TCP/WebSocket         +---------------------+
       |   Benchmark     |<---------------------------> |   Python            |
       |   Workers       |   Results over TCP           |   Orchestrator      |
       |-----------------|                              |---------------------|
       | Python (py)     |       (one connection per    | - TCP Server        |
       | Ruby (rb)       |        language, or single   | - WebSocket Server  |
       | Java (jar)      |        queue sender)         | - Launches Workers  |
       | Rust (bin)      |                              | - Broadcasts to     |
       +-----------------+                              |   Dashboard         |
                                                        +-----------+---------+
                                                                    |
                                                        WebSocket   |
                                                                    v
                                                          +------------------+
                                                          |   Dashboard      |
                                                          | (HTML+JS)        |
                                                          +------------------+

3. Project Structure

Processor-Runtime-Analysis-Framework/
├── .gitignore
├── README.md                               # you are here, LOL
├── praf_orchestrator.py
│
├── dashboard/
│   ├── dashboard.html
│   ├── main.js
│   └── style.css
│
├── java_benchmark/
│    └──src/java/com/benchmark: Benchmark.java
├── python_benchmark/
│    └──benchmark.py
├── ruby_benchmark/
│    └──benchmark.rb
├── rust_benchmark/ 
│    └──src: main.rs
│
└── tools/
    └── build_manager.py


4. Prerequisites:

- Python 3.10+
- Ruby 3+ 
- Java (JDK 21) & Maven
- Rust toolchain (Cargo)
  All should be in your system PATH.

Build Workers (one-time, or after changes to Java/Rust code):

    python tools/build_manager.py

Run Framework
Starts orchestrator, launches workers, and opens the dashboard in your default browser:

    python praf_orchestrator.py

---

5. Vision & Scope

5.1 Executive Summary

P-RAF is a cross-platform analysis tool for benchmarking multiple programming languages, managed by a Python orchestrator, with real-time data streaming and a modern, interactive web dashboard.

5.2 Project Objectives

In-Scope for v1.0:
- Single, cross-platform Python app to manage all workers (run/terminate)
- Efficient real-time IPC: Persistent TCP sockets for high-throughput, fair multi-language data streaming
- Interactive web dashboard for live performance metrics
- Graceful termination of all child processes (Ctrl+C, etc.)

Out-of-Scope for v1.0:
- Public network accessibility & security
- Advanced dashboard features (history, CSV export, percentiles)
- Automated test suite

---

6. System Architecture

6.1 High-Level Design

P-RAF v1.1 consists of three main components:
- Orchestrator (Python, process & network manager)
- Benchmark Workers (one per language)
- Web Dashboard (live UI, browser-based)

One TCP connection per worker; one WebSocket per dashboard.

3.2 Architectural Flow

[Worker Threads]   [Worker Sender Thread]         [Orchestrator]             [Dashboard]
    |                       |                         |                           |
+---+---+       +-----------+-----------+      +------+-------+           +-------+--------+
| array  | ---> |  Threadsafe Queue     | ---> | TCP Server   | ------->  | WebSocket      |
| fib    | ---> | (per worker process)  |      | (asyncio)    |           | (HTML+JS)      |
| game   | ---> |                       |      |              |           |                |
+--------+       +----------------------+      +--------------+           +----------------+

- Each worker runs all algorithms concurrently (via threads).
- Results are pushed to a queue, sent over a single TCP connection.
- Orchestrator receives all payloads, time-stamps, and broadcasts to dashboard.

4. Component & Protocol Specifications

4.1 The Orchestrator

Role: Process manager, TCP/WebSocket server, dashboard broadcaster.

Responsibilities:
- Launch and monitor all worker processes (auto-restart safe).
- Listen for results on TCP, decode, and time-stamp them.
- Broadcast results and system status to all dashboards over WebSocket.
- Gracefully terminates all workers on exit.

[Start] --> [Launch Workers] --> [Accept TCP connections] --> [Accept WS dashboards]
            |                                    |
            +----> [Restart on worker crash]      +--> [Broadcast data to all dashboards]

4.2 Benchmark Workers
Role: Algorithm executors, TCP clients.
Concurrency: Each algorithm runs in its own thread (or equivalent).

Queue-based Model:
           +-----------------------------------------+
           |                Worker                   |
           |-----------------------------------------|
           |  [array_sort] --+                       |
           |  [fibonacci] -- +---> [Result Queue] -- +--> [Sender Thread] --> [TCP]
           |  ...            |                       |
           +-----------------------------------------+

4.3 Data Payload Schema

Worker-to-Orchestrator: (per result, sent as a line of JSON)

    {
      "lang": "Rust",
      "algo": "matrix_multiplication",
      "duration": 0.00012345
    }

Orchestrator-to-Dashboard (adds timestamp):

    {
      "lang": "Rust",
      "algo": "matrix_multiplication",
      "duration": 0.00012345,
      "timestamp": 1720430123.123
    }

Fields:
- lang (String): "Python", "Ruby", "Java", "Rust"
- algo (String): e.g., "array_sort"
- duration (Float): Execution time in seconds
- timestamp (Float): Unix epoch time (added by orchestrator)

4.4 Sequence Diagram: A Single Payload's Journey

+-----------+           +--------------+           +--------------+           +--------------+
| Algorithm |           |  Worker TCP  |           | Orchestrator |           |  Dashboard   |
|  Thread   |           |   Sender     |           |              |           |  (WebSocket) |
+-----------+           +--------------+           +--------------+           +--------------+
     |                          |                           |                         |
     |     run & time algo      |                           |                         |
     |------------------------->|                           |                         |
     |                          |   JSON line (payload)     |                         |
     |                          |-------------------------->|                         |
     |                          |                           |   add timestamp         |
     |                          |                           |-----------------------> |
     |                          |                           |   send JSON to browser  |
     |                          |                           |                         |

4.5 The Web Dashboard

- WebSocket Client: Connects to ws://localhost:9001
- Data Handling: Parses incoming JSON; logs to console for debugging
- State Management: In-memory stats per language/algorithm
- DOM Updates: Counters and charts update live

UX Features:
- Connection Status indicator
- Reset button (clears stats)
- Status/error area (for orchestrator notifications)

---


5. Developer Tools

5.1 Build Manager (tools/build_manager.py)

Purpose:
A dev utility to compile Java and Rust workers.

Usage:
Run after changing Java/Rust code, before starting the orchestrator.

    python tools/build_manager.py

Note: This script is not part of the runtime execution path. Orchestrator assumes workers are pre-compiled.

6. Benchmark Methodology & Measurement

P-RAF (currently) focuses on algorithmic microbenchmarks—short, well-defined computational tasks implemented in each language.
Each algorithm is chosen for its typical presence in real workloads, and its varying pressure on the CPU, memory, and language runtime.

Algorithms currently benchmarked:

- Array sorting (array_sort)
- Fibonacci sequence calculation (fibonacci)
- Conway’s Game of Life simulation (game_of_life)
- Matrix multiplication (matrix_multiplication)
- Prime factorization (prime_factors)
- Leap year check (is_leap_year)

6.1 Benchmark Execution Loop

Each worker repeatedly executes its assigned algorithm in a tight loop:
Start time is recorded (with nanosecond or high-res clock).
The algorithm runs to completion.
Duration (elapsed time in seconds) is calculated.
Result is sent immediately as a JSON payload to the orchestrator via TCP.
Each worker runs as its own OS thread/process for true concurrency and to best reflect typical language runtime performance.

6.3 Timing & Overhead

Timing: Uses high-precision clocks (Process.clock_gettime in Ruby, std::time::Instant in Rust, System.nanoTime in Java, time.time() in Python) to avoid measuring unrelated system delays.
I/O Overhead: Sending results is done after timing is stopped. Only pure algorithm execution time is measured.
Backoff & Resilience: If a worker disconnects (network or orchestrator restart), it retries every 2s

6.4 Measurement Caveats

Each language’s implementation is as direct as possible (idiomatic, not “hyper-optimized” for one).
Results are not synchronized between languages—each algorithm loop is independent, so dashboard rates reflect both speed and thread/process scheduling.
Benchmarks are microbenchmarks; real-world code may behave differently due to GC, JIT, OS effects, etc.

6.5 Visualizing Results

The Web Dashboard live-aggregates all measurements, letting you compare:

Throughput (runs/sec)
Average and minimum duration
Per-language, per-algorithm breakdown

7. Contributions

Just me, testing and trying out things.

---


Licence MIT (c) Thomas Tannenberg, 2025

Questions? Feature requests? Open an issue or pull request!