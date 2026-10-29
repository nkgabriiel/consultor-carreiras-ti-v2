"""Carregamento e validação da base de conhecimento (regras_carreiras.json).

Todo o conhecimento do sistema (perguntas, pesos, penalidades, habilidades e roadmaps)
mora no JSON. Este módulo só lê o arquivo e garante que ele é consistente, para que um
erro de digitação na base falhe na carga e não no meio de uma consulta.
"""

import json
from functools import lru_cache
from pathlib import Path

CAMINHO_PADRAO = Path(__file__).with_name("regras_carreiras.json")
OPERADORES = ("<=", ">=", "==", "<", ">")


class BaseInvalida(ValueError):
    """O arquivo de regras existe, mas está inconsistente."""


def carregar_base(caminho=None) -> dict:
    """Lê o JSON, valida e devolve a base como dict."""
    caminho = Path(caminho) if caminho else CAMINHO_PADRAO
    with open(caminho, encoding="utf-8") as f:
        base = json.load(f)
    validar_base(base)
    return base


@lru_cache(maxsize=1)
def base_padrao() -> dict:
    """Base padrão em cache (não modifique o dict retornado)."""
    return carregar_base()


def validar_base(base: dict) -> None:
    erros = []
    for secao in ("escala_likert", "classificacao", "perfil", "perguntas", "trilhas",
                  "regras_combinadas", "habilidades", "niveis_conhecimento", "roadmap"):
        if secao not in base:
            erros.append(f"seção ausente: {secao}")
    if erros:
        raise BaseInvalida("; ".join(erros))

    ids_perguntas = [p["id"] for p in base["perguntas"]]
    if len(set(ids_perguntas)) != len(ids_perguntas):
        erros.append("ids de perguntas duplicados")
    for p in base["perguntas"]:
        if p.get("etapa") not in ("afinidades", "objetivos"):
            erros.append(f"pergunta {p['id']}: etapa inválida {p.get('etapa')!r}")

    trilhas = base["trilhas"]
    if len(trilhas) != 10:
        erros.append(f"o escopo exige 10 trilhas, a base tem {len(trilhas)}")

    for chave, t in trilhas.items():
        positivos = 0
        for qid, peso in t["pesos"].items():
            if qid not in ids_perguntas:
                erros.append(f"trilha {chave}: peso para pergunta inexistente {qid!r}")
            if not isinstance(peso, (int, float)) or not -5 <= peso <= 5:
                erros.append(f"trilha {chave}: peso fora de -5..5 em {qid!r}")
            elif peso > 0:
                positivos += peso
        if positivos <= 0:
            erros.append(f"trilha {chave}: não tem nenhum peso positivo")

    for r in base["regras_combinadas"]:
        if r.get("tipo") not in ("penalidade", "sinergia"):
            erros.append(f"regra {r.get('id')}: tipo inválido")
        for cond in r["se"]:
            qid, op, valor = cond
            if qid not in ids_perguntas:
                erros.append(f"regra {r['id']}: pergunta inexistente {qid!r}")
            if op not in OPERADORES:
                erros.append(f"regra {r['id']}: operador inválido {op!r}")
            if not base["escala_likert"]["min"] <= valor <= base["escala_likert"]["max"]:
                erros.append(f"regra {r['id']}: valor fora da escala em {cond}")
        for trilha in r["ajustes"]:
            if trilha not in trilhas:
                erros.append(f"regra {r['id']}: trilha inexistente {trilha!r}")

    for chave in trilhas:
        if chave not in base["roadmap"]:
            erros.append(f"roadmap ausente para a trilha {chave}")
            continue
        rm = base["roadmap"][chave]
        for item in rm["junior"]:
            if item["habilidade"] not in base["habilidades"]:
                erros.append(f"roadmap {chave}: habilidade inexistente {item['habilidade']!r}")
            if str(item["nivel"]) not in base["niveis_conhecimento"]:
                erros.append(f"roadmap {chave}: nível inválido em {item['habilidade']!r}")
        if not rm["certificacoes"] or not rm["projetos"]:
            erros.append(f"roadmap {chave}: faltam certificações ou projetos")
        for proj in rm["projetos"]:
            if proj["nivel"] not in ("basico", "intermediario"):
                erros.append(f"roadmap {chave}: nível de projeto inválido {proj['nivel']!r}")

    for exp, dados in base["perfil"]["experiencia"].items():
        if dados["projetos"] not in ("basico", "intermediario"):
            erros.append(f"experiência {exp}: nível de projeto inválido")

    if erros:
        raise BaseInvalida("; ".join(erros))
