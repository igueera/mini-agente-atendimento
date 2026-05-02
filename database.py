import sqlite3
import json


def conectar():
    conn = sqlite3.connect("agente.db")
    return conn


def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pergunta TEXT,
        resposta TEXT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def criar_tabela_conhecimento():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conhecimento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT,
        keywords TEXT,
        resposta TEXT
    )
    """)
    conn.commit()
    conn.close()


def criar_tabela_memoria():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memoria (
        numero TEXT PRIMARY KEY,
        mensagens TEXT,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def buscar_memoria(numero: str) -> list:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT mensagens FROM memoria WHERE numero = ?", (numero,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return []

    # Desserializa o JSON de volta para lista Python
    return json.loads(row[0])


def salvar_memoria(numero: str, mensagens: list):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO memoria (numero, mensagens, atualizado_em)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (numero, json.dumps(mensagens, ensure_ascii=False)))
    conn.commit()
    conn.close()


def limpar_memoria(numero: str):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memoria WHERE numero = ?", (numero,))
    conn.commit()
    conn.close()


def salvar_conversa(pergunta, resposta):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO historico (pergunta, resposta)
    VALUES (?, ?)
    """, (pergunta, resposta))
    conn.commit()
    conn.close()


def buscar_historico():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT pergunta, resposta, data FROM historico")
    dados = cursor.fetchall()
    conn.close()
    return dados


def popular_conhecimento():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM conhecimento")
    total = cursor.fetchone()[0]
    if total > 0:
        conn.close()
        return
    dados = [
        ("horario", "horario,horarios,funciona,abre,fechar", "Funcionamos das 6h às 22h, de segunda a sábado."),
        ("planos", "plano,planos,preco,valor,mensal,anual", "Temos plano mensal por R$120 e plano anual por R$1100."),
        ("localizacao", "onde,localizacao,endereco,fica", "Estamos localizados na Rua Central, 123.")
    ]
    cursor.executemany("""
    INSERT INTO conhecimento (categoria, keywords, resposta)
    VALUES (?, ?, ?)
    """, dados)
    conn.commit()
    conn.close()


def buscar_conhecimento():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT categoria, keywords, resposta FROM conhecimento")
    dados = cursor.fetchall()
    conn.close()
    conhecimento = []
    for categoria, keywords, resposta in dados:
        conhecimento.append({
            "categoria": categoria,
            "keywords": keywords.split(","),
            "resposta": resposta
        })
    return conhecimento


def adicionar_conhecimento(categoria, keywords, resposta):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO conhecimento(categoria, keywords, resposta)
    VALUES (?, ?, ?)
    """, (categoria, keywords, resposta))
    conn.commit()
    conn.close()


def limpar_memorias_antigas(horas: int = 24):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM memoria
        WHERE atualizado_em < datetime('now', ? || ' hours')
    """, (f"-{horas}",))
    removidos = cursor.rowcount
    conn.commit()
    conn.close()
    if removidos > 0:
        print(f"Limpeza de memória: {removidos} conversa(s) antiga(s) removida(s).")