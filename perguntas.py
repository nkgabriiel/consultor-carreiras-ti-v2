"""Perguntas da entrevista e catálogo das 10 trilhas.

Cada pergunta tem uma chave (usada como campo do Fact `Perfil`), o texto exibido
e as opções no formato {valor_interno: rótulo_exibido}.
"""

TRILHAS = {
    "backend": ("Desenvolvimento Back-end",
                "Lógica de servidores, construção de APIs, regras de negócio e bancos de dados."),
    "frontend": ("Desenvolvimento Front-end & UI/UX",
                 "Interfaces web responsivas, experiência do usuário e frameworks reativos."),
    "ciencia_dados": ("Ciência de Dados e Machine Learning",
                      "Estatística, modelagem preditiva, análise de grandes massas de dados e IA."),
    "eng_dados": ("Engenharia de Dados",
                  "Arquitetura de dados, pipelines (ETL/ELT) e infraestrutura para Data Lakes."),
    "ciberseguranca": ("Cibersegurança (Security / Pentesting)",
                       "Defesa cibernética, análise de vulnerabilidades, criptografia e redes seguras."),
    "devops": ("DevOps & SRE",
               "Automação de processos, integração e entrega contínua (CI/CD) e contêineres."),
    "cloud": ("Computação em Nuvem (Cloud Architecture)",
              "Planejamento, migração e gestão de infraestruturas escaláveis (AWS/Azure/GCP)."),
    "mobile": ("Desenvolvimento Mobile",
               "Ecossistema de dispositivos móveis (nativo ou multiplataforma com Flutter/React Native)."),
    "qa": ("Engenharia de Qualidade e Testes (QA)",
           "Testes automatizados, confiabilidade de software e processos de qualidade."),
    "produto": ("Gestão de Produtos (Product Management)",
                "Ponte entre negócio, design e desenvolvimento, metodologias ágeis e priorização."),
}

# Ordem usada como último critério de desempate (e na exibição).
ORDEM_TRILHAS = list(TRILHAS.keys())

PERGUNTAS = [
    {
        "chave": "matematica",
        "texto": "Qual é a sua afinidade com matemática e estatística?",
        "opcoes": {"baixa": "Baixa", "media": "Média", "alta": "Alta"},
    },
    {
        "chave": "atuacao",
        "texto": "O que você mais gostaria de fazer no dia a dia de trabalho?",
        "opcoes": {
            "algoritmos": "Escrever algoritmos lógicos e regras de negócio",
            "layouts": "Criar layouts visuais e interfaces",
            "servidores": "Lidar com servidores e a lógica por trás das aplicações",
            "dados_brutos": "Analisar dados brutos",
            "seguranca": "Garantir segurança e encontrar vulnerabilidades",
            "automacao": "Automatizar processos de build, deploy e operação",
            "arquitetura_nuvem": "Desenhar e dimensionar infraestrutura na nuvem",
            "testes": "Testar software e caçar defeitos",
            "apps_celular": "Construir aplicativos para celular",
            "produto": "Definir o que construir e priorizar o trabalho do time",
        },
    },
    {
        "chave": "linguagem",
        "texto": "Com qual linguagem ou ferramenta você tem mais afinidade hoje?",
        "opcoes": {
            "python": "Python",
            "javascript": "JavaScript / TypeScript",
            "java_go_csharp": "Java, C# ou Go",
            "sql": "SQL / bancos de dados",
            "linux_redes": "Linux / Redes",
            "mobile": "Dart, Kotlin ou Swift",
            "nenhuma": "Nenhuma / Iniciante",
        },
    },
    {
        "chave": "entrega",
        "texto": "Que tipo de entrega de valor você prefere?",
        "opcoes": {
            "produto_usuario": "O produto final que o usuário usa",
            "infraestrutura": "A infraestrutura que sustenta o sistema",
            "seguranca": "A segurança contra invasões",
            "insights_dados": "Insights e previsões a partir de dados",
            "qualidade": "A confiança de que o software funciona",
            "decisao_negocio": "Decisões de negócio bem fundamentadas",
        },
    },
    {
        "chave": "dados",
        "texto": "Se o trabalho envolver dados, qual parte te atrai mais?",
        "opcoes": {
            "nao": "Não quero trabalhar com foco em dados",
            "modelar": "Analisar e criar modelos preditivos",
            "pipelines": "Construir pipelines que coletam e transformam dados em escala",
        },
    },
    {
        "chave": "automatiza",
        "texto": "Você gosta de automatizar tarefas repetitivas (scripts, CI/CD, contêineres)?",
        "opcoes": {"sim": "Sim", "nao": "Não"},
    },
    {
        "chave": "nuvem",
        "texto": "Você tem interesse em provedores de nuvem (AWS, Azure, GCP)?",
        "opcoes": {"sim": "Sim", "nao": "Não"},
    },
    {
        "chave": "interacao",
        "texto": "Você gosta de conversar com clientes e áreas de negócio para decidir prioridades?",
        "opcoes": {"sim": "Sim", "nao": "Não"},
    },
    {
        "chave": "visual",
        "texto": "A aparência e a usabilidade das telas são importantes para você?",
        "opcoes": {"sim": "Sim", "nao": "Não"},
    },
]

CHAVES = [p["chave"] for p in PERGUNTAS]
OPCOES_VALIDAS = {p["chave"]: set(p["opcoes"]) for p in PERGUNTAS}
