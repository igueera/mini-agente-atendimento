# rag.py
# Pipeline completo do RAG (Retrieval-Augmented Generation)
# Responsável por: ler o documento, dividir em chunks,
# gerar embeddings e buscar os trechos mais relevantes para uma pergunta

from docx import Document
from docx.oxml.ns import qn
from dotenv import load_dotenv
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.table import Table as DocxTable
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os

load_dotenv()

# Modelo multilingual — o mesmo já usado no projeto
modelo = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Caminho do documento (na mesma pasta do projeto)
CAMINHO_DOCUMENTO = os.path.join(os.path.dirname(__file__), os.getenv("DOCUMENTO_PATH", "academia_forcamax.docx"))


def extrair_texto_docx(caminho: str) -> list[str]:
    """
    Lê o documento Word e retorna uma lista de textos não vazios.
    Extrai tanto parágrafos normais quanto conteúdo de tabelas.
    """
    doc = Document(caminho)
    textos = []

    for elemento in doc.element.body:
        # Parágrafo normal
        if elemento.tag == qn('w:p'):
            para = DocxParagraph(elemento, doc)
            texto = para.text.strip()
            if texto:
                textos.append(texto)

        # Tabela — extrai linha por linha
        elif elemento.tag == qn('w:tbl'):
            tabela = DocxTable(elemento, doc)
            for linha in tabela.rows:
                celulas = [c.text.strip() for c in linha.cells if c.text.strip()]
                if celulas:
                    textos.append(" | ".join(celulas))

    return textos


def criar_chunks(paragrafos: list[str], tamanho: int = 3) -> list[str]:
    """
    Agrupa textos em chunks de N itens cada.
    Chunks maiores dão mais contexto ao LLM.
    """
    chunks = []
    for i in range(0, len(paragrafos), tamanho):
        chunk = " ".join(paragrafos[i:i + tamanho])
        chunks.append(chunk)
    return chunks


def carregar_base() -> tuple[list[str], np.ndarray]:
    """
    Lê o documento, cria os chunks e gera os embeddings de cada um.
    Retorna os chunks e seus embeddings prontos para busca.
    """
    paragrafos = extrair_texto_docx(CAMINHO_DOCUMENTO)
    chunks = criar_chunks(paragrafos, tamanho=3)
    print(f"Base carregada: {len(chunks)} chunks gerados do documento.")
    embeddings = modelo.encode(chunks, convert_to_numpy=True)
    return chunks, embeddings


def buscar_chunks_relevantes(pergunta: str, chunks: list[str], embeddings: np.ndarray, top_k: int = 3) -> str:
    """
    Recebe a pergunta do usuário, compara com todos os chunks
    via similaridade de cosseno e retorna os top_k mais relevantes
    como um único texto de contexto para o LLM.
    """
    embedding_pergunta = modelo.encode([pergunta], convert_to_numpy=True)
    similaridades = cosine_similarity(embedding_pergunta, embeddings)[0]

    # Pega os índices dos top_k chunks mais similares
    indices_top = np.argsort(similaridades)[::-1][:top_k]

    # Junta os chunks relevantes em um único contexto
    contexto = "\n\n".join([chunks[i] for i in indices_top])
    return contexto


# Carrega a base uma única vez quando o módulo é importado
# (evita reprocessar o documento a cada requisição)
chunks_base, embeddings_base = carregar_base()


def buscar_contexto(pergunta: str) -> str:
    """
    Função principal — recebe a pergunta e retorna o contexto relevante.
    Esta é a função que será chamada pelo main.py.
    """
    return buscar_chunks_relevantes(pergunta, chunks_base, embeddings_base, top_k=5)