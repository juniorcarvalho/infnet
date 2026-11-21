"""Executa os casos de uso com o LLM real (Groq) e gera docs/resultados_casos_de_uso.md."""
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent, perguntar  # noqa: E402

# (id, cenário, [turnos], thread compartilhada com)
CASOS = [
    ("UC1", "Cotação", ["Quanto está o dólar hoje?"], None),
    ("UC2", "Cálculo", ["Quanto rendem R$ 5.000 a 1% ao mês por 24 meses?"], "UC2"),
    ("UC3", "Encadeado (multi-tool)", ["Se eu aplicar R$ 10.000 no CDI por 2 anos, quanto terei? Quanto isso vale em euros?"], None),
    ("UC4", "Memória (follow-up)", ["E se fossem 36 meses?"], "UC2"),
    ("UC5", "Memória (contexto pessoal)", ["Tenho R$ 2.000 guardados.", "Quanto eu teria na Selic em 12 meses?"], None),
    ("UC6", "Erro tratado", ["Qual a cotação da moeda XYZ?"], None),
    ("UC7", "Sem tool", ["O que são juros compostos?"], None),
]


def main() -> None:
    agent = build_agent()
    threads: dict[str, str] = {}
    linhas = ["# Resultados dos casos de uso (LLM real)\n"]
    for uc, nome, turnos, grupo in CASOS:
        chave = grupo or uc
        tid = threads.setdefault(chave, uuid4().hex)
        linhas.append(f"## {uc}: {nome}\n")
        for t in turnos:
            ini = time.time()
            falhou = False
            try:
                r = perguntar(agent, t, tid)
                passos, texto = r.passos, r.texto
            except Exception as e:  # registra a falha como evidência
                passos, texto, falhou = [], f"FALHA: {e}", True
            dur = time.time() - ini
            linhas.append(f"**Pergunta:** {t}\n")
            if passos:
                linhas.append("**Rastro:**\n")
                for p in passos:
                    linhas.append(f"- Ação: `{p.acao}({p.entrada})`\n  - Observação: {p.observacao}")
                linhas.append("")
            else:
                linhas.append("**Rastro:** (nenhuma ferramenta)\n")
            linhas.append(f"**Resposta:** {texto}\n\n*Tempo: {dur:.1f}s*\n")
            print(f"{uc} {'FALHA' if falhou else 'ok'} ({dur:.1f}s)")
    out = ROOT / "docs" / "resultados_casos_de_uso.md"
    out.write_text("\n".join(linhas), encoding="utf-8")
    print(f"Gravado em {out}")


if __name__ == "__main__":
    main()
