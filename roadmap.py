"""Análise de gaps e geração de roadmap personalizado (Fase 3).

Cruza a trilha escolhida com o conhecimento atual do usuário (0 a 3 por habilidade) e
mostra o que falta para o nível Júnior, em que ordem estudar, quais certificações buscar
e que projetos colocar no portfólio do GitHub.
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
    prioridade: int

    @property
    def lacuna(self) -> int:
        return max(0, self.requerido - self.atual)


@dataclass
class Roadmap:
    trilha: str
    nome_trilha: str
    prontidao_pct: float  # quanto do nível Júnior já foi atingido
    gaps: list  # só habilidades com lacuna, na ordem de estudo
    atingidas: list  # habilidades que já atendem o nível Júnior
    horas_totais: int
    semanas: int
    fases: list = field(default_factory=list)  # [(titulo, [Gap])]
    certificacoes: list = field(default_factory=list)
    projetos: list = field(default_factory=list)


def habilidades_da_trilha(trilha: str, base: dict = None) -> list:
    """Habilidades exigidas para Júnior na trilha, na ordem de prioridade."""
    base = base or base_padrao()
    itens = sorted(base["roadmap"][trilha]["junior"], key=lambda i: i["prioridade"])
    return [dict(id=i["habilidade"], nome=base["habilidades"][i["habilidade"]]["nome"],
                 requerido=i["nivel"]) for i in itens]


def analisar_gaps(trilha: str, conhecimento: dict, base: dict = None) -> list:
    """Devolve um Gap por habilidade exigida, na ordem de prioridade (inclusive as já atendidas).

    `conhecimento` mapeia id da habilidade para 0..3; habilidade ausente conta como 0.
    """
    base = base or base_padrao()
    if trilha not in base["roadmap"]:
        raise ValueError(f"Trilha desconhecida: {trilha}")
    maximo = max(int(k) for k in base["niveis_conhecimento"])
    gaps = []
    for item in sorted(base["roadmap"][trilha]["junior"], key=lambda i: i["prioridade"]):
        hid = item["habilidade"]
        atual = conhecimento.get(hid, 0)
        if isinstance(atual, bool) or not isinstance(atual, int) or not 0 <= atual <= maximo:
            raise ValueError(f"Nível inválido para '{hid}': {atual!r} (use 0 a {maximo})")
        hab = base["habilidades"][hid]
        gaps.append(Gap(hid, hab["nome"], hab["estudar"], atual, item["nivel"], item["prioridade"]))
    return gaps


def gerar_roadmap(trilha: str, conhecimento: dict, experiencia: str = "estudante",
                  horas_semana: int = 5, base: dict = None) -> Roadmap:
    base = base or base_padrao()
    if horas_semana <= 0:
        raise ValueError("horas_semana deve ser positivo")
    exp = base["perfil"]["experiencia"].get(experiencia)
    if exp is None:
        raise ValueError(f"Experiência desconhecida: {experiencia}")

    todas = analisar_gaps(trilha, conhecimento, base)
    gaps = [g for g in todas if g.lacuna > 0]
    atingidas = [g for g in todas if g.lacuna == 0]

    exigido = sum(g.requerido for g in todas)
    possuido = sum(min(g.atual, g.requerido) for g in todas)
    prontidao = round(possuido / exigido * 100, 1) if exigido else 100.0

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
    # Quem já tem experiência recebe projetos intermediários primeiro, mas sempre vê os dois níveis.
    pref = exp["projetos"]
    projetos = sorted(rm["projetos"], key=lambda p: 0 if p["nivel"] == pref else 1)

    return Roadmap(
        trilha=trilha, nome_trilha=base["trilhas"][trilha]["nome"],
        prontidao_pct=prontidao, gaps=gaps, atingidas=atingidas,
        horas_totais=horas, semanas=semanas, fases=fases,
        certificacoes=list(rm["certificacoes"]), projetos=projetos,
    )


def roadmap_para_markdown(rm: Roadmap, nome_usuario: str = "") -> str:
    """Plano de ação em Markdown, pronto para baixar ou colar no README do GitHub."""
    saudacao = f" de {nome_usuario}" if nome_usuario else ""
    linhas = [f"# Plano de ação{saudacao}: {rm.nome_trilha}", "",
              f"- Prontidão para Júnior: **{rm.prontidao_pct:.0f}%**",
              f"- Esforço estimado: **{rm.horas_totais} h** (cerca de **{rm.semanas} semanas**)", ""]
    if rm.fases:
        linhas.append("## O que estudar, em ordem")
        for titulo, gaps in rm.fases:
            linhas += ["", f"### {titulo}", ""]
            for g in gaps:
                linhas.append(f"- **{g.nome}** (nível {g.atual} → {g.requerido}): {g.estudar}")
    else:
        linhas.append("Você já atende todos os requisitos de Júnior desta trilha.")
    if rm.atingidas:
        linhas += ["", "## Já atingido", ""] + [f"- {g.nome}" for g in rm.atingidas]
    linhas += ["", "## Certificações", ""]
    linhas += [f"- {c['nome']} ({c['nivel']})" for c in rm.certificacoes]
    linhas += ["", "## Projetos para o portfólio no GitHub", ""]
    linhas += [f"- **{p['titulo']}** ({p['nivel']}): {p['descricao']}" for p in rm.projetos]
    return "\n".join(linhas) + "\n"
