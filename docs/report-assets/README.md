# Evidências do relatório ian.ternational

Gere o PDF a partir da raiz com `.venv/bin/python -m scripts.report`.
O gerador lê as saídas já salvas nos notebooks e em `output/`. Não precisa
de credenciais, navegador, chamadas externas ou do currículo original.

- `app-atlas.png`: captura do painel “Por que este resultado?” da UI local
  em modo demo, com anúncios e currículo fictícios. Mostra a correção
  deliberada do caso Atlas; não faz parte do experimento com modelo real.
- `langsmith-*.jpg`: recortes da interface do experimento
  [radar-integrador-modelo-real-bc026520](https://smith.langchain.com/o/f3d9bd48-9e7a-4483-9e65-dd3af105169e/datasets/0406dbb8-f458-4ea9-95bb-ff90a92f00c6/compare?selectedSessions=64ae75ce-55e8-48a5-a13f-9b69b9519e17).
  Incluem tabela, referência, saída do caso de busca com currículo e saída do
  caso de câmbio. O experimento usou OpenAI com dados de teste fixos.
- `perfil-curriculo.json`: saída de `perfil_chain()` aplicada a um recorte
  profissional do currículo do autor, no modo local. O relatório não inclui
  o PDF pessoal nem os dados de contato.
- As marcações e os diagramas são desenhados no PDF pelo gerador. O arquivo
  raster de cada captura contém apenas a região usada na página.
- `ianternational-wordmark.png`: marca da interface Vue em tema escuro,
  com o cursor visível, fornecida pelo autor para a capa.

Origem das marcas, preservadas como SVG com cópias PNG para o gerador:

| Marca | Origem |
|---|---|
| Python | [Devicon](https://github.com/devicons/devicon/blob/master/icons/python/python-original.svg) |
| LangChain | [Simple Icons](https://cdn.simpleicons.org/langchain) |
| OpenAI | [Simple Icons, versão 13.21.0](https://github.com/simple-icons/simple-icons/blob/13.21.0/icons/openai.svg) |
| FastAPI | [Devicon](https://github.com/devicons/devicon/blob/master/icons/fastapi/fastapi-original.svg) |
| Vue | [Devicon](https://github.com/devicons/devicon/blob/master/icons/vuejs/vuejs-original.svg) |
| LangSmith | [Lobe Icons](https://github.com/lobehub/lobe-icons/blob/master/packages/static-svg/icons/langsmith.svg) |

Os logos identificam as tecnologias usadas no trabalho.
