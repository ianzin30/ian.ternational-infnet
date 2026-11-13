import os
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from threading import RLock

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import DATA

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
INDEX = DATA / "runtime" / "faiss_index"
INDEX_OPENAI = DATA / "runtime" / "faiss_index_openai"
_LOCK = RLock()


class MultilingualEmbeddings(Embeddings):
    def __init__(self):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(EMBED_MODEL, device="cpu")

    def embed_documents(self, texts):
        with _LOCK:
            return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text):
        return self.embed_documents([text])[0]


@lru_cache(maxsize=2)
def embeddings(real=False):
    """Local MiniLM keeps dummy mode keyless; real mode uses OpenAI embeddings."""
    if real:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL") or "text-embedding-3-small")
    return MultilingualEmbeddings()


def default_index(real=False):
    # Vector sizes differ between providers (384 vs 1536), so each one has its own index.
    return INDEX_OPENAI if real else INDEX


def read_pdf(path):
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions(do_ocr=False, do_table_structure=False)
    return DocumentConverter(format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=options),
    }).convert(path).document.export_to_markdown()


def index_for_resume(resume, real=False):
    fingerprint = sha256(resume.read_bytes()).hexdigest()[:24]
    return INDEX.parent / ("indices_curriculo_openai" if real else "indices_curriculo") / fingerprint


def build_index(jobs, resume=DATA / "curriculo.pdf", destination=None, *, real=False):
    destination = destination or default_index(real)
    text = read_pdf(resume)
    docs = [Document(page_content=text, metadata={"source": resume.name, "kind": "curriculo"})]
    docs.extend(Document(page_content=f"{j.title}\n{j.description}", metadata={
        "source": j.source, "url": j.url, "id": j.id, "kind": "vaga",
    }) for j in jobs)
    chunks = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60).split_documents(docs)
    index = FAISS.from_documents(chunks, embeddings(real))
    index.save_local(str(destination))
    return len(chunks)


@lru_cache(maxsize=4)
def load_index(path=INDEX, real=False):
    # FAISS stores its metadata in a pickle. Only load artifacts generated locally by notebook 01.
    if not Path(path, "index.faiss").is_file() or not Path(path, "index.pkl").is_file():
        return None
    return FAISS.load_local(str(path), embeddings(real), allow_dangerous_deserialization=True)


def retrieve(query, k=3, *, kind=None, index_path=None, real=False):
    index = load_index(index_path or default_index(real), real)
    if index is None:
        return None
    return [{"trecho": d.page_content, **d.metadata} for d in
            index.similarity_search(query, k=k, fetch_k=50, filter={"kind": kind} if kind else None)]


def rewrite_job_query(query, llm=None):
    """Match known domain vocabulary locally, or ask the configured model for an English search."""
    if llm:
        result = llm.invoke(f"Reescreva como termos de busca em inglês. Responda apenas com a consulta.\n{query}")
        return result.text.strip()[:200]
    from .rules import plain

    normalized = plain(query)
    if all(word in normalized for word in ("backend", "senior")):
        return "Senior Backend Engineer"
    return query
