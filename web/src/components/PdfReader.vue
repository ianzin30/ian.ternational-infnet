<script setup>
import { vm } from '../store.js'
import PdfPage from './PdfPage.vue'
</script>

<template>
  <template v-if="vm.leitorAberto">
    <div class="leitor-veu" aria-hidden="true" @click="vm.lt.fechar($event)"></div>
    <div class="leitor" id="rr-leitor" :style="`width: ${vm.lt.caixaW}px`" role="dialog" aria-modal="true" aria-labelledby="rr-leitor-titulo" @keydown="vm.lt.teclar($event)">
      <div class="leitor-barra" id="rr-leitor-barra">
        <h2 class="leitor-titulo" id="rr-leitor-titulo" :title="vm.cv.arquivo">{{ vm.cv.arquivo }}</h2>
        <div class="leitor-grupo" role="group" aria-label="Páginas">
          <button type="button" class="btn btn-ghost btn-icon" aria-label="Página anterior" :aria-disabled="vm.lt.antDesligado" @click="vm.lt.anterior($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"></path></svg></button>
          <span class="leitor-num" aria-live="polite"><span class="sr">Página </span>{{ vm.lt.pagina }} de {{ vm.lt.total }}</span>
          <button type="button" class="btn btn-ghost btn-icon" aria-label="Próxima página" :aria-disabled="vm.lt.proxDesligado" @click="vm.lt.proxima($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"></path></svg></button>
        </div>
        <div class="leitor-grupo" role="group" aria-label="Zoom">
          <button type="button" class="btn btn-ghost btn-icon" aria-label="Diminuir zoom" :aria-disabled="vm.lt.menosDesligado" @click="vm.lt.menos($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 12h12"></path></svg></button>
          <button type="button" class="btn btn-ghost leitor-zoom leitor-num" :aria-label="vm.lt.zoomRotulo" @click="vm.lt.zoomReset($event)">{{ vm.lt.zoomTexto }}</button>
          <button type="button" class="btn btn-ghost btn-icon" aria-label="Aumentar zoom" :aria-disabled="vm.lt.maisDesligado" @click="vm.lt.mais($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 6v12M6 12h12"></path></svg></button>
          <button type="button" class="btn btn-ghost btn-icon" aria-label="Página inteira" title="Página inteira (tecla 0)" :aria-pressed="vm.lt.ajustadoAttr" @click="vm.lt.ajustar($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9V5a1 1 0 0 1 1-1h4M15 4h4a1 1 0 0 1 1 1v4M20 15v4a1 1 0 0 1-1 1h-4M9 20H5a1 1 0 0 1-1-1v-4"></path></svg></button>
        </div>
        <a class="btn btn-ghost btn-icon" href="/curriculo" target="_blank" rel="noopener noreferrer" aria-label="Abrir em nova aba" title="Abrir em nova aba"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 5h5v5M19 5l-8 8M17 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h4"></path></svg></a>
        <button type="button" class="btn btn-ghost btn-icon" id="rr-leitor-fechar" aria-label="Fechar leitor" @click="vm.lt.fechar($event)"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"></path></svg></button>
      </div>
      <div class="leitor-palco" id="rr-leitor-palco" :style="`height: ${vm.lt.palcoH}px`">
        <div class="leitor-folha" id="rr-leitor-folha" :style="`width: ${vm.lt.w}px; height: ${vm.lt.h}px`">
          <PdfPage :pagina="vm.lt.pagina" :largura="vm.lt.w" :altura="vm.lt.h" :chave="vm.cv.chave" />
        </div>
      </div>
    </div>
  </template>
</template>
