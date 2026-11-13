# Handoff · interface do ian.ternational

## Referência
- Lousa (Claude Design): https://claude.ai/artifact/2mEyDKYwzrDaZtXgY4gg83
- Fonte da verdade: o quadro **Main** (`project/Main.dc.html`), um protótipo interativo. Abra com Play para usar.
- Apoio na mesma lousa:
  - `Tokens` (tokens em 3 camadas: primitivos, semânticos e de componente).
  - Quadros `Estado-*`: cache, correção, carregando, leitor de PDF, envio de currículo, erro, modelo e tema escuro.
  - Linha "Propostas": o que cada peça da rubrica mostra e onde aparece.
- Ícone, favicon e snippet do `<head>`: `web/icone/`.

## Como usar
Implemente a interface de forma **fiel** ao Main: layout, copy em pt-BR, tokens, estados, acessibilidade e microinterações.
Você tem **liberdade crítica** para mudar o que for preciso para deixar a rubrica mais visível ou mais correta. A rubrica está em `docs/` ou no enunciado do projeto. Quando mudar algo, registre o motivo no PR.
**A única rubrica fora do escopo é a 5.5 (Streamlit).** A entrega é a interface web servida pelo FastAPI.

## O que entra
- **Cabeçalho**
  - Logo `ian.ternational` em mono, com o ponto na cor de acento.
  - O cursor do logo pisca 4 vezes ao abrir e some. Volta a piscar enquanto o agente trabalha.
  - Seletor de modelo: trocar de modelo inicia uma nova conversa.
- **Trilho de conversas (esquerda)**
  - Só aparece depois da primeira conversa. Antes disso, fica a página inicial com as sugestões.
  - "Nova conversa" e lista de conversas; apagar uma conversa pede confirmação ali mesmo.
  - Memória no pé do trilho, com três abas:
    - Longo prazo: tipo CoALA (semântica, episódica ou procedural), origem e botão "esquecer".
    - Nesta conversa.
    - Janela: tokens usados por parte.
- **Conversa**
  - Resposta em stream e cards de vaga com status.
  - Painel "Por que este resultado?" e nota de correção da verificação NLI.
  - Linhas "Guardei: …" e "Memória usada: … (similaridade)".
  - Rodapé de cada resposta com o resumo do turno, "Ver como cheguei aqui" e "Ver no LangSmith".
- **Coluna direita**
  - Currículo, com leitor de PDF em popup e troca de arquivo com etapas e erros.
  - Bloco "Avaliação no LangSmith".
  - Diagrama de etapas.
  - Linha do tempo. Cada etapa tem:
    - status com cor, ícone e texto;
    - chips de rubrica numa linha própria;
    - selo do tipo de ferramenta (hardcoded ou semântica; API externa ou interna);
    - detalhes ao abrir: JSON da intenção, rota do RouterChain, prompt PTCF com few-shot, Thought/Action, antes e depois da recuperação no FAISS, SQL, verificação e janela de memória.
- **Layout**
  - As duas colunas laterais recolhem para faixas de 56 px em telas a partir de 960 px. Guarde essa preferência no navegador.
  - Abaixo de 960 px, as colunas viram gavetas.
- **Tema** claro e escuro.

## Simulado no protótipo; precisa vir do backend real
- Eventos de etapa (status e tempo) → SSE de `/chat/stream`.
- Similaridades do FAISS, tokens da janela e métricas do LangSmith (hoje aparecem como "—"). Não invente números.
- Extração de memória:
  - No protótipo é feita por regex. No app real, o LLM decide e grava por uma ferramenta.
  - Memória curta = `RunnableWithMessageHistory` por `session_id`.
  - Memória longa = índice FAISS por usuário, recuperando as k=3 memórias mais parecidas.
- As vagas, o câmbio e o currículo (`Curriculo.dc.html`) são fictícios.

## Ignore (só existem para a lousa)
- As props `estado`, `tema`, `modo`, `simularFalha`, `gaveta`, `curriculo`, `erroEnvio`, `leitor` e `menuModelo`.
- O código residual de "propostas" (`propLista`, `verProposta`, `propAberto`). As 8 propostas são fixas.
- No vídeo de demonstração, nada de "Modo demo" nem do selo "Dados simulados": a interação precisa ser real.
