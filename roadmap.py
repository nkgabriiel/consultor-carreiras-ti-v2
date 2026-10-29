"""Análise de gaps e geração de roadmap personalizado (Fase 3).

Cruza a trilha escolhida com o conhecimento atual do usuário (0 a 3 por habilidade) e
mostra o que falta para o nível-alvo (Júnior, Pleno ou Sênior), em que ordem estudar, quais
certificações buscar e que projetos colocar no portfólio do GitHub.

Os requisitos são cumulativos: quem mira Pleno precisa de tudo o que se exige de Júnior (com o
nível mais alto, quando o JSON o eleva) mais as habilidades novas do Pleno. Idem para Sênior.
"""

import math
from dataclasses import dataclass, field

from base_conhecimento import base_padrao


@dataclass
class Gap:
    habilidade: str
    nome: str
    estudar: str
    atual: int
    requerido: int
    prioridade: int  # posição na ordem de estudo (1 = estudar primeiro)
    desde: str = "junior"  # nível de carreira em que a habilidade passa a ser exigida

    @property
    def lacuna(self) -> int:
        return max(0, self.requerido - self.atual)


@dataclass
class Roadmap:
    trilha: str
    nome_trilha: str
    nivel: str  # nível-alvo: "junior", "pleno" ou "senior"
    rotulo_nivel: str
    experiencia_tipica: str
    prontidao_pct: float  # quanto do nível-alvo já foi atingido
    gaps: list  # só habilidades com lacuna, na ordem de estudo
    atingidas: list  # habilidades que já atendem o nível-alvo
    horas_totais: int
    semanas: int
    fases: list = field(default_factory=list)  # [(titulo, [Gap])]
    certificacoes: list = field(default_factory=list)
    projetos: list = field(default_factory=list)


def _validar_nivel(nivel: str, base: dict) -> None:
    if nivel not in base["niveis_carreira"]:
        raise ValueError(f"Nível desconhecido: {nivel!r} (use {', '.join(base['niveis_carreira'])})")


def habilidades_da_trilha(trilha: str, nivel: str = "junior", base: dict = None) -> list:
    """Habilidades exigidas até o nível informado, na ordem de estudo.

    Cada item: id, nome, estudar, requerido (maior nível exigido até aqui), desde (nível em que
    a habilidade apareceu pela primeira vez) e prioridade (posição na ordem de estudo).
    """
    base = base or base_padrao()
    if trilha not in base["roadmap"]:
        raise ValueError(f"Trilha desconhecida: {trilha}")
    _validar_nivel(nivel, base)

    niveis = list(base["niveis_carreira"])
    acumulado = {}
    for n in niveis[: niveis.index(nivel) + 1]:
        for item in sorted(base["roadmap"][trilha][n], key=lambda i: i["prioridade"]):
            hid = item["habilidade"]
            if hid in acumulado:
                acumulado[hid]["requerido"] = max(acumulado[hid]["requerido"], item["nivel"])
            else:
                acumulado[hid] = dict(id=hid, requerido=item["nivel"], desde=n,
                                      ordem=(niveis.index(n), item["prioridade"]))
    ordenadas = sorted(acumulado.values(), key=lambda h: h["ordem"])
    for posicao, h in enumerate(ordenadas, start=1):
        hab = base["habilidades"][h["id"]]
        h.update(nome=hab["nome"], estudar=hab["estudar"], prioridade=posicao)
        del h["ordem"]
    return ordenadas


def analisar_gaps(trilha: str, conhecimento: dict, nivel: str = "junior", base: dict = None) -> list:
    """Devolve um Gap por habilidade exigida, na ordem de estudo (inclusive as já atendidas).

    `conhecimento` mapeia id da habilidade para 0..3; habilidade ausente conta como 0.
    """
    base = base or base_padrao()
    maximo = max(int(k) for k in base["niveis_conhecimento"])
    gaps = []
    for h in habilidades_da_trilha(trilha, nivel, base):
        atual = conhecimento.get(h["id"], 0)
        if isinstance(atual, bool) or not isinstance(atual, int) or not 0 <= atual <= maximo:
            raise ValueError(f"Nível inválido para '{h['id']}': {atual!r} (use 0 a {maximo})")
        gaps.append(Gap(h["id"], h["nome"], h["estudar"], atual, h["requerido"], h["prioridade"], h["desde"]))
    return gaps


def _prontidao(gaps: list) -> float:
    exigido = sum(g.requerido for g in gaps)
    possuido = sum(min(g.atual, g.requerido) for g in gaps)
    return round(possuido / exigido * 100, 1) if exigido else 100.0


def prontidao_por_nivel(trilha: str, conhecimento: dict, base: dict = None) -> dict:
    """Prontidão (%) para cada nível de carreira, do Júnior ao Sênior."""
    base = base or base_padrao()
    return {n: _prontidao(analisar_gaps(trilha, conhecimento, n, base)) for n in base["niveis_carreira"]}


def gerar_roadmap(trilha: str, conhecimento: dict, experiencia: str = "estudante",
                  horas_semana: int = 5, nivel: str = "junior", base: dict = None) -> Roadmap:
    base = base or base_padrao()
    if horas_semana <= 0:
        raise ValueError("horas_semana deve ser positivo")
    exp = base["perfil"]["experiencia"].get(experiencia)
    if exp is None:
        raise ValueError(f"Experiência desconhecida: {experiencia}")

    todas = analisar_gaps(trilha, conhecimento, nivel, base)
    gaps = [g for g in todas if g.lacuna > 0]
    atingidas = [g for g in todas if g.lacuna == 0]

    horas_nivel = {int(k): v for k, v in base["perfil"]["horas_por_nivel"].items()}
    horas = sum(horas_nivel[g.requerido] - horas_nivel[g.atual] for g in gaps)
    horas = math.ceil(horas * exp["fator_tempo"])
    semanas = math.ceil(horas / horas_semana) if horas else 0

    fases = []
    if gaps:
        fundamentos = [g for g in gaps if g.atual == 0]
        reforco = [g for g in gaps if g.atual > 0]
        if fundamentos:
            fases.append(("Fase 1 - Comece por aqui (ainda não estudou)", fundamentos))
        if reforco:
            fases.append((f"Fase {len(fases) + 1} - Reforce o que você já conhece", reforco))

    rm = base["roadmap"][trilha]
    carreira = base["niveis_carreira"][nivel]
    certificacoes = [c for c in rm["certificacoes"] if c["nivel"] in carreira["certificacoes"]]
    # Quem já tem experiência recebe projetos intermediários primeiro, mas sempre vê todos os do nível.
    pref = exp["projetos"]
    projetos = sorted((p for p in rm["projetos"] if p["nivel"] in carreira["projetos"]),
                      key=lambda p: 0 if p["nivel"] == pref else 1)

    return Roadmap(
        trilha=trilha, nome_trilha=base["trilhas"][trilha]["nome"],
        nivel=nivel, rotulo_nivel=carreira["rotulo"], experiencia_tipica=carreira["experiencia_tipica"],
        prontidao_pct=_prontidao(todas), gaps=gaps, atingidas=atingidas,
        horas_totais=horas, semanas=semanas, fases=fases,
        certificacoes=certificacoes, projetos=projetos,
    )


def roadmap_para_markdown(rm: Roadmap, nome_usuario: str = "") -> str:
    """Plano de ação em Markdown, pronto para baixar ou colar no README do GitHub."""
    saudacao = f" de {nome_usuario}" if nome_usuario else ""
    linhas = [f"# Plano de ação{saudacao}: {rm.nome_trilha} ({rm.rotulo_nivel})", "",
              f"- Nível-alvo: **{rm.rotulo_nivel}** (experiência típica: {rm.experiencia_tipica})",
              f"- Prontidão para {rm.rotulo_nivel}: **{rm.prontidao_pct:.0f}%**",
              f"- Esforço estimado de estudo: **{rm.horas_totais} h** (cerca de **{rm.semanas} semanas**)", ""]
    if rm.nivel != "junior":
        linhas += [f"> Estas horas cobrem só o estudo. Chegar a {rm.rotulo_nivel} também exige experiência "
                   f"prática, em geral {rm.experiencia_tipica}.", ""]
    if rm.fases:
        linhas.append("## O que estudar, em ordem")
        for titulo, gaps in rm.fases:
            linhas += ["", f"### {titulo}", ""]
            for g in gaps:
                linhas.append(f"- **{g.nome}** (nível {g.atual} → {g.requerido}): {g.estudar}")
    else:
        linhas.append(f"Você já atende todos os requisitos de {rm.rotulo_nivel} desta trilha.")
    if rm.atingidas:
        linhas += ["", "## Já atingido", ""] + [f"- {g.nome}" for g in rm.atingidas]
    linhas += ["", "## Certificações", ""]
    linhas += [f"- {c['nome']} ({c['nivel']})" for c in rm.certificacoes]
    linhas += ["", "## Projetos para o portfólio no GitHub", ""]
    linhas += [f"- **{p['titulo']}** ({p['nivel']}): {p['descricao']}" for p in rm.projetos]
    return "\n".join(linhas) + "\n"
