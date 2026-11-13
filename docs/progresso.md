# Progresso e evidências

Mapeamento dos 29 itens da [rubrica oficial do Infnet](https://lms.infnet.edu.br/moodle/mod/assign/view.php?id=475711). Os IDs indicam a competência e sua posição na rubrica. **Evidenciado** significa que há uma saída local ou uma descrição verificável; não representa a nota atribuída pelo professor.

| Marco | Situação | Próximo passo |
|---|---|---|
| M0 · Ambiente | [Notebook 00](../notebooks/00_visao_geral.ipynb) apresenta o projeto; Python 3.12, dependências fixadas, imports e pesos locais validados | Validar modelo OpenAI com a chave do projeto |
| M1 · Chain | Notebook 02 executado | Repetir com o modelo real, se desejado |
| M2 · ReAct | Notebook 03 executado; HTTP real com modelo roteirizado | Repetir a chamada estruturada com OpenAI |
| M3 · Memória | Notebook 03 e quatro turnos no navegador validados | Mostrar a recuperação contextual na gravação |
| M4 · Ferramentas | Notebook 05 executado; SQLite e reescrita PT/EN validados | Executar text-to-SQL com OpenAI |
| M5 · Integrador | Chat, NLI local, histórico e avaliação local validados | Executar LangSmith e conferir acesso ao link |
| M6 · Defesa | PDF, código, notebooks com saídas e roteiro preparados | Gravar com o autor na webcam |

| ID | Cenário / saída esperada | Evidência | Status | Bloqueio ou limite |
|---|---|---|---|---|
| 1.1 | Anatomia, padrão híbrido e maturidade | 02 · arquitetura | Evidenciado | — |
| 1.2 | Plano hierárquico, memória curta e longa | 02 · arquitetura | Evidenciado | — |
| 1.3 | Prompts de texto e de chat | 02 · lcel | Evidenciado | — |
| 1.4 | JSON validado como PerfilCandidato | 02 · lcel | Evidenciado | — |
| 1.5 | Invoke, batch, stream e @chain | 02 · lcel | Evidenciado | — |
| 1.6 | LCEL e decisão técnica | 02 · lcel e justificativa | Evidenciado | — |
| 2.1 | Comparar quatro orquestradores | 03 · orquestradores | Evidenciado | — |
| 2.2 | ReAct clássico com memória e ferramentas | 03 · react | Evidenciado | Decisão do modelo roteirizada |
| 2.3 | Sequencial, paralela e RouterChain | 03 · composicao | Evidenciado | — |
| 2.4 | Function calling aciona API externa | 03 · http; [registro](../output/chamadas-http.json) | Evidenciado | HTTP real; geração da chamada por OpenAI pendente |
| 2.5 | PTCF, poucos exemplos e etapas públicas de decisão | 03 · ptcf | Evidenciado | Demonstra resumo verificável, sem cadeia privada |
| 2.6 | Parser, memória, FAISS, callbacks | 03 · react e confiabilidade | Evidenciado | Contagem de tokens não existe no modelo roteirizado |
| 3.1 | Classificar memórias com CoALA | 04 · coala | Evidenciado | — |
| 3.2 | Janela, sumarização e busca vetorial | 04 · turnos | Evidenciado | Memória mantida no processo |
| 3.3 | Comparar ferramentas de memória | 04 · coala | Evidenciado | — |
| 3.4 | ConversationBufferMemory em conversa | 04 · buffer | Evidenciado | — |
| 3.5 | Intenção de câmbio e posição 2 | 04 · turnos | Evidenciado | — |
| 3.6 | Resolver referência em quatro turnos | 04 · turnos e navegador | Evidenciado | Dados fictícios |
| 4.1 | Ferramentas fixas e semânticas | 05 · ferramentas | Evidenciado | — |
| 4.2 | Separar API externa e interface interna | 05 · ferramentas; 03 · http | Evidenciado | — |
| 4.3 | Texto vira SQL e retorna Atlas | 05 · sql | Evidenciado | Regras no dummy; geração via LLM pendente de chave |
| 4.4 | Recuperador usa FAISS existente | 01 · seções 5 a 7; 05 · recuperacao | Evidenciado | — |
| 4.5 | Alvo fora do top 2 e recuperado após reescrita | 05 · recuperacao | Evidenciado | Corpus fictício |
| 5.1 | Contradição NLI e correção no agente | 06 · integracao | Evidenciado | NLI e regra executados; checagem com LLM remoto pendente |
| 5.2 | API, SQL, câmbio e RAG no mesmo integrador | 06 · integracao e código | Evidenciado | — |
| 5.3 | create_openai_tools_agent + AgentExecutor | 06 · integracao | Evidenciado | Executor real, modelo roteirizado |
| 5.4 | Histórico por session_id | 06 · integracao; 04 · turnos | Evidenciado | — |
| 5.5 | Interface Streamlit | 06 · integracao comprova HTTP/HTML | Alternativa | A rubrica nomeia Streamlit; a UI de entrega provisória é HTML. A CLI é prevista no enunciado para o vídeo. |
| 5.6 | Avaliação publicada no LangSmith | 06 · avaliacao e [regressão local](../output/avaliacao-local.json) | Bloqueado | Faltam credenciais OpenAI e LangSmith neste workspace |

Os estados de acompanhamento são **A fazer**, **Em andamento**, **Bloqueado** e **Evidenciado**. A marca **Alternativa** identifica um desvio intencional da tecnologia pedida pela rubrica. Não somar o 5.5 nem o 5.6 como comprovados no formato nominal.
