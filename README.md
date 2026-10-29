# Consultor Avançado de Carreiras em TI (Etapa 2)

Evolução do [consultor de carreiras da Etapa 1](https://github.com/nkgabriiel/consultor-carreiras-ti):
um sistema especialista com **pontuação ponderada e tratamento de incerteza**, em Python + Streamlit.
Em vez de recomendar uma única trilha por regras SE-ENTÃO, ele lê respostas graduais (escala 1 a 5),
calcula a **compatibilidade percentual** com 10 trilhas, aponta as **lacunas de competência** para o nível
Júnior e gera um **roadmap personalizado** (o que estudar, certificações e projetos de portfólio).

Trabalho da disciplina de Inteligência Artificial, Ciência da Computação, UNIPAC Barbacena.

## Trilhas

Back-end, Front-end & UI/UX, Ciência de Dados e ML, Engenharia de Dados, Cibersegurança, DevOps & SRE,
Cloud Architecture, Mobile, QA e Gestão de Produtos.

## Como instalar e executar

Requer Python 3.10 ou superior (testado em 3.14).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Validação:

```bash
python personas.py     # tabela com esperado x obtido
pytest -q              # 72 testes (motor, roadmap, casos limite e fluxo da interface)
```

### Windows (PowerShell), sem ativar o venv

Se o `.venv` já existe e tem as dependências instaladas, chame o Python dele direto, a partir da pasta
do projeto. Assim não é preciso ativar nada:

```powershell
cd C:\caminho\para\consultor-carreiras-ti-v2
.venv\Scripts\python.exe -m streamlit run app.py     # interface em http://localhost:8501
.venv\Scripts\python.exe personas.py                 # personas: esperado x obtido
.venv\Scripts\python.exe -m pytest -q                # testes automatizados
```

Na primeira vez, crie o ambiente e instale as dependências:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se os acentos saírem quebrados no terminal, rode antes `$env:PYTHONIOENCODING="utf-8"`.

## Estrutura

| Arquivo | Conteúdo |
|---|---|
| `regras_carreiras.json` | **Toda a base de conhecimento**: perguntas, pesos por trilha, penalidades, sinergias, habilidades e roadmaps |
| `base_conhecimento.py` | Carrega o JSON e valida a consistência (pesos, trilhas e habilidades referenciadas existem) |
| `engine.py` | Motor de inferência: pontuação ponderada, ranking Top 3, justificativas e detecção de empate parcial |
| `roadmap.py` | Análise de gaps, estimativa de esforço e geração do roadmap (também exporta Markdown) |
| `app.py` | Interface Streamlit em etapas (wizard) |
| `personas.py` | 10 personas (uma por trilha) e 2 perfis ambíguos |
| `test_engine.py`, `test_roadmap.py`, `test_app.py` | Testes automatizados |

## Como o motor funciona

**Entrada gradual.** As 21 perguntas usam escala Likert de 1 a 5 (14 de afinidades técnicas e 7 de
objetivos de carreira). Cada resposta vira um grau em [0, 1]: `(resposta - 1) / 4`.

**Pontuação ponderada.** Para cada trilha, `pontos = Σ grau × peso`, com pesos de −5 a +5 definidos no
JSON. O peso negativo desconta pontos quando o usuário tem muita afinidade com algo que conflita com a
trilha. A aderência base é `pontos / máximo`, em que o máximo é a soma dos pesos positivos da trilha
(100% = quem respondeu 5 em tudo que a trilha valoriza).

**Penalidades e sinergias** (`regras_combinadas` no JSON). Ajustam o percentual em pontos percentuais (pp):

- *Penalidade* para perfis conflitantes. Ex.: "não gosto de escrever código" (P01) tira 25 pp de Back-end;
  matemática baixa (P02) tira 25 pp de Ciência de Dados.
- *Sinergia* para combinações típicas. Ex.: infraestrutura alta + automação alta (S03) dá +8 pp a DevOps;
  matemática alta + dados alta (S01) dá +8 pp a Ciência de Dados e −4 pp a Engenharia de Dados.

O resultado é limitado a [0, 100] e ordenado. Desempate: maior aderência, depois maior pontuação bruta,
depois a ordem das trilhas no JSON.

**Incerteza.** O diagnóstico informa:

- *confiança*: alta (1ª à frente da 2ª por 10 pp ou mais), média, ou baixa (5 pp ou menos, "perfil misto");
- *empate parcial*: lista as trilhas dentro de 5 pp da primeira e quais respostas puxam as duas para cima;
- *inconclusivo*: nenhuma trilha passa de 25% (respostas pouco informativas ou contraditórias).

**Gaps e roadmap.** Cada trilha define as habilidades exigidas de um Júnior, com nível alvo (0 a 3) e
prioridade. O usuário informa seu nível atual e o sistema calcula a lacuna de cada habilidade, a prontidão
para Júnior (%), as horas estimadas (a partir de `horas_por_nivel`, ajustadas pela experiência) e o prazo
em semanas segundo as horas de estudo por semana. O plano separa o que nunca foi estudado do que precisa de
reforço e sugere certificações e projetos para o GitHub. Quem já tem experiência vê primeiro os projetos
intermediários. O plano pode ser baixado em Markdown.

## Interface (Streamlit)

Wizard em 5 etapas: **1** Perfil pessoal, **2** Afinidades técnicas, **3** Objetivos de carreira,
**4** Resultado (Top 3 com percentuais, radar, barras, tabela e justificativa por trilha) e
**5** Plano de ação (autoavaliação das habilidades, métricas de prontidão, fases de estudo, certificações e
projetos). A aba "Base de conhecimento" mostra a matriz de pesos (Pandas) e as regras combinadas lidas do JSON.

## Alterando o conhecimento sem mexer no código

Edite `regras_carreiras.json` (um peso, uma regra, uma certificação) e reinicie o app. Na carga, o
`base_conhecimento.py` rejeita a base se algo estiver inconsistente, como peso para pergunta inexistente,
trilha sem roadmap ou operador inválido. Um teste (`test_codigo_python_nao_conhece_as_trilhas`) garante que
nenhuma trilha ou pergunta fica fixa no código do motor.

## Testes de robustez e casos limite (Fase 5)

- Todas as respostas em 1: resultado **inconclusivo**. Em 5: percentual limitado a 100% e **empate parcial**.
  Em 3 (neutro): confiança nunca "alta".
- **Marina** (gosta de dados e de web): Ciência de Dados 90% e Front-end 85% ficam juntas no topo, com
  confiança baixa e explicação do empate. **Rafael** (infra + nuvem + automação): Cloud 82% e DevOps 79%.
- Entradas inválidas (valor fora de 1 a 5, tipo errado, pergunta faltando ou desconhecida) levantam erro claro.
- Base de conhecimento corrompida é recusada na carga.

## Limitações conhecidas

- Os pesos são julgamento de quem montou a base, não vêm de dados reais; as personas foram escritas junto
  com os pesos, então acertar todas é uma verificação de consistência, não de precisão.
- A aderência percentual é relativa ao perfil ideal de cada trilha, não uma probabilidade estatística.
- Estimativas de horas e a lista de certificações são referências gerais e mudam com o tempo.
