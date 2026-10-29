"""Motor de inferência por pontuação ponderada com tratamento de incerteza.

Como funciona (tudo que é conhecimento vem do JSON, nada está fixo aqui):

1. Cada resposta Likert (1 a 5) vira um grau de afinidade em [0, 1]:  (r - 1) / 4.
2. Pontos da trilha = soma de  grau × peso  sobre todas as perguntas. Pesos negativos
   descontam pontos quando o usuário tem muita afinidade com algo que conflita com a trilha.
3. Aderência base (%) = pontos / máximo possível da trilha (soma dos pesos positivos),
   ou seja, 100% é o perfil que respondeu 5 em tudo o que a trilha valoriza.
4. Regras combinadas ajustam o percentual em pontos percentuais (pp): penalidades para
   perfis conflitantes (ex.: "não gosto de código" derruba as trilhas de desenvolvimento)
   e sinergias para combinações típicas (ex.: infra alta + automação alta reforça DevOps).
5. O resultado final é limitado a [0, 100] e ordenado em ranking.
"""

import operator
from dataclasses import dataclass, field

from base_conhecimento import base_padrao

_OPS = {"<=": operator.le, ">=": operator.ge, "==": operator.eq,
        "<": operator.lt, ">": operator.gt}


class RespostasInvalidas(ValueError):
    """Respostas faltando ou fora da escala."""


@dataclass
class Contribuicao:
    pergunta: str
    texto: str
    resposta: int
    peso: float
    pontos: float  # grau × peso (pode ser negativo)


@dataclass
class Ajuste:
    regra: str
    tipo: str  # "penalidade" ou "sinergia"
    pp: float
    motivo: str


@dataclass
class ResultadoTrilha:
    chave: str
    nome: str
    descricao: str
    pontos: float
    maximo: float
    base_pct: float  # aderência antes das regras combinadas
    percentual: float  # aderência final, limitada a [0, 100]
    contribuicoes: list = field(default_factory=list)
    ajustes: list = field(default_factory=list)


@dataclass
class Diagnostico:
    ranking: list  # list[ResultadoTrilha], da maior para a menor aderência
    top3: list
    inconclusivo: bool  # aderência máxima abaixo do limiar: respostas pouco informativas
    empate_parcial: bool  # 1ª e 2ª dentro da tolerância
    empatadas: list  # nomes das trilhas dentro da tolerância da 1ª colocada
    regras_disparadas: list  # ids de todas as regras combinadas que dispararam
    confianca: str  # "alta", "média" ou "baixa"
    margem_pp: float


def validar_respostas(respostas: dict, base: dict = None) -> None:
    base = base or base_padrao()
    lo, hi = base["escala_likert"]["min"], base["escala_likert"]["max"]
    faltando = [p["id"] for p in base["perguntas"] if p["id"] not in respostas]
    if faltando:
        raise RespostasInvalidas(f"Respostas faltando: {', '.join(faltando)}")
    ids = {p["id"] for p in base["perguntas"]}
    for qid, valor in respostas.items():
        if qid not in ids:
            raise RespostasInvalidas(f"Pergunta desconhecida: {qid}")
        if isinstance(valor, bool) or not isinstance(valor, int) or not lo <= valor <= hi:
            raise RespostasInvalidas(f"Valor inválido para '{qid}': {valor!r} (use inteiros de {lo} a {hi})")


def _grau(resposta: int, base: dict) -> float:
    lo, hi = base["escala_likert"]["min"], base["escala_likert"]["max"]
    return (resposta - lo) / (hi - lo)


def _regra_dispara(regra: dict, respostas: dict) -> bool:
    return all(_OPS[op](respostas[qid], valor) for qid, op, valor in regra["se"])


def calcular_ranking(respostas: dict, base: dict = None) -> Diagnostico:
    """Calcula a compatibilidade (%) das 10 trilhas e devolve o diagnóstico completo."""
    base = base or base_padrao()
    validar_respostas(respostas, base)

    textos = {p["id"]: p["texto"] for p in base["perguntas"]}
    disparadas = [r for r in base["regras_combinadas"] if _regra_dispara(r, respostas)]

    resultados = []
    for chave, t in base["trilhas"].items():
        contribs = []
        for qid, peso in t["pesos"].items():
            contribs.append(Contribuicao(qid, textos[qid], respostas[qid], peso,
                                         round(_grau(respostas[qid], base) * peso, 4)))
        pontos = sum(c.pontos for c in contribs)
        maximo = sum(p for p in t["pesos"].values() if p > 0)
        base_pct = max(0.0, pontos / maximo * 100)

        ajustes = [Ajuste(r["id"], r["tipo"], r["ajustes"][chave], r["motivo"])
                   for r in disparadas if chave in r["ajustes"]]
        final = min(100.0, max(0.0, base_pct + sum(a.pp for a in ajustes)))

        resultados.append(ResultadoTrilha(
            chave=chave, nome=t["nome"], descricao=t["descricao"],
            pontos=round(pontos, 2), maximo=maximo,
            base_pct=round(base_pct, 1), percentual=round(final, 1),
            contribuicoes=sorted(contribs, key=lambda c: -c.pontos), ajustes=ajustes))

    # Desempate: maior aderência, depois maior pontuação bruta, depois a ordem da base.
    ordem = {k: i for i, k in enumerate(base["trilhas"])}
    resultados.sort(key=lambda r: (-r.percentual, -r.pontos, ordem[r.chave]))

    cls = base["classificacao"]
    topo, segundo = resultados[0], resultados[1]
    margem = round(topo.percentual - segundo.percentual, 1)
    empatadas = [r.nome for r in resultados
                 if topo.percentual - r.percentual <= cls["limiar_empate_parcial_pp"]]
    if margem >= 10:
        confianca = "alta"
    elif margem > cls["limiar_empate_parcial_pp"]:
        confianca = "média"
    else:
        confianca = "baixa"

    return Diagnostico(
        ranking=resultados,
        top3=resultados[:3],
        inconclusivo=topo.percentual < cls["limiar_inconclusivo_pct"],
        empate_parcial=len(empatadas) > 1,
        empatadas=empatadas,
        regras_disparadas=[r["id"] for r in disparadas],
        confianca=confianca,
        margem_pp=margem,
    )


def justificar(resultado: ResultadoTrilha, n: int = 3) -> list:
    """Frases curtas explicando por que a trilha pontuou como pontuou."""
    frases = []
    favor = [c for c in resultado.contribuicoes if c.pontos > 0][:n]
    for c in favor:
        frases.append(f"**{c.texto}** (resposta {c.resposta}/5, peso {c.peso:+g}) "
                      f"somou {c.pontos:+.1f} pontos.")
    for c in sorted((c for c in resultado.contribuicoes if c.pontos < 0), key=lambda c: c.pontos):
        frases.append(f"**{c.texto}** (resposta {c.resposta}/5, peso {c.peso:+g}) "
                      f"descontou {abs(c.pontos):.1f} pontos.")
    for a in resultado.ajustes:
        sinal = "Penalidade" if a.tipo == "penalidade" else "Sinergia"
        frases.append(f"{sinal} {a.regra} ({a.pp:+g} pp): {a.motivo}.")
    return frases


def explicar_empate(diag: Diagnostico) -> str:
    """Texto para perfis ambíguos: quais trilhas estão praticamente empatadas e por quê."""
    if not diag.empate_parcial:
        return ""
    a, b = diag.top3[0], diag.top3[1]
    comuns = [c.texto for c in a.contribuicoes
              if c.pontos > 0 and any(o.pergunta == c.pergunta and o.pontos > 0 for o in b.contribuicoes)][:2]
    nomes = ", ".join(n.split(" (")[0] for n in diag.empatadas[:3])
    if len(diag.empatadas) > 3:
        nomes += f" e mais {len(diag.empatadas) - 3}"
    folga = diag.ranking[0].percentual - diag.ranking[len(diag.empatadas) - 1].percentual
    base = f"Perfil misto: {nomes} estão a até {folga:.1f} pp da primeira colocada."
    if comuns:
        base += " Respostas que puxam as duas para cima: " + "; ".join(f"“{t}”" for t in comuns) + "."
    return base + " Vale explorar as duas trilhas antes de decidir."


def matriz_pesos(base: dict = None):
    """Matriz de pesos (perguntas × trilhas) como DataFrame do pandas."""
    import pandas as pd

    base = base or base_padrao()
    linhas = {p["id"]: {t["nome"]: t["pesos"].get(p["id"], 0) for t in base["trilhas"].values()}
              for p in base["perguntas"]}
    return pd.DataFrame.from_dict(linhas, orient="index")


if __name__ == "__main__":
    print(matriz_pesos().to_string())
