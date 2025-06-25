Design-Dokument: P-RAF 2.0

Version: 2.0 
Datum: 25. Juni 2025
Autor: Thomas Tannenberg

1. Einleitung und Vision
P-RAF 2.0 soll ein modulares, methodisch belastbares und wissenschaftlich ernstzunehmendes Framework für Leistungsvergleiche zwischen Programmiersprachen sein.
Werte:

Fairness (reproduzierbare, vergleichbare Tests)

Modularität (einfache Erweiterbarkeit)

Robustheit (langfristig wartbar, stabil auch bei Fehlern)

Exzellente Usability (Dashboard als Herzstück)

2. Analyse Ist-Zustand (V1.x)
Stärken:

Performante, persistente TCP-Verbindungen pro Worker

Breite Sprachabdeckung

Live-Dashboard für sofortiges Feedback

Grundlegende Robustheit (Rekonnektierungsmechanismen)

Schwächen:

Fehlende Isolation → Messwerte durch Ressourcenkonkurrenz verfälscht

Monolithischer Code: Infrastruktur und Logik vermischt

Ungefilterter Datenfluss („Daten-Spam“)

Erweiterbarkeit durch hart verdrahtete Algorithmen eingeschränkt

Kaum Wiederverwendbarkeit von Komponenten

3. Zielarchitektur P-RAF 2.0
3.1 Prinzipien und Pattern
Klares Core/Library-Splitting (zentrale Vorgabe!)

Kommandogesteuerte Steuerung (Orchestrator gibt alles vor)

Phase- und Batch-basiertes Benchmarking (verhindert Bias & Overhead)

Extrem lose Kopplung: Alles, was sich unabhängig testen, bauen oder ersetzen lässt, ist ein Modul.

3.2 Kern-Design: Verantwortlichkeiten & Flows
3.2.1 Komponenten- und Kommunikationsübersicht

graph TD
    subgraph Orchestrator
      O[Orchestrator]
    end
    subgraph Worker
      C[Core/Runner] --> L(Benchmark Library)
    end
    O --"RUN_TEST / SHUTDOWN"--> C
    C --"Batch-Resultate, Fehler"--> O
    O --"Result-Events, Status"--> D(Dashboard)
    D --"User-Aktionen"--> O

3.2.2 Ausführungsablauf (Sequenzdiagramm)
sequenceDiagram
    participant User
    participant D as Dashboard
    participant O as Orchestrator
    participant C as Worker-Core
    participant L as Library

    User->>D: Klickt "Start Test"
    D->>O: sendet Start-Request
    O->>C: sendet RUN_TEST
    C->>L: ruft Benchmark-Funktion n mal auf
    loop Messphase
      L-->>C: liefert Ergebnis zurück
      C-->>O: schickt Batch mit Resultaten
      O-->>D: broadcastet Result-Batch (Live-Update)
    end
    O->>C: sendet SHUTDOWN
    C-->>O: sendet Abschluss-Status
    O->>D: sendet Scorecard (Abschluss)


4. Projekt- und Code-Struktur
Empfohlenes Projektlayout für maximale Klarheit und Trennung:

Processor-Runtime-Analysis-Framework/
├── config.yaml
├── praf_orchestrator.py
├── dashboard/
│   ├── dashboard.html
│   ├── main.js
│   ├── style.css
├── python_benchmark/
│   ├── runner.py
│   └── benchmarks/
│       └── algorithms.py
├── ruby_benchmark/
│   ├── runner.rb
│   └── benchmarks/
│       └── algorithms.rb
├── java_benchmark/
│   └── src/
│       └── main/java/com/benchmark/
│           ├── Runner.java
│           └── benchmarks/
│               └── Algorithms.java
├── rust_benchmark/
│   └── src/
│       ├── main.rs
│       └── benchmarks/
│           └── algorithms.rs

- Testkonfiguration und Testplan vollständig über config.yaml steuerbar!

- Jede Sprache mit identischer Runner-/Library-Struktur: → Sprachen sind untereinander austauschbar.

5. Steuerungs- und Datenprotokoll (mit Beispielen)
5.1 Steuerprotokoll (Orchestrator → Worker)

{
  "command": "RUN_TEST",
  "payload": {
    "test_id": "test-2025-06-25-001",
    "language": "Python",
    "algorithm": "matrix_multiplication",
    "warmup_sec": 15,
    "measure_sec": 60,
    "params": { "dimension": 100 }
  }
}

- Immer „test_id“ mitschicken, um alle Resultate eindeutig zuordnen zu könne

5.2 Antwortprotokoll (Worker → Orchestrator, Batchweise!)

{
  "status": "success",
  "type": "data_batch",
  "payload": {
    "test_id": "test-2025-06-25-001",
    "results": [
      {"duration": 0.0051, "timestamp": 1720430123.123},
      {"duration": 0.0049, "timestamp": 1720430123.128}
    ]
  }
}

5.3 Fehlerprotokoll

{
  "status": "error",
  "type": "error_report",
  "payload": {
    "test_id": "test-2025-06-25-001",
    "error_code": 501,
    "message": "Benchmark function 'matrix_multiplication' failed: OutOfMemoryError"
  }
}


- Codes für Fehlertypen (Timeout, Exception, Parametrierungsfehler) vorab definieren.


6. Benchmark-Runner-Design (Python-Beispiel)

6.1 Benchmark-Library: Einfach und immer parametrisierbar

# benchmarks/algorithms.py
import random

def matrix_multiplication(params):
    d = params.get("dimension", 100)
    a = [[random.random() for _ in range(d)] for _ in range(d)]
    b = [[random.random() for _ in range(d)] for _ in range(d)]
    res = [[0] * d for _ in range(d)]
    for i in range(d):
        for j in range(d):
            res[i][j] = sum(a[i][k] * b[k][j] for k in range(d))
    return res  # explizites Resultat zur Validierung

AVAILABLE_BENCHMARKS = {"matrix_multiplication": matrix_multiplication}

6.2 Core Framework (Runner) – Verantwortlichkeiten explizit trennen!

# runner.py
from benchmarks.algorithms import AVAILABLE_BENCHMARKS
import time, threading, queue, json, socket

class BenchmarkRunner:
    def __init__(self, command):
        self.command = command
        self.results = queue.Queue()
        self.running = False

    def run_benchmark(self, algo_func, params):
        while self.running:
            start = time.perf_counter()
            try:
                algo_func(params)
                duration = time.perf_counter() - start
                self.results.put({"duration": duration, "timestamp": time.time()})
            except Exception as e:
                # Error-Handling: Fehlerreport an Orchestrator schicken
                pass

    def execute(self):
        payload = self.command['payload']
        algo = payload['algorithm']
        params = payload['params']
        warmup, measure = payload['warmup_sec'], payload['measure_sec']
        if algo not in AVAILABLE_BENCHMARKS:
            # Error-Report senden
            return
        self.running = True
        t = threading.Thread(target=self.run_benchmark, args=(AVAILABLE_BENCHMARKS[algo], params))
        t.start()
        time.sleep(warmup)
        with self.results.mutex:
            self.results.queue.clear() # Queue leeren
        time.sleep(measure)
        self.running = False
        t.join()
        batch = [self.results.get() for _ in range(self.results.qsize())]
        # batch an Orchestrator senden

7. Konfiguration: test_plan, Benchmarks & Zeitsteuerung
Alles in einer YAML-Datei zentral steuern!

test_plan:
  - language: Python
    runner_command: ["python", "python_benchmark/runner.py"]
  - language: Rust
    runner_command: ["./rust_benchmark/target/release/rust_benchmark_worker"]

timing:
  warmup_seconds: 15
  measure_seconds: 60

benchmarks:
  matrix_multiplication:
    enabled: true
    params:
      dimension: 100
  fibonacci:
    enabled: true
    params:
      iterations: 30


8. Dashboard: Interaktion und Visualisierung
User Flow:

- Start-Bildschirm → "Test starten" → Phasenindikator (Farbschema!) → Live-Chart (z.B. Runs/Sek) → Scorecard → Vergleichsübersicht

Visualisierungstypen:

- Liniendiagramm: Durchsatz (Runs/Sek) über die Zeit (während Messphase)

- Histogramm: Verteilung der Latenzen (Boxplot/Violinplot)

- Balkendiagramm: Finaler Vergleich aller Sprachen/Benchmarks

- Scorecards: Min, Median, 90. Perzentil, Max (pro Benchmark)

Zusatz:
- Export-Funktion (CSV): Ergebnisse direkt per Knopfdruck exportieren.

- Reproduzierbarkeit: Dashboard bietet Download aller Test-Settings als JSON.


9. Logging & Monitoring
Orchestrator: Nutzt strukturiertes Logging (logging in Python)

Worker: Schreibt Fehlerreports ins Log und sendet relevante Fehler an Orchestrator

Loglevel vorsehen: INFO, WARNING, ERROR, DEBUG
Empfehlung: Fehler immer mit test_id und Zeitstempel loggen.


10. Best Practices, Erweiterbarkeit & Quality Gates
Jede neue Benchmark-Funktion als Einzelfunktion ohne Seiteneffekte

Unit-Tests für Library-Funktionen (insbesondere für Korrektheit/Validierung!)

Konsequentes Versionieren (Test-ID, Settings in jedem Batch mitschicken!)

Modularisierung und DRY: Doppelte Logik vermeiden, Templates/Abstraktionen nutzen

Dokumentation: Jede Komponente erhält eigene README oder Docstrings

12. Ausblick: Mögliche nächste Schritte
Integration weiterer Sprachen (z.B. Go, C#)

Erweiterung des Dashboards (History, Filtern nach Algorithmen)

Optionale Validierung der Ergebnisse (Sanity Checks pro Durchlauf)

Optional: Auswertung auf mehreren Maschinen (Verteiltes Benchmarking)

Flame-Chart: Zeigt Anteil einzelner Algorithmen am Gesamtverbrauch

Phasenübersicht: Gantt-Chart für Benchmark-Läufe

Timeline-Ansicht: Visualisiert Benchmarks mit Start/Ende/Fehlern

