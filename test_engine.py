import copy
import json
from pathlib import Path

import pytest

from base_conhecimento import BaseInvalida, base_padrao, carregar_base, validar_base
from engine import (RespostasInvalidas, calcular_ranking, explicar_empate, justificar,
                    matriz_pesos, validar_respostas)
from personas import PERSONAS, PERSONAS_AMBIGUAS, TOP3_AMBIGUAS, respostas

BASE = base_padrao()


# --- Base de conhecimento desacoplada -------------------------------------------------
def test_base_tem_10_trilhas_e_valida():
    assert len(BASE["trilhas"]) == 10
    validar_base(BASE)


def test_codigo_python_nao_conhece_as_trilhas():
    """O conhecimento fica no JSON: nenhuma chave de trilha ou de pergunta aparece no motor."""
    fonte = "\n".join(Path(f).read_text(encoding="utf-8") for f in ("engine.py", "roadmap.py"))
    for chave in list(BASE["trilhas"]) + [p["id"] for p in BASE["perguntas"]]:
        assert f'"{chave}"' not in fonte and f"'{chave}'" not in fonte, chave


def test_alterar_o_json_muda_o_resultado_sem_tocar_no_codigo(tmp_path):
    nova = copy.deepcopy(BASE)
    nova["trilhas"]["qa"]["pesos"]["matematica"] = 5  # absurdo, mas só no JSON
    arquivo = tmp_path / "outras_regras.json"
    arquivo.write_text(json.dumps(nova), encoding="utf-8")
    r = respostas(matematica=5, testes=1)
    original = next(t for t in calcular_ranking(r).ranking if t.chave == "qa")
    alterada = next(t for t in calcular_ranking(r, carregar_base(arquivo)).ranking if t.chave == "qa")
    assert alterada.pontos > original.pontos


@pytest.mark.parametrize("mutacao, trecho", [
    (lambda b: b["trilhas"]["qa"]["pesos"].update(inexistente=3), "pergunta inexistente"),
    (lambda b: b["trilhas"]["qa"]["pesos"].update(testes=9), "fora de -5..5"),
    (lambda b: b["regras_combinadas"][0]["ajustes"].update(fantasma=-5), "trilha inexistente"),
    (lambda b: b["regras_combinadas"][0]["se"].append(["codigo", "!=", 2]), "operador inválido"),
    (lambda b: b["roadmap"]["qa"]["junior"].append({"habilidade": "x", "nivel": 1, "prioridade": 9}), "habilidade inexistente"),
    (lambda b: b["trilhas"].pop("qa"), "10 trilhas"),
])
def test_base_inconsistente_e_rejeitada_na_carga(mutacao, trecho):
    ruim = copy.deepcopy(BASE)
    mutacao(ruim)
    with pytest.raises(BaseInvalida, match=trecho):
        validar_base(ruim)


# --- Pontuação ponderada --------------------------------------------------------------
@pytest.mark.parametrize("persona", PERSONAS, ids=[p["nome"] for p in PERSONAS])
def test_persona_recebe_trilha_esperada(persona):
    d = calcular_ranking(persona["respostas"])
    assert not d.inconclusivo
    assert d.top3[0].chave == persona["esperada"]


def test_top3_ordenado_e_com_percentuais_validos():
    d = calcular_ranking(PERSONAS[0]["respostas"])
    assert len(d.top3) == 3
    pcts = [t.percentual for t in d.ranking]
    assert pcts == sorted(pcts, reverse=True)
    assert all(0 <= p <= 100 for p in pcts)
    assert len(d.ranking) == 10


def test_resposta_multiplica_o_peso():
    """Pontos = Σ grau × peso, com grau = (resposta - 1) / 4."""
    r = respostas(1, logica=5, codigo=3)
    be = next(t for t in calcular_ranking(r).ranking if t.chave == "backend")
    pesos = BASE["trilhas"]["backend"]["pesos"]
    esperado = sum((r[q] - 1) / 4 * w for q, w in pesos.items())
    assert be.pontos == pytest.approx(esperado, abs=0.01)


def test_resposta_mais_alta_nunca_reduz_a_trilha_que_valoriza_a_pergunta():
    baixa = calcular_ranking(respostas(2, mobile=3, codigo=4))
    alta = calcular_ranking(respostas(2, mobile=5, codigo=4))
    pega = lambda d: next(t for t in d.ranking if t.chave == "mobile").percentual
    assert pega(alta) > pega(baixa)


def test_penalidade_para_perfil_conflitante():
    """Quem não gosta de código perde pontos nas trilhas de desenvolvimento."""
    gosta = calcular_ranking(respostas(2, logica=5, bancos=4, codigo=4))
    odeia = calcular_ranking(respostas(2, logica=5, bancos=4, codigo=1))
    be_gosta = next(t for t in gosta.ranking if t.chave == "backend")
    be_odeia = next(t for t in odeia.ranking if t.chave == "backend")
    assert any(a.regra == "P01" and a.tipo == "penalidade" for a in be_odeia.ajustes)
    assert be_odeia.percentual < be_gosta.percentual - 20


def test_sinergia_soma_pontos_percentuais():
    d = calcular_ranking(respostas(2, infra=5, automacao=5))
    devops = next(t for t in d.ranking if t.chave == "devops")
    assert any(a.regra == "S03" for a in devops.ajustes)
    assert devops.percentual >= devops.base_pct  # a sinergia nunca é desfeita por si só


def test_regra_cientista_x_engenheiro_de_dados():
    cient = calcular_ranking(respostas(2, dados=5, matematica=5, bancos=3))
    engen = calcular_ranking(respostas(2, dados=5, matematica=3, bancos=5))
    assert cient.top3[0].chave == "ciencia_dados"
    assert engen.top3[0].chave == "eng_dados"


def test_justificativa_cita_perguntas_e_regras():
    d = calcular_ranking(respostas(2, codigo=1, logica=5, bancos=4))
    be = next(t for t in d.ranking if t.chave == "backend")
    texto = " ".join(justificar(be))
    assert "somou" in texto and "P01" in texto


def test_resultado_e_deterministico_e_nao_vaza_estado_entre_consultas():
    a = calcular_ranking(PERSONAS[0]["respostas"])
    b = calcular_ranking(PERSONAS[0]["respostas"])
    assert [(t.chave, t.percentual) for t in a.ranking] == [(t.chave, t.percentual) for t in b.ranking]


def test_matriz_de_pesos_pandas():
    m = matriz_pesos()
    assert m.shape == (len(BASE["perguntas"]), 10)


# --- Fase 5: robustez e casos limite --------------------------------------------------
def test_tudo_1_e_inconclusivo():
    d = calcular_ranking(respostas(1))
    assert d.inconclusivo
    assert d.top3[0].percentual < BASE["classificacao"]["limiar_inconclusivo_pct"]


def test_tudo_5_nao_estoura_100_e_gera_empate_parcial():
    d = calcular_ranking(respostas(5))
    assert all(t.percentual <= 100 for t in d.ranking)
    assert d.empate_parcial and d.confianca == "baixa"


def test_tudo_neutro_nao_inventa_certeza():
    d = calcular_ranking(respostas(3))
    assert d.confianca != "alta"


@pytest.mark.parametrize("persona", PERSONAS_AMBIGUAS, ids=[p["nome"] for p in PERSONAS_AMBIGUAS])
def test_perfil_ambiguo_mantem_ambas_no_top3_e_sinaliza_incerteza(persona):
    d = calcular_ranking(persona["respostas"])
    assert TOP3_AMBIGUAS[persona["nome"]] <= {t.chave for t in d.top3} | {t.chave for t in d.ranking[:4]}
    assert d.empate_parcial
    assert d.confianca == "baixa"
    assert "Perfil misto" in explicar_empate(d)


def test_dados_e_web_aparecem_juntos():
    d = calcular_ranking(PERSONAS_AMBIGUAS[0]["respostas"])
    top = {t.chave for t in d.top3}
    assert {"frontend", "ciencia_dados"} <= top


def test_empate_exato_e_resolvido_por_ordem_da_base_sem_erro():
    d = calcular_ranking(respostas(1))
    assert [t.chave for t in d.ranking][:1] == [d.top3[0].chave]


def test_respostas_contraditorias_nao_dao_porcentagem_negativa():
    r = respostas(1, codigo=5, design=5, infra=5, matematica=1, dados=1, comunicacao=1, gestao=1)
    d = calcular_ranking(r)
    assert all(t.percentual >= 0 for t in d.ranking)


def test_sem_explicacao_de_empate_quando_ha_vencedora_clara():
    assert explicar_empate(calcular_ranking(PERSONAS[3]["respostas"])) == ""


@pytest.mark.parametrize("ruim", [0, 6, -1, 2.5, "3", None, True])
def test_valor_fora_da_escala_ou_de_tipo_errado_e_rejeitado(ruim):
    with pytest.raises(RespostasInvalidas):
        validar_respostas(respostas(codigo=ruim))


def test_respostas_faltando_ou_desconhecidas_sao_rejeitadas():
    parcial = respostas()
    parcial.pop("codigo")
    with pytest.raises(RespostasInvalidas, match="faltando"):
        calcular_ranking(parcial)
    extra = respostas()
    extra["curiosidade"] = 3
    with pytest.raises(RespostasInvalidas, match="desconhecida"):
        calcular_ranking(extra)
