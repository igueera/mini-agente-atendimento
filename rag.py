# Pipeline completo do RAG (Retrieval-Augmented Generation)
# Responsável por: ler o documento, dividir em chunks,
# gerar embeddings e buscar os trechos mais relevantes para uma pergunta

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.table import Table as DocxTable
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from logger import get_logger
import numpy as np
import os

load_dotenv()

logger = get_logger(__name__)

modelo = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

CAMINHO_DOCUMENTO = os.path.join(
    os.path.dirname(__file__),
    os.getenv("DOCUMENTO_PATH", "academia_forcamax.docx")
)


def extrair_texto_docx(caminho: str) -> list[str]:
    doc = Document(caminho)
    textos = []

    for elemento in doc.element.body:
        if elemento.tag == qn('w:p'):
            para = DocxParagraph(elemento, doc)
            texto = para.text.strip()
            if texto:
                textos.append(texto)

        elif elemento.tag == qn('w:tbl'):
            tabela = DocxTable(elemento, doc)
            for linha in tabela.rows:
                celulas = [c.text.strip() for c in linha.cells if c.text.strip()]
                if celulas:
                    textos.append(" | ".join(celulas))

    return textos


def criar_chunks(paragrafos: list[str], tamanho: int = 3) -> list[str]:
    chunks = []
    for i in range(0, len(paragrafos), tamanho):
        chunk = " ".join(paragrafos[i:i + tamanho])
        chunks.append(chunk)
    return chunks


def carregar_base() -> tuple[list[str], np.ndarray]:
    try:
        paragrafos = extrair_texto_docx(CAMINHO_DOCUMENTO)
        chunks = criar_chunks(paragrafos, tamanho=3)
        logger.info(f"Base carregada: {len(chunks)} chunks gerados do documento.")
        embeddings = modelo.encode(chunks, convert_to_numpy=True)
        return chunks, embeddings
    except Exception as e:
        logger.error(f"Erro ao carregar base de conhecimento: {e}")
        return [], np.array([])


def buscar_chunks_relevantes(pergunta: str, chunks: list[str], embeddings: np.ndarray, top_k: int = 3) -> str:
    if not chunks or len(embeddings) == 0:
        logger.warning("Base de conhecimento vazia — retornando contexto vazio.")
        return ""

    embedding_pergunta = modelo.encode([pergunta], convert_to_numpy=True)
    similaridades = cosine_similarity(embedding_pergunta, embeddings)[0]

    # Pega os índices dos top_k chunks mais similares
    indices_top = np.argsort(similaridades)[::-1][:top_k]

    # Junta os chunks relevantes em um único contexto
    contexto = "\n\n".join([chunks[i] for i in indices_top])
    return contexto


chunks_base, embeddings_base = carregar_base()


def buscar_contexto(pergunta: str) -> str:
    return buscar_chunks_relevantes(pergunta, chunks_base, embeddings_base, top_k=5)