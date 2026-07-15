from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
CORS(app)

# 1. FUNÇÃO INTELIGENTE DE CONEXÃO (Detecta local ou nuvem)
def conectar_banco():
    url_banco_nuvem = os.environ.get("DATABASE_URL")
    
    if url_banco_nuvem:
        # Se estiver no Render (PostgreSQL)
        return psycopg2.connect(url_banco_nuvem)
    else:
        # Se estiver no seu computador (MySQL local)
        return mysql.connector.connect(
            host="localhost",
            user="root",        
            password="",        
            database="folheando"
        )

# 2. FUNÇÃO AUXILIAR PARA GERAR O CURSOR CORRETO
def obter_cursor(banco, dictionary=False):
    # Verifica se é uma conexão PostgreSQL (psycopg2)
    if isinstance(banco, psycopg2.extensions.connection):
        if dictionary:
            return banco.cursor(cursor_factory=RealDictCursor)
        else:
            return banco.cursor()
    else:
        # Se for MySQL local
        if dictionary:
            return banco.cursor(dictionary=True)
        else:
            return banco.cursor()

# 3. VERIFICAÇÃO LOCAL DO BANCO (Só roda no computador local)
# 3. CRIAÇÃO AUTOMÁTICA DAS TABELAS (Roda local e na nuvem de graça)
def inicializar_banco_de_dados():
    try:
        banco = conectar_banco()
        cursor = banco.cursor()
        
        # Se for PostgreSQL (Render)
        if isinstance(banco, psycopg2.extensions.connection):
            # Criação das tabelas no Postgres
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL UNIQUE,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    senha VARCHAR(255) NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS livros (
                    id SERIAL PRIMARY KEY,
                    titulo VARCHAR(255) NOT NULL,
                    autor VARCHAR(100) NOT NULL,
                    genero VARCHAR(50)
                );
                
                CREATE TABLE IF NOT EXISTS status_leitura (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(50) NOT NULL UNIQUE
                );
                
                CREATE TABLE IF NOT EXISTS leituras (
                    id SERIAL PRIMARY KEY,
                    id_usuario INT REFERENCES usuarios(id) ON DELETE CASCADE,
                    id_livro INT REFERENCES livros(id) ON DELETE CASCADE,
                    id_status INT REFERENCES status_leitura(id) ON DELETE CASCADE,
                    nota INT CHECK (nota >= 1 AND nota <= 5),
                    resenha TEXT,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Insere os status padrão
                INSERT INTO status_leitura (nome) VALUES ('Lendo') ON CONFLICT (nome) DO NOTHING;
                INSERT INTO status_leitura (nome) VALUES ('Lido') ON CONFLICT (nome) DO NOTHING;
                INSERT INTO status_leitura (nome) VALUES ('Quero Ler') ON CONFLICT (nome) DO NOTHING;
                INSERT INTO status_leitura (nome) VALUES ('Abandonado') ON CONFLICT (nome) DO NOTHING;
            """)
            banco.commit()
            print("✅ Tabelas verificadas/criadas com sucesso no PostgreSQL!")
            
        else:
            # Se for MySQL local (mantém o que você já tinha)
            try:
                cursor.execute("ALTER TABLE leituras ADD COLUMN resenha TEXT;")
                banco.commit()
            except mysql.connector.Error as err:
                if err.errno != 1060: pass
                
            try:
                cursor.execute("ALTER TABLE leituras ADD COLUMN data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                banco.commit()
            except mysql.connector.Error as err:
                if err.errno != 1060: pass
                
        cursor.close()
        banco.close()
    except Exception as err:
        print(f"⚠️ Erro ao inicializar banco de dados: {err}")

# Executa a criação/verificação ao iniciar o servidor
inicializar_banco_de_dados()

# ==================== ROTAS DA API ====================

# 1. ROTA DE RELATÓRIO
@app.route('/relatorio', methods=['GET'])
def obtener_relatorio():
    usuario_filtro = request.args.get('usuario')
    
    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco, dictionary=True)
        
        if usuario_filtro:
            comando_sql = """
            SELECT usuarios.nome as leitor, livros.titulo, status_leitura.nome as status, 
                   leituras.nota, leituras.resenha, leituras.data_registro
            FROM leituras
            INNER JOIN usuarios ON leituras.id_usuario = usuarios.id
            INNER JOIN livros ON leituras.id_livro = livros.id
            INNER JOIN status_leitura ON leituras.id_status = status_leitura.id
            WHERE usuarios.nome = %s
            ORDER BY leituras.data_registro DESC;
            """
            cursor.execute(comando_sql, (usuario_filtro,))
        else:
            comando_sql = """
            SELECT usuarios.nome as leitor, livros.titulo, status_leitura.nome as status, 
                   leituras.nota, leituras.resenha, leituras.data_registro
            FROM leituras
            INNER JOIN usuarios ON leituras.id_usuario = usuarios.id
            INNER JOIN livros ON leituras.id_livro = livros.id
            INNER JOIN status_leitura ON leituras.id_status = status_leitura.id
            ORDER BY leituras.data_registro DESC;
            """
            cursor.execute(comando_sql)
            
        resultados = cursor.fetchall()
        cursor.close()
        banco.close()
        
        return jsonify(resultados), 200
    except Exception as erro:
        return jsonify({"erro": f"Erro ao buscar relatório: {erro}"}), 500


# 2. ROTA DE LOGIN
@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    nick = dados.get('nick')
    senha = dados.get('senha')
    
    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco)
        
        comando_sql = "SELECT id, nome FROM usuarios WHERE nome = %s AND senha = %s;"
        cursor.execute(comando_sql, (nick, senha))
        resultado = cursor.fetchone()
        
        cursor.close()
        banco.close()
        
        if resultado:
            return jsonify({
                "mensagem": "Login realizado com sucesso!",
                "usuario": {
                    "id": resultado[0],
                    "nome": resultado[1]
                }
            }), 200
        else:
            return jsonify({"erro": "Usuário ou senha incorretos!"}), 401
            
    except Exception as erro:
        return jsonify({"erro": f"Erro no servidor: {erro}"}), 500


# 3. ROTA DE CADASTRO DE USUÁRIO
@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    dados = request.json
    nick = dados.get('nick')
    email = dados.get('email')
    senha = dados.get('senha')
    
    if not nick or not email or not senha:
        return jsonify({"erro": "Todos os campos são obrigatórios!"}), 400
        
    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco)
        
        cursor.execute("SELECT id FROM usuarios WHERE nome = %s;", (nick,))
        if cursor.fetchone():
            cursor.close()
            banco.close()
            return jsonify({"erro": "Este nickname já está em uso!"}), 400
            
        comando_sql = "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s);"
        cursor.execute(comando_sql, (nick, email, senha))
        banco.commit()
        
        cursor.close()
        banco.close()
        
        return jsonify({"mensagem": f"Usuário '{nick}' criado com sucesso!"}), 201
    except Exception as erro:
        return jsonify({"erro": f"Erro ao cadastrar: {erro}"}), 500


# 4. ROTA PARA LISTAR LIVROS CADASTRADOS
@app.route('/livros', methods=['GET'])
def listar_livros():
    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco, dictionary=True)
        cursor.execute("SELECT id, titulo, autor, genero FROM livros;")
        livros = cursor.fetchall()
        cursor.close()
        banco.close()
        return jsonify(livros), 200
    except Exception as erro:
        return jsonify({"erro": f"Erro ao listar livros: {erro}"}), 500


# 5. ROTA PARA ADICIONAR NOVA LEITURA
@app.route('/adicionar_leitura', methods=['POST'])
def adicionar_leitura():
    dados = request.json
    id_usuario = dados.get('id_usuario')
    id_livro = dados.get('id_livro')
    id_status = dados.get('id_status')
    nota = dados.get('nota')
    resenha = dados.get('resenha')
    
    novo_titulo = dados.get('novo_titulo')
    novo_autor = dados.get('novo_autor')
    novo_genero = dados.get('novo_genero')
    
    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco, dictionary=True) # Dicionário ajuda a pegar o ID retornado no Postgres
        
        if id_livro == 0 or id_livro == "0":
            # CORRIGIDO:
            if not novo_titulo or not novo_autor: 
                return jsonify({"erro": "Título e Autor do livro são necessários!"}), 400
            
            # Lógica inteligente para capturar o ID do livro criado (funciona no MySQL e Postgres)
            if isinstance(banco, psycopg2.extensions.connection):
                # No Postgres usamos RETURNING id
                comando_livro = "INSERT INTO livros (titulo, autor, genero) VALUES (%s, %s, %s) RETURNING id;"
                cursor.execute(comando_livro, (novo_titulo, novo_autor, novo_genero))
                banco.commit()
                id_livro = cursor.fetchone()['id']
            else:
                # No MySQL local usamos cursor.lastrowid
                comando_livro = "INSERT INTO livros (titulo, autor, genero) VALUES (%s, %s, %s);"
                cursor.execute(comando_livro, (novo_titulo, novo_autor, novo_genero))
                banco.commit()
                id_livro = cursor.lastrowid
            
        comando_leitura = """
        INSERT INTO leituras (id_usuario, id_livro, id_status, nota, resenha)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(comando_leitura, (id_usuario, id_livro, id_status, nota, resenha))
        banco.commit()
        
        cursor.close()
        banco.close()
        
        return jsonify({"mensagem": "Leitura registrada com sucesso!"}), 201
    except Exception as erro:
        return jsonify({"erro": f"Erro ao registrar leitura: {erro}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)