"""Motor de inferência do Consultor Inteligente de Carreiras em TI.

Base de conhecimento com 25 regras (Experta, encadeamento para frente):

* R01-R02: regras de DERIVAÇÃO (estágio 1). Cruzam várias respostas e declaram
  um fato intermediário `Inferido(perfil=...)`.
* R03-R25: regras de PONTUAÇÃO (estágio 2). Cada uma soma (ou subtrai) pontos
  de uma ou mais trilhas e registra o motivo. Algumas leem fatos inferidos, o
  que é o encadeamento para frente de fato (fato -> fato -> conclusão).

A trilha recomendada é a de maior pontuação. Desempate: (1) maior peso de uma
única regra, (2) ordem das trilhas em `perguntas.ORDEM_TRILHAS`.
"""

# --- Patch de compatibilidade -------------------------------------------------
# Experta 1.9.x depende de frozendict 1.2, que usa `collections.Mapping`, removido
# no Python 3.10. Este patch precisa rodar ANTES de `import experta`.
import collections
import collections.abc

for _nome in ("Mapping", "MutableMapping", "Sequence", "Iterable", "Callable"):
    if not hasattr(collections, _nome):
        setattr(collections, _nome, getattr(collections.abc, _nome))
# ------------------------------------------------------------------------------

from dataclasses import dataclass, field

from experta import KnowledgeEngine, Fact, Rule, L

from perguntas import TRILHAS, ORDEM_TRILHAS, CHAVES, OPCOES_VALIDAS


class Perfil(Fact):
    """Respostas do usuário (um único fato com todos os campos da entrevista)."""


class Inferido(Fact):
    """Fatos derivados por regras do estágio 1 (ex.: perfil científico)."""


# Tabela de decisão (Fase 1). A condição é a descrição legível; a condição
# executável está no decorador @Rule do método correspondente em MotorCarreira.
REGRAS = {
    "R01": dict(
        condicao="matemática = alta E dados = modelar",
        efeitos={},
        derivada="perfil científico",
        motivo="Matemática alta somada ao interesse em modelagem indica perfil científico",
    ),
    "R02": dict(
        condicao="atuação em {servidores, automação, nuvem} E entrega = infraestrutura",
        efeitos={},
        derivada="perfil de infraestrutura",
        motivo="Atuação com servidores/automação/nuvem voltada à infraestrutura indica perfil de infra",
    ),
    "R03": dict(
        condicao="atuação = algoritmos",
        efeitos={"backend": 3},
        motivo="Prefere escrever algoritmos lógicos e regras de negócio",
    ),
    "R04": dict(
        condicao="atuação = servidores E entrega = produto para o usuário",
        efeitos={"backend": 4},
        motivo="Quer lidar com servidores para entregar um produto que o usuário usa (APIs e regras de negócio)",
    ),
    "R05": dict(
        condicao="linguagem em {Java/C#/Go, SQL} E dados = não E visual = não",
        efeitos={"backend": 2},
        motivo="Afinidade com linguagem/banco típicos de back-end, sem foco em dados analíticos nem em telas",
    ),
    "R06": dict(
        condicao="atuação = layouts",
        efeitos={"frontend": 4},
        motivo="Prefere criar layouts visuais e interfaces",
    ),
    "R07": dict(
        condicao="visual = sim E entrega = produto para o usuário",
        efeitos={"frontend": 3},
        motivo="Valoriza aparência e usabilidade e quer entregar o produto final ao usuário",
    ),
    "R08": dict(
        condicao="[fato inferido] perfil científico",
        efeitos={"ciencia_dados": 5, "eng_dados": -2},
        motivo="Perfil científico (matemática alta + modelagem) aponta para Ciência de Dados, não para engenharia de pipelines",
    ),
    "R09": dict(
        condicao="atuação = dados brutos E dados = modelar",
        efeitos={"ciencia_dados": 3},
        motivo="Gosta de analisar dados brutos com foco em modelos preditivos",
    ),
    "R10": dict(
        condicao="matemática = baixa E dados = modelar",
        efeitos={"ciencia_dados": -3},
        motivo="Modelagem preditiva exige base matemática/estatística, que está baixa",
    ),
    "R11": dict(
        condicao="dados = pipelines E atuação em {dados brutos, servidores}",
        efeitos={"eng_dados": 5},
        motivo="Quer construir pipelines de dados lidando com dados brutos e servidores",
    ),
    "R12": dict(
        condicao="dados = pipelines E matemática em {baixa, média}",
        efeitos={"eng_dados": 2, "ciencia_dados": -2},
        motivo="Foco em pipelines sem exigência de matemática avançada distingue Eng. de Dados de Cientista de Dados",
    ),
    "R13": dict(
        condicao="atuação = segurança",
        efeitos={"ciberseguranca": 5},
        motivo="Quer trabalhar garantindo segurança e encontrando vulnerabilidades",
    ),
    "R14": dict(
        condicao="entrega = segurança",
        efeitos={"ciberseguranca": 3},
        motivo="O valor que prefere entregar é a segurança contra invasões",
    ),
    "R15": dict(
        condicao="atuação = automação E automatiza = sim",
        efeitos={"devops": 5},
        motivo="Gosta de automatizar build, deploy e operação",
    ),
    "R16": dict(
        condicao="linguagem = Linux/Redes E automatiza = sim",
        efeitos={"devops": 3},
        motivo="Afinidade com Linux/redes e gosto por automação são a base de DevOps/SRE",
    ),
    "R17": dict(
        condicao="[fato inferido] perfil de infra E nuvem = não",
        efeitos={"devops": 3},
        motivo="Perfil de infraestrutura sem foco em provedores de nuvem tende a DevOps/SRE",
    ),
    "R18": dict(
        condicao="atuação = arquitetura em nuvem",
        efeitos={"cloud": 5},
        motivo="Quer desenhar e dimensionar infraestrutura na nuvem",
    ),
    "R19": dict(
        condicao="[fato inferido] perfil de infra E nuvem = sim",
        efeitos={"cloud": 4},
        motivo="Perfil de infraestrutura com interesse em AWS/Azure/GCP aponta para Cloud Architecture",
    ),
    "R20": dict(
        condicao="atuação = apps para celular",
        efeitos={"mobile": 5},
        motivo="Quer construir aplicativos para celular",
    ),
    "R21": dict(
        condicao="linguagem = Dart/Kotlin/Swift E entrega = produto para o usuário",
        efeitos={"mobile": 3},
        motivo="Domina linguagem de mobile e quer entregar o produto final ao usuário",
    ),
    "R22": dict(
        condicao="atuação = testes",
        efeitos={"qa": 5},
        motivo="Prefere testar software e caçar defeitos",
    ),
    "R23": dict(
        condicao="entrega = qualidade",
        efeitos={"qa": 4},
        motivo="O valor que prefere entregar é a confiança de que o software funciona",
    ),
    "R24": dict(
        condicao="atuação = produto",
        efeitos={"produto": 5},
        motivo="Quer definir o que construir e priorizar o trabalho do time",
    ),
    "R25": dict(
        condicao="interação = sim E entrega = decisão de negócio",
        efeitos={"produto": 4},
        motivo="Gosta de conversar com negócio e entregar decisões bem fundamentadas",
    ),
}


class MotorCarreira(KnowledgeEngine):
    """Base de conhecimento. Crie uma instância NOVA a cada consulta."""

    def __init__(self):
        super().__init__()
        self.pontos = {t: 0 for t in ORDEM_TRILHAS}
        self.maior_peso = {t: 0 for t in ORDEM_TRILHAS}
        self.disparadas = []  # ordem de disparo

    # -- utilitários -------------------------------------------------------
    def _registrar(self, rid):
        info = REGRAS[rid]
        for trilha, delta in info["efeitos"].items():
            self.pontos[trilha] += delta
            if delta > self.maior_peso[trilha]:
                self.maior_peso[trilha] = delta
        self.disparadas.append({
            "id": rid,
            "condicao": info["condicao"],
            "efeitos": dict(info["efeitos"]),
            "motivo": info["motivo"],
            "derivada": info.get("derivada"),
        })

    # -- estágio 1: derivação ---------------------------------------------
    @Rule(Perfil(matematica="alta", dados="modelar"))
    def r01_perfil_cientifico(self):
        self._registrar("R01")
        self.declare(Inferido(perfil="cientifico"))

    @Rule(Perfil(atuacao=L("servidores") | L("automacao") | L("arquitetura_nuvem"),
                 entrega="infraestrutura"))
    def r02_perfil_infra(self):
        self._registrar("R02")
        self.declare(Inferido(perfil="infra"))

    # -- Back-end ----------------------------------------------------------
    @Rule(Perfil(atuacao="algoritmos"))
    def r03(self):
        self._registrar("R03")

    @Rule(Perfil(atuacao="servidores", entrega="produto_usuario"))
    def r04(self):
        self._registrar("R04")

    @Rule(Perfil(linguagem=L("java_go_csharp") | L("sql"), dados="nao", visual="nao"))
    def r05(self):
        self._registrar("R05")

    # -- Front-end ---------------------------------------------------------
    @Rule(Perfil(atuacao="layouts"))
    def r06(self):
        self._registrar("R06")

    @Rule(Perfil(visual="sim", entrega="produto_usuario"))
    def r07(self):
        self._registrar("R07")

    # -- Ciência de Dados / Engenharia de Dados ---------------------------
    @Rule(Inferido(perfil="cientifico"))
    def r08(self):
        self._registrar("R08")

    @Rule(Perfil(atuacao="dados_brutos", dados="modelar"))
    def r09(self):
        self._registrar("R09")

    @Rule(Perfil(matematica="baixa", dados="modelar"))
    def r10(self):
        self._registrar("R10")

    @Rule(Perfil(dados="pipelines", atuacao=L("dados_brutos") | L("servidores")))
    def r11(self):
        self._registrar("R11")

    @Rule(Perfil(dados="pipelines", matematica=L("baixa") | L("media")))
    def r12(self):
        self._registrar("R12")

    # -- Cibersegurança ----------------------------------------------------
    @Rule(Perfil(atuacao="seguranca"))
    def r13(self):
        self._registrar("R13")

    @Rule(Perfil(entrega="seguranca"))
    def r14(self):
        self._registrar("R14")

    # -- DevOps & SRE ------------------------------------------------------
    @Rule(Perfil(atuacao="automacao", automatiza="sim"))
    def r15(self):
        self._registrar("R15")

    @Rule(Perfil(linguagem="linux_redes", automatiza="sim"))
    def r16(self):
        self._registrar("R16")

    @Rule(Inferido(perfil="infra"), Perfil(nuvem="nao"))
    def r17(self):
        self._registrar("R17")

    # -- Cloud -------------------------------------------------------------
    @Rule(Perfil(atuacao="arquitetura_nuvem"))
    def r18(self):
        self._registrar("R18")

    @Rule(Inferido(perfil="infra"), Perfil(nuvem="sim"))
    def r19(self):
        self._registrar("R19")

    # -- Mobile ------------------------------------------------------------
    @Rule(Perfil(atuacao="apps_celular"))
    def r20(self):
        self._registrar("R20")

    @Rule(Perfil(linguagem="mobile", entrega="produto_usuario"))
    def r21(self):
        self._registrar("R21")

    # -- QA ----------------------------------------------------------------
    @Rule(Perfil(atuacao="testes"))
    def r22(self):
        self._registrar("R22")

    @Rule(Perfil(entrega="qualidade"))
    def r23(self):
        self._registrar("R23")

    # -- Gestão de Produtos ------------------------------------------------
    @Rule(Perfil(atuacao="produto"))
    def r24(self):
        self._registrar("R24")

    @Rule(Perfil(interacao="sim", entrega="decisao_negocio"))
    def r25(self):
        self._registrar("R25")


@dataclass
class Resultado:
    inconclusivo: bool
    ranking: list  # [(chave, nome, pontos)] do maior para o menor
    vencedora: str = None
    nome: str = ""
    descricao: str = ""
    motivos: list = field(default_factory=list)  # regras que somaram para a vencedora
    todas_disparadas: list = field(default_factory=list)
    margem: int = 0
    confianca: str = ""
    segunda: str = None  # nome da 2ª colocada


def validar(respostas: dict):
    faltando = [c for c in CHAVES if c not in respostas]
    if faltando:
        raise ValueError(f"Respostas faltando: {', '.join(faltando)}")
    for chave, valor in respostas.items():
        if chave not in OPCOES_VALIDAS:
            raise ValueError(f"Pergunta desconhecida: {chave}")
        if valor not in OPCOES_VALIDAS[chave]:
            raise ValueError(f"Valor inválido para '{chave}': {valor!r}")


def recomendar(respostas: dict) -> Resultado:
    """Roda o motor de inferência e devolve a trilha recomendada com justificativa."""
    validar(respostas)

    motor = MotorCarreira()
    motor.reset()
    motor.declare(Perfil(**respostas))
    motor.run()

    ordem = {t: i for i, t in enumerate(ORDEM_TRILHAS)}
    ordenadas = sorted(
        ORDEM_TRILHAS,
        key=lambda t: (-motor.pontos[t], -motor.maior_peso[t], ordem[t]),
    )
    ranking = [(t, TRILHAS[t][0], motor.pontos[t]) for t in ordenadas]

    if motor.pontos[ordenadas[0]] <= 0:
        return Resultado(inconclusivo=True, ranking=ranking,
                         todas_disparadas=motor.disparadas,
                         confianca="nenhuma")

    venc = ordenadas[0]
    margem = motor.pontos[venc] - motor.pontos[ordenadas[1]]
    if margem >= 4:
        confianca = "alta"
    elif margem >= 2:
        confianca = "média"
    else:
        confianca = "baixa (perfil misto)"

    motivos = [d for d in motor.disparadas if d["efeitos"].get(venc, 0) > 0]
    return Resultado(
        inconclusivo=False,
        ranking=ranking,
        vencedora=venc,
        nome=TRILHAS[venc][0],
        descricao=TRILHAS[venc][1],
        motivos=motivos,
        todas_disparadas=motor.disparadas,
        margem=margem,
        confianca=confianca,
        segunda=TRILHAS[ordenadas[1]][0] if motor.pontos[ordenadas[1]] > 0 else None,
    )


def matriz_markdown() -> str:
    """Gera a tabela de decisão (Fase 1) a partir de REGRAS."""
    linhas = [
        "# Matriz de decisão",
        "",
        "Cada linha mostra uma regra, a condição que a dispara e o efeito sobre a trilha. "
        "Regras que afetam mais de uma trilha aparecem em cada uma delas. "
        "Pontuação final = soma dos efeitos; vence a trilha com mais pontos.",
        "",
        "## Estágio 1: regras de derivação (geram fatos inferidos)",
        "",
        "| Regra | Condição | Fato derivado |",
        "|---|---|---|",
    ]
    for rid, r in REGRAS.items():
        if r.get("derivada"):
            linhas.append(f"| {rid} | {r['condicao']} | {r['derivada']} |")

    linhas += ["", "## Estágio 2: regras de pontuação por trilha", ""]
    for chave in ORDEM_TRILHAS:
        linhas += [f"### {TRILHAS[chave][0]}", "",
                   "| Regra | Condição | Pontos |", "|---|---|---|"]
        for rid, r in REGRAS.items():
            if chave in r["efeitos"]:
                linhas.append(f"| {rid} | {r['condicao']} | {r['efeitos'][chave]:+d} |")
        linhas.append("")
    return "\n".join(linhas)


if __name__ == "__main__":
    print(matriz_markdown())
