import logging
from dataclasses import dataclass, field
from threading import RLock

from langchain_classic.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_core.chat_history import InMemoryChatMessageHistory

from .eventos import Emissor
from .models import Entidades, Vaga
from .rag import embeddings

logger = logging.getLogger(__name__)


@dataclass
class Session:
    history: InMemoryChatMessageHistory = field(default_factory=InMemoryChatMessageHistory)
    lock: RLock = field(default_factory=RLock)
    summary: str = ""
    entities: Entidades = field(default_factory=Entidades)
    visible: list[str] = field(default_factory=list)
    jobs: dict[str, Vaga] = field(default_factory=dict)
    knowledge: list[str] = field(default_factory=list)
    memory_index: FAISS | None = None
    known: set[str] = field(default_factory=set)
    real: bool = False
    prefs: list[str] = field(default_factory=list)
    emit: Emissor = field(default_factory=Emissor)
    user_id: str = "local"
    janela: dict = field(default_factory=dict)
    ultimo: dict = field(default_factory=dict)
    buffer: ConversationBufferMemory = None

    def __post_init__(self):
        # Short-term memory: the classic buffer wraps the same history that
        # RunnableWithMessageHistory reads and writes for this session_id.
        self.buffer = ConversationBufferMemory(chat_memory=self.history, return_messages=True)

    def mensagens(self):
        return self.buffer.load_memory_variables({})["history"]

    def trim(self, llm=None, limit=8):
        excess = len(self.history.messages) - limit
        if excess <= 0:
            return
        old = "\n".join(f"{m.type}: {m.text[:300]}" for m in self.history.messages[:excess])
        merged = f"{self.summary}\n{old}"
        if llm:
            try:
                merged = llm.invoke("Resuma as preferências explícitas e o contexto em português, em até 150 palavras.\n" + merged).text
            except Exception:
                logger.warning("Sumarização remota indisponível; preservando a janela textual.")
        self.summary = str(merged)[-1600:]
        del self.history.messages[:excess]

    def remember(self, facts):
        for fact in facts:
            if fact in self.known or len(self.known) >= 100:
                continue
            self.known.add(fact)
            self.knowledge.append(fact)
            try:
                if self.memory_index:
                    self.memory_index.add_texts([fact])
                else:
                    self.memory_index = FAISS.from_texts(self.knowledge, embeddings(self.real))
            except Exception:
                logger.warning("Memória vetorial indisponível; fatos mantidos na sessão.")
                break

    def retrieve(self, query):
        if not self.memory_index:
            return self.knowledge[-3:]
        return [d.page_content for d in self.memory_index.similarity_search(query, k=3)]
