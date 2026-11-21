"""CLI do assistente financeiro."""
import logging
import sys
from uuid import uuid4

from agent import build_agent, perguntar
from exceptions import ConfigError, ExternalServiceError

AJUDA = """Comandos: /sair  /nova (nova conversa)  /passos (liga/desliga rastro)  /ajuda
Exemplos:
  - Quanto está o dólar hoje?
  - Quanto rendem R$ 5.000 a 1% ao mês por 24 meses?
  - E se fossem 36 meses?
  - Se eu aplicar R$ 10.000 no CDI por 2 anos, quanto terei? E em euros?"""


def main() -> int:
    """Laço da CLI: lê comandos/perguntas e delega ao agente; um thread_id por conversa."""
    try:
        agent = build_agent()
    except ConfigError as e:
        print(f"Erro de configuração: {e}")
        return 1
    thread_id = uuid4().hex
    mostrar_passos = True
    print("💰 Assistente Financeiro (ReAct + memória)\n" + AJUDA + "\n")
    while True:
        try:
            texto = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAté logo!")
            return 0
        if not texto:
            continue
        cmd = texto.lower()
        if cmd == "/sair":
            print("Até logo!")
            return 0
        if cmd == "/ajuda":
            print(AJUDA)
            continue
        if cmd == "/nova":
            thread_id = uuid4().hex
            print("Nova conversa iniciada (memória descartada).")
            continue
        if cmd == "/passos":
            mostrar_passos = not mostrar_passos
            print(f"Rastro {'ligado' if mostrar_passos else 'desligado'}.")
            continue
        try:
            r = perguntar(agent, texto, thread_id)
        except ExternalServiceError as e:
            print(f"Erro: {e}")
            continue
        except Exception:
            logging.exception("Erro inesperado")
            thread_id = uuid4().hex  # evita thread com tool_call sem resposta
            print("Ocorreu um erro inesperado; a conversa foi reiniciada.")
            continue
        if mostrar_passos:
            for p in r.passos:
                print(f"Ação: {p.acao}({p.entrada})")
                print(f"👁 Observação: {p.observacao}")
        print(f"Assistente: {r.texto}\n")


if __name__ == "__main__":
    sys.exit(main())
