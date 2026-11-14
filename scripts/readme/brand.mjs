// Gera o wordmark animado, os cartões de link e a capa do LinkedIn usados nos READMEs (docs/readme/img e social).
// Uso: node scripts/readme/brand.mjs
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { MONO, SANS, THEMES } from './flow.mjs';

const DOCS = join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'docs', 'readme');
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');

// "ian" em negrito, ponto na cor de destaque, cursor piscando. textLength fixa a largura em qualquer fonte mono.
function marca(c, x, y, size) {
  const ch = size * 0.6, w = ch * 15;
  return `<text x="${x}" y="${y}" textLength="${w}" lengthAdjust="spacing" style="font:${size}px ${MONO}">`
    + `<tspan font-weight="700" fill="${c.text}">ian</tspan><tspan fill="${c.accent}">.</tspan><tspan fill="${c.muted}">ternational</tspan></text>`
    + `<rect x="${x + w + ch * 0.15}" y="${y - size * 0.82}" width="${ch * 0.62}" height="${size}" fill="${c.accent}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/></rect>`;
}

function wordmark(theme) {
  const c = THEMES[theme], size = 46, w = size * 0.6 * 15.8;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 84" role="img" aria-label="ian.ternational">${marca(c, (520 - w) / 2, 58, size)}</svg>\n`;
}

const ICONS = {
  video: c => `<path d="M33 30l16 10-16 10z" fill="${c.accent}"/>`,
  flow: c => `<g fill="none" stroke="${c.accent}" stroke-width="2"><rect x="34" y="27" width="12" height="8" rx="2"/><rect x="27" y="45" width="10" height="8" rx="2"/><rect x="43" y="45" width="10" height="8" rx="2"/><path d="M40 35v5M32 45v-5h16v5"/></g>`,
  report: c => `<g fill="none" stroke="${c.accent}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M32 27h11l6 6v20H32z"/><path d="M36 40h9M36 46h9"/></g>`,
};

const CARDS = {
  en: { video: ['Watch the demo', 'YouTube · in Portuguese'], flow: ['Explore the flow', 'interactive · in Portuguese'], report: ['Read the report', 'PDF · in Portuguese'] },
  pt: { video: ['Assista à demo', 'YouTube · vídeo da defesa'], flow: ['Explore o fluxo', 'artefato interativo'], report: ['Leia o relatório', 'PDF técnico'] },
};

function card(kind, lang, theme) {
  const c = THEMES[theme], [t, s] = CARDS[lang][kind];
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 80" role="img" aria-label="${esc(t)}">`
    + `<rect x="1" y="1" width="298" height="78" rx="12" fill="${c.surface}" stroke="${c.border}" stroke-width="1.5"/>`
    + `<circle cx="40" cy="40" r="20" fill="${c.subtle}"/>${ICONS[kind](c)}`
    + `<text x="74" y="36" style="font:600 16px ${SANS}" fill="${c.text}">${esc(t)}</text>`
    + `<text x="74" y="56" style="font:11px ${MONO}" fill="${c.muted}">${esc(s)}</text>`
    + `<path d="M272 34l6 6-6 6" fill="none" stroke="${c.muted}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>\n`;
}

// Capa 1200×627 para o LinkedIn (rasterizada em PNG pelo record.mjs, cena "telas").
function cover() {
  const c = THEMES.dark;
  const chip = (x, t) => { const w = t.length * 9.2 + 36; return [`<rect x="${x}" y="418" width="${w}" height="44" rx="22" fill="${c.surface}" stroke="${c.border}" stroke-width="1.5"/><text x="${x + w / 2}" y="446" text-anchor="middle" style="font:500 17px ${SANS}" fill="${c.text}">${esc(t)}</text>`, w]; };
  let x = 90, chips = '';
  for (const t of ['Accepts Brazil?', 'Salary in reais', 'Fits my résumé?', 'Fact-checked']) { const [s, w] = chip(x, t); chips += s; x += w + 14; }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 627" width="1200" height="627"><rect width="1200" height="627" fill="${c.bg}"/>`
    + `<circle cx="1040" cy="120" r="260" fill="${c.subtle}" opacity=".55"/>`
    + marca(c, 90, 250, 84)
    + `<text x="90" y="330" style="font:500 34px ${SANS}" fill="${c.text}">A remote-job agent for people who live in Brazil.</text>`
    + `<text x="90" y="376" style="font:22px ${SANS}" fill="${c.muted}">It searches, filters, converts the salary and checks every claim against the job ad.</text>`
    + chips
    + `<text x="90" y="560" style="font:16px ${MONO}" fill="${c.muted}">LangChain · FastAPI · Vue 3 · LangSmith</text></svg>\n`;
}

mkdirSync(join(DOCS, 'img'), { recursive: true });
mkdirSync(join(DOCS, 'social'), { recursive: true });
for (const theme of ['light', 'dark']) {
  writeFileSync(join(DOCS, 'img', `wordmark-${theme}.svg`), wordmark(theme));
  for (const lang of ['en', 'pt']) for (const kind in ICONS) writeFileSync(join(DOCS, 'img', `card-${kind}-${lang}-${theme}.svg`), card(kind, lang, theme));
}
writeFileSync(join(DOCS, 'social', 'cover.svg'), cover());
console.log('wordmark, cartões e capa em', DOCS);
