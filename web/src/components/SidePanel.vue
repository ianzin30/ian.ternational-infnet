<script setup>
import { vm } from '../store.js'
import PdfPage from './PdfPage.vue'
</script>

<template>
  <template v-if="vm.veuVisivel">
    <div class="veu" aria-hidden="true" @click="vm.fecharGaveta($event)"></div>
  </template>
  <aside :class="vm.ladoClasse" id="rr-etapas" aria-label="Currículo e etapas do agente">
    <div class="lado-mini mini-col">
      <button type="button" class="btn btn-ghost btn-icon" id="rr-expandir-lado" aria-label="Mostrar currículo e etapas" title="Mostrar currículo e etapas" aria-expanded="false" aria-controls="rr-etapas" @click="vm.expandirLado($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2"></rect><path d="M14.5 4.5v15"></path><path d="M9.5 10l-2 2 2 2"></path></svg></button>
      <button type="button" class="mini-status" tabindex="-1" aria-hidden="true" @click="vm.expandirLado($event)"><template v-if="vm.ladoTrabalhando"><span class="pulso"></span></template><span>{{ vm.ladoStatus }}</span></button>
    </div>
    <div class="lado-in">
      <div class="lado-ctl">
        <button type="button" class="btn btn-ghost btn-recolher" id="rr-recolher-lado" aria-label="Recolher currículo e etapas" title="Recolher currículo e etapas" aria-expanded="true" aria-controls="rr-etapas" @click="vm.recolherLado($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2"></rect><path d="M14.5 4.5v15"></path><path d="M7.5 10l2 2-2 2"></path></svg></button>
      </div>
      <div class="lado-barra">
        <button type="button" class="btn btn-ghost btn-icon" id="rr-fechar-gaveta" aria-label="Fechar painel lateral" @click="vm.fecharGaveta($event)">
          <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"></path></svg>
        </button>
      </div>

      <section class="cv" aria-labelledby="rr-cv-titulo" :aria-busy="vm.cv.ocupadoAttr" @dragenter="vm.cv.arrastaSobre($event)" @dragover="vm.cv.arrastaSobre($event)" @dragleave="vm.cv.arrastaSai($event)" @drop="vm.cv.soltar($event)">
        <div class="cv-topo">
          <h2 id="rr-cv-titulo">Currículo</h2>
          <template v-if="vm.carregando"><span class="sk sk-selo" aria-hidden="true"></span></template>
          <template v-if="vm.pronto">
            <span :class="vm.cv.origemClasse"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="vm.cv.origemD"></path></svg><span class="sr">Origem: </span>{{ vm.cv.origemTexto }}</span>
          </template>
        </div>
        <template v-if="vm.carregando">
          <div class="cv-corpo" aria-hidden="true">
            <span class="sk sk-thumb"></span>
            <div class="cv-info">
              <span class="sk sk-linha sk-w80"></span>
              <span class="sk sk-linha sk-w50"></span>
              <div class="chips"><span class="sk sk-chip"></span><span class="sk sk-chip"></span><span class="sk sk-chip"></span><span class="sk sk-chip"></span></div>
            </div>
          </div>
          <p class="sr" role="status">Carregando o currículo</p>
        </template>
        <template v-if="vm.pronto">
          <div class="cv-corpo">
            <div class="cv-mini" id="rr-cv-mini">
              <div class="cv-mini-pg"><PdfPage v-if="vm.cv.temPdf" :pagina="1" :largura="595" :altura="842" :chave="vm.cv.chave" /></div>
              <span class="cv-mini-dica" aria-hidden="true">Abrir</span>
              <button type="button" class="cv-mini-btn" id="rr-cv-abrir" aria-haspopup="dialog" :aria-label="vm.cv.abrirRotulo" @click="vm.cv.abrir($event)"></button>
            </div>
            <div class="cv-info">
              <p class="cv-arquivo">{{ vm.cv.arquivo }}</p>
              <p class="cv-meta">{{ vm.cv.meta }}</p>
              <ul class="chips" aria-label="Skills extraídas do currículo">
                <template v-for="(k, k_i) in vm.cv.skills" :key="k_i"><li class="chip">{{ k.nome }}</li></template>
              </ul>
            </div>
          </div>
        </template>
        <template v-if="vm.cv.enviando">
          <ol class="tl-lista cv-etapas" :aria-label="vm.cv.etapasRotulo">
            <template v-for="(e, e_i) in vm.cv.etapas" :key="e_i">
              <li :class="e.classe">
                <div class="tl-cab tl-cab-fixo">
                  <span class="tl-marca" aria-hidden="true">
                    <template v-if="e.rodando"><span class="spin"></span></template>
                    <template v-if="e.parado"><svg class="ic" viewBox="0 0 24 24"><path :d="e.icD"></path></svg></template>
                  </span>
                  <span class="tl-nome">{{ e.nome }}</span>
                  <span class="tl-fim"><template v-if="e.temRubrica"><span class="rubrica"><span class="sr">Rubrica </span>{{ e.rubrica }}</span></template></span>
                  <span class="tl-meta"><span class="tl-st">{{ e.stTexto }}</span><span aria-hidden="true">·</span><span class="mono">{{ e.fonte }}</span><template v-if="e.temDur"><span aria-hidden="true">·</span><span class="mono">{{ e.dur }}</span></template></span>
                </div>
              </li>
            </template>
          </ol>
        </template>
        <template v-if="vm.cv.temErro">
          <div class="cv-erro" role="alert"><p><strong>{{ vm.cv.erroTitulo }}</strong> {{ vm.cv.erroTexto }}</p></div>
        </template>
        <template v-if="vm.cv.confirmar">
          <div class="cv-confirma" role="group" aria-labelledby="rr-cv-conf">
            <p id="rr-cv-conf">Voltar para o currículo anterior? O perfil é extraído de novo e as próximas buscas voltam a usá-lo.</p>
            <div class="cv-confirma-acoes">
              <button type="button" class="btn btn-ghost" @click="vm.cv.cancelarRestaurar($event)">Cancelar</button>
              <button type="button" class="btn btn-primary" id="rr-cv-restaurar-ok" @click="vm.cv.restaurar($event)">Restaurar</button>
            </div>
          </div>
        </template>
        <template v-if="vm.pronto">
          <div class="cv-acoes">
            <button type="button" class="btn btn-secondary" id="rr-cv-trocar" :aria-disabled="vm.cv.trocarDesligado" aria-describedby="rr-cv-dica" @click="vm.cv.trocar($event)">
              <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 16V5M7 10l5-5 5 5M5 19h14"></path></svg>
              Trocar currículo
            </button>
            <template v-if="vm.cv.podeRestaurar">
              <button type="button" class="link-btn" id="rr-cv-restaurar" :aria-expanded="vm.cv.confirmarAttr" @click="vm.cv.pedirRestaurar($event)">Restaurar meu currículo</button>
            </template>
          </div>
          <p class="cv-dica" id="rr-cv-dica">Só PDF, até 5 MB. Você também pode arrastar o arquivo para cá.</p>
        </template>
        <input type="file" class="sr" id="rr-cv-arquivo" accept=".pdf,application/pdf" tabindex="-1" aria-hidden="true" @change="vm.cv.aoEscolher($event)">
        <template v-if="vm.cv.arrastando">
          <div class="cv-solta" aria-hidden="true">Solte o PDF para trocar o currículo</div>
        </template>
      </section>

      <template v-if="vm.propLs">
        <section class="aval" aria-labelledby="rr-aval-tit">
          <div class="tl-topo"><h3 id="rr-aval-tit">Avaliação no LangSmith</h3><span class="tl-total">{{ vm.aval.situacao }}</span></div>
          <div class="aval-grade">
            <div><p class="aval-num">{{ vm.aval.correcao }}</p><p class="aval-rot">correção (LLM-juiz)</p></div>
            <div><p class="aval-num">{{ vm.aval.trajetoria }}</p><p class="aval-rot">trajetória de ferramentas</p></div>
            <div><p class="aval-num">{{ vm.aval.verificacao }}</p><p class="aval-rot">afirmações confirmadas (média)</p></div>
          </div>
          <p class="aval-rot">{{ vm.aval.nota }}</p>
          <a v-if="vm.aval.temUrl" class="link-btn" :href="vm.aval.url" target="_blank" rel="noopener noreferrer" style="align-self: flex-start">Abrir o experimento<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" style="width: 14px; height: 14px"><path d="M14 5h5v5M19 5l-8 8M17 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h4"></path></svg><span class="sr"> (abre em nova aba)</span></a>
        </section>
      </template>

      <div class="lado-topo">
        <h2 id="rr-etapas-titulo" tabindex="-1">Etapas do agente</h2>
      </div>
      <p class="lado-status" style="margin-top: -16px">{{ vm.ladoStatus }}</p>
      <template v-if="vm.congelado">
        <div class="congelado">
          <span>{{ vm.congeladoTexto }}</span>
          <button type="button" class="link-btn" @click="vm.voltarAtual($event)">Voltar ao último</button>
        </div>
      </template>

      <div class="fluxo" role="img" :aria-label="vm.fluxoRotulo">
        <div class="linha-nos"><span class="no n-inicio">Seu pedido</span></div>
        <svg class="liga" viewBox="0 0 360 24" aria-hidden="true"><path :class="vm.ed.e0" d="M180 0V24"></path></svg>
        <div class="linha-nos"><span :class="vm.nos.intencao.c"><template v-if="vm.nos.intencao.temIc"><svg :class="vm.nos.intencao.ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="vm.nos.intencao.d"></path></svg></template>Intenção</span></div>
        <svg class="liga" viewBox="0 0 360 24" aria-hidden="true"><path :class="vm.ed.e1" d="M180 0V24"></path></svg>
        <div class="linha-nos"><span :class="vm.nos.ferramentas.c"><template v-if="vm.nos.ferramentas.temIc"><svg :class="vm.nos.ferramentas.ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="vm.nos.ferramentas.d"></path></svg></template>Ferramentas</span></div>
        <svg class="liga" viewBox="0 0 360 28" style="height: 28px" aria-hidden="true"><path :class="vm.ed.e2a" d="M180 0V12H90V28"></path><path :class="vm.ed.e2b" d="M180 0V12H270V28"></path></svg>
        <div class="linha-nos" style="grid-template-columns: repeat(2, minmax(0, 1fr))">
          <span :class="vm.nos.remotive.c"><template v-if="vm.nos.remotive.temIc"><svg :class="vm.nos.remotive.ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="vm.nos.remotive.d"></path></svg></template>Remotive</span>
          <span :class="vm.nos.arbeitnow.c"><template v-if="vm.nos.arbeitnow.temIc"><svg :class="vm.nos.arbeitnow.ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="vm.nos.arbeitnow.d"></path></svg></template>Arbeitnow</span>
        </div>
        <p class="legenda-grupo">em paralelo</p>
        <svg class="liga" viewBox="0 0 360 36" style="height: 36px" aria-hidden="true">
          <path :class="vm.ed.eU" d="M90 0V12H270V0"></path>
          <path :class="vm.ed.e3" d="M180 12V20H60V36"></path>
          <path :class="vm.ed.e4" d="M180 12V36"></path>
          <path :class="vm.ed.e5" d="M180 20H300V36"></path>
        </svg>
        <div class="linha-nos" style="grid-template-columns: repeat(3, minmax(0, 1fr))">
          <span :class="vm.nos.cambio.c"><template v-if="vm.nos.cambio.temIc"><svg :class="vm.nos.cambio.ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="vm.nos.cambio.d"></path></svg></template>Câmbio</span>
          <span :class="vm.nos.curriculo.c"><template v-if="vm.nos.curriculo.temIc"><svg :class="vm.nos.curriculo.ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="vm.nos.curriculo.d"></path></svg></template>Currículo</span>
          <span :class="vm.nos.historico.c"><template v-if="vm.nos.historico.temIc"><svg :class="vm.nos.historico.ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="vm.nos.historico.d"></path></svg></template>Histórico</span>
        </div>
        <p class="legenda-grupo">conforme o pedido</p>
        <svg class="liga" viewBox="0 0 360 32" style="height: 32px" aria-hidden="true"><path :class="vm.ed.e6" d="M60 0V14H300V0M180 14V32"></path><path :class="vm.ed.e6" d="M180 0V14"></path></svg>
        <div class="linha-nos"><span :class="vm.nos.verificacao.c"><template v-if="vm.nos.verificacao.temIc"><svg :class="vm.nos.verificacao.ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="vm.nos.verificacao.d"></path></svg></template>Verificação</span></div>
        <svg class="liga" viewBox="0 0 360 24" aria-hidden="true"><path :class="vm.ed.e7" d="M180 0V24"></path></svg>
        <div class="linha-nos"><span :class="vm.nos.resposta.c"><template v-if="vm.nos.resposta.temIc"><svg :class="vm.nos.resposta.ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="vm.nos.resposta.d"></path></svg></template>Resposta</span></div>
      </div>

      <div class="legenda" aria-hidden="true">
        <span><span class="lg" style="border: 1px solid var(--color-accent); background: var(--color-surface)"></span>concluída</span>
        <span><span class="lg" style="background: var(--color-accent)"></span>agora</span>
        <span><span class="lg" style="border: 1px dashed var(--color-border-control)"></span>na fila</span>
        <span><span class="lg" style="border: 1px solid var(--color-warning); background: var(--color-warning-bg)"></span>do cache</span>
        <span><span class="lg" style="border: 1px solid var(--color-warning); background: var(--color-surface)"></span>incerta</span>
        <span><span class="lg" style="border: 1px solid var(--color-border-control); background: var(--color-surface)"></span>simulada</span>
        <span><span class="lg" style="border: 1px solid var(--color-danger); background: var(--color-danger-bg)"></span>erro</span>
        <span><span class="lg" style="border: 1px dashed var(--color-border-strong)"></span>não usada</span>
      </div>

      <template v-if="vm.semLinha">
        <p class="lado-lead">Envie um pedido. Cada etapa aparece aqui com fonte, duração e o item da rubrica que ela cobre.</p>
      </template>
      <template v-if="vm.temLinha">
        <section :class="vm.tlClasse" id="rr-tl" aria-labelledby="rr-tl-titulo">
          <div class="tl-topo">
            <h3 id="rr-tl-titulo">Linha do tempo</h3>
            <span class="tl-total">{{ vm.tlTotal }}</span>
          </div>
          <template v-if="vm.propTipos">
            <div class="tl-legenda-tipos">
              <span><span class="selo-tipo tp-hard">hardcoded</span> lógica fixa no código · <span class="selo-tipo tp-sem">semântica</span> o modelo interpreta</span>
              <span>API interna: <span class="mono">POST /candidaturas</span>, quando você salva ou marca “Já apliquei”.</span>
              <span>Cada linha chega por SSE a partir dos callbacks do AgentExecutor. <span class="rubrica"><span class="sr">Rubrica </span>2.6 Callbacks</span></span>
            </div>
          </template>
          <ol class="tl-lista">
            <template v-for="(it, it_i) in vm.tl" :key="it_i">
              <li :class="it.classe" :id="it.liId">
                <template v-if="it.grupo">
                  <div class="tl-grupo"><span class="tl-grupo-marca" aria-hidden="true"></span>Busca de vagas · Remotive e Arbeitnow em paralelo</div>
                </template>
                <template v-if="it.item">
                  <button type="button" class="tl-cab" :aria-expanded="it.abertoAttr" :aria-controls="it.detId" :aria-disabled="it.desligado" @click="it.alternar($event)">
                    <span class="tl-marca" aria-hidden="true">
                      <template v-if="it.rodando"><span class="spin"></span></template>
                      <template v-if="it.parado"><svg class="ic" viewBox="0 0 24 24"><path :d="it.icD"></path></svg></template>
                    </span>
                    <span class="tl-nome">{{ it.nome }}</span>
                    <span class="tl-fim">
                      <template v-if="it.expansivel"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"></path></svg></template>
                    </span>
                    <span class="tl-meta">
                      <span class="tl-st">{{ it.stTexto }}</span>
                      <span aria-hidden="true">·</span>
                      <span class="mono">{{ it.fonte }}</span>
                      <template v-if="it.temDur"><span aria-hidden="true">·</span><span class="mono">{{ it.dur }}</span></template>
                    </span>
                    <span class="tl-rubs">
                      <span class="rubrica"><span class="sr">Rubrica </span>{{ it.rubrica }}</span>
                      <template v-if="it.temRub2"><span class="rubrica rubrica-novo"><span class="sr">Rubrica </span>{{ it.rub2 }}</span></template>
                    </span>
                    <template v-if="it.temTipos">
                      <span class="tl-tipos"><span :class="it.tipoLogCls">{{ it.tipoLog }}</span><span class="selo-tipo tp-int">{{ it.tipoInt }}</span></span>
                    </template>
                  </button>
                  <template v-if="it.aberto">
                    <div class="tl-det" :id="it.detId">
                      <p>{{ it.resumo }}</p>
                      <template v-if="it.temLinhas">
                        <ul class="tl-linhas">
                          <template v-for="(l, l_i) in it.linhas" :key="l_i"><li>{{ l.t }}</li></template>
                        </ul>
                      </template>
                      <template v-if="it.temPtcf">
                        <div class="det-bloco">
                          <span class="det-sub">Prompt do agente · PTCF</span>
                          <pre class="cod"><code>{{ it.ptcf }}</code></pre>
                          <span class="det-sub">Exemplos few-shot dos casos ambíguos</span>
                          <ul class="fs"><template v-for="(f, f_i) in it.fewshot" :key="f_i"><li><span :class="f.cls">{{ f.rot }}</span><span>{{ f.t }}</span></li></template></ul>
                          <span class="det-sub">Raciocínio passo a passo (chain-of-thought) · instrução do prompt</span>
                          <pre class="cod"><code>{{ it.cot }}</code></pre>
                          <span class="det-sub">{{ it.executor }}</span>
                        </div>
                      </template>
                      <template v-if="it.temCodigo">
                        <span v-if="it.temCodigoRotulo" class="det-sub">{{ it.codigoRotulo }}</span>
                        <pre class="cod"><code>{{ it.codigo }}</code></pre>
                      </template>
                      <template v-if="it.temPtcf">
                        <div class="det-bloco">
                          <span class="det-sub">ReAct clássico com o mesmo pedido <span class="rubrica"><span class="sr">Rubrica </span>2.2 initialize_agent</span></span>
                          <button type="button" class="btn btn-secondary" style="align-self: flex-start" :aria-disabled="it.reactDesligado" @click="it.rodarReact($event)">
                            <span v-if="it.reactRodando" class="spin" aria-hidden="true"></span>{{ it.reactTexto }}
                          </button>
                          <template v-if="it.temReact">
                            <span class="det-sub">{{ it.reactModelo }}</span>
                            <pre class="cod"><code>{{ it.reactCiclo }}</code></pre>
                          </template>
                          <p v-if="it.temReactErro" class="det-nota" role="alert">{{ it.reactErro }}</p>
                        </div>
                      </template>
                      <template v-if="it.temRota">
                        <div class="det-bloco">
                          <span class="det-sub">RouterChain escolheu a rota</span>
                          <div class="rotas"><template v-for="(r, r_i) in it.rotas" :key="r_i"><span :class="r.cls"><template v-if="r.on"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg></template>{{ r.nome }}<span class="sr">{{ r.sr }}</span></span></template></div>
                          <p class="det-nota">Critério: {{ it.rotaMotivo }}</p>
                          <span class="det-sub">Composição desta rota</span>
                          <pre class="cod"><code>{{ it.rotaComp }}</code></pre>
                        </div>
                      </template>
                      <template v-if="it.temRec">
                        <div class="det-bloco">
                          <span class="det-sub">A primeira busca voltou fora do tema. Reescrevi a consulta e busquei de novo.</span>
                          <div class="antes-depois">
                            <div class="det-bloco"><span class="det-sub">Antes</span><pre class="cod"><code>{{ it.rec.antesQ }}</code></pre><ul class="docs"><template v-for="(d, d_i) in it.rec.antes" :key="d_i"><li><span class="sim sim-ruim">{{ d.s }}</span><span>{{ d.t }}</span></li></template></ul></div>
                            <div class="det-bloco"><span class="det-sub">Depois · {{ it.rec.tecnica }}</span><pre class="cod"><code>{{ it.rec.depoisQ }}</code></pre><ul class="docs"><template v-for="(d, d_i) in it.rec.depois" :key="d_i"><li><span class="sim sim-boa">{{ d.s }}</span><span>{{ d.t }}</span></li></template></ul></div>
                          </div>
                          <p class="det-nota"><strong>Diagnóstico:</strong> {{ it.rec.diag }}</p>
                        </div>
                      </template>
                      <template v-if="it.temMem">
                        <div class="det-bloco">
                          <span class="det-sub">Janela de contexto · {{ it.mem.usoTxt }}</span>
                          <div class="janela" role="img" :aria-label="it.mem.rotulo"><template v-for="(g, g_i) in it.mem.segs" :key="g_i"><span :class="g.cls" :style="`width: ${g.w}%`"></span></template></div>
                          <div class="janela-leg" aria-hidden="true"><span><i class="jn-sis"></i>sistema</span><span><i class="jn-res"></i>resumo</span><span><i class="jn-buf"></i>buffer</span><span><i class="jn-lon"></i>memória longa</span><span><i class="jn-fer"></i>ferramentas</span></div>
                          <span class="det-sub">Curto prazo</span>
                          <ul class="mem"><template v-for="(m, m_i) in it.mem.curto" :key="m_i"><li><span class="selo-tipo tp-sem">{{ m.tag }}</span><span>{{ m.t }}</span></li></template></ul>
                          <span class="det-sub">Longo prazo · FAISS de memória (tipos CoALA)</span>
                          <ul class="mem"><template v-for="(m, m_i) in it.mem.longo" :key="m_i"><li><span class="selo-tipo tp-hard">{{ m.tag }}</span><span>{{ m.t }}</span></li></template></ul>
                        </div>
                      </template>
                    </div>
                  </template>
                </template>
              </li>
            </template>
          </ol>
        </section>
      </template>
    </div>
  </aside>
</template>
