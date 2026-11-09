"""Inicia os serviços locais e encerra seus processos juntos """

import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-host", default="127.0.0.1")
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--web-host", default="127.0.0.1")
    parser.add_argument("--web-port", type=int, default=8501)
    args = parser.parse_args()
    if not all(1 <= port <= 65535 for port in (args.api_port, args.web_port)):
        parser.error("As portas devem estar entre 1 e 65535.")
    if args.api_port == args.web_port:
        parser.error("API e Streamlit devem usar portas diferentes.")

    env = os.environ.copy()
    # Mesmo com bind em 0.0.0.0, o cliente usa o endereço local do serviço.
    api_address = "127.0.0.1" if args.api_host == "0.0.0.0" else args.api_host
    env["SANEAMENTO_API_URL"] = f"http://{api_address}:{args.api_port}"
    commands = [
        ("API", [sys.executable, "-m", "uvicorn", "src.api:app",
                 "--host", args.api_host, "--port", str(args.api_port),
                 "--reload", "--reload-dir", "src"]),
        ("Streamlit", [sys.executable, "-m", "streamlit", "run", "app.py",
                       "--server.address", args.web_host,
                       "--server.port", str(args.web_port),
                       "--server.headless", "true"]),
    ]
    processes = []
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        for name, command in commands:
            if stopping:
                break
            process = subprocess.Popen(command, cwd=PROJECT_ROOT, env=env, start_new_session=True)
            processes.append((name, process))
        print(f"API: {env['SANEAMENTO_API_URL']}/docs", flush=True)
        web_address = "127.0.0.1" if args.web_host == "0.0.0.0" else args.web_host
        print(f"Painel: http://{web_address}:{args.web_port} — Ctrl+C encerra os dois serviços.", flush=True)
        while not stopping:
            for name, process in processes:
                status = process.poll()
                if status is not None:
                    print(f"{name} encerrou (código {status}); encerrando os serviços.", file=sys.stderr)
                    return status if status > 0 else 1
            time.sleep(0.2)
        return 0
    except OSError as exc:
        print(f"Não foi possível iniciar os serviços: {exc}", file=sys.stderr)
        return 1
    finally:
        for _, process in processes:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for _, process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()


if __name__ == "__main__":
    sys.exit(main())
