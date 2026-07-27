from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

def conectar_banco():
    database_url = "postgresql://postgres.pdgodnriqadkyyywnsjb:sorvetedepedra@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
    return psycopg2.connect(database_url, sslmode='require')

def obter_cursor(banco, dictionary=False):
    return banco.cursor(cursor_factory=RealDictCursor)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/livros', methods=['GET'])
def listar_livros():
    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco, dictionary=True)

        query = """
            SELECT 
                l.id, l.titulo, l.autor, l.genero, l.link,
                COALESCE(AVG(lt.nota), 0) as media_notas,
                STRING_AGG(CONCAT(u.nome, ': ', lt.resenha), '|||') as resenhas
            FROM livros l
            LEFT JOIN leituras lt ON l.id = lt.livro_id AND lt.resenha IS NOT NULL AND lt.resenha != ''
            LEFT JOIN usuarios u ON lt.usuario_id = u.id
            GROUP BY l.id, l.titulo, l.autor, l.genero, l.link;
        """

        cursor.execute(query)
        livros = cursor.fetchall()
        cursor.close()
        banco.close()
        return jsonify(livros), 200
    except Exception as erro:
        return jsonify({"erro": f"Erro ao carregar livros: {erro}"}), 500

@app.route('/relatorio', methods=['GET'])
def listar_relatorio():
    usuario_filtro = request.args.get('usuario')
    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco, dictionary=True)

        if usuario_filtro:
            query = """
                SELECT l.id, u.nome as leitor, liv.titulo, s.nome as status, l.nota, l.resenha, l.data_registro
                FROM leituras l
                JOIN usuarios u ON l.usuario_id = u.id
                JOIN livros liv ON l.livro_id = liv.id
                JOIN status s ON l.id_status = s.id
                WHERE u.nome = %s
                ORDER BY l.data_registro DESC;
            """
            cursor.execute(query, (usuario_filtro,))
        else:
            query = """
                SELECT l.id, u.nome as leitor, liv.titulo, s.nome as status, l.nota, l.resenha, l.data_registro
                FROM leituras l
                JOIN usuarios u ON l.usuario_id = u.id
                JOIN livros liv ON l.livro_id = liv.id
                JOIN status s ON l.id_status = s.id
                ORDER BY l.data_registro DESC;
            """
            cursor.execute(query)

        resultados = cursor.fetchall()
        cursor.close()
        banco.close()
        return jsonify(resultados), 200
    except Exception as erro:
        return jsonify({"erro": f"Erro ao carregar relatório: {erro}"}), 500

@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    nome = dados.get('nick') or dados.get('nome')
    senha = dados.get('senha')
    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco, dictionary=True)
        query = "SELECT id, nome FROM usuarios WHERE nome = %s AND senha = %s"
        cursor.execute(query, (nome, senha))
        usuario = cursor.fetchone()
        cursor.close()
        banco.close()

        if usuario:
            return jsonify({"mensagem": "Login bem-sucedido!", "usuario": {"id": usuario['id'], "nome": usuario['nome']}}), 200
        else:
            return jsonify({"erro": "Nome ou senha inválidos."}), 401
    except Exception as erro:
        return jsonify({"erro": f"Erro no login: {erro}"}), 500

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    dados = request.json
    nome = dados.get('nick') or dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')
    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco, dictionary=True)
        query = "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)"
        cursor.execute(query, (nome, email, senha))
        banco.commit()
        cursor.close()
        banco.close()
        return jsonify({"mensagem": "Usuário cadastrado com sucesso!"}), 201
    except Exception as erro:
        return jsonify({"erro": f"Erro ao cadastrar usuário: {erro}"}), 500

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
    novo_link = dados.get('novo_link')

    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco, dictionary=True)

        if id_livro == 0 or id_livro == "0":
            if not novo_titulo or not novo_autor:
                cursor.close()
                banco.close()
                return jsonify({"erro": "Título e Autor do livro são necessários!"}), 400

            comando_livro = "INSERT INTO livros (titulo, autor, genero, link) VALUES (%s, %s, %s, %s) RETURNING id;"
            cursor.execute(comando_livro, (novo_titulo, novo_autor, novo_genero, novo_link))
            banco.commit()
            id_livro = cursor.fetchone()['id']

        comando_leitura = """
            INSERT INTO leituras (usuario_id, livro_id, id_status, nota, resenha)
            VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(comando_leitura, (id_usuario, id_livro, id_status, nota, resenha))
        banco.commit()

        cursor.close()
        banco.close()
        return jsonify({"mensagem": "Leitura registrada com sucesso!"}), 201
    except Exception as erro:
        return jsonify({"erro": f"Erro ao adicionar leitura: {erro}"}), 500

@app.route('/atualizar_leitura/<int:id_leitura>', methods=['PUT'])
def atualizar_leitura(id_leitura):
    dados = request.json
    id_status = dados.get('id_status')
    nota = dados.get('nota')
    resenha = dados.get('resenha')
    try:
        banco = conectar_banco()
        cursor = obter_cursor(banco, dictionary=True)
        query = "UPDATE leituras SET id_status = %s, nota = %s, resenha = %s WHERE id = %s"
        cursor.execute(query, (id_status, nota, resenha, id_leitura))
        banco.commit()
        cursor.close()
        banco.close()
        return jsonify({"mensagem": "Leitura atualizada com sucesso!"}), 200
    except Exception as erro:
        return jsonify({"erro": f"Erro ao atualizar leitura: {erro}"}), 500

if __name__ == '__main__':
    app.run(debug=True)