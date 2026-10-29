"""Teste de fumaça do wizard Streamlit, sem navegador (streamlit.testing)."""

from streamlit.testing.v1 import AppTest


def _botao(at, rotulo):
    return next(b for b in at.button if b.label == rotulo)


def _avancar(at):
    next(b for b in at.get("form_submit_button") if b.proto.label == "Próximo").click()
    at.run()


def test_fluxo_completo_do_wizard():
    at = AppTest.from_file("app.py", default_timeout=30).run()
    assert not at.exception
    assert "Passo 1 de 5" in at.subheader[0].value

    _avancar(at)  # perfil -> afinidades
    assert "Passo 2 de 5" in at.subheader[0].value
    for s in at.select_slider:
        if s.key in ("w_design", "w_codigo", "w_obj_usuario"):
            s.set_value(5)
        elif s.key == "w_infra":
            s.set_value(1)
    _avancar(at)  # afinidades -> objetivos (valores de form só valem junto com o submit)
    assert "Passo 3 de 5" in at.subheader[0].value
    _avancar(at)  # objetivos -> resultado

    assert not at.exception
    assert "Passo 4 de 5" in at.subheader[0].value
    assert len(at.metric) == 3
    assert at.metric[0].label.startswith("Front-end")

    _botao(at, "Gerar plano de ação").click()
    at.run()
    assert not at.exception
    assert "Passo 5 de 5" in at.subheader[0].value
    assert any(m.label == "Prontidão para Júnior" and m.value == "0%" for m in at.metric)

    # marcar HTML/CSS como dominado deve subir a prontidão imediatamente
    next(s for s in at.select_slider if s.key == "hab_frontend_html_css").set_value(3)
    at.run()
    prontidao = next(m for m in at.metric if m.label == "Prontidão para Júnior")
    assert prontidao.value != "0%"
    assert not at.exception


def test_aba_base_de_conhecimento_renderiza():
    at = AppTest.from_file("app.py", default_timeout=30).run()
    assert not at.exception
    assert len(at.dataframe) >= 2
