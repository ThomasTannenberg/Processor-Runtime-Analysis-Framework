# Processor-Runtime Analysis Framework (P-RAF)

**Version:** 1.0  
**Date:** 24 June 2025  
**Author:** Thomas Tannenberg

---

## 1. Quickstart Guide

**Prerequisites:**

- Python 3
- Ruby
- Java (JDK) & Maven
- Rust toolchain (Cargo)  
  _All should be in your system `PATH`._

**Build Workers** (one-time, or after changes to Java/Rust code):

```bash
python tools/build_manager.py
```

**Run Framework**  
Starts orchestrator, launches workers, and opens the dashboard in your default browser:

```bash
python praf_orchestrator.py
```

---

## 2. Vision & Scope

### 2.1 Executive Summary

P-RAF is a cross-platform analysis tool for benchmarking multiple programming languages, managed by a Python orchestrator, with real-time data streaming and a modern, interactive web dashboard.

### 2.2 Project Objectives

**In-Scope for v1.0:**
- Single, cross-platform Python app to manage all workers (run/terminate)
- Real-time IPC pipeline using TCP and WebSockets (no file-based I/O)
- Interactive web dashboard for live performance metrics
- Graceful termination of all child processes (Ctrl+C, etc.)

**Out-of-Scope for v1.0:**
- Public network accessibility & security
- Advanced dashboard features (history, CSV export, percentiles)
- Automated test suite

---

## 3. System Architecture

### 3.1 High-Level Design

P-RAF v1.0 consists of three main components:
- **Orchestrator** (Python, process & network manager)
- **Benchmark Workers** (one per language)
- **Web Dashboard** (live UI, browser-based)

### 3.2 Architectural Flow

```
+-----------------------------------------------+
|     Python Orchestrator (praf_orchestrator.py)|
|    [A] Process Manager                        |
|    [B] TCP Server (Worker data)               |----(WebSocket @ 9001)---> [Web Browser]
|    [C] WebSocket Server (UI data)             |                        (dashboard.html)
+-----------------------------------------------+
 [Rust Worker]  --(TCP @ 9000)--->
 [Java Worker]  --(TCP @ 9000)--->
 [Python Worker]--(TCP @ 9000)--->
     ...and so on
```

---

## 4. Component & Protocol Specifications

### 4.1 The Orchestrator

- **Process Spawning:** Launches each benchmark worker as a managed subprocess
- **TCP Server (localhost:9000):** Receives data from workers
- **WebSocket Server (localhost:9001):** Broadcasts data to dashboard(s)
- **Data Relay:** Adds Unix timestamp to each JSON payload before broadcast
- **Graceful Shutdown:** SIGINT (Ctrl+C) kills all workers
- **UI Launch:** Opens `dashboard/dashboard.html` in your default browser
- **Logging & Error Handling:** Logs events, errors, and worker crashes; notifies dashboard on crash

### 4.2 Benchmark Workers

Each worker:
- Computes benchmark results in a loop
- After each run:
    - Connects to `localhost:9000` (TCP)
    - Sends JSON payload (see below)
    - Closes connection

### 4.3 Data Payload Schema

**Worker-to-Orchestrator:**

```json
{
  "lang": "Rust",
  "algo": "matrix_multiplication",
  "duration": 0.00012345
}
```

**Orchestrator-to-Dashboard (adds timestamp):**

```json
{
  "lang": "Rust",
  "algo": "matrix_multiplication",
  "duration": 0.00012345,
  "timestamp": 1720430123.123
}
```

**Fields:**
- `lang` (String): `"Python"`, `"Ruby"`, `"Java"`, `"Rust"`
- `algo` (String): e.g., `"array_sort"`
- `duration` (Float): Execution time in seconds
- `timestamp` (Float): Unix epoch time (added by orchestrator)

### 4.4 Sequence Diagram: A Single Payload's Journey

```
[Worker]                [Orchestrator]                      [Dashboard UI]
   |                          |                                   |
(run algorithm)               |                                   |
   |--- TCP CONNECT (9000) -->|                                   |
   |--- SEND JSON ----------->| (receives & parses JSON)          |
   |--- CLOSE connection ---->| (adds timestamp)                  |
   |                          |--- WebSocket PUSH (9001)--------->|
   |                          |                                   | (parse/update UI)
(loop to next run)            |                                   |
```

### 4.5 The Web Dashboard

- **WebSocket Client:** Connects to `ws://localhost:9001`
- **Data Handling:** Parses incoming JSON; logs to console for debugging
- **State Management:** In-memory stats per language/algorithm
- **DOM Updates:** Counters and charts update live

**UX Features:**
- Connection Status indicator
- Reset button (clears stats)
- Status/error area (for orchestrator notifications)

---

## 5. Project Structure

```
Processor-Runtime-Analysis-Framework/
├── .gitignore
├── README.md           # you are here, LOL
├── praf_orchestrator.py
│
├── dashboard/
│   ├── dashboard.html
│   ├── main.js
│   └── style.css
│
├── java_benchmark/ ...
├── python_benchmark/ ...
├── ruby_benchmark/ ...
├── rust_benchmark/ ...
│
└── tools/
    └── build_manager.py
```

---

## 6. Developer Tools

### 6.1 Build Manager (`tools/build_manager.py`)

**Purpose:**  
A dev utility to compile Java and Rust workers.

**Usage:**  
Run after changing Java/Rust code, before starting the orchestrator.
```bash
python tools/build_manager.py
```
> _Note: This script is not part of the runtime execution path. Orchestrator assumes workers are pre-compiled._

---

## 7. Development Roadmap

- **Phase 1:** Orchestrator Core (process management, shutdown, servers)
- **Phase 2:** Dashboard foundation (HTML/CSS, WebSocket client, console log)
- **Phase 3:** Worker integration (update workers, verify data flow)
- **Phase 4:** UI visualization (charting, dynamic DOM)

---

## 8. Risks & Extensibility

- **Port Conflicts:** Hardcoded ports for v1.0; `config.yaml` planned for v2.0
- **IPC Overhead:** “Connect-per-result” TCP is robust for v1.0; future optimization possible
- **Extensibility:**
    - **Workers:** Add new languages by adding a worker directory and updating process list
    - **Dashboard:** Future: Support custom JS chart modules for visualization

---

**Questions? Feature requests? Open an issue or pull request!**
