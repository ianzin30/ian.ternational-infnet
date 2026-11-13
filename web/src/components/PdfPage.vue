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
let pedido = 0

// Width changes arrive in bursts (fit, zoom); only the latest request may draw on the canvas.
async function desenhar() {
  const meu = ++pedido
  const canvas = tela.value
  if (!canvas) return
  try {
    const page = await paginaPdf(props.chave, props.pagina)
    if (meu !== pedido) return
    if (tarefa) {
      tarefa.cancel()
      try { await tarefa.promise } catch { /* cancelada */ }
      if (meu !== pedido) return
    }
    const base = page.getViewport({ scale: 1 })
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const viewport = page.getViewport({ scale: (props.largura / base.width) * dpr })
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
