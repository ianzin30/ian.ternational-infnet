from textwrap import dedent

import nbformat as nb

from scripts.notebook_overview import generate_overview
from src.config import ROOT

DEST = ROOT / "notebooks"
BOOT = """
import os, sys
root = Path.cwd() if (Path.cwd() / 'src').is_dir() else Path.cwd().parent
sys.path.insert(0, str(root))
from pprint import pprint
from src.config import DATA
"""


def md(value, key=None):
    cell = nb.v4.new_markdown_cell(dedent(value).strip())
    if key:
        cell["id"] = key
    return cell


def code(key, value):
    cell = nb.v4.new_code_cell(dedent(value).strip())
    cell["id"] = key
    return cell


def create(name, title, cells, evidence, *, bootstrap=True):
    links = "\n".join(f"- **{criterion}** → [{cell}](#{cell}): {description}"
                      for criterion, cell, description in evidence)
    preamble = [md(f"# {title}")] + ([code("ambiente", BOOT)] if bootstrap else [])
    appendix = [md("## Evidência\n\n" + links)] if evidence else []
    notebook = nb.v4.new_notebook(cells=[*preamble, *cells, *appendix],
                                  metadata={"kernelspec": {"name": "python3", "language": "python",
                                                           "display_name": "Python 3"}})
    nb.write(notebook, DEST / f"{name}.ipynb")


def generate():
    generate_overview()
    create("01_indexacao", "01 · Preparar a base documental", [
        md('## 1. Configuração do projeto', 'e1134ce5'),
        code('642205e3', '# Localiza a raiz para permitir os imports do projeto.\nimport sys\nfrom pathlib import Path\nfrom pprint import pprint\n\nroot = Path.cwd() if (Path.cwd() / "src").is_dir() else Path.cwd().parent\nsys.path.insert(0, str(root))\nfrom src.config import DATA\n\nprint("Raiz do projeto:", root)\nprint("Pasta de dados:", DATA)'),
        md('## 2. Arquivos do currículo', '190762a5'),
        code('3aac7d14', '# O PDF é a fonte da indexação; o TXT é auxiliar nesta demonstração.\ncurriculo_txt = DATA / "curriculo.txt"\ncurriculo_pdf = DATA / "curriculo.pdf"\n\nprint("Arquivo realmente usado na indexação:", curriculo_pdf)\nprint("Existe?", curriculo_pdf.is_file())\nprint("\\nArquivo auxiliar usado para gerar o PDF:", curriculo_txt)\nprint("Existe?", curriculo_txt.is_file())'),
        md('## 3. Criação do PDF', 'ead6a86b'),
        code('b4594621', '# Gera data/curriculo.pdf a partir do TXT auxiliar.\nfrom scripts.setup_assets import resume_pdf\n\nresume_pdf()\n\nprint("PDF criado em:", curriculo_pdf)\nprint("Existe?", curriculo_pdf.is_file())'),
        md('## 4. Carregamento das vagas', 'd056a8be'),
        code('826d7c58', '# Lê as vagas fictícias de data/vagas_dummy.json.\nfrom src.repository import fixtures\n\nvagas_arquivo = DATA / "vagas_dummy.json"\nvagas = fixtures(DATA)\n\nprint("Arquivo de vagas:", vagas_arquivo)\nprint("Quantidade de vagas carregadas:", len(vagas))\nprint("\\nPrimeira vaga:")\npprint(vagas[0].model_dump())'),
        md('## 5. Criação do índice', '574af887'),
        code('6fed45f6', '# Lê o PDF, cria os vetores e salva o índice FAISS.\nfrom src.rag import build_index, INDEX\n\nquantidade_trechos = build_index(vagas, resume=curriculo_pdf)\n\nprint("Currículo usado na indexação:", curriculo_pdf)\nprint("Índice salvo em:", INDEX)\nprint("Quantidade de trechos indexados:", quantidade_trechos)'),
        md('## 6. Arquivos gerados', '4e68d321'),
        code('aeb55321', '# Confere os arquivos do índice local.\nprint("Arquivos gerados no índice:")\nfor arquivo in sorted(INDEX.iterdir()):\n    print("-", arquivo.name)'),
        md('## 7. Teste de recuperação', '7320e221'),
        code('733893eb', '# Busca somente documentos marcados como currículo.\nfrom src.rag import load_index, retrieve\n\nload_index.cache_clear()\nresultado = retrieve("currículo de Python", k=1, kind="curriculo")\npprint(resultado)'),
        md('## 8. Modelo NLI', '8ce1d25b'),
        code('2434f782', '# Carrega o modelo usado para verificar afirmações.\nfrom src.verificador import nli_model\n\nverificador = nli_model()\nprint("Rótulos do NLI:", verificador.model.config.id2label)'),
        md('## Onde este notebook atende à rubrica\n\n**4.4 — Preparar o índice FAISS.** Nas seções 5 a 7, confira a quantidade de trechos, os arquivos do índice e a recuperação de um trecho do currículo. O [notebook 05](05_ferramentas_rag.ipynb) usa esse índice já construído.', 'c131764f'),
    ], [], bootstrap=False)

    create("02_chain_mvp", "02 · Extrair um perfil estruturado", [
        md("""
        <a id="arquitetura"></a>

        **Anatomia.** O modelo é escolhido via `OPENAI_MODEL`. O modo sem chave usa um adaptador
        determinístico. A mensagem de sistema limita a extração a fatos do currículo. As ferramentas
        previstas são busca, câmbio, SQL e FAISS; o currículo e os anúncios formam a base de conhecimento.

        **Padrão e maturidade.** A chain MVP é fixa. O integrador será híbrido: reage a pedidos
        de busca e aplica uma sequência deliberada para comparar vagas ou preparar uma candidatura.

        **Planejamento.** Encontrar vagas → extrair perfil → interpretar restrições → consultar fontes
        → filtrar → ranquear → verificar. Memória curta mantém turnos recentes e a ordem da lista.
        A memória longa representa perfil, preferências e descartes recuperáveis por similaridade.
        """, "arquitetura"),
        code("lcel", """
            from src.config import live_model
            from src.prompts import perfil_chain, resumo_chain
            from src.demo import perfil_imperativo
            cv = (DATA / 'curriculo.txt').read_text()
            llm = live_model() if os.getenv('NOTEBOOK_OPENAI') == '1' else None
            chain = perfil_chain(llm)
            print('invoke:'); pprint(chain.invoke({'curriculo': cv}).model_dump())
            print('batch:')
            for result in chain.batch([{'curriculo': text} for text in (
                cv, 'Skills: Java, Docker\\nInglês: B1', 'Skills: TypeScript, React')]):
                pprint(result.model_dump())
            print('stream:', end=' ')
            for fragment in resumo_chain(llm).stream({'vaga': 'Worldwide remote. Python and Docker. Salary not disclosed.'}):
                print(fragment, end='')
            print()
            print('@chain:', perfil_imperativo.invoke(cv).model_dump())
        """),
        md("""O encadeamento LCEL isola template, modelo, parser e validação. Isso permite
        trocar um componente sem duplicar a sequência e adicionar retry no ponto da falha.
        A versão imperativa usa uma condição de entrada vazia e reaproveita a composição."""),
    ], [
        ("1.1", "arquitetura", "Anatomia, padrão híbrido e maturidade."),
        ("1.2", "arquitetura", "Decomposição e memória curta/longa."),
        ("1.3", "lcel", "Templates de chat e texto."),
        ("1.4", "lcel", "Parser JSON seguido de validação Pydantic."),
        ("1.5", "lcel", "Invoke, batch, stream e @chain."),
        ("1.6", "lcel", "Composição LCEL e justificativa.")
    ])

    create("03_agente_react", "03 · ReAct, composição e ferramentas", [
        md("""
        <a id="orquestradores"></a>

        | Orquestrador | Autonomia | Abstração | Modularidade |
        |---|---|---|---|
        | LangChain | Seleção de ferramenta dentro do executor | Runnables, ferramentas e agentes | Componentes intercambiáveis |
        | LangGraph | Controle por nós e arestas | Grafo de estado | Subgrafos e persistência |
        | CrewAI | Cooperação orientada por papéis | Agentes, tarefas e crews | Divisão por agente e fluxo |
        | AutoGen | Conversas coordenadas | Agentes e equipes | Participantes e estratégias de conversa |

        LangChain reaproveita as chains LCEL e demonstra as interfaces exigidas com menos
        infraestrutura. `initialize_agent` é legado e fica neste exercício didático.
        """, "orquestradores"),
        code("react", """
            from src.demo import react_demo, composicao, reliability_demo, provider_function_call
            live = os.getenv('NOTEBOOK_LIVE_APIS') == '1'
            pprint(react_demo(live=live))
        """),
        code("composicao", "pprint(composicao())"),
        code("http", "pprint(provider_function_call(live=live))"),
        code("ptcf", "from src.prompts import AGENT_SYSTEM\nprint(AGENT_SYSTEM)"),
        md("""Os exemplos PTCF mostram conclusões verificáveis e um resumo da decisão. A
        demonstração sem chave roteiriza a etapa didática Thought/Action/Observation; no
        modo com chave, o notebook exibe apenas ação, observação e evidência pública.
        O parser tenta reparar uma saída quebrada. O buffer limita o custo de descrições
        longas. FAISS recupera texto fonte. Callbacks expõem duração e tokens quando o
        provedor disponibiliza contagem."""),
        code("confiabilidade", "pprint(reliability_demo())"),
    ], [
        ("2.1", "orquestradores", "Comparação pelos três critérios."),
        ("2.2", "react", "ReAct clássico com ferramentas, memória e trajetória."),
        ("2.3", "composicao", "Sequencial, paralela e RouterChain."),
        ("2.4", "http", "Function calling. O campo http_real informa se houve HTTP real."),
        ("2.5", "ptcf", "PTCF, exemplos ambíguos e etapas públicas de decisão."),
        ("2.6", "confiabilidade", "Parser reparado, FAISS, memória e callbacks no ReAct.")
    ])

    create("04_memoria", "04 · Memória em uma conversa", [
        md("""
        <a id="coala"></a>

        **CoALA.** Perfil e skills são memória semântica; vagas vistas e descartadas são
        episódios; filtros que o usuário quer manter são regras procedurais. Uma janela
        retém os últimos turnos; o histórico anterior é resumido. O índice vetorial de
        sessão fica separado dos documentos para preservar a origem de cada dado.

        | Ferramenta | Arquitetura | Uso típico |
        |---|---|---|
        | LangMem | Componentes de extração e manutenção sobre armazenamento do agente | Agentes integrados ao ecossistema LangGraph |
        | Mem0 | Camada de extração e recuperação de memórias por escopo | Aplicações que precisam reutilizar preferências entre sessões |
        | Letta | Estado e blocos de memória administrados pelo agente | Agentes de longa duração |

        O FAISS local reduz dependências para a avaliação. O protótipo não persiste o
        histórico conversacional entre reinícios do servidor.
        """, "coala"),
        code("buffer", "from src.demo import buffer_demo, QUESTIONS\npprint(buffer_demo())"),
        code("turnos", """
            from src.agente import Radar
            from src.rules import interpretar
            from tempfile import TemporaryDirectory
            with TemporaryDirectory() as temp:
                radar = Radar(db_path=Path(temp) / 'vagas.db')
                for question in QUESTIONS:
                    response = radar.chat('sessao-1', question)
                    print(question, '→', response.answer)
                pprint(interpretar(QUESTIONS[2]).model_dump(exclude_none=True))
                print('Sessão isolada:', radar.chat('sessao-2', QUESTIONS[2]).answer)
                session = radar.session('sessao-1')
                session.trim(limit=4)
                print('Janela:', len(session.history.messages), 'mensagens')
                print('Resumo:', session.summary[:300])
                pprint(session.retrieve('qual vaga descartada e por quê?'))
        """),
    ], [
        ("3.1", "coala", "Memória semântica, episódica e procedural."),
        ("3.2", "turnos", "Janela, resumo e recuperação vetorial."),
        ("3.3", "coala", "Comparação de três ferramentas."),
        ("3.4", "buffer", "ConversationBufferMemory em dois turnos."),
        ("3.5", "turnos", "Intenção de câmbio e posição 2."),
        ("3.6", "turnos", "Quatro turnos reais da API interna do agente, com sessão isolada.")
    ])

    create("05_ferramentas_rag", "05 · Consultar SQL e documentos existentes", [
        md("""
        <a id="ferramentas"></a>

        | Ferramenta | Tipo | Operação |
        |---|---|---|
        | buscar_vagas | API externa | Remotive e Arbeitnow normalizam anúncios e preservam a fonte |
        | converter_moeda | API externa e regra fixa | AwesomeAPI fornece a taxa; Decimal calcula BRL |
        | consultar_candidaturas | Text-to-query e SQLite | A pergunta vira consulta de leitura; a visão é limitada à sessão |
        | recuperar_contexto | Busca semântica | FAISS carrega o índice do notebook 01 |
        | avaliar_fit | Regra fixa | Interseção das habilidades explícitas |
        | verify | Semântica e regras | NLI compara anúncio e afirmação; regras bloqueiam restrições explícitas |

        FastAPI expõe o chat e uma rota de registro de candidatura. A escrita é explícita e
        parametrizada; o executor de SQL gerado não pode escrever.
        """, "ferramentas"),
        code("sql", """
            from tempfile import TemporaryDirectory
            from unittest.mock import patch
            from fastapi.testclient import TestClient
            from src.agente import Radar
            from src.api import app
            question = 'Quais vagas acima de 5k USD eu ainda não apliquei?'
            with TemporaryDirectory() as temp:
                radar = Radar(db_path=Path(temp) / 'vagas.db')
                with patch('src.api.get_radar', return_value=radar):
                    client = TestClient(app)
                    client.post('/chat', json={'session_id':'s1','message':'Mostre vagas de Python'}).raise_for_status()
                    recorded = client.post('/candidaturas', json={'session_id':'s1','vaga_id':'demo-aurora','status':'enviada'})
                    print('Registro manual:', recorded.raise_for_status().json())
                if os.getenv('NOTEBOOK_OPENAI') == '1':
                    from src.config import live_model
                    radar.llm = live_model()
                query, rows = radar._sql(question, 's1')
                print(question, '\\n', query)
                pprint(rows)
        """),
        code("recuperacao", """
            from src.demo import recovery_demo
            result = recovery_demo()
            pprint(result)
        """),
        md("""No conjunto avaliado, Aurora ficou fora do top 2. A consulta original
        privilegiou outros anúncios de software Python sem o cargo backend esperado.
        Reescrever para Senior Backend Engineer aproximou a consulta da terminologia
        do título da Aurora sem alterar o índice, os documentos ou o valor de k."""),
    ], [
        ("4.1", "ferramentas", "Catálogo com descrição e tipo."),
        ("4.2", "ferramentas", "Registro HTTP interno na célula SQL; HTTP externo no 02."),
        ("4.3", "sql", "Pergunta, consulta SQL e linha retornada."),
        ("4.4", "recuperacao", "Executor chama recuperação sobre o índice salvo."),
        ("4.5", "recuperacao", "Antes e depois com os próprios documentos recuperados.")
    ])

    create("06_integrador_avaliacao", "06 · Integrar, verificar e avaliar", [
        md("""O mesmo `Radar.chat` atende FastAPI, CLI, notebooks e avaliação. O executor
        recebe todas as ferramentas. O modelo real é configurável; no modo dummy, uma
        chamada estruturada roteirizada exercita o executor sem credenciais. A resposta
        passa pelo verificador antes de entrar no histórico."""),
        code("integracao", """
            from fastapi.testclient import TestClient
            from unittest.mock import patch
            from src.agente import Radar
            from src.api import app
            from src.demo import QUESTIONS
            # Cenário reprodutível (vagas fictícias com o caso Atlas), independente do MODO_DUMMY do .env.
            patcher = patch('src.api.get_radar', return_value=Radar(dummy=True))
            patcher.start()
            client = TestClient(app)
            print('Interface HTTP:', client.get('/').status_code)
            for q in QUESTIONS:
                res = client.post('/chat', json={'session_id': 'notebook-05', 'message': q})
                res.raise_for_status()
                data = res.json()
                print(data['answer'])
                print('Ferramentas:', [item['name'] for item in data['tool_calls']])
                if q == QUESTIONS[0]:
                    pprint(next(v for v in data['verification'] if v['job_id'] == 'demo-atlas'))
            combined = client.post('/chat', json={'session_id': 'notebook-05-combinado',
                'message': 'Busque vagas de Python e compare com meu currículo'}).json()
            print('Pedido combinado:', combined['answer'].splitlines()[-1])
            print('Trajetória:', [t['name'] for t in combined['tool_calls']])
            patcher.stop()
        """),
        code("avaliacao", """
            from scripts.evaluate import local_report, upload_experiment
            pprint(local_report())
            if os.getenv('NOTEBOOK_LANGSMITH') == '1':
                upload_experiment()
            else:
                print('LangSmith pendente nesta execução: rode python -m scripts.evaluate --langsmith com as chaves.')
        """),
        md("""A taxa de afirmações confirmadas não é a acurácia: casos de contradição e
        ausência de fonte devem permanecer no denominador. Analise por caso, especialmente
        geografia, conversão e uso de memória. O item Streamlit é registrado separadamente
        porque a interface temporária é HTML, e a CLI também executa o agente."""),
    ], [
        ("5.1", "integracao", "NLI e regra geográfica corrigem a afirmação US only."),
        ("5.2", "integracao", "Busca e RAG no mesmo pedido; câmbio no mesmo Radar."),
        ("5.3", "integracao", "Executor real com adaptador de modelo roteirizado; OpenAI pendente."),
        ("5.4", "integracao", "Histórico preserva referência à segunda vaga."),
        ("5.5", "integracao", "UI provisória usa FastAPI; desvio do Streamlit."),
        ("5.6", "avaliacao", "Regressão local salva; publicação no LangSmith depende de chave.")
    ])


if __name__ == "__main__":
    generate()
