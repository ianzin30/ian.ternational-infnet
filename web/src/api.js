// Cliente da API do FastAPI. Mesma origem em produção; no dev o Vite faz o proxy.

async function json(resp) {
  if (resp.ok) return resp.json()
  let detail = ''
  try { detail = (await resp.json()).detail } catch { /* corpo sem JSON */ }
  const erro = new Error(typeof detail === 'string' && detail ? detail : `O servidor respondeu ${resp.status}.`)
  erro.status = resp.status
  throw erro
}

export const get = (url) => fetch(url).then(json)
export const del = (url) => fetch(url, { method: 'DELETE' }).then(json)
export const post = (url, body) => fetch(url, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body ?? {}),
}).then(json)

// Lê um corpo text/event-stream e entrega um objeto por evento `data:`.
export async function* lerSse(resp) {
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let fim
    while ((fim = buffer.indexOf('\n\n')) >= 0) {
      const bloco = buffer.slice(0, fim)
      buffer = buffer.slice(fim + 2)
      for (const linha of bloco.split('\n')) {
        if (linha.startsWith('data:')) yield JSON.parse(linha.slice(5))
      }
    }
  }
}

export async function* chatStream(body, signal) {
  const resp = await fetch('/chat/stream', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal,
  })
  if (!resp.ok) await json(resp)
  yield* lerSse(resp)
}

export async function* enviarCurriculo(arquivo) {
  const form = new FormData()
  form.append('arquivo', arquivo)
  const resp = await fetch('/curriculo', { method: 'POST', body: form })
  if (!resp.ok) await json(resp)
  yield* lerSse(resp)
}
