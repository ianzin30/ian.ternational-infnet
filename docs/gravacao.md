# Roteiro da defesa em vídeo

Vídeo gravado: <https://youtu.be/I91282WyBMc>

A defesa usa a interface web (`.venv/bin/uvicorn src.api:app`, depois [localhost:8000](http://127.0.0.1:8000)) em modo real, com a webcam ligada. A interface usa o mesmo executor e a mesma memória da CLI. Antes de gravar, rode `.venv/bin/python -m scripts.setup_assets` e faça um turno de aquecimento para os pesos já estarem carregados.

## 1. Visão geral do fluxo

Apresente o caminho de uma pergunta: memória, roteador de intenção, agente com cinco ferramentas, regras fixas de elegibilidade, verificação por NLI e resposta em stream. Destaque o que é decisão do modelo e o que é código fixo.

## 2. Interface em modo real

1. "Mostre vagas remotas de Python que aceitam Brasil". Acompanhe a linha do tempo: intenção, escolha de ferramentas e as chamadas reais à Remotive e à Arbeitnow. Abra o "Por quê?" de uma vaga para mostrar o trecho do anúncio.
2. "Converta o salário da primeira". Mostre a cotação da AwesomeAPI e explique que a posição foi resolvida pela lista do turno anterior (memória entre turnos).
3. "Lembre que prefiro evitar vagas que pedem Docker". Mostre a linha "Guardei" e a aba "Longo prazo" do painel de memória.
4. Repita a busca e mostre a preferência aplicada.
5. Opcional: "Qual combina mais com meu currículo?" (RAG) e "Quais vagas eu ainda não apliquei?" (text-to-SQL).

Os três requisitos do enunciado ficam cobertos pelos passos 1 e 2: raciocínio com decisão de ferramenta, chamada real de API externa e memória entre turnos.

## 3. LangSmith

Abra "Ver no LangSmith" em uma resposta para mostrar o trace do turno. Depois abra o [experimento com os seis casos do modelo real](https://smith.langchain.com/public/b64697c5-7b1f-4b57-8614-0e56daf802d9/d) (resultados também em `output/langsmith-real.json`) e compare, em um caso, a rota e as ferramentas esperadas com as executadas.

A [correspondência entre a interface e a rubrica](ui-rubrica.md) lista onde cada item aparece.
