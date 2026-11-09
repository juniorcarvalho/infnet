"""Coleta exemplos reais e latencias das APIs locais do TP2.

Uso (com as apps rodando, ver README.md da raiz):

    python docs/benchmark.py            # gera docs/benchmark_results.json
    python docs/benchmark.py p2q2       # mede so as apps indicadas e mescla no JSON existente

Apps que nao estiverem no ar (ou sem OPENAI_API_KEY) sao registradas como
indisponiveis, sem interromper a coleta.
"""

import json
import sys
import statistics
from concurrent.futures import ThreadPoolExecutor
import subprocess
import time
from pathlib import Path

import httpx

DOCS = Path(__file__).resolve().parent
REPEAT = 3
CONCURRENCY = 8

SHORT_EN = "Hello, how are you? I hope you are having a great day."
LONG_EN = " ".join(
    [
        "Artificial intelligence is transforming the way companies build software.",
        "Large language models can generate text, translate documents and answer questions.",
        "However, they also have important limitations regarding accuracy, cost and latency.",
        "Engineers must evaluate these trade-offs carefully before deploying them in production.",
    ]
    * 10
)  # 40 frases, ~3.300 caracteres
IDIOMS = [
    "It's raining cats and dogs.",
    "Break a leg tonight!",
    "That exam was a piece of cake.",
    "He kicked the bucket last year.",
    "Let's call it a day.",
    "I'm feeling under the weather.",
    "That's lit, bro, no cap.",
    "The bank was closed, so we sat on the bank of the river.",
]
GPT2_PROMPTS = [
    "Once upon a time in a small village,",
    "The capital of Brazil is",
    "Artificial intelligence will",
    "The best way to cook rice is",
]

APPS = {
    "p1q1": ("http://127.0.0.1:8001", "/generate"),
    "p1q2": ("http://127.0.0.1:8002", "/translate"),
    "p2q1": ("http://127.0.0.1:8011", "/chat"),
    "p2q2": ("http://127.0.0.1:8012", "/translate"),
    "p2q3": ("http://127.0.0.1:8013", "/translate"),
}
CHAT_QUESTIONS = ["Olá!", "O que é LangChain?", "o que e fastapi", "Qual o horário de atendimento?", "Quanto é 2+2?"]


def rss_mb(port: int) -> float | None:
    """RSS do processo que escuta na porta (Linux, best-effort)."""
    try:
        out = subprocess.run(["ss", "-ltnpH", f"sport = :{port}"], capture_output=True, text=True).stdout
        pid = out.split("pid=")[1].split(",")[0]
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return round(int(line.split()[1]) / 1024, 1)
    except (IndexError, OSError):
        return None
    return None


def timed_post(client: httpx.Client, url: str, payload: dict) -> tuple[float, httpx.Response]:
    start = time.perf_counter()
    response = client.post(url, json=payload)
    return (time.perf_counter() - start) * 1000, response


def median_latency(client: httpx.Client, url: str, payload: dict) -> dict:
    times, last = [], None
    for _ in range(REPEAT):
        ms, last = timed_post(client, url, payload)
        times.append(ms)
    return {
        "median_ms": round(statistics.median(times), 1),
        "min_ms": round(min(times), 1),
        "status": last.status_code,
        "response": last.json(),
    }


def concurrent_throughput(url: str, payload: dict, n: int = CONCURRENCY) -> dict:
    """Dispara n requisicoes simultaneas e mede o tempo total e o throughput."""

    def one(_: int) -> float:
        with httpx.Client(timeout=300) as c:
            ms, response = timed_post(c, url, payload)
            response.raise_for_status()
            return ms

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n) as pool:
        latencies = list(pool.map(one, range(n)))
    wall_s = time.perf_counter() - start
    return {
        "requests": n,
        "wall_ms": round(wall_s * 1000, 1),
        "throughput_rps": round(n / wall_s, 2),
        "median_latency_ms": round(statistics.median(latencies), 1),
        "max_latency_ms": round(max(latencies), 1),
    }


def is_up(client: httpx.Client, base: str) -> bool:
    try:
        return client.get(f"{base}/health").status_code == 200
    except httpx.HTTPError:
        return False


def main(only: list[str]) -> None:
    out_file = DOCS / "benchmark_results.json"
    results: dict = json.loads(out_file.read_text()) if only and out_file.exists() else {}
    with httpx.Client(timeout=300) as client:
        for key, (base, path) in APPS.items():
            if only and key not in only:
                continue
            url = base + path
            port = int(base.rsplit(":", 1)[1])
            if not is_up(client, base):
                results[key] = {"available": False}
                print(f"[{key}] indisponivel")
                continue
            entry: dict = {"available": True, "health": client.get(f"{base}/health").json()}
            print(f"[{key}] coletando...")
            if key == "p1q1":
                entry["examples"] = [
                    client.post(url, json={"prompt": p, "max_new_tokens": 40, "seed": 42}).json()
                    for p in GPT2_PROMPTS
                ]
                entry["latency_20_tokens"] = median_latency(client, url, {"prompt": GPT2_PROMPTS[0], "max_new_tokens": 20})
                entry["latency_100_tokens"] = median_latency(client, url, {"prompt": GPT2_PROMPTS[0], "max_new_tokens": 100})
                entry["latency_200_tokens"] = median_latency(client, url, {"prompt": GPT2_PROMPTS[0], "max_new_tokens": 200})
                entry["concurrent_50_tokens"] = concurrent_throughput(url, {"prompt": GPT2_PROMPTS[0], "max_new_tokens": 50})
            elif key == "p2q1":
                entry["examples"] = [client.post(url, json={"message": q}).json() for q in CHAT_QUESTIONS]
                entry["latency"] = median_latency(client, url, {"message": "O que é LangChain?"})
            else:
                first_ms, first = timed_post(client, url, {"text": SHORT_EN})
                if first.status_code != 200:
                    entry.update(available=False, status=first.status_code, detail=first.json())
                    results[key] = entry
                    print(f"[{key}] erro {first.status_code}: {first.json()}")
                    continue
                entry["first_call_short_ms"] = round(first_ms, 1)
                entry["short"] = median_latency(client, url, {"text": SHORT_EN})
                entry["long"] = median_latency(client, url, {"text": LONG_EN})
                entry["long"]["source_chars"] = len(LONG_EN)
                entry["long"]["response"]["source_text"] = entry["long"]["response"]["source_text"][:120] + "..."
                cached_ms, _ = timed_post(client, url, {"text": SHORT_EN})
                entry["repeat_short_ms"] = round(cached_ms, 1)
                entry["concurrent_short"] = concurrent_throughput(url, {"text": SHORT_EN})
                entry["idioms"] = [
                    {"en": s, "out": client.post(url, json={"text": s}).json()["translated_text"]} for s in IDIOMS
                ]
            entry["rss_mb"] = rss_mb(port)
            results[key] = entry

    out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Resultados em {out_file}")


if __name__ == "__main__":
    main(sys.argv[1:])
