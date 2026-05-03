# Testes unitários — testam funções isoladas sem depender
# de serviços externos (banco, API, WhatsApp, etc)

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rag import criar_chunks, extrair_texto_docx
from utils import limpar_texto
from database import conectar, criar_tabela, criar_tabela_memoria, buscar_memoria, salvar_memoria, limpar_memorias_antigas


class TestCriarChunks:
    def test_chunks_tamanho_correto(self):
        paragrafos = ["a", "b", "c", "d", "e", "f"]
        chunks = criar_chunks(paragrafos, tamanho=3)
        assert len(chunks) == 2

    def test_chunks_conteudo_correto(self):
        paragrafos = ["hello", "world"]
        chunks = criar_chunks(paragrafos, tamanho=2)
        assert chunks[0] == "hello world"

    def test_chunks_lista_vazia(self):
        chunks = criar_chunks([], tamanho=3)
        assert chunks == []

    def test_chunks_tamanho_maior_que_lista(self):
        paragrafos = ["a", "b"]
        chunks = criar_chunks(paragrafos, tamanho=10)
        assert len(chunks) == 1



class TestLimparTexto:

    def test_remove_acentos(self):
        assert limpar_texto("horário") == "horario"

    def test_converte_para_minusculo(self):
        assert limpar_texto("HORÁRIO") == "horario"

    def test_texto_sem_acentos(self):
        assert limpar_texto("academia") == "academia"

    def test_texto_vazio(self):
        assert limpar_texto("") == ""



class TestMemoria:
    def setup_method(self):
        criar_tabela()
        criar_tabela_memoria()

    def test_buscar_memoria_numero_inexistente(self):
        resultado = buscar_memoria("5500000000000@s.whatsapp.net")
        assert resultado == []

    def test_salvar_e_buscar_memoria(self):
        numero = "5511111111111@s.whatsapp.net"
        historico = [
            {"role": "user", "content": "Qual o horário?"},
            {"role": "assistant", "content": "Das 6h às 22h."}
        ]
        salvar_memoria(numero, historico)
        resultado = buscar_memoria(numero)
        assert len(resultado) == 2
        assert resultado[0]["content"] == "Qual o horário?"

    def test_salvar_memoria_substitui_anterior(self):
        numero = "5522222222222@s.whatsapp.net"
        salvar_memoria(numero, [{"role": "user", "content": "msg1"}])
        salvar_memoria(numero, [{"role": "user", "content": "msg2"}])
        resultado = buscar_memoria(numero)
        assert len(resultado) == 1
        assert resultado[0]["content"] == "msg2"

    def test_limpar_memorias(self):
        import sqlite3
        numero = "5533333333333@s.whatsapp.net"
        conn = sqlite3.connect("agente.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO memoria (numero, mensagens, atualizado_em)
            VALUES (?, ?, datetime('now', '-2 hours'))
        """, (numero, '[{"role": "user", "content": "teste"}]'))
        conn.commit()
        conn.close()

        limpar_memorias_antigas(horas=1)
        resultado = buscar_memoria(numero)
        assert resultado == []