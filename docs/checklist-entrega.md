# Checklist de entrega

Tudo o que falta para entregar o Radar Remoto, em ordem. Marque `[x]` ao concluir. A matriz dos 29 critérios continua em [progresso.md](progresso.md); este arquivo só controla o que ainda precisa ser feito.

Situação em 12/11/2026: o agente roda no modo real (gpt-6-luna, `text-embedding-3-small`, LangSmith) e os 17 testes passam. O [experimento mais recente no LangSmith](https://smith.langchain.com/o/f3d9bd48-9e7a-4483-9e65-dd3af105169e/projects/p/a3120d0b-7f4e-4661-aa38-fb299c061a6b) deu correção semântica 12/12, regressão 12/12, trajetória 12/12 e afirmações confirmadas 6/8. Gasto acumulado: cerca de US$ 0,02.

## 1. Decisões

- [x] **Interface (rubrica 5.5).** Decidido em 12/11/2026: a única interface é a do Claude Design ([prompt](prompt-claude-design.md)), em HTML com Vue. Não haverá Streamlit. O 5.5 continua como "Alternativa", e o risco de perder esse item foi aceito. A UI fica para depois (passo 2.2).

## 2. Técnico

- [x] **2.1 Investigar os cenários reprovados pelo juiz.** A nota foi de 9/12 para 12/12:
  - a evidência agora inclui fuso e inglês;
  - a mensagem nomeia a fonte que falhou;
  - a resposta do SQL inclui a empresa;
  - o resumo do RAG traz as consultas e o top 2;
  - o juiz recebe a trilha de ferramentas e sabe que o campo `vagas` só existe em buscas.
- [ ] **2.2 Endpoints da interface do Claude Design** (deixado para depois, quando o front estiver pronto): `/chat/stream` (SSE com as etapas de `_turn`), `GET`/`POST /curriculo`, `/curriculo/info`, `/curriculo/reset`, `/modelos` e `/modelo`, conforme o contrato do prompt. Depois, salvar o HTML exportado em `web/index.html`.
- [x] **2.3 Reexecutar os notebooks com o modelo real.** Os notebooks 01 a 06 rodaram sem erro com `NOTEBOOK_OPENAI=1`, `NOTEBOOK_LIVE_APIS=1` e `NOTEBOOK_LANGSMITH=1`. Ficaram nas células:
  - o perfil extraído pelo gpt-6-luna (02);
  - o ReAct e a function calling com tokens reais (03);
  - o SQL gerado pelo LLM retornando a Atlas (05);
  - o link do LangSmith (06).
  O 06 agora fixa o cenário Atlas em modo dummy, independente do `.env`. O `stop` passou a ser aplicado no cliente, porque o ReAct clássico depende dele.
- [ ] **2.4 Rodar uma busca mais ampla para a demonstração**, como "backend" ou "engenheiro de software". A busca por "Python" trouxe só 3 vagas reais, e a recomendada não informa salário, então a conversão de câmbio fica sem exemplo.

## 3. Documentação

- [ ] **3.1 `progresso.md`:**
  - mudar o 5.6 de "Bloqueado" para "Evidenciado", com o link do experimento;
  - remover os "pendente de chave" dos itens 2.4, 4.3 e 5.1;
  - atualizar as notas de rubrica no fim dos notebooks, que ainda dizem "OpenAI pendente" e "depende de chave". Edite em `scripts/notebooks.py` e nas células markdown já executadas, sem regerar os notebooks, para não perder as saídas;
  - atualizar a tabela de marcos;
  - no 5.5, trocar "UI de entrega provisória é HTML" por: a interface final é HTML com Vue, feita no Claude Design.
- [ ] **3.2 README:**
  - remover "O experimento remoto ainda não foi executado";
  - registrar os resultados da avaliação;
  - citar a compatibilidade com modelos de raciocínio (o `stop` descartado e o texto extraído dos blocos de conteúdo).
- [ ] **3.3 Relatório em PDF** (`output/pdf/ian_trinta_ai-agents_langchain-agents.pdf`): incluir os resultados do modo real e do LangSmith, além do custo medido.
- [ ] **3.4 `gravacao.md`:** ajustar o roteiro à interface do Claude Design e às perguntas que funcionam com as vagas reais.

## 4. Ponto final (só depois de tudo acima)

Estes passos congelam a entrega. Se alguma coisa das seções 1 a 3 mudar depois, refaça os passos a partir dela.

- [ ] **4.1 Testes finais:** `.venv/bin/python -m pytest -q` e `.venv/bin/python -m scripts.evaluate`.
- [ ] **4.2 Avaliação final no LangSmith:** `.venv/bin/python -m scripts.evaluate --langsmith --share`. O `--share` gera um link **público** do dataset fictício.
- [ ] **4.3 Testar o link compartilhado numa janela anônima.**
- [ ] **4.4 Gerar o ZIP de novo:** `.venv/bin/python -m scripts.package_submission`. O ZIP atual é anterior às correções de 12/11. Confira se o currículo pessoal (`data/curriculos/`) e o `.env` ficaram **fora** do ZIP.
- [ ] **4.5 Gravar o vídeo da defesa**, com você na webcam, seguindo o [roteiro](gravacao.md). Antes, rode `scripts.setup_assets` e faça um turno de aquecimento para os pesos já estarem carregados.
- [ ] **4.6 Enviar no Moodle:** o ZIP, o PDF, o vídeo e o link do LangSmith.
- [ ] **4.7 Depois da entrega:** revogar ou rotacionar as chaves da OpenAI e do LangSmith se elas aparecerem no vídeo ou em algum print.
