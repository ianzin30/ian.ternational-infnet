<script setup>
import { vm } from '../store.js'
</script>

<template>
  <template v-if="vm.comTrilho">
  <template v-if="vm.trilhoVeu">
    <div class="veu" aria-hidden="true" @click="vm.fecharTrilho($event)"></div>
  </template>
  <nav :class="vm.trilhoClasse" id="rr-trilho" aria-label="Conversas e memória">
    <div class="tr-mini mini-col">
      <button type="button" class="btn btn-ghost btn-icon" id="rr-expandir-trilho" aria-label="Mostrar conversas" title="Mostrar conversas" aria-expanded="false" aria-controls="rr-trilho" @click="vm.expandirTrilho($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2"></rect><path d="M9.5 4.5v15"></path><path d="M14.5 10l2 2-2 2"></path></svg></button>
      <button type="button" class="btn btn-ghost btn-icon" aria-label="Nova conversa" title="Nova conversa" :aria-disabled="vm.trocaDesligada" @click="vm.novaConversa($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"></path></svg></button>
      <span class="mini-esp"></span>
      <button type="button" class="btn btn-ghost btn-icon mini-mem" id="rr-mem-mini" :aria-label="vm.mem.miniRotulo" title="Memória" :aria-expanded="vm.mem.abertoAttr" aria-controls="rr-mem-pn" @click="vm.mem.alternar($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5a3 3 0 0 0-5.6 1.5A3 3 0 0 0 4 10a3 3 0 0 0 1 5.2A3 3 0 0 0 9 19a3 3 0 0 0 3-1M12 5a3 3 0 0 1 5.6 1.5A3 3 0 0 1 20 10a3 3 0 0 1-1 5.2A3 3 0 0 1 15 19a3 3 0 0 1-3-1M12 5v13"></path></svg><template v-if="vm.mem.temNovas"><span class="mini-badge" aria-hidden="true"></span></template></button>
      <span class="mini-pct" aria-hidden="true">{{ vm.mem.pct }}</span>
    </div>
    <div class="tr-topo">
      <button type="button" class="btn btn-secondary tr-nova" id="rr-nova-conv" :aria-disabled="vm.trocaDesligada" @click="vm.novaConversa($event)">
        <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"></path></svg>
        Nova conversa
      </button>
      <button type="button" class="btn btn-ghost btn-recolher" id="rr-recolher-trilho" aria-label="Recolher conversas" title="Recolher conversas" aria-expanded="true" aria-controls="rr-trilho" @click="vm.recolherTrilho($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2"></rect><path d="M9.5 4.5v15"></path><path d="M16.5 10l-2 2 2 2"></path></svg></button>
    </div>
    <h2 class="tr-rot" id="rr-tr-rot">Conversas</h2>
    <ul class="tr-lista" aria-labelledby="rr-tr-rot">
      <template v-for="(c, c_i) in vm.conversas" :key="c_i">
        <li :class="c.classe">
          <template v-if="c.virtual">
            <span class="tr-conv" aria-current="page"><span class="tr-tit">Nova conversa</span><span class="tr-meta">ainda sem mensagens</span></span>
          </template>
          <template v-if="c.normal">
            <button type="button" class="tr-conv" :aria-current="c.atualAttr" :aria-disabled="c.desligada" @click="c.abrir($event)"><span class="tr-tit">{{ c.titulo }}</span><span class="tr-meta">{{ c.meta }}</span></button>
            <button type="button" class="btn btn-ghost btn-icon tr-apagar" :id="c.apagarId" :aria-label="c.apagarRotulo" title="Apagar conversa" :aria-disabled="c.desligada" @click="c.pedirApagar($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true" style="width: 15px; height: 15px"><path d="M5 7h14M10 7V5h4v2M7 7l1 12h8l1-12M10.5 11v5M13.5 11v5"></path></svg></button>
          </template>
          <template v-if="c.confirmando">
            <div class="tr-conf" role="group" :aria-labelledby="c.confId">
              <p :id="c.confId"><strong>Apagar “{{ c.titulo }}”?</strong> As mensagens e a memória desta conversa somem. A memória de longo prazo continua.</p>
              <div class="tr-conf-acoes">
                <button type="button" class="btn btn-ghost" @click="c.cancelar($event)">Cancelar</button>
                <button type="button" class="btn btn-perigo" :id="c.okId" @click="c.apagar($event)">Apagar</button>
              </div>
            </div>
          </template>
        </li>
      </template>
    </ul>
    <div class="tr-mem">
      <button type="button" :class="vm.mem.btnClasse" id="rr-mem-btn" :aria-expanded="vm.mem.abertoAttr" aria-controls="rr-mem-pn" @click="vm.mem.alternar($event)">
        <span class="tr-mem-l1"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5a3 3 0 0 0-5.6 1.5A3 3 0 0 0 4 10a3 3 0 0 0 1 5.2A3 3 0 0 0 9 19a3 3 0 0 0 3-1M12 5a3 3 0 0 1 5.6 1.5A3 3 0 0 1 20 10a3 3 0 0 1-1 5.2A3 3 0 0 1 15 19a3 3 0 0 1-3-1M12 5v13"></path></svg>Memória<span class="tr-mem-pct"><span class="sr">Janela de contexto em uso: </span>{{ vm.mem.pct }}</span><svg class="ic tr-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 15l6-6 6 6"></path></svg></span>
        <span class="janela" aria-hidden="true" style="height: 6px"><template v-for="(g, g_i) in vm.mem.segs" :key="g_i"><span :class="g.cls" :style="`width: ${g.w}%`"></span></template></span>
        <span class="tr-mem-l2">{{ vm.mem.resumo }}</span>
        <template v-if="vm.mem.temNovas"><span class="tr-mem-novo">{{ vm.mem.novasTxt }}</span></template>
      </button>
    </div>
  </nav>
  <template v-if="vm.mem.aberto">
    <div class="mem-veu" aria-hidden="true" @click="vm.mem.fechar($event)"></div>
    <section class="mem-pn" id="rr-mem-pn" role="region" aria-labelledby="rr-mem-tit">
      <div class="mem-pn-topo">
        <h2 id="rr-mem-tit">Memória do agente</h2>
        <span class="rubrica rubrica-novo"><span class="sr">Rubrica </span>3.1 · 3.2 · 3.4</span>
        <button type="button" class="btn btn-ghost btn-icon" aria-label="Fechar memória" @click="vm.mem.fechar($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true" style="width: 14px; height: 14px"><path d="M7 7l10 10M17 7L7 17"></path></svg></button>
      </div>
      <div class="mem-abas" role="tablist" aria-label="Tipo de memória">
        <template v-for="(a, a_i) in vm.mem.abas" :key="a_i">
          <button type="button" class="mem-aba" role="tab" :id="a.id" :aria-selected="a.sel" aria-controls="rr-mem-corpo" :tabindex="a.tab" @click="a.escolher($event)" @keydown="vm.mem.teclarAbas($event)">{{ a.rot }}<template v-if="a.temN"><span class="mono">{{ a.n }}</span></template></button>
        </template>
      </div>
      <div class="mem-corpo" id="rr-mem-corpo" role="tabpanel" :aria-labelledby="vm.mem.abaId">
        <p class="mem-lead">{{ vm.mem.lead }}</p>
        <template v-if="vm.mem.temItens">
          <ul class="mem-lista">
            <template v-for="(m, m_i) in vm.mem.itens" :key="m_i">
              <li :class="m.classe">
                <span class="mem-txt"><span :class="m.tipoClasse">{{ m.tipo }}</span><span>{{ m.texto }}</span></span>
                <span class="mem-orig">{{ m.origem }}</span>
                <button v-if="m.podeApagar" type="button" class="btn btn-ghost btn-icon" :aria-label="m.apagarRotulo" title="Esquecer" @click="m.apagar($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true" style="width: 14px; height: 14px"><path d="M7 7l10 10M17 7L7 17"></path></svg></button>
              </li>
            </template>
          </ul>
        </template>
        <template v-if="vm.mem.vazio"><p class="mem-vazio">{{ vm.mem.vazioTxt }}</p></template>
        <template v-if="vm.mem.abaJanela">
          <div class="janela" role="img" :aria-label="vm.mem.janelaRotulo"><template v-for="(g, g_i) in vm.mem.segs" :key="g_i"><span :class="g.cls" :style="`width: ${g.w}%`"></span></template></div>
          <div class="mem-tab">
            <template v-for="(l, l_i) in vm.mem.linhas" :key="l_i"><i :class="l.cls"></i><span>{{ l.nome }}</span><span class="n">{{ l.n }}</span><span class="p">{{ l.p }}</span></template>
          </div>
        </template>
      </div>
      <p class="mem-rodape">{{ vm.mem.rodape }}</p>
    </section>
  </template>
  </template>
</template>
