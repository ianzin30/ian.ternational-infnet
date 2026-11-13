# Contexto de continuação · Radar Remoto no Claude Design

Cole este bloco DEPOIS do prompt original ("Prompt único para o Claude Design"). Ele diz onde o trabalho parou e o que já foi decidido.

## Onde está o trabalho

- Lousa (canvas do tipo Design, privada, conta do usuário): https://claude.ai/artifact/2mEyDKYwzrDaZtXgY4gg83
  - Título da lousa: "Lousa em branco". Tudo do projeto vive nela, como protótipo. NÃO criar outra lousa nem outro artefato.
  - Para ler o estado atual: `read` da lousa com `path` `project/canvas.json` e, depois, cada `project/<arquivo>.dc.html` que for editar.
- Descartados (não fazem parte da aprovação, podem ser ignorados):
  - Página separada https://claude.ai/artifact/D8eTFDEXrvTWeAUpyvbVPv (primeira tentativa, fora da lousa).
  - `web/redesign/index.html` no repositório local (versão Vue antiga do Lote 1, desatualizada).

## Situação no protocolo de lotes

- Lote 1 entregue e ajustado duas vezes, aguardando "aprovado".
  - Ajuste 1: o usuário pediu 5 explorações mais visuais para "Etapas do agente". Feitas (A trilho, B radar, C agora/feitas/a seguir, D diagrama de fluxo, E tambor).
  - Ajuste 2: o usuário escolheu a D ("simplesmente perfeita") e pediu para transplantá-la. Feito: a coluna lateral do protótipo principal agora é o diagrama D, ligado ao turno real.
- Decisão do usuário: foco total na versão WEB. A versão celular fica para o final ("depois traduzimos tudo para mobile"). Os quadros de celular estão em pausa, com aviso laranja na lousa.
- Próximo passo: quando o usuário responder "aprovado", executar o Lote 2 SOBRE o protótipo principal, sem redesenhar o aprovado. Toda mensagem de entrega termina exatamente com a linha de encerramento do protocolo.

## Arquivos da lousa (project/)

| Arquivo | Quadro | Papel |
|---|---|---|
| canvas.json | índice | quadros, posições, notas |
| Main.dc.html | 1440×900, PAGE (`expand: fill`), `is_interactive` | protótipo interativo; todos os outros quadros de estado o importam |
| Tokens.dc.html | 1440×1560 | prancha dos tokens em 3 camadas, com contraste medido |
| Estado-Processando / Estado-Resultado (modo real) / Estado-Erro / Estado-Escuro .dc.html | 1440×900 | `<dc-import name="Main" estado=… tema=… modo=…>` |
| Celular-Vazio / Celular-Resultado / Celular-Gaveta .dc.html | 390×844 | em pausa (o diagrama de 360 px não cabe na gaveta) |
| Etapas-A-Trilho … Etapas-E-Tambor .dc.html | 400×860 | as 5 explorações; D foi a escolhida |

Layout no canvas: linha 1 (y=0) Main + Tokens + nota "Como testar"; linha 2 (y=1980) estados; linha 3 (y=3300) celular + aviso; linha 4 (y=4560) explorações + nota. Títulos `title1` ficam 300 px acima de cada linha.

## Props (Tweaks) do Main.dc.html

`estado`: vazio | processando | resultado | erro · `tema`: sistema | claro | escuro · `modo`: simulado | real · `simularFalha`: boolean (falha na busca de vagas; "Tentar de novo" refaz sem falhar) · `gaveta`: boolean.

## Decisões de design já aprovadas

- Estilo suíço minimalista (base ui-ux-pro-max). Um acento azul-petróleo; cinzas com leve viés para ele.
- Fonte: Geist (Google Fonts) para a interface; Geist Mono só para dados (salário, número de etapa, rubrica, SQL).
- Tokens em 3 camadas, como variáveis CSS escopadas em `.rr`:
  - Primitivos `--p-*` (cinzas `--p-gray-*`, `--p-ink-*`, `--p-petrol-*`, `--p-green/amber/red-*`, escala de tipo `--p-size-*` com razão 1,125 sobre 16 px, espaço em grade de 4 px, raios 4/6/10/999, duas sombras, durações 120/200/320 ms).
  - Semânticos `--color-*`, `--text-*`, `--space-*`, `--radius-*`, `--dur-*`: única camada que muda com tema (`data-tema="escuro"` ou `"sistema"` + prefers-color-scheme) e com reduced-motion (durações viram 0).
  - Componente `--btn-*`, `--card-*`, `--chip-*`, `--input-*`, `--header-*`, `--sidebar-*` (`--sidebar-w: 400px`), `--toast-*`.
- Cores-chave (claro / escuro): fundo #fbfcfc / #0b0f12; texto #0f171c / #e6ebee; texto secundário #5a666e / #98a5ae; acento #0b6a85 / #5cc3dc; borda de controle #848f97 / #5f6c76 (corrigida para ≥3:1, WCAG 1.4.11); sucesso #1b7a3e / #5fd38e; alerta #845400 / #f2c35a; perigo #b3261e / #f58b80.
- Status sempre com cor + ícone + texto: Recomendada (verde, check), Pendente (âmbar, relógio), Descartada (vermelho, X).
- Proibido: gradientes decorativos, glass, emojis, ícones decorativos, rótulo/eyebrow acima de título, cards genéricos.
- Copy em pt-BR curto e ativo; erros dizem o que aconteceu e o que fazer.

## O que o protótipo principal já faz (Lote 1 + ajustes)

- Cabeçalho: "Radar Remoto", indicador "Modo demo" + selo "Dados simulados" (ou "Modo real · GPT-6 Luna"), botão de tema, "Nova sessão" com confirmação inline.
- Estado vazio: título, frase do que o agente faz, 4 sugestões clicáveis do prompt.
- Campo de mensagem: Enter envia, Shift+Enter quebra linha, envio bloqueado durante o turno.
- Turno simulado: avança pelas etapas com tempos variados; indicador "Etapa N de 8 · nome da etapa…".
- Resposta: texto + cards (título, empresa, fonte, salário em mono, motivo, chips de skills, "Ver anúncio", "Salvar" e "Já apliquei" com toast; ficam travados depois de usados). Descartadas recolhidas em "N descartadas · ver motivo".
- Erro de rede com "Tentar de novo".
- Coluna lateral = diagrama D, ligado ao último turno:
  - Seu pedido → Intenção → Ferramentas → [Remotive | Arbeitnow] "em paralelo" → [Câmbio | Currículo | Histórico] "conforme o pedido" → Verificação → Resposta.
  - Estados dos nós: concluída (borda acento + check), agora (preenchido + pulso), na fila (tracejado), não usada (tracejado claro + riscado), erro (vermelho + X). A ligação que chega à etapa atual corre tracejada.
  - Cartão abaixo: rótulo, nome completo da etapa, fonte (mono) e chip da rubrica. No fim do turno: fontes consultadas e quantas rubricas o turno cobriu.
  - Legenda dos 4 estados. `role="img"` com `aria-label` descrevendo o estado de cada etapa.
- Acessibilidade: link "Pular para a mensagem", aria-live para a etapa atual e para a resposta, foco visível, Esc fecha gaveta/confirmação, alvos de 44 px em toque, reduced-motion respeitado.

## Regras técnicas da lousa (aprendidas na prática)

- Cada quadro é um `.dc.html` com `<x-dc>`, `<helmet>` e `<script type="text/x-dc" data-dc-script>` com `class Component extends DCLogic`. Holes `{{x}}` são só lookup; tudo é calculado em `renderVals()`. Eventos: `onClick="{{fn}}"`. Laços `<sc-for>`, condicionais `<sc-if>` (sempre com `hint-*`).
- Sem rede (só Google Fonts). Por isso não dá para rodar Vue nem chamar a API na lousa: o protótipo é sempre simulado.
- Fluxo de publicação: escrever um arquivo, publicar, só então o próximo. Enviar `canvas.json` apenas quando mudar quadros/notas, e ler o `canvas.json` da lousa logo antes.
- Regra do tipo Design: não verificar renderizando (sem screenshot) a menos que o usuário peça.

## Pendências conhecidas

- Lote 2 (linha do tempo ao vivo com detalhes expansíveis, "Ver como cheguei aqui", painel "Por que este resultado?" com a correção lado a lado, resumo por turno, simulação com erro + cache + contradição) deve evoluir o diagrama D já aplicado, não substituí-lo.
- Celular: refazer gaveta e telas no final, a pedido do usuário.
- Entrega final em código: o prompt pede um único `index.html` com Vue 3 servido pelo FastAPI. A lousa não roda Vue; gerar o `index.html` a partir do protótipo aprovado no final.
- Skills usadas: ui-ux-pro-max (+ design-system, ui-styling), design-systems, interaction-design, ux-writing, accessibility-audit, design-critique, design-elevation, impeccable, ux-copy, accessibility-review. frontend-design não existe no ambiente (princípios aplicados). Flutter/mobile-design fora do escopo web.
