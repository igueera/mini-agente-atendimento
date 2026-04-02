import sqlite3

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