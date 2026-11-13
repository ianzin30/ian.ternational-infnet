<script setup>
import { vm } from '../store.js'
</script>

<template>
  <header class="hdr">
    <div class="hdr-in">
      <span class="marca"><span class="marca-dom" aria-hidden="true"><b>ian</b><span class="marca-ponto">.</span><span class="marca-tld">ternational</span><span :class="vm.marcaCursor"></span></span><span class="sr">Ianternational</span></span>
      <div class="modelo">
        <template v-if="vm.carregando">
          <span class="sk sk-modelo" aria-hidden="true"></span><span class="sr">Carregando modelos</span>
        </template>
        <template v-if="vm.pronto">
          <button type="button" class="btn btn-ghost modelo-btn" id="rr-modelo-btn" aria-haspopup="menu" :aria-expanded="vm.menuAttr" aria-controls="rr-modelo-menu" @click="vm.alternarMenu($event)" @keydown="vm.teclarBotaoModelo($event)">
            <span class="modo-ponto" aria-hidden="true"></span>
            <span>{{ vm.modeloRotulo }}<span class="modo-sub"> · {{ vm.modoTexto }}</span></span>
            <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"></path></svg>
            <span class="sr">. Trocar modelo</span>
          </button>
        </template>
        <template v-if="vm.menuAberto">
          <div class="menu-veu" aria-hidden="true" @click="vm.fecharMenu($event)"></div>
          <div class="menu" id="rr-modelo-menu" role="menu" aria-label="Modelo do agente" @keydown="vm.teclarMenu($event)">
            <template v-for="(m, m_i) in vm.modelos" :key="m_i">
              <button type="button" class="menu-item" role="menuitemradio" :id="m.domId" :aria-checked="m.ativoAttr" :aria-disabled="m.desligado" tabindex="-1" @click="m.escolher($event)">
                <span class="menu-marca" aria-hidden="true"><template v-if="m.ativo"><svg class="ic" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg></template></span>
                <span><span class="menu-rot">{{ m.rotulo }}</span><span class="menu-desc">{{ m.descricao }}</span></span>
              </button>
            </template>
          </div>
        </template>
      </div>
      <template v-if="vm.simulado">
        <span class="selo-sim" title="O agente está no modo demo: vagas, câmbio e currículo são fictícios e o modelo é roteirizado.">Dados simulados</span>
      </template>
      <div class="hdr-acoes">
        <template v-if="vm.comTrilho">
          <button type="button" class="btn btn-ghost so-trilho" id="rr-abrir-trilho" aria-controls="rr-trilho" :aria-expanded="vm.trilhoExpandido" @click="vm.abrirTrilho($event)">
            <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 6.5h14M5 12h14M5 17.5h9"></path></svg>
            <span>Conversas</span>
          </button>
        </template>
        <button type="button" class="btn btn-ghost so-gaveta" id="rr-abrir-gaveta" aria-controls="rr-etapas" :aria-expanded="vm.gavetaExpandida" @click="vm.abrirGaveta($event)">
          <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2"></rect><path d="M14.5 4.5v15"></path></svg>
          <span class="rotulo-etapas">Etapas</span><span class="sr">Abrir etapas do agente</span>
        </button>
        <button type="button" class="btn btn-ghost btn-icon" :aria-label="vm.temaRotulo" :title="vm.temaRotulo" @click="vm.alternarTema($event)">
          <template v-if="vm.escuro">
            <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"></path></svg>
          </template>
          <template v-if="vm.claro">
            <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"></path></svg>
          </template>
        </button>
        <template v-if="vm.mostrarNovaSessao">
          <button type="button" class="btn btn-secondary" id="rr-nova" :aria-expanded="vm.confirmarExpandido" @click="vm.pedirNova($event)">{{ vm.novaRotulo }}</button>
        </template>
      </div>
    </div>
    <template v-if="vm.confirmar">
      <div class="confirma" role="group" aria-labelledby="rr-confirma-texto">
        <p id="rr-confirma-texto">Começar do zero? A conversa e o contexto desta sessão serão apagados.</p>
        <button type="button" class="btn btn-ghost" @click="vm.cancelarNova($event)">Cancelar</button>
        <button type="button" class="btn btn-primary" id="rr-confirma-nova" @click="vm.novaSessao($event)">Começar nova sessão</button>
      </div>
    </template>
    <template v-if="vm.trocandoModelo">
      <div class="confirma" role="group" aria-labelledby="rr-modelo-conf">
        <p id="rr-modelo-conf">Trocar para {{ vm.modeloAlvo }}? Isso inicia uma nova conversa. A atual fica guardada no trilho, mas o agente recomeça sem o contexto dela.</p>
        <button type="button" class="btn btn-ghost" @click="vm.cancelarModelo($event)">Cancelar</button>
        <button type="button" class="btn btn-primary" id="rr-modelo-ok" :aria-disabled="vm.trocandoAttr" @click="vm.confirmarModelo($event)">{{ vm.confirmarModeloTexto }}</button>
      </div>
    </template>
  </header>
</template>
