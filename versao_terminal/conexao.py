import mysql.connector

def testar_conexao():
    try:
        # Conectando ao banco de dados usando as configurações do meu Wamp
        banco = mysql.connector.connect(
            host="localhost",
            user="root",          
            password="",          
            database="folheando"  
        )
        
        # Se a conexão der certo, exibe a mensagem de sucesso
        if banco.is_connected():
            print("🎉 Sucesso! O Python conseguiu se conectar ao banco do Folheando!")
            banco.close()
            
    except Exception as erro:
        print(f"❌ Opa, deu erro na conexão: {erro}")

testar_conexao()