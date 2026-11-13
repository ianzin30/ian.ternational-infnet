// Carrega o PDF do currículo uma vez por versão e reaproveita o documento entre miniatura e leitor.
import * as pdfjs from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl

const documentos = new Map()

export function documentoPdf(chave) {
  if (!documentos.has(chave)) {
    documentos.clear() // only the active résumé is kept
    documentos.set(chave, pdfjs.getDocument({ url: `/curriculo?v=${encodeURIComponent(chave)}` }).promise)
  }
  return documentos.get(chave)
}

export async function paginaPdf(chave, numero) {
  const doc = await documentoPdf(chave)
  return doc.getPage(Math.min(Math.max(1, numero), doc.numPages))
}

export async function medidasPdf(chave) {
  const doc = await documentoPdf(chave)
  const viewport = (await doc.getPage(1)).getViewport({ scale: 1 })
  return { paginas: doc.numPages, largura: viewport.width, altura: viewport.height }
}
