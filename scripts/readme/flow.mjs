// Gera os diagramas animados do fluxo usados nos READMEs (docs/readme/flow/*.svg).
// O GitHub não executa JS no README, então a animação vai dentro do próprio SVG (CSS + SMIL).
// Mesmo mapa do artefato interativo; os textos dos nós são simplificados para quem não é técnico.
// Uso: node scripts/readme/flow.mjs
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const OUT = join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'docs', 'readme', 'flow');

export const THEMES = {
  light: { bg: '#fbfcfc', surface: '#ffffff', text: '#0f171c', muted: '#5a666e', border: '#dce2e5', line: '#c3cbd0',
    accent: '#0b6a85', onAccent: '#ffffff', subtle: '#e8f3f6', ia: '#0b6a85', regra: '#848f97', dados: '#845400' },
  dark: { bg: '#0b0f12', surface: '#161c21', text: '#e6ebee', muted: '#98a5ae', border: '#2b353d', line: '#5f6c76',
    accent: '#5cc3dc', onAccent: '#04171d', subtle: '#0e2a33', ia: '#5cc3dc', regra: '#98a5ae', dados: '#f2c35a' },
};
export const SANS = 'ui-sans-serif,system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif';
export const MONO = 'ui-monospace,SFMono-Regular,SF Mono,Menlo,Consolas,monospace';

// x, y, w, h, tipo (ia | regra | dados)
const N = {
  pedido: [240, 16, 280, 52, 'regra'],
  memoria: [240, 92, 280, 52, 'dados'],
  intencao: [240, 168, 280, 52, 'ia'],
  agente: [240, 244, 280, 52, 'ia'],
  buscar: [22, 340, 132, 56, 'dados'],
  curriculo: [168, 340, 132, 56, 'dados'],
  cambio: [314, 340, 132, 56, 'dados'],
  sql: [460, 340, 132, 56, 'dados'],
  guardar: [606, 340, 132, 56, 'dados'],
  regras: [22, 436, 292, 52, 'regra'],
  verificacao: [280, 524, 200, 52, 'ia'],
  resposta: [240, 608, 280, 52, 'ia'],
  langsmith: [22, 568, 196, 92, 'dados'],
};

const E = {
  'pedido>memoria': 'M380 68V92', 'memoria>intencao': 'M380 144V168', 'intencao>agente': 'M380 220V244',
  'agente>buscar': 'M380 296C380 322 88 314 88 340', 'agente>curriculo': 'M380 296C380 322 234 316 234 340',
  'agente>cambio': 'M380 296V340', 'agente>sql': 'M380 296C380 322 526 316 526 340', 'agente>guardar': 'M380 296C380 322 672 314 672 340',
  'buscar>regras': 'M88 396C88 416 120 416 120 436', 'curriculo>regras': 'M234 396C234 416 216 416 216 436',
  'regras>verificacao': 'M168 488C168 512 340 500 340 524', 'cambio>verificacao': 'M380 396V524',
  'verificacao>resposta': 'M380 576V608', 'sql>resposta': 'M526 396C526 500 524 556 474 608',
  'guardar>resposta': 'M672 396C672 540 620 634 520 634',
};

const TXT = {
  en: {
    nodes: {
      pedido: ['You ask', 'the question leaves the screen'],
      memoria: ['Remember', 'this chat + earlier chats'],
      intencao: ['Understand the request', 'picks 1 of 6 routes'],
      agente: ['Choose the tools', 'one agent, five tools'],
      buscar: ['Search jobs', 'Remotive', 'Arbeitnow'],
      curriculo: ['Read the résumé', 'matching excerpts'],
      cambio: ['Convert salary', "today's rate"],
      sql: ['Check history', 'seen and applied'],
      guardar: ['Save a memory', 'for next time'],
      regras: ['Filter and score the fit', 'fixed rules, no AI'],
      verificacao: ['Fact-check', 'claims vs. the job ad'],
      resposta: ['Write the answer', 'word by word'],
      langsmith: ['LangSmith', 'records every step', 'trace + evaluation'],
    },
    back: 'comes back in the next chat',
    legend: ['AI decides', 'Fixed code', 'Data and outside sources'],
    asks: {
      search: 'Show me remote Python jobs that accept Brazil',
      salary: 'Convert the salary of the second one',
      resume: 'Which one fits my résumé best?',
      history: "Which jobs haven't I applied to yet?",
      memory: "Remember that I'd rather avoid PHP",
    },
  },
  pt: {
    nodes: {
      pedido: ['Você pergunta', 'a pergunta sai da tela'],
      memoria: ['Lembrar', 'esta conversa + as anteriores'],
      intencao: ['Entender o pedido', 'escolhe 1 de 6 caminhos'],
      agente: ['Escolher as ferramentas', 'um agente, cinco ferramentas'],
      buscar: ['Buscar vagas', 'Remotive', 'Arbeitnow'],
      curriculo: ['Ler o currículo', 'trechos parecidos'],
      cambio: ['Converter salário', 'cotação do dia'],
      sql: ['Ver o histórico', 'vistas e aplicadas'],
      guardar: ['Guardar memória', 'para a próxima'],
      regras: ['Filtrar e medir aderência', 'regras fixas, sem IA'],
      verificacao: ['Verificar', 'afirmação × anúncio'],
      resposta: ['Escrever a resposta', 'palavra por palavra'],
      langsmith: ['LangSmith', 'registra cada passo', 'trace + avaliação'],
    },
    back: 'volta na próxima conversa',
    legend: ['IA decide', 'Código fixo', 'Dados e fontes externas'],
    asks: {
      search: 'Mostre vagas remotas de Python que aceitam Brasil',
      salary: 'Converta o salário da segunda',
      resume: 'Qual combina mais com meu currículo?',
      history: 'Quais vagas eu ainda não apliquei?',
      memory: 'Lembre que prefiro evitar PHP',
    },
  },
};

const S = {
  search: ['pedido', 'memoria', 'intencao', 'agente', 'buscar', 'regras', 'verificacao', 'resposta'],
  salary: ['pedido', 'memoria', 'intencao', 'agente', 'cambio', 'verificacao', 'resposta'],
  resume: ['pedido', 'memoria', 'intencao', 'agente', 'curriculo', 'regras', 'verificacao', 'resposta'],
  history: ['pedido', 'memoria', 'intencao', 'agente', 'sql', 'resposta'],
  memory: ['pedido', 'memoria', 'intencao', 'agente', 'guardar', 'resposta'],
};

const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');

// Comprimento de um caminho feito só de M, V e C absolutos (é o que o mapa usa).
function pathLength(d) {
  const t = d.match(/[MVC]|-?\d+(?:\.\d+)?/g);
  let x = 0, y = 0, len = 0, i = 0;
  while (i < t.length) {
    const c = t[i++];
    if (c === 'M') { x = +t[i++]; y = +t[i++]; }
    else if (c === 'V') { const ny = +t[i++]; len += Math.abs(ny - y); y = ny; }
    else if (c === 'C') {
      const p = [x, y, +t[i++], +t[i++], +t[i++], +t[i++], +t[i++], +t[i++]];
      let px = x, py = y;
      for (let k = 1; k <= 60; k++) {
        const u = k / 60, v = 1 - u;
        const bx = v * v * v * p[0] + 3 * v * v * u * p[2] + 3 * v * u * u * p[4] + u * u * u * p[6];
        const by = v * v * v * p[1] + 3 * v * v * u * p[3] + 3 * v * u * u * p[5] + u * u * u * p[7];
        len += Math.hypot(bx - px, by - py); px = bx; py = by;
      }
      x = p[6]; y = p[7];
    }
  }
  return len;
}

const STEP = 1.15, DWELL = 0.5, HOLD = 2.6; // segundos: um trecho, a parada em cada nó, a pausa final

function build(id, lang, theme) {
  const c = THEMES[theme], tx = TXT[lang], path = S[id], on = new Set(path);
  const T = (path.length - 1) * STEP + HOLD;
  const pct = s => (Math.min(s, T) / T * 100).toFixed(2) + '%';
  const f = n => +n.toFixed(4);
  const END = '97%';
  let css = `
.edge{fill:none;stroke:${c.line};stroke-width:1.5;opacity:.28}
.edge.p{opacity:.5}
.ghost{fill:none;stroke:${c.line};stroke-width:1.5;stroke-dasharray:2 5;opacity:.5}
.run{fill:none;stroke:${c.accent};stroke-width:2;stroke-dasharray:3 7;stroke-linecap:round;opacity:0}
.box{fill:${c.surface};stroke:${c.border};stroke-width:1.5}
.t{font:600 14px ${SANS};fill:${c.text};text-anchor:middle}
.t.sm{font-size:13px}
.s{font:10.5px ${MONO};fill:${c.muted};text-anchor:middle}
.off{opacity:.3}
.note{font:9.5px ${MONO};fill:${c.muted}}
.lg{font:12px ${SANS};fill:${c.muted}}
.ask{font:500 14px ${SANS};fill:${c.onAccent};text-anchor:middle}
.lbl{font:10.5px ${MONO};fill:${c.muted};text-anchor:middle;letter-spacing:.06em}
@keyframes dash{to{stroke-dashoffset:-20}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.run{opacity:1}.lit{fill:${c.subtle};stroke:${c.accent}}}
`;
  let edges = '', runs = '', nodes = '';
  const pathEdges = path.slice(1).map((n, i) => path[i] + '>' + n);

  for (const k in E) edges += `<path class="edge${pathEdges.includes(k) ? ' p' : ''}" d="${E[k]}"/>`;
  edges += `<path class="ghost" d="M738 368H744Q752 368 752 360V126Q752 118 744 118H520"/><path class="ghost" d="M218 614H240"/>`;
  edges += `<text class="note" transform="translate(766 244) rotate(-90)" text-anchor="middle">${esc(tx.back)}</text>`;

  pathEdges.forEach((k, i) => {
    const start = i * STEP + DWELL;
    css += `@keyframes e${i}{0%,${pct(start - 0.01)}{opacity:0}${pct(start)},${END}{opacity:1}100%{opacity:0}}\n`;
    runs += `<path class="run" d="${E[k]}" style="animation:e${i} ${f(T)}s linear infinite,dash 1.2s linear infinite"/>`;
  });

  for (const k in N) {
    const [x, y, w, h, kind] = N[k], [t, s, s2] = tx.nodes[k];
    const cx = x + w / 2, mid = y + h / 2, i = path.indexOf(k);
    let anim = '';
    if (i >= 0) {
      const at = i * STEP;
      css += i === 0
        ? `@keyframes n0{0%,${END}{fill:${c.subtle};stroke:${c.accent}}100%{fill:${c.surface};stroke:${c.border}}}\n`
        : `@keyframes n${i}{0%,${pct(at - 0.01)}{fill:${c.surface};stroke:${c.border}}${pct(at)},${END}{fill:${c.subtle};stroke:${c.accent}}100%{fill:${c.surface};stroke:${c.border}}}\n`;
      anim = ` style="animation:n${i} ${f(T)}s linear infinite"`;
    }
    const cls = k === 'langsmith' || on.has(k) ? '' : ' class="off"';
    nodes += `<g${cls}><rect class="box${i >= 0 ? ' lit' : ''}" x="${x}" y="${y}" width="${w}" height="${h}" rx="8"${k === 'langsmith' ? ' stroke-dasharray="5 4"' : ''}${anim}/>`
      + `<circle cx="${x + w - (w < 140 ? 9 : 13)}" cy="${y + (w < 140 ? 9 : 13)}" r="${w < 140 ? 3 : 3.5}" fill="${c[kind]}"/>`
      + `<text class="t${w < 140 ? ' sm' : ''}" x="${cx}" y="${mid - (s2 ? 12 : 3)}">${esc(t)}</text>`
      + `<text class="s" x="${cx}" y="${mid + (s2 ? 6 : 15)}">${esc(s)}</text>`
      + (s2 ? `<text class="s" x="${cx}" y="${mid + 22}">${esc(s2)}</text>` : '') + `</g>`;
  }

  // O pulso percorre os trechos em sequência e para um instante em cada nó.
  const lens = pathEdges.map(k => pathLength(E[k])), L = lens.reduce((a, b) => a + b, 0);
  const kt = [0], kp = [0];
  let acc = 0;
  lens.forEach((len, i) => {
    kt.push(f((i * STEP + DWELL) / T)); kp.push(f(acc / L));
    acc += len;
    kt.push(f(((i + 1) * STEP) / T)); kp.push(f(Math.min(1, acc / L)));
  });
  kt.push(1); kp.push(1);
  const arrive = ((path.length - 1) * STEP) / T;
  const motion = `<animateMotion dur="${f(T)}s" repeatCount="indefinite" calcMode="linear" keyTimes="${kt.join(';')}" keyPoints="${kp.join(';')}" path="${pathEdges.map(k => E[k]).join('')}"/>`;
  const fade = (a, b) => `<animate attributeName="opacity" dur="${f(T)}s" repeatCount="indefinite" values="${a};${a};0;0;${a}" keyTimes="0;${f(arrive + 0.02)};${f(arrive + 0.05)};0.99;1"/>`;
  const pulse = `<circle r="11" fill="${c.accent}" opacity=".22">${motion}${fade(0.22)}</circle><circle r="5" fill="${c.accent}">${motion}${fade(1)}</circle>`;

  const ask = tx.asks[id], aw = Math.round(ask.length * 7.3 + 40);
  const head = `<text class="lbl" x="380" y="-60">${lang === 'en' ? 'THE QUESTION' : 'A PERGUNTA'}</text>`
    + `<rect x="${380 - aw / 2}" y="-50" width="${aw}" height="34" rx="17" fill="${c.accent}"/><text class="ask" x="380" y="-28">${esc(ask)}</text>`
    + `<path class="edge p" d="M380 -16V16"/>`;

  const lw = tx.legend.map(l => l.length * 6.6 + 34), total = lw.reduce((a, b) => a + b, 0);
  let lx = 380 - total / 2, legend = '';
  tx.legend.forEach((l, i) => {
    legend += `<circle cx="${f(lx + 4)}" cy="694" r="4" fill="${[c.ia, c.regra, c.dados][i]}"/><text class="lg" x="${f(lx + 14)}" y="698">${esc(l)}</text>`;
    lx += lw[i];
  });

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-14 -86 800 806" role="img" aria-label="${esc(ask)}">`
    + `<style>${css}</style><rect x="-13" y="-85" width="798" height="804" rx="14" fill="${c.bg}" stroke="${c.border}"/>`
    + head + edges + runs + nodes + pulse + legend + `</svg>\n`;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  mkdirSync(OUT, { recursive: true });
  let n = 0;
  for (const id in S) for (const lang of ['en', 'pt']) for (const theme of ['light', 'dark']) {
    writeFileSync(join(OUT, `${id}-${lang}-${theme}.svg`), build(id, lang, theme)); n++;
  }
  console.log(`${n} diagramas em ${OUT}`);
}
