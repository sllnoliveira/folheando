import mysql.connector

def puxar_relatorio():
    try:
        # Conectando ao banco de dados usando as configurações do meu Wamp
        banco = mysql.connector.connect(
            host="localhost",
            user="root",          
            password="",    
        database="folheando"  
        )

        cursor = banco.cursor()

        comando_sql = """
        SELECT 
            usuarios.nome AS 'Leitor(a)',
            livros.titulo AS 'Livro',
            status_leitura.nome AS 'Status',
            leituras.nota AS 'Nota'
        FROM leituras
        INNER JOIN usuarios ON leituras.id_usuario = usuarios.id
        INNER JOIN livros ON leituras.id_livro = livros.id
        INNER JOIN status_leitura ON leituras.id_status = status_leitura.id
        ORDER BY leituras.nota DESC;
        """

        cursor.execute(comando_sql)
        resultados = cursor.fetchall()

        print("📊 Relatório de Leituras:")

        for linha in resultados:
            print(f"Leitor(a): {linha[0]}, Livro: {linha[1]}, Status: {linha[2]}, Nota: {linha[3]}")
        print("===================================\n")

        cursor.close()
        banco.close()

    except Exception as erro:
        print(f"❌ Opa, deu erro ao puxar o relatório: {erro}")

#puxar_relatorio()