# Onde cada item da rubrica aparece na interface

A interface (`.venv/bin/uvicorn src.api:app`, depois [localhost:8000](http://127.0.0.1:8000)) foi desenhada para servir de roteiro da rubrica. Cada etapa da linha do tempo traz um selo com o item que ela cobre; clique na etapa para ver a evidência. Tudo o que aparece vem do backend: nada é roteirizado no navegador.

## Itens visíveis

| Item | Onde olhar | O que aparece |
|---|---|---|
| 1.3 | Trocar currículo, etapa "Extraindo perfil"; etapa "Escolhendo as ferramentas" | `ChatPromptTemplate` do perfil e o prompt do agente |
| 1.4 | Etapa "Extraindo perfil" do envio do currículo; skills no card | Perfil em JSON validado (`JsonOutputParser` → `PerfilCandidato`) |
| 2.2 | Etapa "Escolhendo as ferramentas" → "Rodar este pedido no ReAct clássico" | Thought, Action e Observation reais de `initialize_agent` |
| 2.3 | Etapa "Interpretando o pedido" | Rota escolhida pelo `RouterChain` e a composição sequencial/paralela da rota |
| 2.4 | Etapas Remotive, Arbeitnow e câmbio | Chamada HTTP, status e contagem de cada API externa |
| 2.5 | Etapa "Escolhendo as ferramentas" | Prompt PTCF, exemplos few-shot e a instrução de raciocínio passo a passo |
| 3.1 | Memória (pé do trilho), aba "Longo prazo" | Tipo CoALA de cada memória, origem e botão de esquecer |
| 3.2 | Memória, aba "Janela"; etapa "Escrevendo a resposta" | Tokens por parte da janela, buffer deslizante e memórias recuperadas por similaridade |
| 3.4 | Etapa "Escrevendo a resposta"; aba "Nesta conversa" | `ConversationBufferMemory` e as mensagens da sessão |
| 3.5 | Etapa "Interpretando o pedido" | JSON da intenção e das entidades |
| 3.6 | Segundo turno em diante ("converta o salário da segunda") | Referência resolvida pelo histórico; "Ver como cheguei aqui" em turnos antigos |
| 4.1 | Selos de cada etapa | hardcoded ou semântica |
| 4.2 | Selos "API externa"; legenda da linha do tempo | APIs externas e a API interna `POST /candidaturas` |
| 4.3 | Etapa "Gerando e executando SQL" | SQL gerado e as linhas devolvidas |
| 4.4 | Etapa "Recuperando trechos do currículo" | Trechos do índice FAISS com a similaridade |
| 4.5 | Etapas de busca ou do currículo, bloco "Antes / Depois" | Falha diagnosticada, consulta reescrita e o resultado depois |
| 5.1 | Etapa "Verificando afirmações"; "Por quê?" em cada vaga; nota "A verificação corrigiu" | Rótulo e score do NLI, veredito e correção aplicada |
| 5.2 | Um turno de busca com comparação de currículo | API, RAG e SQL no mesmo executor |
| 5.3 | Etapa "Escolhendo as ferramentas" | `create_openai_tools_agent` + `AgentExecutor` e as chamadas reais |
| 5.4 | Etapa "Escrevendo a resposta"; trilho de conversas | `RunnableWithMessageHistory` por `session_id` |
| 5.6 | Bloco "Avaliação no LangSmith"; "Ver no LangSmith" em cada resposta | Métricas do experimento e o trace do turno |

Parcialmente visíveis: 1.2 (diagrama de etapas e painel de memória), 1.5 (resposta em stream; `batch` e `@chain` aparecem na composição da rota), 1.6 (LCEL na composição) e 2.6 (a linha do tempo inteira vem dos callbacks do executor). As justificativas escritas desses itens estão nos notebooks.

Fora da interface: 1.1, 2.1 e 3.3 (classificação e comparações, nos notebooks 02, 03 e 04) e 5.5 (Streamlit, não adotado).

## Roteiro sugerido para o vídeo (modo real)

1. "Lembre que prefiro evitar vagas que pedem PHP e quero o salário sempre em reais." Mostre a linha "Guardei" e a aba "Longo prazo".
2. Nova conversa: "Mostre vagas remotas de engenheiro de software que aceitam Brasil". Acompanhe a linha do tempo, abra a etapa da Remotive (consulta reescrita, 4.5) e a verificação (5.1). Mostre "Memória usada".
3. "Converta o salário da primeira" ou "Qual combina mais com meu currículo?": memória entre turnos (3.6), câmbio real (2.4) ou RAG (4.4).
4. "Quais vagas eu ainda não apliquei?" depois de marcar "Já apliquei" numa vaga: SQL (4.3) e memória episódica (3.1).
5. Abra "Ver no LangSmith" e o bloco de avaliação (5.6).

Diferenças em relação ao protótipo da lousa, com o motivo de cada uma, estão na descrição do PR da interface.
