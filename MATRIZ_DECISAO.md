# Matriz de decisão

Cada linha mostra uma regra, a condição que a dispara e o efeito sobre a trilha. Regras que afetam mais de uma trilha aparecem em cada uma delas. Pontuação final = soma dos efeitos; vence a trilha com mais pontos.

## Estágio 1: regras de derivação (geram fatos inferidos)

| Regra | Condição | Fato derivado |
|---|---|---|
| R01 | matemática = alta E dados = modelar | perfil científico |
| R02 | atuação em {servidores, automação, nuvem} E entrega = infraestrutura | perfil de infraestrutura |

## Estágio 2: regras de pontuação por trilha

### Desenvolvimento Back-end

| Regra | Condição | Pontos |
|---|---|---|
| R03 | atuação = algoritmos | +3 |
| R04 | atuação = servidores E entrega = produto para o usuário | +4 |
| R05 | linguagem em {Java/C#/Go, SQL} E dados = não E visual = não | +2 |

### Desenvolvimento Front-end & UI/UX

| Regra | Condição | Pontos |
|---|---|---|
| R06 | atuação = layouts | +4 |
| R07 | visual = sim E entrega = produto para o usuário | +3 |

### Ciência de Dados e Machine Learning

| Regra | Condição | Pontos |
|---|---|---|
| R08 | [fato inferido] perfil científico | +5 |
| R09 | atuação = dados brutos E dados = modelar | +3 |
| R10 | matemática = baixa E dados = modelar | -3 |
| R12 | dados = pipelines E matemática em {baixa, média} | -2 |

### Engenharia de Dados

| Regra | Condição | Pontos |
|---|---|---|
| R08 | [fato inferido] perfil científico | -2 |
| R11 | dados = pipelines E atuação em {dados brutos, servidores} | +5 |
| R12 | dados = pipelines E matemática em {baixa, média} | +2 |

### Cibersegurança (Security / Pentesting)

| Regra | Condição | Pontos |
|---|---|---|
| R13 | atuação = segurança | +5 |
| R14 | entrega = segurança | +3 |

### DevOps & SRE

| Regra | Condição | Pontos |
|---|---|---|
| R15 | atuação = automação E automatiza = sim | +5 |
| R16 | linguagem = Linux/Redes E automatiza = sim | +3 |
| R17 | [fato inferido] perfil de infra E nuvem = não | +3 |

### Computação em Nuvem (Cloud Architecture)

| Regra | Condição | Pontos |
|---|---|---|
| R18 | atuação = arquitetura em nuvem | +5 |
| R19 | [fato inferido] perfil de infra E nuvem = sim | +4 |

### Desenvolvimento Mobile

| Regra | Condição | Pontos |
|---|---|---|
| R20 | atuação = apps para celular | +5 |
| R21 | linguagem = Dart/Kotlin/Swift E entrega = produto para o usuário | +3 |

### Engenharia de Qualidade e Testes (QA)

| Regra | Condição | Pontos |
|---|---|---|
| R22 | atuação = testes | +5 |
| R23 | entrega = qualidade | +4 |

### Gestão de Produtos (Product Management)

| Regra | Condição | Pontos |
|---|---|---|
| R24 | atuação = produto | +5 |
| R25 | interação = sim E entrega = decisão de negócio | +4 |

