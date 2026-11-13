<script setup>
// Renderiza uma página do currículo ativo (GET /curriculo) com pdf.js.
import { onMounted, ref, watch } from 'vue'
import { paginaPdf } from '../pdf.js'

const props = defineProps({
  pagina: { type: Number, default: 1 },
  largura: { type: Number, required: true },
  altura: { type: Number, required: true },
  chave: { type: String, default: '' },
})
const tela = ref(null)
let tarefa = null

async function desenhar() {
  const canvas = tela.value
  if (!canvas) return
  try {
    const page = await paginaPdf(props.chave, props.pagina)
    const base = page.getViewport({ scale: 1 })
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const viewport = page.getViewport({ scale: (props.largura / base.width) * dpr })
    if (tarefa) tarefa.cancel()
    canvas.width = Math.round(viewport.width)
    canvas.height = Math.round(viewport.height)
    tarefa = page.render({ canvas, canvasContext: canvas.getContext('2d'), viewport })
    await tarefa.promise
  } catch (erro) {
    if (erro?.name !== 'RenderingCancelledException') console.warn('Não foi possível desenhar o PDF.', erro)
  }
}

onMounted(desenhar)
watch(() => [props.pagina, props.largura, props.chave], desenhar)
</script>

<template>
  <canvas ref="tela" :style="{ width: largura + 'px', height: altura + 'px', display: 'block' }" role="img" :aria-label="`Página ${pagina} do currículo`"></canvas>
</template>
