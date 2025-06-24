import asyncio
import subprocess
import sys
import webbrowser
import json
import time
from pathlib import Path

# =========================
#   P-RAF: Orchestrator (v1.4 - Extra Robust, Persistent Connections)
# =========================

TCP_HOST = '127.0.0.1'
TCP_PORT = 9000
WEBSOCKET_HOST = '127.0.0.1'
WEBSOCKET_PORT = 9001

ROOT_DIR = Path(__file__).parent.resolve()
DASHBOARD_PATH = ROOT_DIR / "dashboard" / "dashboard.html"

WORKER_COMMANDS = {
    "Python": [sys.executable, str(ROOT_DIR / "python_benchmark" / "benchmark.py")],
    "Ruby": ["ruby", str(ROOT_DIR / "ruby_benchmark" / "benchmark.rb")],
    "Java": ["java", "-jar", str(ROOT_DIR / "java_benchmark" / "target" / "java-benchmark-runner.jar")],
    "Rust": [str(ROOT_DIR / "rust_benchmark" / "target" / "release" / "rust_benchmark_worker.exe")]
}

worker_processes = []
websocket_clients = set()
tcp_server = None
websocket_server = None

# --- WebSocket Broadcasting ---
async def broadcast_message(message_str):
    """Sends a message to all connected WebSocket clients concurrently."""
    if websocket_clients:
        await asyncio.gather(
            *(ws.send(message_str) for ws in websocket_clients),
            return_exceptions=True
        )

async def broadcast_status(level, text):
    """Sends a structured status message to all dashboards."""
    await broadcast_message(json.dumps({"type": "status", "level": level, "message": text}))

# --- Server Implementations ---
async def handle_tcp_client(reader, writer):
    """Handles a single, persistent TCP connection from a benchmark worker."""
    client_addr = writer.get_extra_info('peername')
    print(f"✅ [TCP] Worker connected from {client_addr}")
    try:
        while not reader.at_eof():
            data = await reader.readline()
            if not data:
                break
            message = data.decode().strip()
            if message:
                try:
                    payload = json.loads(message)
                    payload["timestamp"] = time.time()
                    await broadcast_message(json.dumps(payload))
                except json.JSONDecodeError:
                    print(f"❌ [TCP] Invalid JSON from {client_addr}: {message}")
    except (ConnectionResetError, asyncio.IncompleteReadError):
        # Connection closed by client or forcibly terminated
        pass
    except Exception as e:
        print(f"❌ [TCP] Unexpected error with worker {client_addr}: {e}")
    finally:
        print(f"ℹ️  [TCP] Worker {client_addr} disconnected.")
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def websocket_handler(websocket):
    """Handles a single dashboard client connection."""
    print(f"✅ [WebSocket] Dashboard connected: {websocket.remote_address}")
    websocket_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        print(f"ℹ️  [WebSocket] Dashboard disconnected: {websocket.remote_address}")
        websocket_clients.remove(websocket)

# --- Main Application Logic ---
def launch_workers(abort_on_fail=False):
    """Launches all benchmark workers as subprocesses."""
    print("\n--- Launching Workers ---")
    loop = asyncio.get_running_loop()
    for lang, command in WORKER_COMMANDS.items():
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            proc = subprocess.Popen(command, creationflags=creationflags)
            worker_processes.append(proc)
            print(f"🚀 Launched {lang} worker (PID: {proc.pid})")
        except Exception as e:
            error_msg = f"Failed to launch {lang} worker: {e}"
            print(f"❌ ERROR: {error_msg}")
            loop.create_task(broadcast_status("error", error_msg))
            if abort_on_fail:
                terminate_workers()
                raise RuntimeError("Aborted due to worker launch failure.")

def terminate_workers():
    """Terminates all running worker subprocesses."""
    print("\n--- Terminating Worker Processes ---")
    for p in worker_processes:
        print(f"🛑 Terminating PID {p.pid}...")
        p.terminate()
    time.sleep(1)
    for p in worker_processes:
        if p.poll() is None:
            print(f"   Force-killing PID {p.pid}...")
            p.kill()
    print("All worker processes terminated.")

async def main():
    """Sets up and runs the main application event loop."""
    global tcp_server, websocket_server
    try:
        import websockets
    except ImportError:
        print("❌ ERROR: `pip install websockets` is required.")
        sys.exit(1)

    # --- Start TCP server (persistent handlers for each worker)
    tcp_server = await asyncio.start_server(handle_tcp_client, TCP_HOST, TCP_PORT)
    print(f"✅ TCP Server listening on {TCP_PORT}")

    # --- Start WebSocket server
    websocket_server = await websockets.serve(websocket_handler, WEBSOCKET_HOST, WEBSOCKET_PORT)
    print(f"✅ WebSocket Server listening on {WEBSOCKET_PORT}")

    # --- Launch workers (once, at orchestrator startup)
    launch_workers(abort_on_fail=False)

    try:
        webbrowser.open(DASHBOARD_PATH.as_uri())
    except Exception as e:
        print(f"⚠️  Could not open dashboard in browser: {e}\n   Manually open: {DASHBOARD_PATH}")

    print("\n--- Orchestrator is running. Press Ctrl+C to stop. ---")
    await asyncio.Event().wait()

async def shutdown():
    """Performs a graceful shutdown of all tasks and processes."""
    print("\n--- Shutting Down Gracefully ---")
    terminate_workers()
    # Closing servers
    if websocket_server:
        websocket_server.close()
        await websocket_server.wait_closed()
        print("✅ WebSocket server closed.")
    if tcp_server:
        tcp_server.close()
        await tcp_server.wait_closed()
        print("✅ TCP server closed.")

if __name__ == "__main__":
    print("="*44)
    print("  Processor-Runtime Analysis Framework (P-RAF)")
    print("="*44)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Shutting down...")
        try:
            asyncio.run(shutdown())
        except Exception:
            pass
    finally:
        print("P-RAF has shut down. Goodbye!")
