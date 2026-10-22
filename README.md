# Consultor Inteligente de Carreiras em TI

Sistema especialista baseado em regras (Python + [Experta](https://github.com/nilp0inter/experta) + Streamlit)
que entrevista o usuário e recomenda uma entre 10 trilhas de carreira em TI, mostrando as regras que
levaram à conclusão.

Trabalho da disciplina de Inteligência Artificial, Ciência da Computação, UNIPAC Barbacena.

## Trilhas

Back-end, Front-end & UI/UX, Ciência de Dados e ML, Engenharia de Dados, Cibersegurança, DevOps & SRE,
Cloud Architecture, Mobile, QA e Gestão de Produtos.

## Como instalar e executar

Requer Python 3.10 ou superior (testado em 3.13).

```bash
git clone <url-do-repositorio>
cd consultor-carreiras-ti

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Para rodar as personas de validação:

```bash
python personas.py      # tabela com esperado x obtido
pytest -q               # testes automatizados
```

### Observação sobre o Experta no Python 3.10+

O Experta depende do `frozendict==1.2`, que usa `collections.Mapping` (removido no Python 3.10).
Sem correção, o `import experta` falha com `AttributeError`. O topo de `engine.py` faz um patch
de compatibilidade antes do import, então nada precisa ser feito manualmente. **Importe sempre
`engine` antes de qualquer outro módulo que use o Experta.**

## Estrutura

| Arquivo | Conteúdo |
|---|---|
| `perguntas.py` | Catálogo das 10 trilhas e das 9 perguntas da entrevista |
| `engine.py` | Base de conhecimento (25 regras Experta), tabela `REGRAS` e função `recomendar()` |
| `app.py` | Interface Streamlit |
| `personas.py` | 12 personas de teste com a trilha esperada |
| `test_personas.py` | Testes pytest |
| `MATRIZ_DECISAO.md` | Matriz de decisão (Fase 1), gerada por `python engine.py > MATRIZ_DECISAO.md` |

## Como o motor funciona

**Entrevista.** São 9 perguntas objetivas: as 4 dimensões do enunciado (afinidade matemática,
preferência de atuação, linguagem/ferramenta, tipo de entrega) mais 5 de apoio (foco em dados,
gosto por automação, interesse em nuvem, interação com negócio e importância do visual). As extras
existem porque 4 dimensões não separam 10 trilhas, principalmente QA, Produto, Cloud e DevOps.

**Fatos.** As respostas viram um único fato `Perfil(...)`. Regras de derivação criam fatos
intermediários `Inferido(perfil=...)`.

**Regras em dois estágios (encadeamento para frente).**

1. *Derivação (R01-R02):* cruzam várias respostas e declaram um fato inferido
   (`perfil científico`, `perfil de infraestrutura`).
2. *Pontuação (R03-R25):* cada regra soma ou subtrai pontos de trilhas e registra o motivo.
   Algumas (R08, R17, R19) só disparam por causa de um fato inferido no estágio 1.

**Decisão.** Vence a trilha com mais pontos. Desempate: maior peso de uma única regra, depois a
ordem das trilhas. Se nenhuma trilha fica com pontos positivos, o sistema diz que as respostas são
contraditórias em vez de chutar. A confiança vem da margem entre a 1ª e a 2ª colocada
(≥4 alta, 2-3 média, <2 perfil misto).

**Cientista x Engenheiro de Dados.** São separados por regras cruzadas:

- R08 (matemática alta + modelagem) dá +5 a Ciência de Dados e −2 a Eng. de Dados.
- R11 (pipelines + dados brutos/servidores) dá +5 a Eng. de Dados.
- R12 (pipelines + matemática baixa/média) dá +2 a Eng. de Dados e −2 a Ciência de Dados.
- R10 (matemática baixa + modelagem) tira 3 pontos de Ciência de Dados.

**Justificativa.** A interface mostra a trilha, as regras que somaram para ela, o ranking e a
lista completa das regras disparadas na ordem de execução.

## Validação com personas

`python personas.py` roda 12 personas: as 4 do enunciado (analítica, infra/segurança,
visual/front-end, negócios/produto), uma para cada trilha restante e 2 casos confundíveis entre
Ciência e Engenharia de Dados. Resultado atual: **12/12 corretas**.

Limitação: as personas foram escritas junto com os pesos das regras, então acertar todas é uma
verificação de consistência, não de precisão. Em uma amostra de 4.000 respostas aleatórias (que
são incoerentes por natureza), cerca de 4% resultam em "inconclusivo" e cerca de 10% terminam em
empate exato no topo, resolvido pelo critério de desempate.

## Limitações conhecidas

- Os pesos são julgamento de quem montou a base, não vêm de dados reais.
- As trilhas vizinhas (DevOps/Cloud, Back-end/Eng. de Dados) dependem das perguntas de apoio. Se o
  usuário responde de forma ambígua, a confiança sai baixa e o sistema indica a 2ª opção.
