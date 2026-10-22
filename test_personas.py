import pytest

from engine import MotorCarreira, REGRAS, recomendar, validar
from perguntas import CHAVES, OPCOES_VALIDAS, TRILHAS
from personas import PERSONAS


@pytest.mark.parametrize("persona", PERSONAS, ids=[p["nome"] for p in PERSONAS])
def test_persona_recebe_trilha_esperada(persona):
    resultado = recomendar(persona["respostas"])
    assert not resultado.inconclusivo
    assert resultado.vencedora == persona["esperada"]


@pytest.mark.parametrize("persona", PERSONAS, ids=[p["nome"] for p in PERSONAS])
def test_justificativa_nao_vazia(persona):
    resultado = recomendar(persona["respostas"])
    assert resultado.motivos, "toda recomendação deve citar ao menos uma regra"
    for motivo in resultado.motivos:
        assert motivo["efeitos"][resultado.vencedora] > 0


def test_todas_as_10_trilhas_sao_cobertas_por_personas():
    assert {p["esperada"] for p in PERSONAS} == set(TRILHAS)


def test_quantidade_de_regras():
    n = len(MotorCarreira().get_rules())
    assert 20 <= n <= 25
    assert n == len(REGRAS), "tabela REGRAS e métodos @Rule devem andar juntos"


def test_encadeamento_para_frente():
    """R08 só dispara porque R01 declarou o fato inferido."""
    r = recomendar(PERSONAS[0]["respostas"])
    ids = [d["id"] for d in r.todas_disparadas]
    assert ids.index("R01") < ids.index("R08")


def test_respostas_incoerentes_geram_resultado_inconclusivo():
    respostas = {c: next(iter(OPCOES_VALIDAS[c])) for c in CHAVES}
    respostas.update(matematica="baixa", atuacao="dados_brutos", linguagem="nenhuma",
                     entrega="insights_dados", dados="nao", automatiza="nao", nuvem="nao",
                     interacao="nao", visual="nao")
    assert recomendar(respostas).inconclusivo


def test_validacao_de_entrada():
    with pytest.raises(ValueError):
        validar({"matematica": "alta"})
    base = dict(PERSONAS[0]["respostas"])
    base["matematica"] = "enorme"
    with pytest.raises(ValueError):
        validar(base)


def test_motor_e_isolado_entre_consultas():
    a = recomendar(PERSONAS[0]["respostas"])
    b = recomendar(PERSONAS[0]["respostas"])
    assert a.ranking == b.ranking
