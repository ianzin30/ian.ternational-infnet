# Roteiro para gravar a defesa

O enunciado prevê a CLI para a defesa. Abra um terminal com a CLI e mantenha a webcam ligada. Prepare primeiro o FAISS e os pesos com `.venv/bin/python -m scripts.setup_assets`.

1. No modo demo, pergunte por vagas remotas de Python. Mostre as recomendações e o caso Atlas: a proposta dizia que aceita Brasil, o anúncio diz `Remote, US only.`, e a vaga foi descartada antes da resposta.
2. Na mesma sessão, filtre para vagas que aceitam Brasil e peça a conversão da segunda. Explique como o ID da vaga exibida permite resolver a referência sem refazer a lista. Mostre moeda, período e cotação fictícia.
3. Pergunte qual vaga combina mais com o currículo. Mostre a recuperação via FAISS e as habilidades em comum que fundamentaram a escolha.
4. Em outra janela, execute `.venv/bin/python -m scripts.live_smoke --openai` com a chave configurada. Mostre os estados e as fontes HTTP da chamada. Se também for demonstrar o chat com dados reais, execute `MODO_DUMMY=false .venv/bin/python -m scripts.cli`. Se faltar a chave OpenAI, `scripts.live_smoke` comprova as chamadas HTTP usando decisões roteirizadas; identifique essa diferença ao narrar.
5. Mostre a matriz de evidências e a avaliação. Quando o experimento LangSmith estiver disponível, abra as métricas e um caso de contradição. Assista à gravação antes de enviar o link pelo canal de entrega do curso.

Nenhum vídeo ou envio externo foi criado por este projeto. A defesa exige a participação do autor.
