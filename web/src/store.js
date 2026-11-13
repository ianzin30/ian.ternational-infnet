// Estado da interface e o modelo de visão (`vm`) que os templates leem.
// A estrutura segue o protótipo Main da lousa; tudo que lá era simulado aqui vem da API.
import { computed, reactive, watch } from 'vue'
import { chatStream, del, enviarCurriculo, get, post } from './api.js'
import { medidasPdf } from './pdf.js'

// ---- constantes de apresentação -----------------------------------------------------------
const IC = {
  check: 'M5 12.5l4.5 4.5L19 7.5',
  x: 'M7 7l10 10M17 7L7 17',
  anel: 'M12 7a5 5 0 1 1 0 10a5 5 0 1 1 0-10z',
  ponto: 'M12 6a6 6 0 1 1 0 12a6 6 0 1 1 0-12z',
  duvida: 'M9.5 9.5a2.5 2.5 0 1 1 3.6 2.2c-.7.4-1.1 1-1.1 1.8v.5M12 17.5v.01',
  cache: 'M4.5 12a7.5 7.5 0 1 0 2.2-5.3M4.5 4.5v3.5H8M12 8.5V12l2.5 1.5',
  simulada: 'M9 4.5H6.5a2 2 0 0 0-2 2V9M15 4.5h2.5a2 2 0 0 1 2 2V9M9 19.5H6.5a2 2 0 0 1-2-2V15M15 19.5h2.5a2 2 0 0 0 2-2V15',
  traco: 'M7 12h10',
}
// Estado de cada etapa: texto, ícone e nome usado no diagrama.
const ST = {
  pendente: { texto: 'Na fila', d: IC.anel, no: 'fila', fala: 'na fila' },
  running: { texto: 'Executando', d: IC.ponto, no: 'ativo', fala: 'em andamento' },
  ok: { texto: 'Concluída', d: IC.check, no: 'feito', fala: 'concluída' },
  erro: { texto: 'Erro', d: IC.x, no: 'erro', fala: 'com erro' },
  incerto: { texto: 'Incerta', d: IC.duvida, no: 'incerto', fala: 'incerta' },
  cache: { texto: 'Do cache', d: IC.cache, no: 'cache', fala: 'do cache' },
  dummy: { texto: 'Simulada', d: IC.simulada, no: 'dummy', fala: 'simulada' },
  pulada: { texto: 'Não usada', d: IC.traco, no: 'pulada', fala: 'não usada' },
}
const VEREDITO = {
  confirmada: { texto: 'Confirmada', cls: 'status st-rec', d: IC.check },
  contradita: { texto: 'Contradita', cls: 'status st-des', d: IC.x },
  incerta: { texto: 'Incerta', cls: 'status st-pen', d: IC.duvida },
  'indisponível': { texto: 'Indisponível', cls: 'status st-nd', d: IC.traco },
}
const EXTERNAS = ['Remotive', 'Arbeitnow', 'AwesomeAPI', 'OpenAI']
// Uma linha por etapa do turno. Remotive e Arbeitnow rodam em paralelo (RunnableParallel).
const ITENS = [
  { chave: 'intencao', etapa: 0, curto: 'Intenção', nome: 'Interpretando o pedido', fonte: 'OpenAI', rubrica: '3.5 Intenção e entidades' },
  { chave: 'ferramentas', etapa: 1, curto: 'Ferramentas', nome: 'Escolhendo as ferramentas', fonte: 'OpenAI', rubrica: '5.3 AgentExecutor · 5.2 Agente único' },
  { chave: 'remotive', etapa: 2, curto: 'Remotive', nome: 'Buscando vagas na Remotive', fonte: 'Remotive', rubrica: '2.4 Function calling', sub: true },
  { chave: 'arbeitnow', etapa: 2, curto: 'Arbeitnow', nome: 'Buscando vagas na Arbeitnow', fonte: 'Arbeitnow', rubrica: '2.4 Function calling', sub: true },
  { chave: 'cambio', etapa: 3, curto: 'Câmbio', nome: 'Consultando câmbio na AwesomeAPI', fonte: 'AwesomeAPI', rubrica: '4.2 API externa' },
  { chave: 'curriculo', etapa: 4, curto: 'Currículo', nome: 'Recuperando trechos do currículo', fonte: 'FAISS documental', rubrica: '4.4 RAG/FAISS' },
  { chave: 'historico', etapa: 5, curto: 'Histórico', nome: 'Gerando e executando SQL', fonte: 'SQLite', rubrica: '4.3 Text-to-SQL' },
  { chave: 'verificacao', etapa: 6, curto: 'Verificação', nome: 'Verificando afirmações', fonte: 'NLI local', rubrica: '5.1 NLI + correção' },
  { chave: 'resposta', etapa: 7, curto: 'Resposta', nome: 'Escrevendo a resposta', fonte: 'OpenAI', rubrica: '5.4 Memória por sessão · 1.5 stream' },
]
const POR_CHAVE = Object.fromEntries(ITENS.map((it) => [it.chave, it]))
const TIPOS = {
  intencao: ['semântica', 'saída estruturada'], ferramentas: ['semântica', 'AgentExecutor'],
  remotive: ['hardcoded', 'API externa'], arbeitnow: ['hardcoded', 'API externa'], cambio: ['hardcoded', 'API externa'],
  curriculo: ['semântica', 'RAG'], historico: ['semântica', 'text-to-query'], verificacao: ['semântica', 'NLI local'],
  resposta: ['semântica', 'memória'],
}
const SUGESTOES = [
  'Mostre vagas remotas de Python que aceitam Brasil',
  'Converta o salário da segunda',
  'Qual combina mais com meu currículo?',
  'Quais vagas acima de 5000 USD eu ainda não apliquei?',
]
const ETAPAS_CV = {
  enviando: { nome: 'Enviando', fonte: 'POST /curriculo' },
  lendo: { nome: 'Lendo PDF (Docling)', fonte: 'Docling' },
  indexando: { nome: 'Indexando no FAISS', fonte: 'FAISS documental', rubrica: '4.4 RAG/FAISS' },
  extraindo: { nome: 'Extraindo perfil', fonte: 'OpenAI', rubrica: '1.3 Prompt · 1.4 Saída em JSON' },
}

const fmtMs = (ms) => (ms == null ? '' : ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1).replace('.', ',')} s`)
const pl = (n, um, varios) => `${n} ${n === 1 ? um : varios}`
const br = (n) => Number(n).toLocaleString('pt-BR')
const fmtSim = (x) => (x == null ? '—' : Number(x).toFixed(2).replace('.', ','))
const calmo = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
const novoId = (prefixo) => `${prefixo}-${Math.random().toString(36).slice(2, 7)}${Date.now().toString(36).slice(-4)}`

function guardado(chave, padrao) {
  try { const v = localStorage.getItem(chave); return v == null ? padrao : JSON.parse(v) } catch { return padrao }
}
function guardar(chave, valor) {
  try { localStorage.setItem(chave, JSON.stringify(valor)) } catch { /* armazenamento indisponível */ }
}

// ---- estado -------------------------------------------------------------------------------
const salvo = guardado('ian.conversas', { conversas: [], arquivo: {} })
export const state = reactive({
  tema: guardado('ian.tema', 'sistema'),
  usuario: guardado('ian.usuario', null) || novoId('u'),
  sessao: novoId('ian'),
  turnos: [], rascunho: '', ocupado: false, confirmar: false, gaveta: false,
  acoes: {}, toasts: [], aviso: '', foco: null, painel: null,
  carregando: true, apiFora: false,
  modelos: { ativo: null, modo: 'dummy', opcoes: [] }, menu: false, trocarPara: null, trocando: false,
  cv: null, pdf: { paginas: 1, largura: 595, altura: 842 }, cvEnvio: null, cvErro: null, cvConfirmar: false,
  arrastando: false, leitor: null,
  // Only conversations whose turns were saved come back after a reload.
  conversas: (salvo.conversas || []).filter((c) => salvo.arquivo?.[c.id]?.turnos?.length), convAtual: null, arquivo: salvo.arquivo || {},
  memLonga: [], memSessao: [], memNovas: [], janela: {}, memAberto: false, memAba: 'longo', apagando: null,
  trilho: false, trilhoMin: guardado('ian.trilhoMin', false), ladoMin: guardado('ian.ladoMin', false),
  aval: { disponivel: false }, largura: window.innerWidth, escuroSistema: false,
})
guardar('ian.usuario', state.usuario)

watch(() => state.tema, (v) => guardar('ian.tema', v))
watch(() => state.trilhoMin, (v) => guardar('ian.trilhoMin', v))
watch(() => state.ladoMin, (v) => guardar('ian.ladoMin', v))
watch(() => [state.conversas, state.arquivo], () => guardar('ian.conversas', { conversas: state.conversas, arquivo: state.arquivo }), { deep: true })

const midia = window.matchMedia?.('(prefers-color-scheme: dark)')
state.escuroSistema = !!midia?.matches
midia?.addEventListener?.('change', (e) => { state.escuroSistema = e.matches })
window.addEventListener('resize', () => { state.largura = window.innerWidth; if (state.leitor) medirLeitor() })

// ---- utilidades de interface --------------------------------------------------------------
const focar = (id) => setTimeout(() => document.getElementById(id)?.focus(), 30)
const anunciar = (texto) => { state.aviso = texto }
function rolar() {
  setTimeout(() => {
    const el = document.getElementById('rr-fio')
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: calmo() ? 'auto' : 'smooth' })
  }, 60)
}
function toast(texto) {
  const id = Date.now() + Math.random()
  state.toasts.push({ id, texto })
  setTimeout(() => fecharToast(id), 5000)
}
function fecharToast(id) { state.toasts = state.toasts.filter((t) => t.id !== id) }
function prenderFoco(e, raizId) {
  const raiz = document.getElementById(raizId)
  const f = raiz?.querySelectorAll('a[href],button:not([disabled]),[tabindex]:not([tabindex="-1"])')
  if (!f?.length) return
  const primeiro = f[0], ultimo = f[f.length - 1]
  if (e.shiftKey && document.activeElement === primeiro) { e.preventDefault(); ultimo.focus() }
  else if (!e.shiftKey && document.activeElement === ultimo) { e.preventDefault(); primeiro.focus() }
}
const temaEfetivo = () => (state.tema === 'claro' || state.tema === 'escuro' ? state.tema : state.escuroSistema ? 'escuro' : 'claro')
const turnoDe = (id) => state.turnos.find((t) => t.id === id)

// ---- carga inicial ------------------------------------------------------------------------
export async function iniciar() {
  try {
    const [modelos, cv, aval] = await Promise.all([get('/modelos'), get('/curriculo/info'), get('/avaliacao')])
    state.modelos = modelos
    aplicarCv(cv)
    state.aval = aval
    await carregarMemoria()
  } catch (erro) {
    state.apiFora = true
    toast(`Não consegui falar com o servidor. ${erro.message}`)
  } finally {
    state.carregando = false
  }
}
function aplicarCv(info) {
  state.cv = { ...info, chave: `${info.origem}-${info.nome}-${info.tamanho}` }
  medidasPdf(state.cv.chave).then((m) => { state.pdf = m }).catch(() => {})
}
async function carregarMemoria() {
  const dados = await get(`/memoria?user_id=${state.usuario}&session_id=${state.sessao}`)
  state.memLonga = dados.longo
  state.memSessao = dados.sessao
  if (dados.janela?.tokens) state.janela = dados.janela
}

// ---- conversa -----------------------------------------------------------------------------
function novoTurno(pergunta) {
  return { id: `t${Date.now()}`, pergunta, status: 'processando', est: {}, erro: '', resposta: '', stream: 0,
    vagas: [], desc: false, abertos: {}, totalMs: 0, inicio: Date.now(), real: state.modelos.modo === 'real',
    guardou: [], memUsada: [], traceUrl: null, react: null }
}

function montarVagas(data) {
  return data.recommendations.map((v) => {
    const checks = data.verification.filter((c) => c.job_id === v.id)
    const corr = checks.find((c) => c.status === 'contradita' && /Correção aplicada/.test(c.reason))
    const vaga = { ...v, verificacoes: checks.map((c) => ({ claim: c.claim, status: c.status, reason: c.reason })) }
    if (corr) {
      const nli = corr.nli_label ? `NLI: ${{ contradiction: 'contradição', entailment: 'sustentação', neutral: 'neutra' }[corr.nli_label] || corr.nli_label} ${fmtSim(corr.nli_score)}` : 'NLI indisponível neste turno'
      const llm = /Coerência LLM: (\w+)/.exec(corr.reason)
      vaga.corrigida = true
      vaga.correcao = {
        proposta: corr.claim, anuncio: corr.evidence, correcao: 'Vaga excluída da lista e movida para as descartadas',
        placar: nli + (llm ? ` · checagem por LLM: ${llm[1]}` : ' · regra de elegibilidade: contradita'),
        nota: `A proposta inicial dizia “${corr.claim}”. O anúncio diz “${corr.evidence}”, então a vaga saiu da lista.`,
      }
    }
    return vaga
  })
}

function aplicarEvento(t, ev) {
  if (ev.type === 'stage') {
    const antes = t.est[ev.key] || {}
    t.est[ev.key] = {
      status: ev.status, ms: ev.duration_ms ?? antes.ms, source: ev.source || antes.source,
      detail: ev.detail || antes.detail || '', data: ev.data && Object.keys(ev.data).length ? ev.data : antes.data || {},
    }
    const it = POR_CHAVE[ev.key]
    if (ev.status === 'running' && it && ev.key !== 'arbeitnow') anunciar(ev.key === 'remotive' ? 'Buscando vagas na Remotive e na Arbeitnow' : it.nome)
    if (ev.status === 'cache') anunciar(`${it.curto}: usei a última resposta salva.`)
  } else if (ev.type === 'token') {
    t.resposta += ev.text
  } else if (ev.type === 'memory') {
    t.memUsada = ev.usadas
    t.guardou = ev.guardadas
  } else if (ev.type === 'final') {
    t.resposta = ev.data.answer
    t.vagas = montarVagas(ev.data)
    t.real = ev.data.mode === 'real'
    t.traceUrl = ev.trace_url
    t.totalMs = Date.now() - t.inicio
    if (ev.janela?.tokens) state.janela = ev.janela
    t.status = 'pronto'
  } else if (ev.type === 'error') {
    throw new Error(ev.message || 'O agente não concluiu o turno.')
  }
}

// A resposta aparece palavra por palavra, no ritmo em que os tokens chegam do stream.
function transmitir(t, aoFim) {
  const passo = () => {
    if (t.stream == null) return
    if (t.stream >= t.resposta.length) {
      if (t.status !== 'processando') { t.stream = null; aoFim(); return }
      setTimeout(passo, 40)
      return
    }
    let prox = t.resposta.indexOf(' ', t.stream + 1)
    if (prox === -1) prox = t.resposta.length
    t.stream = calmo() ? t.resposta.length : prox
    setTimeout(passo, 18 + Math.round(Math.random() * 24))
  }
  setTimeout(passo, 60)
}

async function rodar(t) {
  try {
    for await (const ev of chatStream({ session_id: state.sessao, message: t.pergunta, user_id: state.usuario })) {
      aplicarEvento(t, ev)
    }
    if (t.status !== 'pronto') throw new Error('A conexão terminou antes da resposta.')
    if (t.guardou.length) state.memNovas.push(...t.guardou.map((g) => g.texto))
    if (state.convAtual) state.arquivo[state.convAtual] = foto()
    carregarMemoria().catch(() => {})
  } catch (erro) {
    t.status = 'erro'
    t.stream = null
    t.erro = erro.message === 'Failed to fetch' ? 'O servidor não respondeu. Confira se o uvicorn está rodando e tente de novo.' : erro.message
    state.ocupado = false
    anunciar(`Erro: ${t.erro}`)
  }
}

function enviar(texto) {
  const limpo = String(texto || '').trim()
  if (state.ocupado || !limpo) return
  if (!state.convAtual) registrarConversa(state.turnos.length ? state.turnos[0].pergunta : limpo)
  const t = reactive(novoTurno(limpo))
  state.turnos.push(t)
  Object.assign(state, { rascunho: '', ocupado: true, foco: null, apagando: null })
  const ta = document.getElementById('rr-mensagem'); if (ta) ta.style.height = 'auto'
  anunciar('Processando o pedido')
  rolar()
  transmitir(t, () => {
    state.ocupado = false
    const nv = t.vagas.filter((v) => v.status !== 'descartado').length
    anunciar(`Resposta pronta. ${pl(nv, 'vaga', 'vagas')} na lista.${t.vagas.some((v) => v.corrigida) ? ' A verificação corrigiu 1 afirmação.' : ''}`)
    rolar()
  })
  rodar(t)
}

function tentar(id) {
  const t = turnoDe(id)
  if (state.ocupado || !t) return
  Object.assign(t, { status: 'processando', est: {}, erro: '', resposta: '', stream: 0, vagas: [], inicio: Date.now() })
  Object.assign(state, { ocupado: true, foco: null })
  anunciar('Tentando de novo')
  transmitir(t, () => { state.ocupado = false; rolar() })
  rodar(t)
}

async function registrar(vaga, tipo) {
  const cur = state.acoes[vaga.id] || {}
  if (cur.ocupado || cur[tipo]) return
  state.acoes[vaga.id] = { ...cur, ocupado: true }
  try {
    await post('/candidaturas', { session_id: state.sessao, vaga_id: vaga.id, status: tipo, user_id: state.usuario })
    state.acoes[vaga.id] = { ...state.acoes[vaga.id], ocupado: false, [tipo]: true }
    toast(tipo === 'salva' ? 'Vaga salva no seu histórico. Guardei na memória de longo prazo.'
      : 'Candidatura registrada no histórico. Nada foi enviado à empresa. Guardei na memória de longo prazo.')
    const antes = state.memLonga.map((m) => m.id)
    await carregarMemoria()
    state.memNovas.push(...state.memLonga.filter((m) => !antes.includes(m.id)).map((m) => m.texto))
  } catch (erro) {
    state.acoes[vaga.id] = { ...state.acoes[vaga.id], ocupado: false }
    toast(`Não consegui registrar. ${erro.message}`)
  }
}

async function rodarReact(t) {
  if (t.react?.rodando) return
  t.react = { rodando: true }
  try {
    t.react = { rodando: false, ...(await post('/react', { message: t.pergunta })) }
  } catch (erro) {
    t.react = { rodando: false, erro: erro.message }
  }
}

function abrirPainel(tid, vid, de) { state.painel = { turno: tid, vaga: vid, de }; focar('rr-painel-fechar') }
function fecharPainel() { const de = state.painel?.de; state.painel = null; if (de) focar(de) }
function verComo(tid) {
  const ultimo = state.turnos.at(-1)?.id
  state.foco = tid === ultimo ? null : tid
  if (state.largura < 960) state.gaveta = true
  state.ladoMin = false
  anunciar(`Etapas do turno ${state.turnos.findIndex((t) => t.id === tid) + 1} ao lado.`)
  focar('rr-etapas-titulo')
}

// ---- etapas: estado, resumo e detalhes ----------------------------------------------------
function estadoItem(t, it) {
  if (!t) return 'pendente'
  const reg = t.est[it.chave]
  if (reg) return reg.status
  return t.status === 'pronto' || t.status === 'erro' ? 'pulada' : 'pendente'
}
function atual(t) {
  const rod = ITENS.filter((it) => estadoItem(t, it) === 'running')
  if (rod.length >= 2) return { etapa: rod[0].etapa, nome: 'Buscando vagas na Remotive e na Arbeitnow' }
  if (rod.length) return { etapa: rod[0].etapa, nome: rod[0].nome }
  const vistos = ITENS.filter((it) => t.est[it.chave])
  const u = vistos.at(-1) || ITENS[0]
  return { etapa: u.etapa, nome: u.nome }
}
function resumoTurno(t) {
  const fontes = new Set()
  let cache = 0, etapas = new Set()
  for (const it of ITENS) {
    const e = estadoItem(t, it)
    if (e === 'pulada' || e === 'pendente') continue
    etapas.add(it.etapa)
    if (e === 'cache') { cache += 1; continue }
    if (e === 'dummy') continue
    const fonte = t.est[it.chave]?.source || it.fonte
    if (EXTERNAS.includes(fonte)) fontes.add(fonte)
  }
  const nv = t.vagas.reduce((a, v) => a + v.verificacoes.length, 0) || t.est.verificacao?.data?.total || 0
  const partes = [pl(etapas.size, 'etapa', 'etapas'), pl(fontes.size, 'fonte externa', 'fontes externas')]
  if (cache) partes.push(`${cache} do cache`)
  partes.push(fmtMs(t.totalMs), pl(nv, 'verificação', 'verificações'), t.real ? 'modo real' : 'modo demo', 'chain.stream()')
  return partes.join(' · ')
}

function memoriaTurno(d) {
  const j = d.janela || {}, tk = j.tokens || {}, usadas = d.memoria?.usadas || []
  const total = j.total
  const pct = (v) => (total ? Math.round((v || 0) / total * 1000) / 10 : 0)
  const n = (v) => (v == null ? '—' : br(v))
  return {
    usoTxt: total == null ? 'contagem indisponível' : `${br(total)} tokens neste turno (${j.tokenizador})`,
    rotulo: `Janela de contexto deste turno: sistema ${n(tk.sistema)}, resumo ${n(tk.resumo)}, buffer ${n(tk.buffer)}, memória longa ${n(tk.memoria_longa)}, ferramentas ${n(tk.ferramentas)} tokens.`,
    segs: [['jn-sis', tk.sistema], ['jn-res', tk.resumo], ['jn-buf', tk.buffer], ['jn-lon', tk.memoria_longa], ['jn-fer', tk.ferramentas]].map(([cls, v]) => ({ cls, w: pct(v) })),
    curto: [
      { tag: 'ConversationBufferMemory', t: `${j.mensagens ?? '—'} mensagens nesta conversa · janela deslizante de ${j.limite_mensagens ?? 8}` },
      { tag: 'resumo', t: j.resumiu ? `mensagens antigas resumidas em ${n(tk.resumo)} tokens` : 'ainda não precisou resumir: a conversa cabe na janela' },
    ],
    longo: usadas.length
      ? usadas.map((m) => ({ tag: m.tipo, t: `${m.texto} · similaridade ${fmtSim(m.sim)}` }))
      : [{ tag: 'FAISS', t: 'nenhuma memória guardada para este usuário ainda' }],
  }
}

// O prompt real do agente, separado nas partes que a rubrica 2.5 pede.
function partesDoPrompt(prompt) {
  const [ptcf, resto = ''] = String(prompt || '').split('Exemplos de decisão:')
  const linhas = resto.split('\n').map((l) => l.trim()).filter(Boolean)
  const fewshot = linhas.filter((l) => l.startsWith('Anúncio:')).map((l) => {
    const acao = /Ação: ([^.]*)/.exec(l)?.[1] || ''
    const [rot, cls] = /descart/.test(acao) ? ['descartar', 'status st-des'] : /incerta/.test(acao) ? ['pendente', 'status st-pen'] : ['recomendar', 'status st-rec']
    return { rot, cls, t: l.replace(/^Anúncio:\s*/, '') }
  })
  return { ptcf: ptcf.trim(), fewshot, cot: linhas.find((l) => l.startsWith('Cheque em ordem')) || '' }
}

function detalhe(t, chave, reg) {
  const d = reg.data || {}
  const base = { resumo: reg.detail || '', linhas: [], codigo: '' }
  if (chave === 'intencao') {
    return { ...base, resumo: `O pedido virou uma saída estruturada (Pedido), validada por Pydantic. Classificador: ${d.classificador || '—'}.`,
      linhas: d.referencia ? [`Referência resolvida pelo histórico: ${d.referencia}`] : [], temRef: !!d.referencia,
      codigo: JSON.stringify(d.pedido ?? {}, null, 2),
      rota: d.rota ? { rota: d.rotas?.[d.rota] || d.rota, rotas: Object.values(d.rotas || {}), motivo: d.classificador, comp: d.composicao } : null }
  }
  if (chave === 'ferramentas') {
    const chamadas = (d.chamadas || [])
    const acoes = chamadas.filter((c) => c.evento === 'action')
    const texto = chamadas.map((c) => c.evento === 'action' ? `Action: ${c.tool}\nAction Input: ${c.input}`
      : c.evento === 'observation' ? `Observation (${fmtMs(c.duration_ms)}): ${c.output}` : `Erro em ${c.tool}: ${c.output}`).join('\n')
    const tokens = (d.tokens || []).reduce((a, u) => a + (u.total_tokens || 0), 0)
    return { ...base, resumo: `O AgentExecutor escolheu ${pl(acoes.length, 'ferramenta', 'ferramentas')}. Modelo: ${d.modelo || '—'}${tokens ? ` · ${br(tokens)} tokens` : ''}.`,
      linhas: [...new Set(acoes.map((c) => c.tool))], codigo: texto || 'Nenhuma ferramenta foi chamada pelo modelo neste turno.',
      codigoRotulo: `Chamadas reais, capturadas por ${d.callbacks ?? 0} eventos de callback (Rubrica 2.6)`,
      executor: d.executor, ...(d.prompt ? partesDoPrompt(d.prompt) : {}), temPrompt: !!d.prompt }
  }
  if (chave === 'remotive' || chave === 'arbeitnow') {
    if (reg.status === 'running' || !d.url) return base
    const resumo = reg.status === 'dummy' ? `Modo demo: ${pl(d.recebidas, 'vaga fictícia local', 'vagas fictícias locais')}, sem chamar a API.`
      : reg.status === 'erro' ? reg.detail
      : `${pl(d.recebidas, 'vaga recebida', 'vagas recebidas')}, ${d.correspondem} ${d.termos ? `com “${d.termos}”` : 'na busca'}.${reg.status === 'cache' ? ' Resposta do cache.' : ''}`
    const rec = d.reescrita ? { antesQ: d.reescrita.antesQ, antes: [{ s: '0', t: 'nenhum anúncio com esses termos' }], depoisQ: d.reescrita.depoisQ,
      depois: [{ s: String(d.correspondem), t: `${pl(d.correspondem, 'anúncio encontrado', 'anúncios encontrados')} nesta fonte` }], diag: d.reescrita.diag, tecnica: 'consulta traduzida pelo LLM' } : null
    return { ...base, resumo, rec, codigo: `GET ${d.url.replace('https://', '')}\n${reg.status === 'dummy' ? 'não chamada (modo demo)' : `${d.situacao} · ${pl(d.recebidas, 'vaga', 'vagas')} · ${fmtMs(reg.ms)}`}` }
  }
  if (chave === 'cambio') {
    if (!d.par) return base
    return { ...base, resumo: reg.status === 'dummy' ? 'Modo demo: usei a cotação fictícia, sem chamar a API.' : `Cotação de ${d.data || 'hoje'}, pela ${d.fonte}.`,
      codigo: d.url ? `GET ${d.url.replace('https://', '')}\n200 OK · bid ${d.taxa}` : `${d.par.replace('-', ' → ')} ${d.taxa} (${d.fonte})` }
  }
  if (chave === 'curriculo') {
    const trechos = d.trechos || []
    return { ...base, resumo: trechos.length ? `${pl(trechos.length, 'trecho recuperado', 'trechos recuperados')}, do mais parecido para o menos.` : reg.detail,
      linhas: trechos.map((x) => `${fmtSim(x.s)} · “${x.t}”`),
      codigo: `FAISS.load_local("${d.indice || 'faiss_index'}/")\nsimilarity_search_with_score(k=${d.k ?? 3}) · embeddings ${d.embeddings || ''}`,
      rec: d.rec ? { ...d.rec, antes: d.rec.antes.map((x) => ({ s: fmtSim(x.s), t: x.t })), depois: d.rec.depois.map((x) => ({ s: fmtSim(x.s), t: x.t })) } : null }
  }
  if (chave === 'historico') {
    return { ...base, resumo: d.sql ? `A consulta devolveu ${pl(d.n, 'linha', 'linhas')}. SQL gerado por ${d.gerador}.` : reg.detail,
      linhas: (d.linhas || []).map((l) => Object.values(l).filter((v) => v != null).join(' · ')), codigo: d.sql || '' }
  }
  if (chave === 'verificacao') {
    const c = d.contagem || {}
    const rot = { contradiction: 'contradição', entailment: 'sustentação', neutral: 'neutralidade' }
    return { ...base, resumo: `${pl(d.total || 0, 'afirmação checada', 'afirmações checadas')}. ${pl(c.confirmada || 0, 'confirmada', 'confirmadas')}${c.contradita ? `, ${pl(c.contradita, 'contradita', 'contraditas')}` : ''}${c.incerta ? `, ${pl(c.incerta, 'incerta', 'incertas')}` : ''}.`,
      linhas: (d.nli || []).map((x) => `${x.job_id}: NLI ${rot[x.rotulo] || x.rotulo} ${fmtSim(x.score)} → ${x.status}${(d.corrigidas || []).includes(x.job_id) ? ' · corrigida' : ''}`),
      codigo: d.modelo ? `NLI: ${d.modelo}\nChecagem lógica: ${d.logica || 'regra de elegibilidade (modo demo)'}` : 'Checagem por regra de evidência: o trecho do anúncio sustenta a afirmação.' }
  }
  if (chave === 'resposta') {
    return { ...base, resumo: `Resposta escrita por ${d.stream || 'resposta_chain.stream()'} e salva na memória da sessão.`,
      codigo: `session_id: ${d.session_id}\nmensagens na memória: ${d.mensagens}\n${d.historico || ''}`, mem: memoriaTurno(d) }
  }
  return base
}

function lado() {
  const s = state
  const ult = s.turnos.at(-1)
  let t = ult, idx = s.turnos.length
  if (s.foco) s.turnos.forEach((x, i) => { if (x.id === s.foco) { t = x; idx = i + 1 } })
  const noEst = (ch) => ST[estadoItem(t, POR_CHAVE[ch])].no
  const feitoish = (e) => ['feito', 'cache', 'incerto', 'dummy', 'erro'].includes(e)
  const no = (ch) => {
    const e = noEst(ch)
    const d = { feito: IC.check, ativo: IC.ponto, fila: IC.anel, erro: IC.x, cache: IC.cache, incerto: IC.duvida, dummy: IC.simulada }[e] || ''
    return { c: `no n-${e}`, temIc: e !== 'pulada', ic: e === 'ativo' ? 'ic ic-cheio' : 'ic', d }
  }
  const ed = (ch) => { const e = noEst(ch); return e === 'ativo' ? 'e-ativo' : feitoish(e) ? 'e-feito' : 'e-fila' }
  const r = noEst('remotive'), a = noEst('arbeitnow')
  const juntou = feitoish(r) && feitoish(a) && !(r === 'erro' && a === 'erro')
  const meio = ['cambio', 'curriculo', 'historico'].some((c) => noEst(c) === 'ativo')
  const usadas = t ? new Set(ITENS.filter((it) => t.est[it.chave]).map((it) => it.etapa)).size : 0

  let status
  if (!t) status = 'Aguardando seu pedido'
  else if (t.status === 'processando') status = `Executando · etapa ${atual(t).etapa + 1} de 8`
  else if (t.status === 'erro') status = `Interrompido na etapa ${atual(t).etapa + 1} de 8`
  else status = `Concluído · ${usadas} de 8 etapas usadas`

  const tl = []
  if (t) {
    for (const it of ITENS) {
      if (it.chave === 'remotive') tl.push({ grupo: true, item: false, classe: 'tl-item' })
      const e = estadoItem(t, it), reg = t.est[it.chave] || {}
      let det = null
      if (e === 'running') det = { resumo: `Em andamento. Aguardando ${reg.source || it.fonte}.` }
      else if (e !== 'pendente' && e !== 'pulada') det = detalhe(t, it.chave, reg)
      const aberto = !!t.abertos[it.chave] && !!det
      let rub2 = null
      if (det?.rec) rub2 = '4.5 Correção'
      if (det?.rota) rub2 = det.temRef ? '2.3 Router · 3.6 Multi-turno' : '2.3 Router'
      if (det?.temPrompt) rub2 = '2.5 PTCF · 2.2 ReAct'
      if (det?.mem) rub2 = '3.1 · 3.2 · 3.4'
      const fonte = reg.source || it.fonte
      // Without a model (demo mode) only retrieval and NLI still depend on a model's interpretation.
      const semantica = t.real || it.chave === 'curriculo' || it.chave === 'verificacao' || TIPOS[it.chave][0] === 'hardcoded'
      const react = t.react
      tl.push({
        grupo: false, item: true,
        classe: `tl-item tl-${e}${it.sub ? ' tl-sub' : ''}`,
        nome: it.chave === 'cambio' && fonte !== 'AwesomeAPI' ? 'Consultando câmbio' : it.nome, rubrica: it.rubrica, fonte,
        stTexto: ST[e].texto, rodando: e === 'running', parado: e !== 'running', icD: ST[e].d,
        temDur: reg.ms != null && e !== 'running', dur: fmtMs(reg.ms),
        expansivel: !!det, desligado: det ? 'false' : 'true',
        aberto, abertoAttr: aberto ? 'true' : 'false', detId: `rr-tl-${t.id}-${it.chave}`,
        alternar: () => { if (det) t.abertos[it.chave] = !t.abertos[it.chave] },
        resumo: det?.resumo || '',
        temLinhas: !!det?.linhas?.length, linhas: (det?.linhas || []).map((x) => ({ t: x })),
        temCodigo: !!det?.codigo, codigo: det?.codigo || '', temCodigoRotulo: !!det?.codigoRotulo, codigoRotulo: det?.codigoRotulo || '',
        liId: `rr-tl-li-${t.id}-${it.chave}`,
        temTipos: true, tipoLog: semantica ? TIPOS[it.chave][0] : 'hardcoded',
        tipoLogCls: `selo-tipo ${(semantica ? TIPOS[it.chave][0] : 'hardcoded') === 'hardcoded' ? 'tp-hard' : 'tp-sem'}`, tipoInt: TIPOS[it.chave][1],
        temRub2: !!rub2, rub2: rub2 || '',
        temRota: !!det?.rota, rotaMotivo: det?.rota?.motivo || '', rotaComp: det?.rota?.comp || '',
        rotas: (det?.rota?.rotas || []).map((nome) => { const on = det.rota.rota === nome; return { nome, on, cls: `rota${on ? ' rota-on' : ''}`, sr: on ? ' (escolhida)' : '' } }),
        temPtcf: !!det?.temPrompt, ptcf: det?.ptcf || '', fewshot: det?.fewshot || [], cot: det?.cot || '', executor: det?.executor || '',
        temRec: !!det?.rec, rec: det?.rec || { antesQ: '', depoisQ: '', antes: [], depois: [], diag: '', tecnica: '' },
        temMem: !!det?.mem, mem: det?.mem || { usoTxt: '', rotulo: '', segs: [], curto: [], longo: [] },
        reactRodando: !!react?.rodando, reactDesligado: react?.rodando ? 'true' : 'false',
        reactTexto: react?.rodando ? 'Rodando o ReAct clássico…' : react?.ciclo ? 'Rodar de novo' : 'Rodar este pedido no ReAct clássico',
        rodarReact: () => rodarReact(t),
        temReact: !!react?.ciclo, reactErro: react?.erro || '', temReactErro: !!react?.erro,
        reactModelo: react?.ciclo ? `initialize_agent · ZERO_SHOT_REACT_DESCRIPTION · modelo ${react.modelo}` : '',
        reactCiclo: (react?.ciclo || []).map((p) => `${p.log}\nObservation: ${p.observation}`).join('\n\n') + (react?.resposta ? `\n\nFinal Answer: ${react.resposta}` : ''),
      })
    }
  }
  const tlTotal = !t ? '' : t.status === 'pronto' ? `congelada · ${fmtMs(t.totalMs)}` : t.status === 'erro' ? 'interrompida' : 'ao vivo'
  const curta = t ? (t.pergunta.length > 38 ? `${t.pergunta.slice(0, 36)}…` : t.pergunta) : ''
  return {
    status, tl, tlTotal, mostrandoId: t?.id ?? null,
    rotulo: `Fluxo do agente: ${ITENS.map((it) => `${it.curto} ${ST[estadoItem(t, it)].fala}`).join(', ')}.`,
    congelado: !!(t && ult && t.id !== ult.id), congeladoTexto: `Turno ${idx} de ${s.turnos.length}: “${curta}”`,
    nos: Object.fromEntries(ITENS.map((it) => [it.chave, no(it.chave)])),
    ed: { e0: ed('intencao'), e1: ed('ferramentas'), e2a: ed('remotive'), e2b: ed('arbeitnow'), eU: juntou ? (meio ? 'e-ativo' : 'e-feito') : 'e-fila',
      e3: ed('cambio'), e4: ed('curriculo'), e5: ed('historico'), e6: ed('verificacao'), e7: ed('resposta') },
  }
}

function painelVals() {
  if (!state.painel) return null
  const t = turnoDe(state.painel.turno)
  const v = t?.vagas.find((x) => x.id === state.painel.vaga)
  if (!v) return null
  const conta = {}
  v.verificacoes.forEach((c) => { conta[c.status] = (conta[c.status] || 0) + 1 })
  const partes = [pl(v.verificacoes.length, 'afirmação', 'afirmações')]
  for (const k of ['confirmada', 'contradita', 'incerta', 'indisponível']) if (conta[k]) partes.push(`${conta[k]} ${VEREDITO[k].texto.toLowerCase()}${conta[k] > 1 ? 's' : ''}`)
  const nli = t.est.verificacao?.data
  return {
    titulo: v.title, company: v.company, source: v.source, url: v.url, reason: v.reason, evidence: v.evidence || 'O anúncio não traz um trecho que sustente a decisão.',
    cite: `${v.source} · anúncio ${v.id}`,
    isRec: v.status === 'recomendado', isPen: v.status === 'pendente', isDes: v.status === 'descartado',
    temCorrecao: !!v.correcao, c: v.correcao || { proposta: '', anuncio: '', correcao: '', placar: '' },
    conta: partes.join(' · '),
    verifs: v.verificacoes.map((c) => { const m = VEREDITO[c.status]; return { claim: c.claim, reason: c.reason, cls: m.cls, texto: m.texto, d: m.d } }),
    rodape: nli?.modelo ? `NLI: ${nli.modelo} · checagem lógica: ${nli.logica || 'regra de elegibilidade'}` : 'Checagem por regra de evidência',
    fechar: fecharPainel,
    teclar: (e) => { if (e.key === 'Tab') prenderFoco(e, 'rr-painel') },
  }
}

// ---- currículo ----------------------------------------------------------------------------
function mensagemCv(tipo, nome, mb) {
  const resto = ' Seu currículo atual continua valendo.'
  if (tipo === 'tipo') return { titulo: 'Esse arquivo não é PDF.', texto: `“${nome}” não pode ser lido. Exporte o currículo em PDF e tente de novo.${resto}` }
  if (tipo === 'grande') return { titulo: 'O arquivo passa de 5 MB.', texto: `“${nome}” tem ${(Math.round(mb * 10) / 10).toFixed(1).replace('.', ',')} MB. Comprima o PDF ou exporte sem imagens e tente de novo.${resto}` }
  if (tipo === 'sem-texto') return { titulo: 'Não encontrei texto neste PDF.', texto: `Ele parece ser uma imagem digitalizada. Exporte o currículo direto do editor de texto e envie de novo.${resto}` }
  return { titulo: 'Não consegui trocar o currículo.', texto: `${nome}${resto}` }
}
function falhaCv(m) { Object.assign(state, { cvErro: m, cvConfirmar: false }); anunciar(`${m.titulo} ${m.texto}`) }

async function escolherArquivo(file) {
  if (!file || (state.cvEnvio && !state.cvEnvio.fim)) return
  const nome = file.name || 'curriculo.pdf'
  const mb = (file.size || 0) / 1048576
  state.cvEnvio = null
  if (!(file.type === 'application/pdf' || /\.pdf$/i.test(nome))) return falhaCv(mensagemCv('tipo', nome, mb))
  if (mb > 5) return falhaCv(mensagemCv('grande', nome, mb))
  Object.assign(state, { cvErro: null, cvConfirmar: false, cvEnvio: { tipo: 'envio', arquivo: nome, ordem: ['enviando', 'lendo', 'indexando', 'extraindo'], est: { enviando: { status: 'running' } }, fim: false } })
  anunciar(`Enviando ${nome}`)
  try {
    for await (const ev of enviarCurriculo(file)) {
      if (ev.type === 'stage') {
        state.cvEnvio.est[ev.key] = { status: ev.status, ms: ev.duration_ms, source: ev.source }
        if (ev.status === 'running') anunciar(ETAPAS_CV[ev.key]?.nome || ev.key)
      } else if (ev.type === 'error') {
        state.cvEnvio.fim = true
        return falhaCv(mensagemCv(ev.erro || 'outro', ev.message || nome, mb))
      } else if (ev.type === 'final') {
        aplicarCv(ev.data)
        state.cvEnvio = null
        toast('Currículo trocado. As próximas buscas usam o novo perfil.')
      }
    }
  } catch (erro) {
    state.cvEnvio = null
    falhaCv(erro.status === 415 ? mensagemCv('tipo', nome, mb) : erro.status === 413 ? mensagemCv('grande', nome, mb) : mensagemCv('outro', erro.message, mb))
  }
}
async function restaurarCv() {
  Object.assign(state, { cvErro: null, cvConfirmar: false, cvEnvio: { tipo: 'restaurar', arquivo: '', ordem: ['indexando', 'extraindo'], est: { indexando: { status: 'running' }, extraindo: { status: 'running' } }, fim: false } })
  anunciar('Restaurando o currículo anterior')
  const inicio = Date.now()
  try {
    aplicarCv(await post('/curriculo/reset'))
    toast('Currículo restaurado.')
  } catch (erro) {
    falhaCv(mensagemCv('outro', erro.message, 0))
  } finally {
    state.cvEnvio = null
    focar('rr-cv-trocar')
  }
  return Date.now() - inicio
}

function cvVals() {
  const s = state
  const info = s.cv || { nome: '', origem: 'ficticio', paginas: null, skills: [], senioridade: null, chave: '' }
  const ORIGEM = {
    pessoal: { texto: 'Pessoal', d: 'M12 12a4 4 0 1 0 0-8a4 4 0 0 0 0 8zM5 20a7 7 0 0 1 14 0' },
    enviado: { texto: 'Enviado', d: 'M12 16V5M7 10l5-5 5 5M5 19h14' },
    ficticio: { texto: 'Fictício', d: IC.simulada },
  }[info.origem]
  const paginas = info.paginas ?? s.pdf.paginas
  const env = s.cvEnvio, ocupado = !!(env && !env.fim)
  const sen = info.senioridade ? info.senioridade[0].toUpperCase() + info.senioridade.slice(1) : 'senioridade não informada'
  return {
    versao: info.origem, arquivo: info.nome, chave: info.chave, temPdf: !!info.chave,
    origemTexto: ORIGEM.texto, origemD: ORIGEM.d, origemClasse: `status or-${info.origem}`,
    meta: `${pl(paginas, 'página', 'páginas')} · ${sen} · ${pl(info.skills.length, 'skill extraída', 'skills extraídas')}`,
    skills: info.skills.map((k) => ({ nome: k })),
    abrirRotulo: `Abrir ${info.nome} no leitor, ${pl(paginas, 'página', 'páginas')}`,
    abrir: abrirLeitor,
    ocupadoAttr: ocupado ? 'true' : 'false',
    enviando: !!env, etapasRotulo: env?.tipo === 'restaurar' ? 'Etapas da restauração' : `Etapas do envio de ${env?.arquivo || ''}`,
    etapas: env ? env.ordem.map((ch) => {
      const reg = env.est[ch] || {}, e = reg.status || 'pendente', E = ETAPAS_CV[ch]
      return { classe: `tl-item tl-${e}`, nome: E.nome, fonte: reg.source || E.fonte, temRubrica: !!E.rubrica, rubrica: E.rubrica || '',
        stTexto: ST[e].texto, rodando: e === 'running', parado: e !== 'running', icD: ST[e].d, temDur: reg.ms != null, dur: fmtMs(reg.ms) }
    }) : [],
    temErro: !!s.cvErro, erroTitulo: s.cvErro?.titulo || '', erroTexto: s.cvErro?.texto || '',
    confirmar: !!s.cvConfirmar, confirmarAttr: s.cvConfirmar ? 'true' : 'false',
    podeRestaurar: !!info.pode_restaurar && !ocupado,
    trocarDesligado: ocupado ? 'true' : 'false',
    trocar: () => { if (!ocupado) document.getElementById('rr-cv-arquivo')?.click() },
    aoEscolher: (e) => { const f = e.target.files?.[0]; e.target.value = ''; escolherArquivo(f) },
    arrastando: !!s.arrastando,
    arrastaSobre: (e) => { e.preventDefault(); if (!s.arrastando && !ocupado) s.arrastando = true },
    arrastaSai: (e) => { if (e.currentTarget && e.relatedTarget && e.currentTarget.contains(e.relatedTarget)) return; s.arrastando = false },
    soltar: (e) => { e.preventDefault(); s.arrastando = false; escolherArquivo(e.dataTransfer?.files?.[0]) },
    pedirRestaurar: () => { const abrir = !s.cvConfirmar; Object.assign(s, { cvConfirmar: abrir, cvErro: null }); if (abrir) focar('rr-cv-restaurar-ok') },
    cancelarRestaurar: () => { s.cvConfirmar = false; focar('rr-cv-restaurar') },
    restaurar: restaurarCv,
  }
}

// ---- leitor de PDF ------------------------------------------------------------------------
let origemLeitor = null
function calcFit(w, h) {
  // Página inteira, no máximo o tamanho real (100%).
  const f = Math.min(w / state.pdf.largura, h / state.pdf.altura, 1)
  return Math.max(0.3, Math.floor(f * 100) / 100)
}
function fitDe(R, barra) {
  const M = R.width < 560 ? 8 : 32, P = 12
  return calcFit(R.width - 2 * M - 2 * P - 2, R.height - 2 * M - barra - 2 * P - 2)
}
function medirLeitor() {
  const raiz = document.getElementById('rr-leitor')?.closest('.rr')
  if (!raiz || !state.leitor) return
  const barra = document.getElementById('rr-leitor-barra')
  state.leitor.fit = fitDe(raiz.getBoundingClientRect(), barra ? barra.offsetHeight : 57)
}
function animarLeitor() {
  const r = origemLeitor, folha = document.getElementById('rr-leitor-folha'), caixa = document.getElementById('rr-leitor')
  if (calmo()) return
  caixa?.animate?.([{ opacity: 0 }, { opacity: 1 }], { duration: 200, easing: 'ease-out' })
  if (!r || !folha?.animate) return
  const f = folha.getBoundingClientRect()
  if (!f.width) return
  folha.animate([
    { transformOrigin: '0 0', transform: `translate(${r.left - f.left}px,${r.top - f.top}px) scale(${r.width / f.width})` },
    { transformOrigin: '0 0', transform: 'none' },
  ], { duration: 360, easing: 'cubic-bezier(.2,.8,.2,1)' })
}
function abrirLeitor() {
  const mini = document.getElementById('rr-cv-mini')
  origemLeitor = mini ? mini.getBoundingClientRect() : null
  const R = mini?.closest('.rr')?.getBoundingClientRect() || { width: window.innerWidth, height: window.innerHeight }
  state.leitor = { pagina: 1, modo: 'ajustar', zoom: 100, fit: fitDe(R, 57) }
  setTimeout(() => { medirLeitor(); animarLeitor(); document.getElementById('rr-leitor-fechar')?.focus() }, 20)
}
function fecharLeitor() { state.leitor = null; focar('rr-cv-abrir') }

function leitorVals() {
  const ZOOMS = [50, 75, 100, 125, 150, 200, 300]
  const L = state.leitor || { pagina: 1, modo: 'ajustar', zoom: 100, fit: 1 }
  const total = state.pdf.paginas, W = state.pdf.largura, H = state.pdf.altura
  const pagina = Math.min(L.pagina, total)
  const ajustado = L.modo === 'ajustar'
  const z = ajustado ? (L.fit || 1) : L.zoom / 100
  const pct = Math.round(z * 100)
  const acima = ZOOMS.filter((x) => x > pct + 1), abaixo = ZOOMS.filter((x) => x < pct - 1)
  const irPag = (n) => { if (n < 1 || n > total || !state.leitor) return; state.leitor.pagina = n; const p = document.getElementById('rr-leitor-palco'); if (p) p.scrollTop = 0 }
  const irZoom = (v) => { if (v != null && state.leitor) Object.assign(state.leitor, { modo: 'livre', zoom: v }) }
  const ajustar = () => { if (state.leitor) state.leitor.modo = 'ajustar'; medirLeitor() }
  return {
    pagina, paginaStr: String(pagina), total,
    w: Math.round(W * z), h: Math.round(H * z), z,
    caixaW: Math.round(W * (L.fit || 1)) + 24 + 2, palcoH: Math.round(H * (L.fit || 1)) + 24,
    zoomTexto: `${pct}%`,
    zoomRotulo: `Zoom em ${pct}%${ajustado ? ', página inteira' : ''}. Voltar para 100%`,
    ajustadoAttr: ajustado ? 'true' : 'false',
    antDesligado: pagina <= 1 ? 'true' : 'false', proxDesligado: pagina >= total ? 'true' : 'false',
    menosDesligado: abaixo.length ? 'false' : 'true', maisDesligado: acima.length ? 'false' : 'true',
    anterior: () => irPag(pagina - 1), proxima: () => irPag(pagina + 1),
    menos: () => irZoom(abaixo.at(-1)), mais: () => irZoom(acima[0]),
    zoomReset: () => irZoom(100), ajustar, fechar: fecharLeitor,
    teclar: (e) => {
      const k = e.key
      if (k === 'ArrowRight' || k === 'PageDown') { e.preventDefault(); irPag(pagina + 1) }
      else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); irPag(pagina - 1) }
      else if (k === '+' || k === '=') { e.preventDefault(); irZoom(acima[0]) }
      else if (k === '-') { e.preventDefault(); irZoom(abaixo.at(-1)) }
      else if (k === '0') { e.preventDefault(); ajustar() }
      else if (k === '1') { e.preventDefault(); irZoom(100) }
      else if (k === 'Tab') prenderFoco(e, 'rr-leitor')
    },
  }
}

// ---- conversas (um session_id cada) e memória ---------------------------------------------
function novaConv(titulo) {
  let t = String(titulo || 'Conversa').replace(/\s+/g, ' ').trim()
  if (t.length > 42) t = `${t.slice(0, 40).replace(/\s+\S*$/, '')}…`
  return { id: novoId('c'), titulo: t, criada: Date.now() }
}
function registrarConversa(titulo) {
  if (state.convAtual) return
  const c = novaConv(titulo)
  state.conversas.unshift(c)
  state.convAtual = c.id
}
const foto = () => ({ turnos: JSON.parse(JSON.stringify(state.turnos.filter((t) => t.status === 'pronto'))).map((t) => ({ ...t, stream: null, react: t.react?.ciclo ? t.react : null })), acoes: { ...state.acoes }, sessao: state.sessao })
function saiDaConversa() {
  if (!state.convAtual && state.turnos.length) registrarConversa(state.turnos[0].pergunta)
  if (state.convAtual) state.arquivo[state.convAtual] = foto()
}
const limpa = () => ({ foco: null, painel: null, apagando: null, confirmar: false, rascunho: '', memAberto: false, trilho: false })
function abrirVazia() {
  Object.assign(state, limpa(), { convAtual: null, turnos: [], acoes: {}, memSessao: [], janela: {}, sessao: novoId('ian') })
}
function abrirArquivada(id) {
  const alvo = state.arquivo[id]
  Object.assign(state, limpa(), { convAtual: id, turnos: alvo.turnos.map((t) => reactive({ ...t, stream: null })), acoes: alvo.acoes, sessao: alvo.sessao })
  carregarMemoria().catch(() => {})
}
function novaConversa() {
  if (state.ocupado) return
  if (!state.convAtual && !state.turnos.length) { state.trilho = false; focar('rr-mensagem'); return }
  saiDaConversa()
  abrirVazia()
  anunciar('Nova conversa. A memória de longo prazo continua valendo.')
  focar('rr-mensagem')
}
function trocarConversa(id) {
  if (id === state.convAtual) { state.trilho = false; return }
  if (state.ocupado) return
  saiDaConversa()
  if (!state.arquivo[id]) return
  abrirArquivada(id)
  anunciar(`Conversa aberta: ${state.conversas.find((c) => c.id === id)?.titulo || ''}.`)
  rolar()
}
function apagarConversa(id) {
  if (state.ocupado) return
  const sessao = id === state.convAtual ? state.sessao : state.arquivo[id]?.sessao
  if (sessao) del(`/sessoes/${sessao}`).catch(() => {})
  state.conversas = state.conversas.filter((c) => c.id !== id)
  delete state.arquivo[id]
  state.apagando = null
  if (id === state.convAtual) {
    const prox = state.conversas[0]
    if (prox && state.arquivo[prox.id]) abrirArquivada(prox.id)
    else abrirVazia()
  }
  toast('Conversa apagada. A memória de longo prazo continua.')
  focar('rr-nova-conv')
}
async function esquecer(m) {
  try {
    await del(`/memoria/${m.id}?user_id=${state.usuario}`)
    state.memLonga = state.memLonga.filter((x) => x.id !== m.id)
    anunciar('Memória apagada.')
  } catch (erro) { toast(`Não consegui apagar a memória. ${erro.message}`) }
  focar('rr-mem-tab-longo')
}
function abrirMem(aba) { Object.assign(state, { memAberto: true, memAba: aba || 'longo' }); focar(`rr-mem-tab-${aba || 'longo'}`) }
function fecharMem() { Object.assign(state, { memAberto: false, memNovas: [] }); focar('rr-mem-btn') }

function memVals() {
  const s = state, j = s.janela || {}, tk = j.tokens || {}
  const nl = s.memLonga.length, ns = s.memSessao.length
  const novas = s.memNovas.length
  const aba = s.memAba || 'longo'
  const ABAS = [{ k: 'longo', rot: 'Longo prazo', n: nl }, { k: 'sessao', rot: 'Nesta conversa', n: ns }, { k: 'janela', rot: 'Janela', n: null }]
  const TIPO = { 'semântica': 'selo-tipo tp-sem', 'episódica': 'selo-tipo tp-epi', procedural: 'selo-tipo tp-pro' }
  const quando = (iso) => { const d = new Date(iso); return Number.isNaN(d.getTime()) ? '' : d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) }
  const itens = aba === 'longo'
    ? s.memLonga.map((m) => ({ classe: `mem-it${s.memNovas.includes(m.texto) ? ' mem-nova' : ''}`, tipo: m.tipo, tipoClasse: TIPO[m.tipo] || 'selo-tipo tp-sem', texto: m.texto,
      origem: `${m.origem} · ${quando(m.criado_em)}`, apagarRotulo: `Esquecer: ${m.texto}`, podeApagar: true, apagar: () => esquecer(m) }))
    : aba === 'sessao'
      ? s.memSessao.map((m) => ({ classe: `mem-it${s.memNovas.includes(m.texto) ? ' mem-nova' : ''}`, tipo: m.tag, tipoClasse: 'selo-tipo tp-ses', texto: m.texto,
        origem: 'vale só nesta conversa', apagarRotulo: '', podeApagar: false, apagar: () => {} }))
      : []
  const partes = [['jn-sis', 'Instruções do sistema', tk.sistema], ['jn-fer', 'Resultados das ferramentas', tk.ferramentas], ['jn-res', 'Resumo das mensagens antigas', tk.resumo],
    ['jn-buf', 'Histórico da conversa (buffer)', tk.buffer], ['jn-lon', 'Memórias recuperadas (FAISS)', tk.memoria_longa]]
  const total = j.total
  const pc = (v) => (total ? `${(Math.round((v || 0) / total * 1000) / 10).toLocaleString('pt-BR')}%` : '—')
  const mensagens = j.mensagens ?? 0, limite = j.limite_mensagens ?? 8
  const pct = `${Math.min(100, Math.round(mensagens / limite * 100))}%`
  const LEAD = {
    longo: 'Vale em todas as conversas. Cada memória vira um vetor no índice FAISS do usuário, com o tipo CoALA. A cada pedido, as 3 mais parecidas entram no contexto.',
    sessao: 'Vale só nesta conversa: o RunnableWithMessageHistory guarda as mensagens por session_id, lidas pelo ConversationBufferMemory. Some ao abrir outra conversa.',
    janela: 'O que entrou na janela de contexto do modelo no último turno, contado em tokens.',
  }
  const VAZIO = {
    longo: 'Nada guardado ainda. Diga uma preferência, como “não quero vagas com Django e mostre o salário sempre em reais”. Depois abra uma nova conversa e veja se ela continua valendo.',
    sessao: 'Nada nesta conversa. Experimente “responde mais curto”: vale aqui e some ao abrir outra conversa.',
  }
  const ids = ABAS.map((a) => `rr-mem-tab-${a.k}`)
  const resumo = nl || ns ? `${nl} de longo prazo · ${ns} nesta conversa` : 'Nada guardado ainda'
  return {
    aberto: s.memAberto, abertoAttr: s.memAberto ? 'true' : 'false', btnClasse: 'tr-mem-btn',
    pct, segs: partes.map(([cls, , v]) => ({ cls, w: total ? Math.round((v || 0) / total * 1000) / 10 : 0 })),
    linhas: total == null
      ? [{ cls: 'livre', nome: 'Envie um pedido para medir a janela', n: '—', p: '' }]
      : [...partes.map(([cls, nome, v]) => ({ cls, nome, n: br(v || 0), p: pc(v) })), { cls: 'livre', nome: 'Mensagens no buffer', n: `${mensagens} de ${limite}`, p: pct }],
    janelaRotulo: total == null ? 'Janela de contexto ainda não medida.' : `Janela de contexto do último turno: ${br(total)} tokens. ${partes.map(([, nome, v]) => `${nome} ${v || 0}`).join(', ')}.`,
    miniRotulo: `Memória: buffer com ${mensagens} de ${limite} mensagens. ${resumo}.`,
    resumo, temNovas: novas > 0 && !s.memAberto, novasTxt: novas === 1 ? '1 nova' : `${novas} novas`,
    alternar: () => { if (s.memAberto) fecharMem(); else abrirMem(nl || !ns ? 'longo' : 'sessao') },
    fechar: fecharMem,
    abas: ABAS.map((a) => ({ id: `rr-mem-tab-${a.k}`, rot: a.rot, n: a.n, temN: a.n != null, sel: a.k === aba ? 'true' : 'false', tab: a.k === aba ? '0' : '-1', escolher: () => { s.memAba = a.k } })),
    teclarAbas: (e) => {
      const at = ids.indexOf(document.activeElement?.id), ks = ABAS.map((a) => a.k)
      const vai = (i) => { i = (i + ks.length) % ks.length; s.memAba = ks[i]; focar(ids[i]) }
      if (e.key === 'ArrowRight') { e.preventDefault(); vai(at + 1) }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); vai(at - 1) }
      else if (e.key === 'Home') { e.preventDefault(); vai(0) }
      else if (e.key === 'End') { e.preventDefault(); vai(ks.length - 1) }
    },
    abaId: `rr-mem-tab-${aba}`, lead: LEAD[aba],
    temItens: itens.length > 0, itens,
    vazio: aba !== 'janela' && !itens.length, vazioTxt: VAZIO[aba] || '',
    abaJanela: aba === 'janela',
    rodape: `session_id: ${s.sessao} · FAISS por usuário, k=3 · ${total == null ? 'janela ainda não medida' : `${br(total)} tokens (${j.tokenizador})`}`,
  }
}

function conversasVals() {
  const s = state
  const hora = (ms) => { const d = new Date(ms); return Date.now() - ms < 60000 ? 'agora' : `${`0${d.getHours()}`.slice(-2)}:${`0${d.getMinutes()}`.slice(-2)}` }
  const lista = s.conversas.map((c) => {
    const atualConv = c.id === s.convAtual, conf = s.apagando === c.id
    const n = atualConv ? s.turnos.length : (s.arquivo[c.id]?.turnos || []).length
    return {
      virtual: false, normal: !conf, confirmando: conf, titulo: c.titulo,
      classe: `tr-it${atualConv ? ' tr-on' : ''}`,
      meta: `${pl(n, 'pedido', 'pedidos')} · ${hora(c.criada)}`,
      atualAttr: atualConv ? 'page' : 'false', desligada: s.ocupado ? 'true' : 'false',
      apagarId: `rr-apagar-${c.id}`, apagarRotulo: `Apagar a conversa ${c.titulo}`,
      confId: `rr-conf-${c.id}`, okId: `rr-conf-ok-${c.id}`,
      abrir: () => trocarConversa(c.id),
      pedirApagar: () => { if (s.ocupado) return; s.apagando = c.id; focar(`rr-conf-ok-${c.id}`) },
      cancelar: () => { s.apagando = null; focar(`rr-apagar-${c.id}`) },
      apagar: () => apagarConversa(c.id),
    }
  })
  const nada = () => {}
  if (!s.convAtual) lista.unshift({ virtual: true, normal: false, confirmando: false, classe: 'tr-it tr-on', titulo: '', meta: '', atualAttr: 'page', desligada: 'true', apagarId: '', apagarRotulo: '', confId: '', okId: '', abrir: nada, pedirApagar: nada, cancelar: nada, apagar: nada })
  return lista
}

// ---- modelo -------------------------------------------------------------------------------
function abrirMenu() { state.menu = true; focar(`rr-modelo-${state.modelos.ativo}`) }
function fecharMenu(devolver) { state.menu = false; if (devolver) focar('rr-modelo-btn') }
async function confirmarModelo() {
  const alvo = state.modelos.opcoes.find((m) => m.id === state.trocarPara)
  if (!alvo || state.trocando) return
  state.trocando = true
  anunciar(`Trocando para ${alvo.rotulo}. Isso pode levar alguns segundos.`)
  try {
    state.modelos = await post('/modelo', { id: alvo.id })
    saiDaConversa()
    abrirVazia()
    Object.assign(state, { trocarPara: null, ocupado: false, toasts: [] })
    get('/curriculo/info').then(aplicarCv).catch(() => {})
    toast(`Modelo trocado para ${alvo.rotulo}. Nova conversa iniciada.`)
    anunciar(`Modelo trocado para ${alvo.rotulo}. Nova conversa iniciada.`)
  } catch (erro) {
    state.trocarPara = null
    toast(`Não consegui trocar o modelo. ${erro.message}`)
  } finally {
    state.trocando = false
    focar('rr-modelo-btn')
  }
}

// ---- avaliação no LangSmith ---------------------------------------------------------------
function avalVals() {
  const a = state.aval || {}
  const m = a.metricas || {}
  const fracao = (x) => (x ? `${x.passou}/${x.total}` : '—')
  return {
    situacao: a.disponivel ? `experimento ${a.experimento || ''}` : 'aguardando o experimento',
    correcao: fracao(m.correcao_semantica), trajetoria: fracao(m.trajetoria), verificacao: fracao(m.afirmacoes_confirmadas),
    temUrl: !!a.url, url: a.url || '#',
    nota: a.disponivel ? `${a.casos} casos de teste · ${a.data || ''}` : 'Rode scripts.evaluate --langsmith para publicar o experimento.',
  }
}

// ---- modelo de visão ----------------------------------------------------------------------
export const vm = computed(() => {
  const s = state
  const efetivo = temaEfetivo()
  const real = s.modelos.modo === 'real'
  const ld = lado()
  const pn = painelVals()
  const ativo = s.modelos.opcoes.find((m) => m.id === s.modelos.ativo)
  const alvo = s.modelos.opcoes.find((m) => m.id === s.trocarPara)
  const narrow = s.largura < 960

  const turnos = s.turnos.map((t) => {
    const rec = t.vagas.filter((v) => v.status !== 'descartado')
    const des = t.vagas.filter((v) => v.status === 'descartado')
    const corr = t.vagas.find((v) => v.correcao)
    const at = t.status === 'processando' ? atual(t) : { etapa: 0, nome: '' }
    const emStream = t.stream != null && t.resposta.length > 0
    const abrir = (v, de) => () => abrirPainel(t.id, v.id, de)
    const pronto = t.status === 'pronto' && !emStream
    const guardou = t.guardou || []
    return {
      id: t.id, pergunta: t.pergunta, erro: t.erro,
      respId: `rr-resp-${t.id}`, emStream, fimStream: pronto,
      temResposta: emStream || t.status === 'pronto',
      respostaVis: t.stream != null ? t.resposta.slice(0, t.stream) : t.resposta,
      propLs: !!t.traceUrl, lsId: `rr-ls-${t.id}`, lsUrl: t.traceUrl || '#', lsClasse: 'link-btn',
      rotuloSecao: `Resposta para: ${t.pergunta}`,
      ocupadoAttr: t.status === 'processando' || emStream ? 'true' : 'false',
      processando: t.status === 'processando' && !emStream, pronto: t.status === 'pronto' || emStream, comErro: t.status === 'erro',
      passo: `Etapa ${at.etapa + 1} de 8`, etapaNome: at.nome,
      tentarDesligado: s.ocupado ? 'true' : 'false', tentar: () => tentar(t.id),
      temCorrecao: !!corr && pronto, notaCorr: corr ? corr.correcao.nota : '', corrId: `rr-corr-${t.id}`,
      verCorrecao: corr ? abrir(corr, `rr-corr-${t.id}`) : () => {},
      temRec: rec.length > 0 && pronto, temDesc: des.length > 0 && pronto,
      rotuloRec: pl(rec.length, 'vaga', 'vagas'),
      rotuloDesc: `${pl(des.length, 'descartada', 'descartadas')}${t.desc ? ' · ocultar' : ' · ver motivo'}`,
      descAberta: t.desc ? 'true' : 'false', mostrarDesc: !!t.desc, descId: `rr-desc-${t.id}`,
      alternarDesc: () => { t.desc = !t.desc },
      descartadas: des.map((d) => { const id = `rr-pq-${t.id}-${d.id}`; return { ...d, corrigida: !!d.corrigida, pqId: id, abrirPq: abrir(d, id) } }),
      resumoLinha: t.status === 'pronto' ? resumoTurno(t) : '',
      temMemUsada: pronto && (t.memUsada || []).length > 0,
      memUsadaTxt: (t.memUsada || []).map((m) => `${m.texto} (${fmtSim(m.sim)})`).join(' · '),
      temGuardou: pronto && guardou.length > 0,
      guardouTxt: `Guardei: ${guardou.map((g) => `${g.texto} (${g.tipo === 'nesta conversa' ? 'nesta conversa' : `longo prazo, ${g.tipo}`})`).join(' · ')}`,
      verMemoria: () => abrirMem(guardou[0]?.tipo === 'nesta conversa' ? 'sessao' : 'longo'),
      verComoPressed: ld.mostrandoId === t.id ? 'true' : 'false', verComo: () => verComo(t.id),
      recomendadas: rec.map((v) => {
        const a = s.acoes[v.id] || {}
        const pqId = `rr-pq-${t.id}-${v.id}`
        return {
          ...v, tituloId: `rr-v-${t.id}-${v.id}`, pqId, abrirPq: abrir(v, pqId),
          abrirArtigo: (e) => { if (e?.target?.closest?.('a,button')) return; abrirPainel(t.id, v.id, pqId) },
          isRec: v.status === 'recomendado', isPen: v.status === 'pendente',
          temSalario: !!v.salary, semSalario: !v.salary,
          skillsLista: v.skills.map((k) => ({ nome: k })),
          salva: !!a.salva, aplicada: !!a.enviada,
          salvaAttr: a.salva ? 'true' : 'false', aplicadaAttr: a.enviada ? 'true' : 'false',
          salvarDesligado: a.salva || a.ocupado ? 'true' : 'false', aplicarDesligado: a.enviada || a.ocupado ? 'true' : 'false',
          salvarClasse: `btn btn-secondary${a.salva ? ' feito' : ''}`, aplicarClasse: `btn btn-secondary${a.enviada ? ' feito' : ''}`,
          salvarTexto: a.salva ? 'Salva' : 'Salvar', aplicarTexto: a.enviada ? 'Aplicada' : 'Já apliquei',
          salvar: () => registrar(v, 'salva'), aplicar: () => registrar(v, 'enviada'),
        }
      }),
    }
  })

  const comTrilho = s.conversas.length > 0 || s.memLonga.length > 0
  return {
    comTrilho,
    corpoClasse: `corpo${comTrilho ? ' com-trilho' : ''}${comTrilho && s.trilhoMin ? ' trilho-min' : ''}${s.ladoMin ? ' lado-min' : ''}`,
    trilhoClasse: `trilho${s.trilho ? ' aberta' : ''}${s.trilhoMin ? ' mini' : ''}`,
    recolherTrilho: () => { Object.assign(s, { trilhoMin: true, apagando: null }); focar('rr-expandir-trilho') },
    expandirTrilho: () => { s.trilhoMin = false; focar('rr-recolher-trilho') },
    recolherLado: () => { s.ladoMin = true; focar('rr-expandir-lado') },
    expandirLado: () => { s.ladoMin = false; focar('rr-recolher-lado') },
    ladoTrabalhando: s.ocupado,
    trilhoExpandido: s.trilho ? 'true' : 'false', trilhoVeu: s.trilho && narrow,
    abrirTrilho: () => { s.trilho = true; focar('rr-nova-conv') },
    fecharTrilho: () => { Object.assign(s, { trilho: false, memAberto: false }); focar('rr-abrir-trilho') },
    trocaDesligada: s.ocupado ? 'true' : 'false',
    novaConversa, conversas: conversasVals(), mem: memVals(),
    mostrarNovaSessao: !comTrilho && s.turnos.length > 0, novaRotulo: 'Nova conversa',
    temaAttr: s.tema, escuro: efetivo === 'escuro', claro: efetivo !== 'escuro',
    temaRotulo: efetivo === 'escuro' ? 'Mudar para tema claro' : 'Mudar para tema escuro',
    alternarTema: () => { s.tema = temaEfetivo() === 'escuro' ? 'claro' : 'escuro' },
    modoReal: real, simulado: !real && !s.carregando, modoTexto: real ? 'Modo real' : 'Modo demo',
    modeloRotulo: ativo?.rotulo || (s.apiFora ? 'Servidor fora do ar' : '—'),
    marcaCursor: `marca-cur${s.ocupado ? ' marca-cur-viva' : ''}`,
    carregando: s.carregando, pronto: !s.carregando,
    menuAberto: s.menu && !s.carregando, menuAttr: s.menu ? 'true' : 'false',
    alternarMenu: () => { if (s.menu) fecharMenu(true); else abrirMenu() },
    fecharMenu: () => fecharMenu(true),
    teclarBotaoModelo: (e) => { if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); abrirMenu() } },
    teclarMenu: (e) => {
      const ids = s.modelos.opcoes.map((m) => `rr-modelo-${m.id}`)
      const at = ids.indexOf(document.activeElement?.id)
      const vai = (i) => document.getElementById(ids[(i + ids.length) % ids.length])?.focus()
      if (e.key === 'ArrowDown') { e.preventDefault(); vai(at + 1) }
      else if (e.key === 'ArrowUp') { e.preventDefault(); vai(at - 1) }
      else if (e.key === 'Home') { e.preventDefault(); vai(0) }
      else if (e.key === 'End') { e.preventDefault(); vai(ids.length - 1) }
      else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); fecharMenu(true) }
      else if (e.key === 'Tab') fecharMenu(false)
    },
    modelos: s.modelos.opcoes.map((m) => {
      const on = m.id === s.modelos.ativo
      return { rotulo: m.rotulo, descricao: m.disponivel ? m.descricao : `${m.descricao} · indisponível`, domId: `rr-modelo-${m.id}`, ativo: on, ativoAttr: on ? 'true' : 'false',
        desligado: m.disponivel ? 'false' : 'true',
        escolher: () => {
          fecharMenu(on)
          if (on) return
          if (!m.disponivel) { toast(m.motivo || 'Este modelo não está configurado.'); return }
          if (s.ocupado) { toast('Aguarde o agente terminar para trocar de modelo.'); return }
          Object.assign(s, { trocarPara: m.id, confirmar: false })
          focar('rr-modelo-ok')
        } }
    }),
    trocandoModelo: !!alvo, modeloAlvo: alvo?.rotulo || '', trocandoAttr: s.trocando ? 'true' : 'false',
    confirmarModeloTexto: s.trocando ? 'Trocando…' : 'Trocar e começar de novo',
    cancelarModelo: () => { if (s.trocando) return; s.trocarPara = null; focar('rr-modelo-btn') },
    confirmarModelo,
    cv: cvVals(), leitorAberto: !!s.leitor && !s.carregando, lt: leitorVals(),
    confirmar: s.confirmar, confirmarExpandido: s.confirmar ? 'true' : 'false',
    pedirNova: novaConversa, cancelarNova: () => { s.confirmar = false; focar('rr-nova') }, novaSessao: novaConversa,
    semTurnos: s.turnos.length === 0,
    sugestoes: SUGESTOES.map((x) => ({ texto: x, desligada: s.ocupado ? 'true' : 'false', usar: () => enviar(x) })),
    turnos,
    rascunho: s.rascunho,
    aoDigitar: (e) => { const el = e.target; el.style.height = 'auto'; el.style.height = `${Math.min(el.scrollHeight, 200)}px`; s.rascunho = el.value },
    aoTeclar: (e) => { if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); enviar(e.target.value) } },
    enviarRascunho: () => enviar(s.rascunho),
    envioDesligado: s.ocupado || !String(s.rascunho).trim() ? 'true' : 'false',
    envioRotulo: s.ocupado ? 'Aguarde o agente terminar' : 'Enviar mensagem',
    dicaTexto: s.ocupado ? 'O agente está trabalhando. Você pode escrever a próxima mensagem.' : 'O agente só registra ações que você já fez. Nenhuma candidatura é enviada.',
    ladoStatus: ld.status, fluxoRotulo: ld.rotulo, nos: ld.nos, ed: ld.ed,
    congelado: ld.congelado, congeladoTexto: ld.congeladoTexto,
    voltarAtual: () => { s.foco = null; focar('rr-etapas-titulo') },
    semLinha: ld.tl.length === 0, temLinha: ld.tl.length > 0, tl: ld.tl, tlTotal: ld.tlTotal, tlClasse: 'tl',
    propTipos: true, propLs: true, aval: avalVals(),
    ladoClasse: `lado${s.gaveta ? ' aberta' : ''}${s.ladoMin ? ' mini' : ''}`,
    gavetaExpandida: s.gaveta ? 'true' : 'false', veuVisivel: s.gaveta && narrow,
    abrirGaveta: () => { s.gaveta = true; focar('rr-fechar-gaveta') },
    fecharGaveta: () => { s.gaveta = false; focar('rr-abrir-gaveta') },
    painelAberto: !!pn,
    pn: pn || { titulo: '', company: '', source: '', url: '#', reason: '', evidence: '', cite: '', isRec: false, isPen: false, isDes: false, temCorrecao: false, c: {}, conta: '', verifs: [], rodape: '', fechar: () => {}, teclar: () => {} },
    aoTeclarRaiz: (e) => {
      if (e.key !== 'Escape') return
      if (s.memAberto) fecharMem()
      else if (s.apagando) { const ap = s.apagando; s.apagando = null; focar(`rr-apagar-${ap}`) }
      else if (s.leitor) fecharLeitor()
      else if (s.menu) fecharMenu(true)
      else if (s.trocarPara && !s.trocando) { s.trocarPara = null; focar('rr-modelo-btn') }
      else if (s.cvConfirmar) { s.cvConfirmar = false; focar('rr-cv-restaurar') }
      else if (s.painel) fecharPainel()
      else if (s.gaveta) { s.gaveta = false; focar('rr-abrir-gaveta') }
      else if (s.trilho) { s.trilho = false; focar('rr-abrir-trilho') }
      else if (s.confirmar) { s.confirmar = false; focar('rr-nova') }
    },
    aviso: s.aviso,
    toasts: s.toasts.map((t) => ({ texto: t.texto, fechar: () => fecharToast(t.id) })),
  }
})
