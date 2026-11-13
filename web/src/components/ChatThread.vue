<script setup>
import { vm } from '../store.js'
</script>

<template>
  <main class="conversa" aria-label="Conversa com o agente">
    <div class="fio" id="rr-fio">
      <div class="fio-in">
        <template v-if="vm.semTurnos">
          <section class="vazio" aria-labelledby="rr-vazio-titulo">
            <h1 id="rr-vazio-titulo">Vagas remotas no exterior que aceitam quem mora no Brasil</h1>
            <p class="vazio-lead">O agente busca na Remotive e na Arbeitnow, descarta o que não aceita candidatos daqui, converte o salário para reais, compara com seu currículo e confere cada afirmação no anúncio.</p>
            <div style="display: flex; flex-direction: column; gap: 12px">
              <h2 class="rotulo" id="rr-sug-titulo">Experimente</h2>
              <div class="sugestoes" role="group" aria-labelledby="rr-sug-titulo">
                <template v-for="(s, s_i) in vm.sugestoes" :key="s_i">
                  <button type="button" class="sug" :aria-disabled="s.desligada" @click="s.usar($event)">
                    <span>{{ s.texto }}</span>
                    <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"></path></svg>
                  </button>
                </template>
              </div>
            </div>
          </section>
        </template>

        <template v-for="(t, t_i) in vm.turnos" :key="t_i">
          <div class="turno">
            <div class="msg-eu"><span class="sr">Você: </span>{{ t.pergunta }}</div>
            <section class="msg-agente" :aria-label="t.rotuloSecao" :aria-busy="t.ocupadoAttr">
              <template v-if="t.processando">
                <div class="progresso">
                  <span class="pulso" aria-hidden="true"></span>
                  <span class="passo">{{ t.passo }}</span>
                  <span>{{ t.etapaNome }}…</span>
                </div>
              </template>
              <template v-if="t.comErro">
                <div class="erro" role="alert">
                  <p><strong>Não consegui concluir.</strong> {{ t.erro }}</p>
                  <button type="button" class="btn btn-secondary" :aria-disabled="t.tentarDesligado" @click="t.tentar($event)">Tentar de novo</button>
                </div>
              </template>
              <template v-if="t.pronto">
                <p class="resposta" :id="t.respId">{{ t.respostaVis }}<template v-if="t.emStream"><span class="stream-cur" aria-hidden="true"></span></template></p>
                <template v-if="t.temCorrecao">
                  <div class="nota-corr">
                    <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"></path></svg>
                    <p><strong>A verificação corrigiu 1 afirmação.</strong> {{ t.notaCorr }}</p>
                    <button type="button" class="btn btn-secondary" :id="t.corrId" aria-haspopup="dialog" @click="t.verCorrecao($event)">Ver correção</button>
                  </div>
                </template>
                <template v-if="t.temRec">
                  <div style="display: flex; flex-direction: column; gap: 12px">
                    <h2 class="rotulo">{{ t.rotuloRec }}</h2>
                    <div class="lista">
                      <template v-for="(v, v_i) in t.recomendadas" :key="v_i">
                        <article class="vaga" :aria-labelledby="v.tituloId" @click="v.abrirArtigo($event)">
                          <div class="vaga-topo">
                            <div style="min-width: 0">
                              <h3 class="vaga-titulo" :id="v.tituloId">{{ v.title }}</h3>
                              <p class="vaga-meta"><span>{{ v.company }}</span><span class="sep" aria-hidden="true">·</span><span>via {{ v.source }}</span></p>
                            </div>
                            <template v-if="v.isRec">
                              <span class="status st-rec"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg>Recomendada</span>
                            </template>
                            <template v-if="v.isPen">
                              <span class="status st-pen"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"></circle><path d="M12 7.5V12l3 2"></path></svg>Pendente</span>
                            </template>
                          </div>
                          <template v-if="v.temSalario">
                            <p class="salario">{{ v.salary }}</p>
                          </template>
                          <template v-if="v.semSalario">
                            <p class="salario-nd">Salário não informado no anúncio</p>
                          </template>
                          <p class="motivo">{{ v.reason }}</p>
                          <ul class="chips" aria-label="Skills pedidas">
                            <template v-for="(k, k_i) in v.skillsLista" :key="k_i">
                              <li class="chip">{{ k.nome }}</li>
                            </template>
                          </ul>
                          <div class="vaga-acoes">
                            <a class="vaga-link" :href="v.url" target="_blank" rel="noopener noreferrer">Ver anúncio<span class="sr"> de {{ v.title }} (abre em nova aba)</span><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 5h5v5M19 5l-8 8M17 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h4"></path></svg></a>
                            <button type="button" class="btn btn-ghost" :id="v.pqId" aria-haspopup="dialog" @click="v.abrirPq($event)">Por quê?<span class="sr"> Ver as verificações de {{ v.title }}</span></button>
                            <button type="button" :class="v.salvarClasse" :aria-pressed="v.salvaAttr" :aria-disabled="v.salvarDesligado" @click="v.salvar($event)">
                              <template v-if="v.salva"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg></template>
                              {{ v.salvarTexto }}<span class="sr"> {{ v.title }}</span>
                            </button>
                            <button type="button" :class="v.aplicarClasse" :aria-pressed="v.aplicadaAttr" :aria-disabled="v.aplicarDesligado" @click="v.aplicar($event)">
                              <template v-if="v.aplicada"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg></template>
                              {{ v.aplicarTexto }}<span class="sr"> para {{ v.title }}</span>
                            </button>
                          </div>
                        </article>
                      </template>
                    </div>
                  </div>
                </template>
                <template v-if="t.temDesc">
                  <div style="display: flex; flex-direction: column; gap: 8px">
                    <button type="button" class="desc-botao" :aria-expanded="t.descAberta" :aria-controls="t.descId" @click="t.alternarDesc($event)">
                      <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"></path></svg>
                      {{ t.rotuloDesc }}
                    </button>
                    <template v-if="t.mostrarDesc">
                      <ul class="desc-lista" :id="t.descId">
                        <template v-for="(d, d_i) in t.descartadas" :key="d_i">
                          <li class="desc-item">
                            <span><strong>{{ d.title }}</strong> · {{ d.company }}</span>
                            <span class="desc-selos">
                              <template v-if="d.corrigida">
                                <span class="status st-pen"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M4.5 12a7.5 7.5 0 1 0 2.2-5.3M4.5 4.5v3.5H8"></path></svg>Corrigida</span>
                              </template>
                              <span class="status st-des"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"></path></svg>Descartada</span>
                            </span>
                            <span class="desc-why">{{ d.reason }}</span>
                            <span class="desc-acoes">
                              <button type="button" class="link-btn" :id="d.pqId" aria-haspopup="dialog" @click="d.abrirPq($event)">Por quê?<span class="sr"> Ver as verificações de {{ d.title }}</span></button>
                              <a :href="d.url" target="_blank" rel="noopener noreferrer" style="font-size: var(--text-sm)">Ver anúncio<span class="sr"> de {{ d.title }} (abre em nova aba)</span></a>
                            </span>
                          </li>
                        </template>
                      </ul>
                    </template>
                  </div>
                </template>
                <template v-if="t.fimStream">
                <template v-if="t.temMemUsada">
                  <p class="mem-linha"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5a3 3 0 0 0-5.6 1.5A3 3 0 0 0 4 10a3 3 0 0 0 1 5.2A3 3 0 0 0 9 19a3 3 0 0 0 3-1M12 5a3 3 0 0 1 5.6 1.5A3 3 0 0 1 20 10a3 3 0 0 1-1 5.2A3 3 0 0 1 15 19a3 3 0 0 1-3-1M12 5v13"></path></svg><span>Memória usada: {{ t.memUsadaTxt }}</span></p>
                </template>
                <template v-if="t.temGuardou">
                  <p class="mem-linha mem-linha-nova"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg><span>{{ t.guardouTxt }}</span><button type="button" class="link-btn" aria-controls="rr-mem-pn" @click="t.verMemoria($event)">Ver memória</button></p>
                </template>
                <div class="resumo-turno">
                  <p class="resumo-linha"><span class="sr">Resumo do turno: </span>{{ t.resumoLinha }}</p>
                  <span class="resumo-acoes">
                    <button type="button" class="link-btn" :aria-pressed="t.verComoPressed" aria-controls="rr-etapas" @click="t.verComo($event)">
                      <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2"></rect><path d="M14.5 4.5v15"></path></svg>
                      Ver como cheguei aqui
                    </button>
                    <template v-if="t.propLs">
                      <a :class="t.lsClasse" :id="t.lsId" :href="t.lsUrl" target="_blank" rel="noopener noreferrer">Ver no LangSmith<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" style="width: 14px; height: 14px"><path d="M14 5h5v5M19 5l-8 8M17 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h4"></path></svg><span class="sr"> (abre em nova aba)</span></a>
                    </template>
                  </span>
                </div>
                </template>
              </template>
            </section>
          </div>
        </template>
      </div>
    </div>

    <div class="compositor">
      <div class="comp">
        <label for="rr-mensagem" class="sr">Mensagem para o agente</label>
        <div class="caixa">
          <textarea id="rr-mensagem" rows="1" :value="vm.rascunho" @input="vm.aoDigitar($event)" @keydown="vm.aoTeclar($event)" placeholder="Peça vagas, conversões ou comparações com seu currículo" aria-describedby="rr-dica"></textarea>
          <button type="button" class="btn btn-primary btn-icon" :aria-disabled="vm.envioDesligado" :aria-label="vm.envioRotulo" @click="vm.enviarRascunho($event)">
            <svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M6 11l6-6 6 6"></path></svg>
          </button>
        </div>
        <div class="dica" id="rr-dica">
          <span>{{ vm.dicaTexto }}</span>
          <span class="dica-teclas"><kbd>Enter</kbd> envia · <kbd>Shift</kbd>+<kbd>Enter</kbd> quebra linha</span>
        </div>
      </div>
    </div>
  </main>
</template>
