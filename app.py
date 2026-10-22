"""Interface web (Streamlit) do Consultor Inteligente de Carreiras em TI.

Execute com:  streamlit run app.py
"""

import streamlit as st

from engine import REGRAS, matriz_markdown, recomendar
from perguntas import ORDEM_TRILHAS, PERGUNTAS, TRILHAS

st.set_page_config(page_title="Consultor de Carreiras em TI", page_icon="🧭", layout="centered")

st.title("Consultor Inteligente de Carreiras em TI")
st.caption("Sistema especialista baseado em regras (Experta). Responda às perguntas e veja "
           "qual das 10 trilhas combina mais com você, com as regras que justificam o resultado.")

aba_entrevista, aba_regras = st.tabs(["Entrevista", "Base de regras"])

with aba_entrevista:
    with st.form("entrevista"):
        respostas = {}
        for i, p in enumerate(PERGUNTAS, start=1):
            respostas[p["chave"]] = st.selectbox(
                f"{i}. {p['texto']}",
                options=list(p["opcoes"]),
                format_func=p["opcoes"].get,
                index=None,
                placeholder="Escolha uma opção",
                key=f"q_{p['chave']}",
            )
        enviar = st.form_submit_button("Descobrir minha trilha", type="primary")

    if enviar:
        faltam = [i for i, p in enumerate(PERGUNTAS, start=1) if respostas[p["chave"]] is None]
        if faltam:
            st.warning("Responda todas as perguntas. Faltam: " + ", ".join(map(str, faltam)) + ".")
        else:
            # Uma engine nova a cada envio: o Streamlit reexecuta o script inteiro.
            r = recomendar(respostas)

            if r.inconclusivo:
                st.error("Não foi possível recomendar uma trilha: nenhuma regra apontou "
                         "pontos positivos para suas respostas.")
                st.info("Suas respostas parecem contraditórias (por exemplo, atuar com dados "
                        "brutos mas não querer foco em dados). Revise e tente de novo.")
            else:
                st.success(f"### {r.nome}")
                st.write(r.descricao)
                col1, col2 = st.columns(2)
                col1.metric("Pontuação", r.ranking[0][2])
                col2.metric("Confiança", r.confianca.split(" ")[0].capitalize())
                if r.confianca.startswith("baixa") and r.segunda:
                    st.info(f"Seu perfil é misto. A segunda trilha mais próxima é **{r.segunda}**.")

                st.subheader("Por que essa trilha?")
                for m in r.motivos:
                    pts = m["efeitos"][r.vencedora]
                    st.markdown(f"- **{m['id']}** (+{pts}): {m['motivo']}.")

                st.subheader("Ranking")
                top = [(nome, pts) for _, nome, pts in r.ranking if pts > 0][:5]
                st.bar_chart({nome: pts for nome, pts in top}, horizontal=True)

                with st.expander("Todas as regras disparadas, na ordem de execução"):
                    for d in r.todas_disparadas:
                        if d["derivada"]:
                            st.markdown(f"- **{d['id']}** → fato inferido *{d['derivada']}* "
                                        f"(quando {d['condicao']})")
                        else:
                            efeitos = ", ".join(f"{TRILHAS[t][0]}: {v:+d}"
                                                for t, v in d["efeitos"].items())
                            st.markdown(f"- **{d['id']}** ({d['condicao']}) → {efeitos}")

with aba_regras:
    st.markdown("Esta é a base de conhecimento carregada no motor: "
                f"**{len(REGRAS)} regras** em dois estágios (derivação e pontuação).")
    st.markdown(matriz_markdown().split("\n", 1)[1])  # remove o título H1
