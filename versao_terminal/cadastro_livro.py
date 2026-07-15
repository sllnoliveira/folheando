import mysql.connector

def cadastrar_novo_livro():
    # Coletando todas as informações do usuário
    titulo_livro = input("Digite o título do livro: ")
    autor_livro = input("Digite o autor do livro: ")
    genero_livro = input("Digite o gênero do livro: ")
    link_livro = input("Digite o link oficial do livro (ou deixe em branco): ")
    
    try:
        banco = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="folheando"
        )
        
        cursor = banco.cursor()
        
        # Corrigido aqui: mudamos de 'link' para 'link_oficial'
        comando_sql = """
        INSERT INTO livros (titulo, autor, genero, link_oficial) 
        VALUES (%s, %s, %s, %s);
        """
        
        # Passamos as variáveis na mesma ordem dos campos do INSERT
        dados = (titulo_livro, autor_livro, genero_livro, link_livro)
        
        cursor.execute(comando_sql, dados)
        
        # Salvando as alterações no banco
        banco.commit()
        
        print(f"\n📖 Sucesso! O livro '{titulo_livro}' foi cadastrado com todos os dados no MySQL!")
        
        cursor.close()
        banco.close()
            
    except Exception as erro:
        print(f"❌ Erro ao cadastrar o livro: {erro}")

# Executa a função
#cadastrar_novo_livro()
