"""Personas de teste (Fase 5).

Cada persona tem respostas Likert fixas e a trilha que o sistema deve colocar em 1º lugar.
As personas ambíguas listam as trilhas que precisam aparecer juntas no Top 3.
Rode `python personas.py` para ver a tabela de validação.
"""

from base_conhecimento import base_padrao


def respostas(padrao: int = 2, **overrides) -> dict:
    """Todas as perguntas com o valor `padrao`, exceto as informadas."""
    r = {p["id"]: padrao for p in base_padrao()["perguntas"]}
    desconhecidas = set(overrides) - set(r)
    assert not desconhecidas, f"perguntas inexistentes: {desconhecidas}"
    r.update(overrides)
    return r


def _p(nome, descricao, esperada, **r):
    return {"nome": nome, "descricao": descricao, "esperada": esperada, "respostas": respostas(**r)}


PERSONAS = [
    _p("Ana (cientista de dados)", "Ama estatística, dados e pesquisa; evita infraestrutura.",
       "ciencia_dados", matematica=5, dados=5, obj_pesquisa=5, logica=4, codigo=3, bancos=3),
    _p("Bruno (segurança)", "Vive no terminal, gosta de redes e de pensar como atacante.",
       "ciberseguranca", seguranca=5, infra=4, obj_investigacao=5, obj_incidentes=4, logica=3, codigo=3),
    _p("Carla (front-end)", "Foca na aparência das telas e na experiência de quem usa.",
       "frontend", design=5, codigo=4, obj_usuario=5, logica=3, comunicacao=3),
    _p("Diego (produto)", "Conversa com clientes, prioriza o que construir e lidera.",
       "produto", comunicacao=5, gestao=5, obj_lideranca=5, obj_usuario=4, design=3, codigo=1, infra=1),
    _p("Eduarda (back-end)", "Gosta de lógica, regras de negócio e bancos de dados.",
       "backend", logica=5, codigo=5, bancos=4, obj_escala=3, dados=2, design=1),
    _p("Felipe (engenharia de dados)", "Pipelines ETL em SQL e Python; matemática só moderada.",
       "eng_dados", dados=5, bancos=5, codigo=4, logica=4, matematica=3, automacao=4, nuvem=4, obj_escala=4),
    _p("Gisele (DevOps/SRE)", "Automatiza deploys, cuida de contêineres e topa plantão.",
       "devops", infra=5, automacao=5, obj_incidentes=5, codigo=3, logica=3, nuvem=3, obj_escala=3),
    _p("Henrique (cloud)", "Desenha arquiteturas escaláveis e migra sistemas para a nuvem.",
       "cloud", nuvem=5, infra=4, obj_escala=5, obj_lideranca=4, comunicacao=3, automacao=3, obj_incidentes=2),
    _p("Isabela (mobile)", "Constrói apps e se importa com a experiência na tela pequena.",
       "mobile", mobile=5, codigo=4, design=4, obj_usuario=5, logica=3),
    _p("João (QA)", "Detalhista, caça defeitos, escreve testes automatizados.",
       "qa", testes=5, obj_qualidade=5, automacao=4, logica=3, codigo=3, comunicacao=3),
]

# Perfis ambíguos: não há uma "resposta certa" única, mas as trilhas citadas devem aparecer no Top 3
# e o sistema deve sinalizar empate parcial/confiança baixa em vez de fingir certeza.
PERSONAS_AMBIGUAS = [
    _p("Marina (dados + web)", "Gosta tanto de dados quanto de desenvolvimento web.",
       None, dados=5, matematica=4, bancos=4, logica=4, codigo=5, design=5, obj_usuario=5, obj_pesquisa=4),
    _p("Rafael (infra + nuvem + automação)", "Perfil clássico de borda entre DevOps e Cloud.",
       None, infra=5, nuvem=5, automacao=5, obj_escala=4, obj_incidentes=3, codigo=3, logica=3),
]
TOP3_AMBIGUAS = {
    "Marina (dados + web)": {"frontend", "ciencia_dados", "eng_dados", "backend"},
    "Rafael (infra + nuvem + automação)": {"devops", "cloud"},
}


def executar() -> bool:
    from engine import calcular_ranking

    acertos = 0
    for p in PERSONAS:
        d = calcular_ranking(p["respostas"])
        topo = d.top3[0]
        ok = topo.chave == p["esperada"]
        acertos += ok
        marca = "OK   " if ok else "FALHA"
        top3 = ", ".join(f"{t.nome.split(' (')[0]} {t.percentual:.0f}%" for t in d.top3)
        print(f"[{marca}] {p['nome']:<34} esperado: {p['esperada']:<15} Top 3: {top3}")
    print(f"\n{acertos}/{len(PERSONAS)} personas corretas")

    print("\nPerfis ambíguos:")
    for p in PERSONAS_AMBIGUAS:
        d = calcular_ranking(p["respostas"])
        top3 = ", ".join(f"{t.nome.split(' (')[0]} {t.percentual:.0f}%" for t in d.top3)
        print(f"  {p['nome']:<36} confiança {d.confianca:<6} margem {d.margem_pp:>4.1f} pp  Top 3: {top3}")
    return acertos == len(PERSONAS)


if __name__ == "__main__":
    raise SystemExit(0 if executar() else 1)
