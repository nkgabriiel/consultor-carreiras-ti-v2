"""Interface web (Streamlit) do Consultor Avançado de Carreiras em TI.

Execute com:  streamlit run app.py

Fluxo em etapas (wizard): 1 Perfil pessoal, 2 Afinidades técnicas, 3 Objetivos de carreira,
4 Resultado (Top 3 + gráficos) e 5 Plano de ação (gaps + roadmap).
"""

import plotly.graph_objects as go
import streamlit as st

from base_conhecimento import base_padrao
from engine import calcular_ranking, explicar_empate, justificar, matriz_pesos
from roadmap import gerar_roadmap, habilidades_da_trilha, prontidao_por_nivel, roadmap_para_markdown

BASE = base_padrao()
NIVEIS_CARREIRA = BASE["niveis_carreira"]
ETAPAS = ["Perfil pessoal", "Afinidades técnicas", "Objetivos de carreira", "Resultado", "Plano de ação"]
LIKERT = BASE["escala_likert"]
ROTULOS_LIKERT = {int(k): v for k, v in LIKERT["rotulos"].items()}
NIVEIS = {int(k): v for k, v in BASE["niveis_conhecimento"].items()}
EXPERIENCIAS = BASE["perfil"]["experiencia"]

st.set_page_config(page_title="Consultor de Carreiras em TI", page_icon="🧭", layout="wide")


# --- Estado -------------------------------------------------------------------------
def iniciar_estado():
    ss = st.session_state
    ss.setdefault("etapa", 0)
    ss.setdefault("perfil", {"nome": "", "experiencia": "estudante", "horas": 5})
    ss.setdefault("respostas", {})
    ss.setdefault("conhecimento", {})
    ss.setdefault("trilha", None)


def ir_para(etapa: int):
    st.session_state.etapa = etapa
    st.rerun()


def reiniciar():
    for chave in list(st.session_state.keys()):
        del st.session_state[chave]
    st.rerun()


def nome_curto(nome: str) -> str:
    return nome.split(" (")[0]


# --- Etapas -------------------------------------------------------------------------
def etapa_perfil():
    st.subheader("Passo 1 de 5: perfil pessoal")
    st.write("Conte um pouco sobre você. Essas respostas não alteram o ranking, mas ajustam o "
             "tempo estimado e o tipo de projeto sugerido no plano de ação.")
    perfil = st.session_state.perfil
    with st.form("form_perfil"):
        nome = st.text_input("Como podemos te chamar? (opcional)", value=perfil["nome"])
        experiencia = st.selectbox(
            "Qual a sua experiência com TI hoje?", options=list(EXPERIENCIAS),
            format_func=lambda k: EXPERIENCIAS[k]["rotulo"], index=list(EXPERIENCIAS).index(perfil["experiencia"]))
        horas = st.select_slider("Quantas horas por semana você consegue estudar?",
                                 options=BASE["perfil"]["horas_semana"], value=perfil["horas"])
        if st.form_submit_button("Próximo", type="primary"):
            st.session_state.perfil = {"nome": nome.strip(), "experiencia": experiencia, "horas": horas}
            ir_para(1)


def etapa_likert(etapa_id: str, numero: int, titulo: str, instrucao: str):
    st.subheader(f"Passo {numero} de 5: {titulo}")
    st.write(instrucao)
    perguntas = [p for p in BASE["perguntas"] if p["etapa"] == etapa_id]
    with st.form(f"form_{etapa_id}"):
        for p in perguntas:
            st.select_slider(
                p["texto"], options=list(ROTULOS_LIKERT), key=f"w_{p['id']}",
                value=st.session_state.respostas.get(p["id"], 3),
                format_func=lambda v: f"{v} - {ROTULOS_LIKERT[v]}")
        voltar, avancar = st.columns(2)
        quer_voltar = voltar.form_submit_button("Voltar")
        quer_avancar = avancar.form_submit_button("Próximo", type="primary")
        if quer_voltar or quer_avancar:
            for p in perguntas:
                st.session_state.respostas[p["id"]] = st.session_state[f"w_{p['id']}"]
            ir_para(numero - 2 if quer_voltar else numero)


def grafico_radar(ranking):
    nomes = [nome_curto(t.nome) for t in ranking]
    valores = [t.percentual for t in ranking]
    fig = go.Figure(go.Scatterpolar(r=valores + valores[:1], theta=nomes + nomes[:1],
                                    fill="toself", name="Compatibilidade (%)"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], ticksuffix="%")),
                      showlegend=False, margin=dict(l=70, r=70, t=30, b=30), height=480)
    return fig


def grafico_barras(ranking):
    ordenado = list(reversed(ranking))
    fig = go.Figure(go.Bar(x=[t.percentual for t in ordenado], y=[nome_curto(t.nome) for t in ordenado],
                           orientation="h", text=[f"{t.percentual:.0f}%" for t in ordenado],
                           textposition="outside"))
    fig.update_layout(xaxis=dict(range=[0, 110], ticksuffix="%"), margin=dict(l=10, r=10, t=10, b=10),
                      height=420)
    return fig


def etapa_resultado():
    st.subheader("Passo 4 de 5: seu resultado")
    ss = st.session_state
    diag = calcular_ranking(ss.respostas)
    nome = ss.perfil["nome"]
    if nome:
        st.write(f"{nome}, aqui está a compatibilidade do seu perfil com as 10 trilhas.")

    if diag.inconclusivo:
        st.warning("Suas respostas indicaram pouca afinidade com qualquer trilha (nenhuma passou de "
                   f"{BASE['classificacao']['limiar_inconclusivo_pct']}%). Revise as respostas dos passos 2 e 3 "
                   "antes de confiar neste ranking.")

    colunas = st.columns(3)
    for i, (col, t) in enumerate(zip(colunas, diag.top3), start=1):
        with col.container(border=True):
            st.caption(f"{i}º lugar")
            st.metric(t.nome, f"{t.percentual:.0f}%")
            st.progress(min(1.0, t.percentual / 100))
            st.write(t.descricao)

    if diag.empate_parcial:
        st.info(explicar_empate(diag))
    st.caption(f"Confiança do diagnóstico: **{diag.confianca}** "
               f"(diferença de {diag.margem_pp:.1f} pp entre a 1ª e a 2ª colocada).")

    aba_radar, aba_barras, aba_tabela = st.tabs(["Radar", "Barras", "Tabela"])
    with aba_radar:
        st.plotly_chart(grafico_radar(diag.ranking), width="stretch")
    with aba_barras:
        st.plotly_chart(grafico_barras(diag.ranking), width="stretch")
    with aba_tabela:
        st.dataframe(
            [{"Posição": i, "Trilha": t.nome, "Compatibilidade (%)": t.percentual,
              "Antes dos ajustes (%)": t.base_pct, "Regras combinadas": ", ".join(a.regra for a in t.ajustes) or "-"}
             for i, t in enumerate(diag.ranking, start=1)],
            hide_index=True, width="stretch")

    st.subheader("Por que esse resultado?")
    abas = st.tabs([f"{i}º {nome_curto(t.nome)}" for i, t in enumerate(diag.top3, start=1)])
    for aba, t in zip(abas, diag.top3):
        with aba:
            st.markdown(f"**{t.percentual:.0f}%** = {t.base_pct:.0f}% de pontos ponderados "
                        f"({t.pontos:.1f} de {t.maximo:g}) com ajustes das regras combinadas.")
            for frase in justificar(t, n=4):
                st.markdown(f"- {frase}")

    st.divider()
    chaves = [t.chave for t in diag.ranking]
    padrao = ss.trilha if ss.trilha in chaves else chaves[0]
    escolha = st.selectbox("Gerar plano de ação para qual trilha?", options=chaves, index=chaves.index(padrao),
                           format_func=lambda k: f"{next(t for t in diag.ranking if t.chave == k).nome} "
                                                 f"({next(t for t in diag.ranking if t.chave == k).percentual:.0f}%)")
    voltar, avancar = st.columns(2)
    if voltar.button("Voltar"):
        ir_para(2)
    if avancar.button("Gerar plano de ação", type="primary"):
        ss.trilha = escolha
        ir_para(4)


def etapa_plano():
    ss = st.session_state
    trilha = ss.trilha
    if trilha is None:
        ir_para(3)
    st.subheader("Passo 5 de 5: gaps e plano de ação")
    st.write(f"Trilha escolhida: **{BASE['trilhas'][trilha]['nome']}**. Escolha o nível que você quer "
             "alcançar e marque seu nível atual em cada habilidade exigida; o plano se atualiza na hora.")

    nivel = st.radio("Nível-alvo", options=list(NIVEIS_CARREIRA), horizontal=True, key="nivel_alvo",
                     format_func=lambda n: f"{NIVEIS_CARREIRA[n]['rotulo']} ({NIVEIS_CARREIRA[n]['experiencia_tipica']})")
    st.caption(NIVEIS_CARREIRA[nivel]["descricao"])
    rotulo = NIVEIS_CARREIRA[nivel]["rotulo"]

    exigidas = habilidades_da_trilha(trilha, nivel)
    colunas = st.columns(2)
    for i, h in enumerate(exigidas):
        ss.conhecimento[h["id"]] = colunas[i % 2].select_slider(
            f"{h['nome']} ({rotulo} = nível {h['requerido']})", options=list(NIVEIS),
            value=ss.conhecimento.get(h["id"], 0), key=f"hab_{trilha}_{h['id']}",
            format_func=lambda v: f"{v} - {NIVEIS[v]}",
            help=f"Exigido desde o nível {NIVEIS_CARREIRA[h['desde']]['rotulo']}.")

    perfil = ss.perfil
    rm = gerar_roadmap(trilha, ss.conhecimento, perfil["experiencia"], perfil["horas"], nivel)

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Prontidão para {rotulo}", f"{rm.prontidao_pct:.0f}%")
    m2.metric("Habilidades com lacuna", f"{len(rm.gaps)} de {len(rm.gaps) + len(rm.atingidas)}")
    m3.metric("Esforço de estudo", f"{rm.horas_totais} h")
    m4.metric("Prazo de estudo", f"{rm.semanas} sem.", help=f"Estudando {perfil['horas']} h por semana.")
    st.progress(min(1.0, rm.prontidao_pct / 100))
    if nivel != "junior":
        st.caption(f"Essas horas cobrem só o estudo: chegar a {rotulo} também exige experiência prática, "
                   f"em geral {rm.experiencia_tipica}.")

    with st.expander("Sua trajetória: prontidão em cada nível"):
        pront = prontidao_por_nivel(trilha, ss.conhecimento)
        for n, pct in pront.items():
            st.progress(min(1.0, pct / 100), text=f"{NIVEIS_CARREIRA[n]['rotulo']}: {pct:.0f}%")
        st.caption("Habilidades que você ainda não avaliou (as de níveis acima do selecionado) contam como 0.")

    if not rm.gaps:
        st.success(f"Você já atende todos os requisitos de {rotulo} desta trilha. "
                   "Foque no portfólio e nas certificações.")
    for titulo, gaps in rm.fases:
        st.markdown(f"#### {titulo}")
        st.dataframe(
            [{"Habilidade": g.nome, "Seu nível": g.atual, f"Nível {rotulo}": g.requerido,
              "Exigido desde": NIVEIS_CARREIRA[g.desde]["rotulo"], "O que estudar": g.estudar}
             for g in gaps], hide_index=True, width="stretch")
    if rm.atingidas:
        st.caption("Já atingido: " + ", ".join(g.nome for g in rm.atingidas))

    col_cert, col_proj = st.columns(2)
    with col_cert:
        st.markdown("#### Certificações")
        for c in rm.certificacoes:
            st.markdown(f"- **{c['nome']}** ({c['nivel']})")
    with col_proj:
        st.markdown("#### Projetos para o portfólio no GitHub")
        for p in rm.projetos:
            st.markdown(f"- **{p['titulo']}** ({p['nivel']}): {p['descricao']}")

    st.divider()
    voltar, baixar, refazer = st.columns(3)
    if voltar.button("Voltar ao resultado"):
        ir_para(3)
    baixar.download_button("Baixar plano (Markdown)", roadmap_para_markdown(rm, perfil["nome"]),
                           file_name=f"plano_{trilha}_{nivel}.md", mime="text/markdown")
    if refazer.button("Refazer o teste"):
        reiniciar()


def aba_base_conhecimento():
    st.markdown(f"Base carregada de `regras_carreiras.json` (versão {BASE['versao']}): "
                f"**{len(BASE['trilhas'])} trilhas**, **{len(BASE['perguntas'])} perguntas**, "
                f"**{len(BASE['regras_combinadas'])} regras combinadas** e **{len(BASE['habilidades'])} habilidades**. "
                "O código Python não contém nenhum desses valores.")
    st.markdown("#### Pesos das perguntas por trilha")
    st.caption("Positivo soma pontos; negativo desconta quando a pessoa tem muita afinidade com algo que conflita com a trilha.")
    st.dataframe(matriz_pesos(), width="stretch")
    st.markdown("#### Regras combinadas (ajustes em pontos percentuais)")
    st.dataframe(
        [{"Regra": r["id"], "Tipo": r["tipo"], "Condição": " E ".join(f"{q} {op} {v}" for q, op, v in r["se"]),
          "Ajustes": ", ".join(f"{nome_curto(BASE['trilhas'][t]['nome'])}: {pp:+g}" for t, pp in r["ajustes"].items()),
          "Motivo": r["motivo"]} for r in BASE["regras_combinadas"]],
        hide_index=True, width="stretch")


# --- Página -------------------------------------------------------------------------
iniciar_estado()
st.title("Consultor Avançado de Carreiras em TI")
st.caption("Sistema especialista com pontuação ponderada e tratamento de incerteza. "
           "Responda em etapas, veja a compatibilidade com 10 trilhas e receba um plano de ação.")

aba_consultor, aba_base = st.tabs(["Consultor", "Base de conhecimento"])
with aba_consultor:
    etapa = st.session_state.etapa
    st.progress((etapa + 1) / len(ETAPAS), text=f"Etapa {etapa + 1} de {len(ETAPAS)}: {ETAPAS[etapa]}")
    if etapa == 0:
        etapa_perfil()
    elif etapa == 1:
        etapa_likert("afinidades", 2, "afinidades técnicas",
                     "Dê uma nota de 1 (nenhuma afinidade) a 5 (total) para cada tema.")
    elif etapa == 2:
        etapa_likert("objetivos", 3, "objetivos de carreira",
                     "Diga o quanto você concorda com cada afirmação, de 1 (nada) a 5 (totalmente).")
    elif etapa == 3:
        etapa_resultado()
    else:
        etapa_plano()
with aba_base:
    aba_base_conhecimento()
