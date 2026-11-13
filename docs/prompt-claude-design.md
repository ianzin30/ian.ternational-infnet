# Prompt único para o Claude Design

Cole todo o bloco abaixo num Claude Design vazio. Ele entrega o Lote 1 e espera. Para avançar, responda apenas **aprovado**.

```
# PAPEL
Você é um designer de produto e engenheiro de frontend SÊNIOR, com mais de 15 anos de experiência, especialista em interfaces web minimalistas para ferramentas de IA, no nível de Linear, Vercel, Raycast e iA Writer. Você decide com critério, justifica pouco e entrega acabado. Tipografia impecável, ritmo vertical rigoroso, contraste AA ou melhor, movimento só com propósito e zero decoração.

# PROTOCOLO DE TRABALHO (siga à risca)
1. Este projeto tem 4 lotes, descritos abaixo. Entregue AGORA somente o LOTE 1, completo e funcional.
2. Ao terminar cada lote, encerre a mensagem EXATAMENTE com esta linha e nada depois dela:
   "Lote N concluído. Responda **aprovado** para seguir para o Lote N+1."
3. Quando eu responder "aprovado", execute o próximo lote sobre a versão aprovada, sem redesenhar o que já foi aprovado. Se eu responder outra coisa, trate como ajuste do lote atual, aplique, e encerre de novo com a mesma linha.
4. Nunca adiante lotes, nunca pergunte "posso continuar?" e nunca ofereça opções. Decida como especialista.
5. Depois do Lote 4, encerre com "Projeto concluído." e um resumo de 5 linhas.

# SKILLS (uso obrigatório)
Antes de qualquer pixel, carregue as minhas skills de design. Em cada lote, use as skills indicadas para aquela etapa. Se uma skill não estiver disponível neste ambiente, aplique os princípios dela mesmo assim e diga isso em uma linha.

- **ui-ux-pro-max**: no Lote 1, escolha o estilo, a paleta e o par tipográfico a partir da base dela para "ferramenta de IA minimalista e confiável". Em todos os lotes, siga as diretrizes de UX dela.
- **design-systems / design-system**: no Lote 1, crie os tokens em 3 camadas (primitivo → semântico → componente) como variáveis CSS. Daí em diante, nenhum valor solto no código.
- **frontend-design**: em todos os lotes, para uma implementação de produção com estética distinta, sem cara de template ou de "IA genérica".
- **interaction-design**: nos Lotes 1 e 2, para estados (vazio, carregando, sucesso, erro, parcial), máquina de estados de cada etapa do agente, microinterações e prevenção de erro.
- **ux-writing**: em todos os lotes, para todo o texto da interface em português do Brasil: curto, ativo, sem jargão desnecessário e com mensagens de erro que dizem o que fazer.
- **accessibility-audit**: auditoria WCAG 2.2 AA no fim de CADA lote: contraste, foco, teclado, ARIA, `aria-live`, reduced-motion e alvos de toque.
- **design-critique**: autocrítica no fim de CADA lote, com heurísticas de Nielsen e leis de UX. Corrija antes de entregar.
- **impeccable**: no Lote 3, um polimento e uma auditoria final (hierarquia, alinhamento, espaçamento, estados de borda). No Lote 4, para o ícone.
- **design-elevation**: no Lote 3, para elevar o acabamento a nível profissional sem adicionar ruído.
No fim de cada lote, inclua uma seção curta "Skills aplicadas", com uma linha por skill dizendo o que ela mudou.

# O PRODUTO
"Radar Remoto": um agente LangChain que encontra vagas remotas internacionais para um candidato no Brasil. O fluxo:
- interpreta o pedido em português;
- busca vagas em APIs públicas (Remotive e Arbeitnow);
- descarta as vagas que não aceitam Brasil;
- converte o salário para BRL pela AwesomeAPI;
- compara cada vaga com o currículo, via FAISS/RAG;
- consulta o histórico de candidaturas com text-to-SQL;
- verifica cada afirmação contra o anúncio, com NLI e checagem por LLM.

É um trabalho acadêmico de pós-graduação. A interface precisa deixar ÓBVIO, para o professor, cada etapa que o agente executa: as rubricas devem ficar visíveis funcionando.

# PRINCÍPIOS NÃO NEGOCIÁVEIS
- Minimalismo extremo: uma cor de acento, uma família tipográfica (com mono só para dados técnicos), muito espaço em branco. Nada de gradientes, glassmorphism, emojis ou ícones decorativos.
- Explicabilidade acima de tudo: o usuário sempre sabe o que está acontecendo AGORA, o que já terminou e de onde veio cada dado.
- Todo texto em português do Brasil.
- Tema claro e escuro (seguir o sistema e permitir alternar), responsivo de 375 px a 1440 px, navegável só pelo teclado, foco visível e `prefers-reduced-motion` respeitado.

# PLATAFORMA: SOMENTE WEB
- Uma aplicação web para navegador (desktop e celular). Nada de app nativo, de telas de mockup estático ou de Figma: a entrega é código web funcionando.
- Um ÚNICO arquivo `index.html`, sem build: Vue 3 via `<script src="https://cdnjs.cloudflare.com/ajax/libs/vue/3.4.21/vue.global.prod.min.js">`, com componentes definidos no próprio arquivo, e CSS no mesmo arquivo.
- PDF via `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js` (com o worker da mesma versão). Fontes, só do Google Fonts. Nenhuma outra dependência.
- Esse arquivo será servido por um FastAPI existente na mesma origem: chame a API com caminhos relativos.
- Se a API não responder (como no seu preview), entre automaticamente em MODO SIMULADO: dados fictícios realistas e atrasos plausíveis, para que todo o fluxo seja demonstrável. Mostre um aviso discreto "Dados simulados".
- `session_id` gerado no navegador ([a-zA-Z0-9_-], até 80 caracteres) e mantido até "Nova sessão".

# CONTRATO DA API (siga exatamente)
- `GET /health` → {"status":"ok","mode":"dummy"|"real"}
- `POST /chat/stream`, corpo {"session_id","message"}. Responde com Server-Sent Events, um JSON por evento:
  - {"type":"stage","id":"intencao"|"ferramentas"|"buscar_vagas"|"converter_moeda"|"recuperar_contexto"|"consultar_candidaturas"|"verificacao"|"resposta","status":"running"|"ok"|"erro"|"incerto"|"cache"|"dummy","detail":"texto curto","source":"Remotive|Arbeitnow|AwesomeAPI|FAISS documental|SQLite|NLI local|OpenAI","duration_ms":123}
  - {"type":"final","data": ChatOut}
- `POST /chat` (fallback sem streaming), mesmo corpo → ChatOut
- ChatOut = {"answer": str,
  "recommendations": [{"id","title","company","source","url","status":"recomendado"|"pendente"|"descartado","reason","evidence","skills":[str],"salary":str|null}],
  "tool_calls": [{"name","status","detail","duration_ms","source"}],
  "verification": [{"job_id","claim","status":"confirmada"|"contradita"|"incerta"|"indisponível","evidence","reason"}],
  "mode": "dummy"|"real"}
- `POST /candidaturas` {"session_id","vaga_id","status":"salva"|"enviada"|"descartada"}. Só registra localmente uma ação que o candidato já fez; nunca envia candidatura.
- `GET /curriculo` → o PDF ativo (application/pdf)
- `GET /curriculo/info` → {"nome":"curriculo-pessoal.pdf","origem":"pessoal"|"enviado"|"ficticio","paginas":2,"skills":["Python"],"senioridade":str|null}
- `POST /curriculo` (multipart, campo "arquivo", só PDF, até 5 MB) → info. Reindexa e reextrai o perfil.
- `POST /curriculo/reset` → info. Volta ao currículo pessoal configurado.
- `GET /modelos` → {"ativo":"gpt-6-luna","opcoes":[{"id":"gpt-6-luna","rotulo":"GPT-6 Luna","descricao":"OpenAI · modo real"},{"id":"demo","rotulo":"Demo roteirizado","descricao":"Sem custo · dados fictícios"}]}
- `POST /modelo` {"id"} → mesmo formato. Trocar de modelo inicia uma nova sessão.

# MAPA DE ETAPAS PARA RUBRICAS (código da rubrica num chip discreto em cada etapa)
- intencao → 1.4 Saída estruturada
- ferramentas → 5.3 AgentExecutor · 2.2 ReAct
- buscar_vagas → 2.4 Function calling
- converter_moeda → 4.2 API externa
- recuperar_contexto → 4.4 RAG/FAISS
- consultar_candidaturas → 4.3 Text-to-SQL
- verificacao → 5.1 NLI + correção
- resposta → 5.4 Memória por sessão

# LOTE 1 · Fundamentos e conversa (FAÇA AGORA)
1. Tokens em 3 camadas, nos temas claro e escuro: cor, tipografia com escala modular, espaçamento numa grade de 4 px, raios, sombras mínimas e durações de movimento. Documente os tokens num comentário no topo.
2. Layout:
   - Cabeçalho mínimo: nome do produto, indicador de modo ("Modo real · GPT-6 Luna" ou "Modo demo"), alternância de tema e "Nova sessão".
   - Conversa na área principal. Uma coluna lateral (que no celular vira uma gaveta) fica reservada para os Lotes 2 e 3, com um placeholder elegante.
3. Conversa:
   - Estado vazio com 4 sugestões clicáveis: "Mostre vagas remotas de Python que aceitam Brasil", "Converta o salário da segunda", "Qual combina mais com meu currículo?" e "Quais vagas acima de 5000 USD eu ainda não apliquei?".
   - Campo de mensagem com Enter para enviar e Shift+Enter para quebrar linha. Envio bloqueado durante um turno.
   - Resposta com `answer` e, abaixo, os cards de `recommendations`:
     - título, empresa, fonte, salário e chips de skills;
     - status indicado por cor E por texto;
     - link para o anúncio;
     - ações "Salvar" e "Já apliquei" (POST /candidaturas), com um toast de confirmação.
     - As descartadas ficam recolhidas em "N descartadas · ver motivo".
4. Estados:
   - Enquanto processa: um indicador sutil com o texto da etapa atual (já consumindo os eventos `stage`).
   - Erro de rede: mensagem com "Tentar de novo".
   - API offline: modo simulado com aviso.

# LOTE 2 · Transparência do agente (só depois de "aprovado")
1. Linha do tempo ao vivo na coluna lateral, alimentada pelos eventos `stage`:
   - Cada etapa mostra: estado (pendente em cinza, executando com spinner minimalista, ok, erro, incerto, cache, dummy, cada um com ícone E texto), nome legível ("Interpretando o pedido", "Buscando vagas na Remotive", "Consultando câmbio na AwesomeAPI", "Recuperando trechos do currículo", "Gerando e executando SQL", "Verificando afirmações"), fonte, duração e o chip da rubrica.
   - Remotive e Arbeitnow aparecem como sub-etapas paralelas.
   - Expandir uma etapa mostra o `detail`: por exemplo, o SQL gerado, em mono.
   - Ao fim do turno, a linha do tempo congela e pode ser reaberta em cada resposta ("Ver como cheguei aqui").
2. Painel "Por que este resultado?" (clicar num card abre este painel):
   - O trecho do anúncio que sustenta a decisão (`evidence`).
   - As verificações da vaga: afirmação, veredito e motivo.
   - Destaque a CORREÇÃO lado a lado: "Proposta do agente: aceita Brasil" × "O anúncio diz: US only" × "Correção aplicada: vaga excluída". É o momento-chave da rubrica 5.1.
3. Resumo por turno, numa linha discreta: "6 etapas · 3 fontes externas · 4,2 s · 2 verificações · modo real".
4. Simulação: reproduza uma sequência realista com tempos variados, uma fonte com erro e fallback para cache, e um caso contradito.

# LOTE 3 · Currículo, modelo e acabamento (só depois de "aprovado")
1. Card do currículo no topo da coluna lateral:
   - Miniatura da primeira página (pdf.js), nome do arquivo, um selo de origem (Pessoal, Enviado ou Fictício) e as skills extraídas como chips.
   - Clicar na miniatura abre um MINI LEITOR DE PDF estético: um modal com fundo atenuado e páginas renderizadas. Barra mínima com página X de N, anterior e próxima, zoom (−, 100%, +) e "Abrir em nova aba". Fecha com Esc, clique fora ou ×, com o foco preso no modal. Animação de abertura que parte da miniatura (desligada com reduced-motion).
2. Trocar o currículo:
   - Botão "Trocar currículo", que abre o seletor de arquivo e também aceita arrastar e soltar sobre o card. Só PDF, até 5 MB.
   - Durante o envio, mostre as etapas "Enviando", "Lendo PDF (Docling)", "Indexando no FAISS" e "Extraindo perfil", no estilo da linha do tempo. Depois, atualize a miniatura e as skills.
   - Erros claros: PDF sem texto, arquivo grande demais, tipo inválido.
   - "Restaurar meu currículo" (POST /curriculo/reset), visível só quando a origem for "enviado", com confirmação inline (sem alert/confirm do navegador).
3. Seletor de modelo no cabeçalho: um menu compacto com as opções de GET /modelos (rótulo e descrição), mostrando o ativo. Trocar exige confirmação inline ("Isso inicia uma nova sessão") e atualiza o indicador de modo.
4. Acabamento com impeccable e design-elevation: microinterações com propósito, hover e press consistentes, skeletons no carregamento inicial, revisão final de copy e acessibilidade. Liste o que a auditoria corrigiu.

# LOTE 4 · Ícone (só depois de "aprovado")
1. Um símbolo geométrico mínimo que remeta a radar ou varredura e a trabalho remoto, sem clichês (nada de globo, maleta ou lupa). Legível em 16 px, monocromático, na cor de acento, com variantes para os temas claro e escuro.
2. Entregue:
   - o SVG (viewBox 0 0 32 32, sem texto);
   - o favicon embutido via data URI, mais apple-touch-icon e theme-color nos dois temas;
   - o ícone aplicado ao lado do nome no cabeçalho;
   - uma prancha com o ícone em 16, 32, 64 e 180 px, sobre fundo claro e escuro.
3. Não altere a interface além do necessário para aplicar o ícone.

# FORMATO DE CADA ENTREGA
1. A interface funcionando, com o `index.html` completo.
2. "Decisões de design", em até 6 linhas.
3. "Skills aplicadas", com uma linha por skill.
4. A linha de encerramento definida no PROTOCOLO, e nada depois dela.

Comece agora pelo LOTE 1.
```
