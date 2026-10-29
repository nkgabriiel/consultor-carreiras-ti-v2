import pytest

from base_conhecimento import base_padrao
from roadmap import (analisar_gaps, gerar_roadmap, habilidades_da_trilha, prontidao_por_nivel,
                     roadmap_para_markdown)

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


# --- Níveis de carreira: Júnior, Pleno e Sênior ---------------------------------------
NIVEIS = list(BASE["niveis_carreira"])


def conhecimento_de(trilha, nivel):
    """Quem tem exatamente o que se exige no nível informado (nem mais, nem menos)."""
    return {h["id"]: h["requerido"] for h in habilidades_da_trilha(trilha, nivel)}


def test_tres_niveis_em_ordem():
    assert NIVEIS == ["junior", "pleno", "senior"]


@pytest.mark.parametrize("trilha", list(BASE["trilhas"]))
def test_requisitos_sao_cumulativos(trilha):
    """Pleno exige tudo de Júnior (no mesmo nível ou maior), e Sênior tudo de Pleno."""
    anterior = {}
    for nivel in NIVEIS:
        atual = {h["id"]: h["requerido"] for h in habilidades_da_trilha(trilha, nivel)}
        for hid, req in anterior.items():
            assert hid in atual and atual[hid] >= req, f"{trilha}/{nivel}: {hid} regrediu"
        assert len(atual) > len(anterior) or any(atual[h] > anterior[h] for h in anterior), \
            f"{trilha}/{nivel} não exige nada além do nível anterior"
        anterior = atual


@pytest.mark.parametrize("trilha", list(BASE["trilhas"]))
def test_prontidao_cai_ao_subir_de_nivel(trilha):
    pronto_junior = conhecimento_de(trilha, "junior")
    pront = prontidao_por_nivel(trilha, pronto_junior)
    assert pront["junior"] == 100
    assert pront["pleno"] < 100
    assert pront["senior"] < pront["pleno"]


@pytest.mark.parametrize("trilha", list(BASE["trilhas"]))
def test_dominar_tudo_atende_todos_os_niveis(trilha):
    tudo = {h: 3 for h in BASE["habilidades"]}
    assert set(prontidao_por_nivel(trilha, tudo).values()) == {100.0}
    assert gerar_roadmap(trilha, tudo, nivel="senior").gaps == []


def test_esforco_cresce_com_o_nivel_alvo():
    horas = [gerar_roadmap("devops", {}, nivel=n).horas_totais for n in NIVEIS]
    assert horas == sorted(horas) and len(set(horas)) == 3


def test_quem_ja_e_junior_so_estuda_o_que_falta_para_pleno():
    conhecimento = conhecimento_de("backend", "junior")
    rm = gerar_roadmap("backend", conhecimento, nivel="pleno")
    assert rm.gaps and all(g.lacuna > 0 for g in rm.gaps)
    ids_junior = {h["id"]: h["requerido"] for h in habilidades_da_trilha("backend", "junior")}
    for g in rm.gaps:
        # ou é habilidade nova do Pleno, ou o JSON elevou o nível exigido
        assert g.desde == "pleno" or g.requerido > ids_junior[g.habilidade]


def test_habilidade_registra_o_nivel_em_que_passa_a_ser_exigida():
    por_id = {h["id"]: h for h in habilidades_da_trilha("backend", "senior")}
    assert por_id["git"]["desde"] == "junior"
    assert por_id["arquitetura"]["desde"] == "pleno"
    assert por_id["lideranca_tecnica"]["desde"] == "senior"


def test_ordem_de_estudo_prioriza_o_nivel_mais_basico():
    desde = [h["desde"] for h in habilidades_da_trilha("cloud", "senior")]
    indices = [NIVEIS.index(d) for d in desde]
    assert indices == sorted(indices)
    prioridades = [h["prioridade"] for h in habilidades_da_trilha("cloud", "senior")]
    assert prioridades == list(range(1, len(prioridades) + 1))


@pytest.mark.parametrize("trilha", list(BASE["trilhas"]))
@pytest.mark.parametrize("nivel", NIVEIS)
def test_certificacoes_e_projetos_em_todo_nivel(trilha, nivel):
    rm = gerar_roadmap(trilha, {}, nivel=nivel)
    permitido = BASE["niveis_carreira"][nivel]
    assert rm.certificacoes and rm.projetos
    assert all(c["nivel"] in permitido["certificacoes"] for c in rm.certificacoes)
    assert all(p["nivel"] in permitido["projetos"] for p in rm.projetos)


def test_senior_so_recebe_certificacoes_e_projetos_avancados():
    rm = gerar_roadmap("produto", {}, nivel="senior")
    assert {c["nivel"] for c in rm.certificacoes} == {"avancado"}
    assert {p["nivel"] for p in rm.projetos} == {"avancado"}


def test_nivel_padrao_continua_sendo_junior():
    assert gerar_roadmap("qa", {}) == gerar_roadmap("qa", {}, nivel="junior")


def test_markdown_informa_nivel_e_alerta_sobre_experiencia():
    md = roadmap_para_markdown(gerar_roadmap("backend", {}, nivel="senior"))
    assert "(Sênior)" in md and "5 anos ou mais" in md and "experiência prática" in md
    assert "experiência prática" not in roadmap_para_markdown(gerar_roadmap("backend", {}, nivel="junior"))


def test_nivel_de_carreira_invalido_e_rejeitado():
    for chamada in (lambda: gerar_roadmap("backend", {}, nivel="estagiario"),
                    lambda: habilidades_da_trilha("backend", "staff"),
                    lambda: analisar_gaps("backend", {}, "master")):
        with pytest.raises(ValueError, match="Nível desconhecido"):
            chamada()
