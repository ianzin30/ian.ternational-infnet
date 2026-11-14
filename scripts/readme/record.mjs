// Grava as cenas da interface usadas nos READMEs e converte em GIF (docs/readme/gif/*.gif).
// Roda contra o servidor em modo demo: vagas, câmbio e currículo fictícios, sem custo e sempre iguais.
//
//   MODO_DUMMY=true LANGSMITH_TRACING=false .venv/bin/uvicorn src.api:app --port 8010
//   PW=<pasta com node_modules/playwright> node scripts/readme/record.mjs [cena ...]
//
// O Playwright fica fora do repositório (npm i playwright em qualquer pasta, apontada por PW).
// CHROME aponta para um Chromium já instalado, se o do Playwright não estiver baixado.
// Precisa do ffmpeg no PATH. Cada cena abre um navegador limpo, então tem usuário e memória próprios.
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const { chromium } = createRequire(resolve(process.env.PW || '.', 'x.js'))('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8010';
const DOCS = join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'docs', 'readme');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const BUSCA = 'Mostre vagas remotas de Python que aceitam Brasil';

// Screenshots não mostram o ponteiro, então a página ganha um ponteiro desenhado que segue o mouse.
const PONTEIRO = () => {
  const liga = () => {
    const c = document.createElement('div');
    c.style.cssText = 'position:fixed;left:0;top:0;z-index:2147483647;pointer-events:none;width:22px;height:22px;transform:translate(-100px,-100px);transition:scale .12s';
    c.innerHTML = '<svg viewBox="0 0 22 22" width="22" height="22"><path d="M3 2l14 7.5-6 1.6-2.4 6.1z" fill="#fff" stroke="#0b0f12" stroke-width="1.4" stroke-linejoin="round"/></svg>';
    document.documentElement.appendChild(c);
    addEventListener('mousemove', e => { c.style.transform = `translate(${e.clientX - 3}px,${e.clientY - 2}px)`; }, true);
    addEventListener('mousedown', () => { c.style.scale = '.8'; }, true);
    addEventListener('mouseup', () => { c.style.scale = '1'; }, true);
  };
  document.readyState === 'loading' ? addEventListener('DOMContentLoaded', liga) : liga();
};

async function cena(nome, { w, h, lado = false, gifW = 1000, mp4 = false }, preparar, roteiro) {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, colorScheme: 'dark', deviceScaleFactor: 1 });
  await ctx.addInitScript(([lado]) => {
    localStorage.setItem('ian.tema', '"escuro"');
    localStorage.setItem('ian.trilhoMin', 'true');
    localStorage.setItem('ian.ladoMin', JSON.stringify(!lado));
  }, [lado]);
  await ctx.addInitScript(PONTEIRO);
  const page = await ctx.newPage();
  const dir = mkdtempSync(join(tmpdir(), 'ian-cena-'));
  const quadros = [];
  let gravando = false, laco = null;

  const k = {
    page,
    pausa: sleep,
    async perguntar(texto, { digitar = true } = {}) {
      const antes = await page.locator('.resumo-turno').count();
      const caixa = page.locator('#rr-mensagem');
      if (digitar) { await k.clicar(caixa, 150); await caixa.pressSequentially(texto, { delay: 34 }); await sleep(420); }
      else await caixa.fill(texto);
      await page.keyboard.press('Enter');
      await page.waitForFunction(n => document.querySelectorAll('.resumo-turno').length > n, antes, { timeout: 90000 });
    },
    async clicar(alvo, espera = 380) {
      const b = await alvo.boundingBox();
      await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 24 });
      await sleep(espera);
      await page.mouse.down(); await sleep(90); await page.mouse.up();
    },
    // Rola a conversa até deixar o alvo a `folga` px do topo.
    async rolar(alvo, folga = 16, suave = true) {
      await alvo.evaluate((el, [folga, suave]) => {
        const fio = document.getElementById('rr-fio');
        const top = fio.scrollTop + el.getBoundingClientRect().top - fio.getBoundingClientRect().top - folga;
        fio.scrollTo({ top, behavior: suave ? 'smooth' : 'auto' });
      }, [folga, suave]);
      await sleep(suave ? 900 : 150);
    },
    gravar() {
      gravando = true;
      laco = (async () => {
        while (gravando) {
          const t = Date.now(), f = join(dir, String(quadros.length).padStart(5, '0') + '.png');
          await page.screenshot({ path: f });
          quadros.push([f, t]);
          await sleep(Math.max(0, 66 - (Date.now() - t)));
        }
      })();
    },
  };

  await page.goto(BASE);
  await page.waitForSelector('#rr-mensagem');
  await sleep(900);
  await page.mouse.move(w * 0.62, h * 0.55);
  if (preparar) await preparar(k);
  k.gravar();
  await roteiro(k);
  gravando = false; await laco;
  await browser.close();

  const lista = quadros.map(([f, t], i) => `file '${f}'\nduration ${(((quadros[i + 1]?.[1] ?? t + 80) - t) / 1000).toFixed(3)}`).join('\n')
    + `\nfile '${quadros.at(-1)[0]}'\n`;
  writeFileSync(join(dir, 'lista.txt'), lista);
  const ff = (...a) => execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', join(dir, 'lista.txt'), ...a]);
  mkdirSync(join(DOCS, 'gif'), { recursive: true });
  const gif = join(DOCS, 'gif', nome + '.gif');
  ff('-vf', `fps=12,scale=${gifW}:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle`, gif);
  if (mp4) {
    mkdirSync(join(DOCS, 'social'), { recursive: true });
    ff('-vf', 'fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', join(DOCS, 'social', nome + '.mp4'));
  }
  rmSync(dir, { recursive: true, force: true });
  console.log(nome, quadros.length, 'quadros');
}

const buscaPronta = async k => { await k.perguntar(BUSCA, { digitar: false }); await sleep(600); };
const turno = k => k.page.locator('.turno').last();

const CENAS = {
  // Abertura: pergunta digitada, etapas do agente à direita, resposta e cartões de vaga.
  busca: () => cena('busca', { w: 1280, h: 760, lado: true, mp4: true }, k => k.page.evaluate(() => document.getElementById('rr-etapas-titulo').scrollIntoView({ block: 'start' })), async k => {
    await k.pausa(900);
    await k.perguntar(BUSCA);
    await k.pausa(1300);
    await k.rolar(turno(k), 12);
    await k.pausa(1700);
    await k.rolar(k.page.locator('.vaga').first(), 12);
    await k.pausa(2000);
    await k.rolar(k.page.locator('.vaga').nth(1), 12);
    await k.pausa(2400);
  }),
  // A verificação derruba a vaga "US only": nota de correção e o painel "Por que este resultado?".
  verificacao: () => cena('verificacao', { w: 1000, h: 700 }, async k => { await buscaPronta(k); await k.rolar(turno(k), 12, false); }, async k => {
    await k.pausa(1500);
    await k.clicar(k.page.locator('.nota-corr button'), 500);
    await k.pausa(4200);
    await k.clicar(k.page.locator('#rr-painel-fechar'), 400);
    await k.pausa(1200);
  }),
  cambio: () => cena('cambio', { w: 1000, h: 700 }, async k => { await buscaPronta(k); await k.rolar(k.page.locator('.vaga').nth(1), 12, false); }, async k => {
    await k.pausa(1200);
    await k.perguntar('Converta o salário da segunda');
    await k.pausa(3600);
  }),
  // "Já apliquei" vira "Aplicada"; depois o agente responde o que ainda falta.
  candidatura: () => cena('candidatura', { w: 1000, h: 700 }, async k => { await buscaPronta(k); await k.rolar(k.page.locator('.vaga').first(), 12, false); }, async k => {
    await k.pausa(1000);
    await k.clicar(k.page.locator('.vaga').first().locator('button', { hasText: 'Já apliquei' }), 500);
    await k.pausa(2600);
    await k.perguntar('Quais vagas eu ainda não apliquei?');
    await k.pausa(3600);
  }),
  // Uma preferência dita numa conversa muda o resultado da conversa seguinte.
  memoria: () => cena('memoria', { w: 1000, h: 700 }, null, async k => {
    await k.pausa(800);
    await k.perguntar('Lembre que prefiro evitar vagas com Docker');
    await k.pausa(2600);
    await k.clicar(k.page.locator('#rr-trilho button[aria-label="Nova conversa"]'), 450);
    await k.pausa(1100);
    await k.perguntar(BUSCA);
    await k.pausa(1200);
    await k.rolar(turno(k), 12);
    await k.pausa(2200);
    const desc = k.page.locator('.desc-botao').last();
    await k.rolar(desc, 120);
    await k.clicar(desc, 450);
    await k.pausa(700);
    await k.rolar(desc, 60);
    await k.pausa(3200);
  }),
};

// Prints estáticos da tela inteira (claro e escuro) e a capa do LinkedIn a partir do SVG.
CENAS.telas = async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
  mkdirSync(join(DOCS, 'img'), { recursive: true });
  for (const [tema, esquema] of [['escuro', 'dark'], ['claro', 'light']]) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: esquema, deviceScaleFactor: 2 });
    await ctx.addInitScript(([tema]) => { localStorage.setItem('ian.tema', JSON.stringify(tema)); localStorage.setItem('ian.trilhoMin', 'true'); }, [tema]);
    const page = await ctx.newPage();
    await page.goto(BASE);
    await page.fill('#rr-mensagem', BUSCA);
    await page.keyboard.press('Enter');
    await page.waitForSelector('.resumo-turno', { timeout: 90000 });
    await sleep(1200);
    await page.evaluate(() => {
      document.getElementById('rr-fio').scrollTo({ top: 0, behavior: 'instant' });
      const alvo = document.getElementById('rr-etapas-titulo');
      let cx = alvo.parentElement;
      while (cx && cx.scrollHeight <= cx.clientHeight + 4) cx = cx.parentElement;
      if (cx && cx !== document.documentElement && cx !== document.body) cx.scrollTop += alvo.getBoundingClientRect().top - cx.getBoundingClientRect().top - 16;
      scrollTo(0, 0);
    });
    await sleep(600);
    await page.screenshot({ path: join(DOCS, 'img', `app-${esquema}.png`) });
    await ctx.close();
  }
  const capa = await browser.newPage({ viewport: { width: 1200, height: 627 }, deviceScaleFactor: 2 });
  await capa.goto(pathToFileURL(join(DOCS, 'social', 'cover.svg')).href);
  await capa.screenshot({ path: join(DOCS, 'social', 'cover.png') });
  await browser.close();
  console.log('telas');
};

const pedidas = process.argv.slice(2);
for (const nome of pedidas.length ? pedidas : Object.keys(CENAS)) await CENAS[nome]();
