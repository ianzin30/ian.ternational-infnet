<script setup>
import { vm } from './store.js'
import AppHeader from './components/AppHeader.vue'
import ConversationRail from './components/ConversationRail.vue'
import ChatThread from './components/ChatThread.vue'
import SidePanel from './components/SidePanel.vue'
import WhyPanel from './components/WhyPanel.vue'
import PdfReader from './components/PdfReader.vue'
</script>

<template>
  <div class="rr" :data-tema="vm.temaAttr" @keydown="vm.aoTeclarRaiz($event)">
    <a class="skip" href="#rr-mensagem">Pular para a mensagem</a>
    <AppHeader />
    <div :class="vm.corpoClasse">
      <ConversationRail />
      <ChatThread />
      <SidePanel />
    </div>
    <WhyPanel />
    <PdfReader />
    <div class="sr" aria-live="polite" role="status">{{ vm.aviso }}</div>
    <div class="toasts" role="status" aria-live="polite">
      <template v-for="(m, m_i) in vm.toasts" :key="m_i">
        <div class="toast">
          <span>{{ m.texto }}</span>
          <button type="button" class="btn btn-ghost btn-icon" aria-label="Fechar aviso" @click="m.fechar($event)">
            <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"></path></svg>
          </button>
        </div>
      </template>
    </div>
  </div>
</template>
