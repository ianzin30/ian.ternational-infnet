# ian.ternational

> Nome do agente na interface. O código e os notebooks ainda usam o nome de trabalho, Radar Remoto.

**Encontre vagas remotas internacionais e confira a evidência por trás de cada recomendação.**

```bash
uv venv --python 3.12
uv pip sync requirements.txt
.venv/bin/python -m scripts.setup_assets
.venv/bin/python -m scripts.cli
```

Digite `Mostre vagas remotas de Python`, depois `Só as que aceitam Brasil` e `Converta o salário da segunda`. A CLI mostra as ferramentas usadas e os trechos que sustentam a decisão. Para usar a interface, execute `.venv/bin/uvicorn src.api:app` e abra [localhost:8000](http://127.0.0.1:8000). Ela mostra, a cada turno, as etapas do agente, a fonte de cada dado e o item da rubrica que a etapa cobre: veja o [mapa da rubrica na interface](docs/ui-rubrica.md).

## Executar sem chave

O modo padrão usa currículo, vagas e taxas fictícias. O modelo de ferramentas é roteirizado, mas FastAPI, AgentExecutor, SQLite, Docling, FAISS e NLI são os mesmos componentes usados no fluxo de execução. O primeiro preparo baixa pesos públicos do Docling, do modelo multilíngue e do NLI; depois, use `HF_HUB_OFFLINE=1` se quiser rodar com os pesos em cache. O índice documental é salvo em `data/runtime/faiss_index/`; carregue apenas um índice produzido localmente pelo projeto.

| Comando | Resultado |
|---|---|
| `.venv/bin/python -m scripts.setup_assets` | Prepara currículo, FAISS e pesos do NLI. |
| `.venv/bin/python -m scripts.cli` | Abre a CLI com evidências por turno. Use `/sair` para encerrar. |
| `.venv/bin/uvicorn src.api:app` | Serve a interface (Vue, já compilada em `web/dist`), a API e `/docs`. |
| `npm --prefix web install && npm --prefix web run build` | Recompila a interface depois de editar `web/src`. Só é preciso Node para isso. |
| `.venv/bin/python -m scripts.evaluate` | Roda os 12 cenários e salva `output/avaliacao-local.json`. |
| `.venv/bin/python -m pytest -q` | Testa os cenários, contrato HTTP, isolamento SQL e regras de evidência. |

A rota `POST /candidaturas` registra uma ação que o candidato já tomou. Depois de buscar, envie `session_id`, `vaga_id` e `status` (`salva`, `enviada` ou `descartada`) pela página `/docs`. A operação atualiza apenas o SQLite local; não envia formulários a empregadores.

## Interface e API

A interface é uma aplicação Vue 3 em `web/src`, transplantada do protótipo do Claude Design ([handoff](web/HANDOFF.md)). O FastAPI serve o build de `web/dist`, então não é preciso Node para rodar.

| Rota | Uso |
|---|---|
| `POST /chat/stream` | Turno em Server-Sent Events: `stage` (cada etapa, com fonte, duração e dados), `token` (resposta), `memory` e `final`. |
| `POST /chat` | O mesmo turno, sem streaming. |
| `POST /react` | Roda o pedido no ReAct clássico (`initialize_agent`) e devolve Thought, Action e Observation. |
| `GET /memoria`, `DELETE /memoria/{id}` | Memória de longo prazo do usuário (SQLite + FAISS, k=3) e a memória da conversa. |
| `GET`/`POST /curriculo`, `/curriculo/info`, `/curriculo/reset` | PDF ativo, troca com etapas em SSE e restauração. |
| `GET /modelos`, `POST /modelo` | Alterna entre o modelo real e o demo roteirizado. |
| `GET /avaliacao` | Métricas do último experimento publicado no LangSmith. |

No modo real, o modelo decide o que guardar na memória pela ferramenta `guardar_memoria`; no modo demo, regras locais fazem esse papel e a interface mostra a origem. Em macOS, `torch` e `faiss-cpu` carregam cada um a sua cópia do OpenMP; `src/config.py` define `KMP_DUPLICATE_LIB_OK=TRUE` para o processo não abortar quando os dois são usados no mesmo turno.

## Verificar APIs reais e OpenAI

```bash
.venv/bin/python -m scripts.live_smoke
```

O teste acima usa chamadas estruturadas roteirizadas e executa HTTP real contra Remotive, Arbeitnow e AwesomeAPI. Consulte [o registro capturado](output/chamadas-http.json). Uma fonte pode responder normalmente sem retornar uma vaga para a busca.

Para validar o modelo também, copie `.env.example` para `.env`, defina `MODO_DUMMY=false` e preencha `OPENAI_API_KEY`. O modelo padrão é `gpt-6-luna` (`OPENAI_MODEL`). No modo real, os embeddings do RAG e da memória usam `text-embedding-3-small` (`OPENAI_EMBEDDING_MODEL`). O modo dummy continua com o MiniLM local e sem chave. Os vetores têm tamanhos diferentes, então cada modo tem seu índice: `data/runtime/faiss_index/` e `data/runtime/faiss_index_openai/`. O NLI de verificação continua local nos dois modos.

```bash
.venv/bin/python -m scripts.setup_assets
.venv/bin/python -m scripts.live_smoke --openai
.venv/bin/python -m scripts.cli
```

O `setup_assets` constrói o índice OpenAI quando `MODO_DUMMY=false` e a chave estão configurados. Para acompanhar o gasto, use a página Usage do painel da OpenAI, que é a fonte oficial e inclui os embeddings. Com `LANGSMITH_TRACING=true` e `LANGSMITH_API_KEY`, cada turno também aparece no projeto `LANGSMITH_PROJECT` do LangSmith, com os tokens e o custo estimado de cada chamada ao modelo.

Para usar outro currículo no modo real, defina `CURRICULO_PDF` com o caminho do PDF local e rode `scripts.setup_assets` novamente. No modo real, o texto extraído é enviado ao modelo configurado para extrair o perfil; use um currículo fictício ou autorizado na defesa.

Se a AwesomeAPI exigir autenticação, configure `AWESOMEAPI_KEY`. Para a interface em outra origem durante o desenvolvimento, configure `CORS_ORIGIN`; o HTML servido pelo FastAPI usa a mesma origem e dispensa CORS.

## Reproduzir os notebooks

Comece pelo [00 · Visão geral](notebooks/00_visao_geral.ipynb), com o mapa do código e dois diagramas. A leitura não exige executar células. Depois, siga para [01 · Indexação](notebooks/01_indexacao.ipynb), [02 · Chain](notebooks/02_chain_mvp.ipynb), [03 · ReAct](notebooks/03_agente_react.ipynb), [04 · Memória](notebooks/04_memoria.ipynb), [05 · Ferramentas e RAG](notebooks/05_ferramentas_rag.ipynb) e [06 · Integração e avaliação](notebooks/06_integrador_avaliacao.ipynb). Cada notebook de prática termina com as referências da rubrica. Os [diagramas editáveis](docs/diagramas/) ficam em formato Excalidraw.

```bash
.venv/bin/python -m ipykernel install --prefix .venv --name python3
for notebook in notebooks/0[1-6]_*.ipynb; do
  .venv/bin/jupyter nbconvert --to notebook --execute --inplace "$notebook" || break
done
```

Para reproduzir as chamadas HTTP reais do notebook 03, execute-o com `NOTEBOOK_LIVE_APIS=1`. Para usar o LLM real nos trechos opcionais de perfil, ReAct, function calling e text-to-SQL, configure as chaves e use `NOTEBOOK_OPENAI=1`.

## Avaliar no LangSmith

Configure `LANGSMITH_API_KEY` e as credenciais do modelo usado como juiz. Depois execute `.venv/bin/python -m scripts.evaluate --langsmith`. O script registra os 12 cenários fictícios, a correção semântica, a trajetória e a proporção de afirmações confirmadas. Use `--share` para gerar também o link público do dataset fictício. Verifique em uma janela anônima o link que será enviado ao professor. O script também grava `output/langsmith.json`, que a interface lê no bloco "Avaliação no LangSmith". Último experimento (13/11/2026): correção semântica 12/12, regressão 12/12, trajetória 12/12 e 75% das afirmações confirmadas.

## Revisar evidências e gravar

- [Roadmap e matriz dos 29 critérios](docs/progresso.md)
- [Relatório técnico](output/pdf/ian_trinta_ai-agents_langchain-agents.pdf)
- [Vídeo da defesa](https://youtu.be/I91282WyBMc)
- [Roteiro usado na gravação](docs/gravacao.md)
- [Avaliação no LangSmith, link público](https://smith.langchain.com/public/b64697c5-7b1f-4b57-8614-0e56daf802d9/d): dataset `radar-modelo-real-c9033593` com os 6 casos e o experimento do modelo real
- [Resultados dessa avaliação em arquivo](output/langsmith-real.json): 6 casos, gerada por `.venv/bin/python -m scripts.evaluate_real` (exige as chaves da OpenAI e do LangSmith)
- [Resultados dos 12 cenários locais](output/avaliacao-local.json)

Os anúncios de demonstração e o currículo são fictícios. O protótipo usa um perfil por instância e mantém a memória conversacional no processo. O servidor deve rodar localmente durante a apresentação. O projeto usou OpenAI Codex na implementação do agente, Claude Design no protótipo da interface e Claude Code na interface em Vue e nas rotas que a servem; a avaliação local e os resultados HTTP foram executados e verificados.
