import pytest

from base_conhecimento import base_padrao
from roadmap import analisar_gaps, gerar_roadmap, habilidades_da_trilha

BASE = base_padrao()


def conhecimento_completo(trilha):
    return {h["id"]: 3 for h in habilidades_da_trilha(trilha)}


def test_iniciante_sem_nada_tem_todas_as_lacunas():
    rm = gerar_roadmap("devops", {})
    exigidas = BASE["roadmap"]["devops"]["junior"]
    assert len(rm.gaps) == len(exigidas)
    assert rm.prontidao_pct == 0
    assert rm.atingidas == []


def test_quem_ja_domina_tudo_nao_tem_gaps_nem_horas():
    rm = gerar_roadmap("backend", conhecimento_completo("backend"))
    assert rm.gaps == [] and rm.fases == []
    assert rm.prontidao_pct == 100
    assert rm.horas_totais == 0 and rm.semanas == 0
    assert rm.projetos and rm.certificacoes  # portfólio e certificações continuam sugeridos


def test_gap_e_a_diferenca_entre_requerido_e_atual():
    gaps = analisar_gaps("backend", {"sql": 1, "git": 3})
    por_id = {g.habilidade: g for g in gaps}
    assert por_id["sql"].lacuna == 1  # requer 2, tem 1
    assert por_id["git"].lacuna == 0  # nível acima do exigido não gera lacuna negativa
    assert por_id["logica"].lacuna == 2


def test_gaps_seguem_a_ordem_de_prioridade_da_base():
    rm = gerar_roadmap("backend", {})
    prioridades = [g.prioridade for g in rm.gaps]
    assert prioridades == sorted(prioridades)


def test_fases_separam_o_que_nunca_estudou_do_que_precisa_reforcar():
    rm = gerar_roadmap("backend", {"sql": 1, "logica": 1})
    nomes_fase1 = {g.habilidade for g in rm.fases[0][1]}
    assert "sql" not in nomes_fase1 and "git" in nomes_fase1
    reforco = {g.habilidade for g in rm.fases[1][1]}
    assert reforco == {"sql", "logica"}


def test_tempo_estimado_depende_das_horas_por_semana_e_da_experiencia():
    lento = gerar_roadmap("frontend", {}, experiencia="iniciante", horas_semana=3)
    rapido = gerar_roadmap("frontend", {}, experiencia="transicao", horas_semana=20)
    assert lento.horas_totais > rapido.horas_totais
    assert lento.semanas > rapido.semanas


def test_horas_calculadas_a_partir_da_base():
    horas_nivel = {int(k): v for k, v in BASE["perfil"]["horas_por_nivel"].items()}
    esperado = sum(horas_nivel[i["nivel"]] for i in BASE["roadmap"]["qa"]["junior"])
    rm = gerar_roadmap("qa", {}, experiencia="estudante", horas_semana=10)
    assert rm.horas_totais == esperado


def test_prontidao_sobe_conforme_o_usuario_aprende():
    antes = gerar_roadmap("cloud", {}).prontidao_pct
    depois = gerar_roadmap("cloud", {"redes": 2, "linux": 2}).prontidao_pct
    assert 0 <= antes < depois <= 100


def test_projetos_para_experiente_comecam_pelo_nivel_intermediario():
    novato = gerar_roadmap("backend", {}, experiencia="iniciante")
    veterano = gerar_roadmap("backend", {}, experiencia="transicao")
    assert novato.projetos[0]["nivel"] == "basico"
    assert veterano.projetos[0]["nivel"] == "intermediario"


@pytest.mark.parametrize("trilha", list(BASE["trilhas"]))
def test_toda_trilha_tem_roadmap_completo(trilha):
    rm = gerar_roadmap(trilha, {})
    assert rm.gaps and rm.certificacoes and len(rm.projetos) >= 2
    assert all(g.estudar for g in rm.gaps)


@pytest.mark.parametrize("conhecimento", [{"git": 4}, {"git": -1}, {"git": 1.5}, {"git": "2"}, {"git": True}])
def test_nivel_de_conhecimento_invalido_e_rejeitado(conhecimento):
    with pytest.raises(ValueError):
        analisar_gaps("backend", conhecimento)


def test_entradas_invalidas():
    with pytest.raises(ValueError):
        gerar_roadmap("astronauta", {})
    with pytest.raises(ValueError):
        gerar_roadmap("backend", {}, horas_semana=0)
    with pytest.raises(ValueError):
        gerar_roadmap("backend", {}, experiencia="lenda")
