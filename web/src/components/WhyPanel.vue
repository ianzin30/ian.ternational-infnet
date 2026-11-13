<script setup>
import { vm } from '../store.js'
</script>

<template>
  <template v-if="vm.painelAberto">
    <div class="painel-veu" aria-hidden="true" @click="vm.pn.fechar($event)"></div>
    <div class="painel" id="rr-painel" role="dialog" aria-modal="true" aria-labelledby="rr-painel-titulo" aria-describedby="rr-painel-vaga" @keydown="vm.pn.teclar($event)">
      <div class="painel-topo">
        <div style="min-width: 0; display: flex; flex-direction: column; gap: 6px">
          <h2 id="rr-painel-titulo">Por que este resultado?</h2>
          <p class="vaga-meta" id="rr-painel-vaga" style="margin-top: 0"><strong style="color: var(--color-text); font-weight: 500">{{ vm.pn.titulo }}</strong><span class="sep" aria-hidden="true">·</span><span>{{ vm.pn.company }}</span><span class="sep" aria-hidden="true">·</span><span>via {{ vm.pn.source }}</span></p>
        </div>
        <button type="button" class="btn btn-ghost btn-icon" id="rr-painel-fechar" aria-label="Fechar painel" @click="vm.pn.fechar($event)">
          <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"></path></svg>
        </button>
      </div>
      <div class="painel-corpo">
        <template v-if="vm.pn.temCorrecao">
          <section class="corr" aria-labelledby="rr-corr-titulo">
            <div class="painel-cab">
              <h3 id="rr-corr-titulo">Correção aplicada pela verificação</h3>
              <span class="rubrica"><span class="sr">Rubrica </span>5.1 NLI + correção</span>
            </div>
            <div class="corr-grade">
              <div class="corr-col corr-p">
                <span class="corr-rot">Proposta do agente</span>
                <p class="corr-txt"><span class="sr">Descartada: </span>{{ vm.pn.c.proposta }}</p>
              </div>
              <span class="corr-sep" aria-hidden="true">×</span>
              <div class="corr-col corr-a">
                <span class="corr-rot"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"></path></svg>O anúncio diz</span>
                <p class="corr-txt" lang="en">“{{ vm.pn.c.anuncio }}”</p>
              </div>
              <span class="corr-sep" aria-hidden="true">→</span>
              <div class="corr-col corr-c">
                <span class="corr-rot"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg>Correção aplicada</span>
                <p class="corr-txt">{{ vm.pn.c.correcao }}</p>
              </div>
            </div>
            <p class="cite">{{ vm.pn.c.placar }}</p>
          </section>
        </template>

        <section class="painel-sec" aria-labelledby="rr-dec-titulo">
          <h3 id="rr-dec-titulo">Decisão</h3>
          <div class="decisao">
            <template v-if="vm.pn.isRec"><span class="status st-rec"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg>Recomendada</span></template>
            <template v-if="vm.pn.isPen"><span class="status st-pen"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"></circle><path d="M12 7.5V12l3 2"></path></svg>Pendente</span></template>
            <template v-if="vm.pn.isDes"><span class="status st-des"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"></path></svg>Descartada</span></template>
            <p>{{ vm.pn.reason }}</p>
          </div>
        </section>

        <section class="painel-sec" aria-labelledby="rr-trecho-titulo">
          <h3 id="rr-trecho-titulo">Trecho do anúncio</h3>
          <blockquote class="trecho" lang="en">{{ vm.pn.evidence }}</blockquote>
          <p class="cite">{{ vm.pn.cite }}</p>
        </section>

        <section class="painel-sec" aria-labelledby="rr-ver-titulo">
          <div class="painel-cab">
            <h3 id="rr-ver-titulo">Verificações</h3>
            <span class="painel-conta">{{ vm.pn.conta }}</span>
          </div>
          <ul class="verifs">
            <template v-for="(c, c_i) in vm.pn.verifs" :key="c_i">
              <li class="verif">
                <span class="verif-claim">{{ c.claim }}</span>
                <span :class="c.cls"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path :d="c.d"></path></svg>{{ c.texto }}</span>
                <span class="verif-why">{{ c.reason }}</span>
              </li>
            </template>
          </ul>
          <p class="cite">{{ vm.pn.rodape }}</p>
        </section>
      </div>
      <div class="painel-pe">
        <a class="vaga-link" :href="vm.pn.url" target="_blank" rel="noopener noreferrer" style="margin-right: 0">Ver anúncio<span class="sr"> (abre em nova aba)</span><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 5h5v5M19 5l-8 8M17 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h4"></path></svg></a>
        <button type="button" class="btn btn-secondary" @click="vm.pn.fechar($event)">Fechar</button>
      </div>
    </div>
  </template>
</template>
