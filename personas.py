"""Personas de teste (Fase 4).

Cada persona tem respostas fixas e a trilha que o sistema DEVE recomendar.
Rode `python personas.py` para ver a tabela de validação.
"""


def _p(nome, descricao, esperada, **respostas):
    return {"nome": nome, "descricao": descricao, "esperada": esperada, "respostas": respostas}


PERSONAS = [
    # --- As 4 do enunciado --------------------------------------------------
    _p("Ana (analítica)",
       "Gosta de estatística, analisa dados brutos e quer prever fenômenos com modelos.",
       "ciencia_dados",
       matematica="alta", atuacao="dados_brutos", linguagem="python", entrega="insights_dados",
       dados="modelar", automatiza="nao", nuvem="nao", interacao="nao", visual="nao"),
    _p("Bruno (infra/segurança)",
       "Vive no terminal Linux, gosta de redes e de proteger sistemas contra invasões.",
       "ciberseguranca",
       matematica="media", atuacao="seguranca", linguagem="linux_redes", entrega="seguranca",
       dados="nao", automatiza="nao", nuvem="nao", interacao="nao", visual="nao"),
    _p("Carla (visual/front-end)",
       "Foca na aparência das telas e na experiência de quem usa o produto.",
       "frontend",
       matematica="baixa", atuacao="layouts", linguagem="javascript", entrega="produto_usuario",
       dados="nao", automatiza="nao", nuvem="nao", interacao="nao", visual="sim"),
    _p("Diego (negócios/produto)",
       "Conversa com clientes, prioriza o que construir e decide com base em negócio.",
       "produto",
       matematica="baixa", atuacao="produto", linguagem="nenhuma", entrega="decisao_negocio",
       dados="nao", automatiza="nao", nuvem="nao", interacao="sim", visual="nao"),

    # --- As demais trilhas --------------------------------------------------
    _p("Eduarda (back-end)",
       "Gosta de lógica, regras de negócio e bancos de dados; Java é a linguagem principal.",
       "backend",
       matematica="media", atuacao="algoritmos", linguagem="java_go_csharp", entrega="produto_usuario",
       dados="nao", automatiza="nao", nuvem="nao", interacao="nao", visual="nao"),
    _p("Felipe (engenheiro de dados)",
       "Quer montar pipelines ETL em SQL e Python sobre dados brutos; modelagem não é o foco.",
       "eng_dados",
       matematica="media", atuacao="dados_brutos", linguagem="sql", entrega="infraestrutura",
       dados="pipelines", automatiza="nao", nuvem="sim", interacao="nao", visual="nao"),
    _p("Gisele (DevOps)",
       "Automatiza deploys, escreve pipelines de CI/CD e cuida de contêineres em Linux.",
       "devops",
       matematica="media", atuacao="automacao", linguagem="linux_redes", entrega="infraestrutura",
       dados="nao", automatiza="sim", nuvem="nao", interacao="nao", visual="nao"),
    _p("Henrique (cloud)",
       "Quer desenhar arquiteturas escaláveis e migrar sistemas para AWS/Azure/GCP.",
       "cloud",
       matematica="media", atuacao="arquitetura_nuvem", linguagem="python", entrega="infraestrutura",
       dados="nao", automatiza="nao", nuvem="sim", interacao="nao", visual="nao"),
    _p("Isabela (mobile)",
       "Constrói apps para celular em Flutter e se importa com a experiência na tela pequena.",
       "mobile",
       matematica="media", atuacao="apps_celular", linguagem="mobile", entrega="produto_usuario",
       dados="nao", automatiza="nao", nuvem="nao", interacao="nao", visual="sim"),
    _p("João (QA)",
       "Gosta de achar defeitos, escrever testes automatizados e garantir a qualidade.",
       "qa",
       matematica="media", atuacao="testes", linguagem="java_go_csharp", entrega="qualidade",
       dados="nao", automatiza="sim", nuvem="nao", interacao="nao", visual="nao"),

    # --- Casos confundíveis (Cientista de Dados x Engenheiro de Dados) --------
    _p("Karina (matemática alta, mas pipelines)",
       "Ótima em matemática, mas prefere construir a infraestrutura que alimenta os dados.",
       "eng_dados",
       matematica="alta", atuacao="dados_brutos", linguagem="python", entrega="insights_dados",
       dados="pipelines", automatiza="nao", nuvem="sim", interacao="nao", visual="nao"),
    _p("Lucas (SQL, mas modelagem)",
       "Usa SQL no dia a dia, mas o que importa é modelar e prever com os dados.",
       "ciencia_dados",
       matematica="alta", atuacao="dados_brutos", linguagem="sql", entrega="insights_dados",
       dados="modelar", automatiza="nao", nuvem="sim", interacao="nao", visual="nao"),
]


def executar():
    from engine import recomendar
    from perguntas import TRILHAS

    acertos = 0
    for p in PERSONAS:
        r = recomendar(p["respostas"])
        ok = r.vencedora == p["esperada"]
        acertos += ok
        marca = "OK  " if ok else "FALHA"
        top = f"{r.nome} ({r.ranking[0][2]} pts)" if not r.inconclusivo else "inconclusivo"
        print(f"[{marca}] {p['nome']:<42} esperado: {TRILHAS[p['esperada']][0]:<42} obtido: {top}")
    print(f"\n{acertos}/{len(PERSONAS)} personas corretas")
    return acertos == len(PERSONAS)


if __name__ == "__main__":
    raise SystemExit(0 if executar() else 1)
