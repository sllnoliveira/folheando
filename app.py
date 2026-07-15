from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

# Função para garantir a estrutura do banco
def verificar_e_atualizar_banco():
    try:
        banco = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="folheando"
        )
        cursor = banco.cursor()
        
        # 1. Garante que a coluna resenha exista
        try:
            cursor.execute("ALTER TABLE leituras ADD COLUMN resenha TEXT;")
            banco.commit()
        except mysql.connector.Error as err:
            if err.errno != 1060: # Ignora se o erro for 'coluna já existe'
                print(f"⚠️ Erro ao adicionar coluna resenha: {err}")
                
        # 2. Garante que a coluna data_registro exista (salva automaticamente a data atual)
        try:
            cursor.execute("ALTER TABLE leituras ADD COLUMN data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
            banco.commit()
        except mysql.connector.Error as err:
            if err.errno != 1060: # Ignora se o erro for 'coluna já existe'
                print(f"⚠️ Erro ao adicionar coluna data_registro: {err}")

        cursor.close()
        banco.close()
    except Exception as err:
        print(f"⚠️ Erro geral ao verificar banco: {err}")

verificar_e_atualizar_banco()

# Função auxiliar para conectar ao banco de dados facilmente
def conectar_banco():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="folheando"
    )

# 1. ROTA DE RELATÓRIO (Atualizada para puxar a data_registro)
@app.route('/relatorio', methods=['GET'])
def obtener_relatorio():
    usuario_filtro = request.args.get('usuario')
    
    try:
        banco = conectar_banco()
        cursor = banco.cursor(dictionary=True)
        
        if usuario_filtro:
            comando_sql = """
            SELECT usuarios.nome as leitor, livros.titulo, status_leitura.nome as status, 
                   leituras.nota, leituras.resenha, leituras.data_registro
            FROM leituras
            INNER JOIN usuarios ON leituras.id_usuario = usuarios.id
            INNER JOIN livros ON leituras.id_livro = livros.id
            INNER JOIN status_leitura ON leituras.id_status = status_leitura.id
            WHERE usuarios.nome = %s
            ORDER BY leituras.data_registro DESC; -- Ordena pelas leituras mais recentes primeiro!
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
            ORDER BY leituras.data_registro DESC; -- Ordena pelas leituras mais recentes primeiro!
            """
            cursor.execute(comando_sql)
            
        resultados = cursor.fetchall()
        cursor.close()
        banco.close()
        
        # O Flask converte automaticamente objetos de data (datetime) para string no JSON
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
        cursor = banco.cursor()
        
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
        cursor = banco.cursor()
        
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
        cursor = banco.cursor(dictionary=True)
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
        cursor = banco.cursor()
        
        if id_livro == 0 or id_livro == "0":
            if not novo_titulo or not novo_autor:
                return jsonify({"erro": "Título e Autor do livro são necessários!"}), 400
                
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