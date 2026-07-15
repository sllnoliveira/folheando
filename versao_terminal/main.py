import mysql.connector

# Variável para controlar se temos um usuário logado no sistema
usuario_logado = None

# Função auxiliar para garantir que a coluna 'resenha' exista na tabela 'leituras'
def verificar_e_atualizar_banco():
    try:
        banco = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="folheando"
        )
        cursor = banco.cursor()
        # Tenta adicionar a coluna resenha. Se já existir, o MySQL vai dar erro e nós tratamos no 'except'
        cursor.execute("ALTER TABLE leituras ADD COLUMN resenha TEXT;")
        banco.commit()
        cursor.close()
        banco.close()
    except mysql.connector.Error as err:
        # Se o erro for que a coluna já existe (erro 1060), ignoramos silenciosamente
        if err.errno == 1060:
            pass
        else:
            print(f"⚠️ Aviso ao verificar estrutura do banco: {err}")

# Executa a verificação assim que o programa abre
verificar_e_atualizar_banco()


def puxar_relatorio():
    try:
        banco = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="folheando"
        )
        cursor = banco.cursor()
        
        filtrar_por_usuario = False
        
        if usuario_logado is not None:
            print("\n📊 === OPÇÕES DE RELATÓRIO ===")
            print("[ 1 ] Ver APENAS Minhas Leituras")
            print("[ 2 ] Ver Relatório GERAL (Todos os Leitores)")
            escolha = input("Escolha o tipo de relatório: ")
            
            if escolha == '1':
                filtrar_por_usuario = True

        if filtrar_por_usuario:
            print(f"\n📚 === MEU RELATÓRIO DE LEITURAS (Logado como: {usuario_logado}) ===")
            comando_sql = """
            SELECT usuarios.nome, livros.titulo, status_leitura.nome, leituras.nota, leituras.resenha
            FROM leituras
            INNER JOIN usuarios ON leituras.id_usuario = usuarios.id
            INNER JOIN livros ON leituras.id_livro = livros.id
            INNER JOIN status_leitura ON leituras.id_status = status_leitura.id
            WHERE usuarios.nome = %s
            ORDER BY leituras.nota DESC;
            """
            cursor.execute(comando_sql, (usuario_logado,))
        else:
            print("\n📚 === RELATÓRIO GERAL DE LEITURAS ===")
            comando_sql = """
            SELECT usuarios.nome, livros.titulo, status_leitura.nome, leituras.nota, leituras.resenha
            FROM leituras
            INNER JOIN usuarios ON leituras.id_usuario = usuarios.id
            INNER JOIN livros ON leituras.id_livro = livros.id
            INNER JOIN status_leitura ON leituras.id_status = status_leitura.id
            ORDER BY leituras.nota DESC;
            """
            cursor.execute(comando_sql)
            
        resultados = cursor.fetchall()
        
        if not resultados:
            print("Nenhuma leitura encontrada.")
        else:
            for linha in resultados:
                nota_exibicao = linha[3] if linha[3] is not None else "Sem nota"
                resenha_exibicao = linha[4] if linha[4] else "Nenhuma resenha escrita."
                
                print(f"Leitor(a): {linha[0]} | Livro: {linha[1]} | Status: {linha[2]} | Nota: {nota_exibicao}")
                print(f"✍️  Resenha: {resenha_exibicao}")
                print("-" * 50) # Linha pontilhada para separar as leituras de forma organizada
        print("=================================\n")
        
        cursor.close()
        banco.close()
    except Exception as erro:
        print(f"❌ Erro ao puxar dados: {erro}\n")

def fazer_login():
    global usuario_logado
    print("\n🔑 === LOGIN DO LEITOR ===")
    nick = input("Digite seu nickname: ")
    senha = input("Digite sua senha: ")
    
    try:
        banco = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="folheando"
        )
        cursor = banco.cursor()
        
        comando_sql = "SELECT nome FROM usuarios WHERE nome = %s AND senha = %s;"
        cursor.execute(comando_sql, (nick, senha))
        resultado = cursor.fetchone() 
        
        if resultado:
            usuario_logado = resultado[0]
            print(f"✅ Bem-vindo(a) de volta, {usuario_logado}! Login realizado com segurança.\n")
        else:
            print("❌ Usuário ou senha incorretos! Verifique os dados.\n")
            
        cursor.close()
        banco.close()
    except Exception as erro:
        print(f"❌ Erro ao tentar fazer login: {erro}\n")

def fazer_logout():
    global usuario_logado
    if usuario_logado:
        print(f"\n🚪 Logout realizado! Até logo, {usuario_logado}.\n")
        usuario_logado = None
    else:
        print("\nℹ️ Você já está no Modo Visitante!\n")

def cadastrar_novo_usuario():
    print("\n👤 === CADASTRO DE NOVO LEITOR ===")
    nick = input("Digite um nickname único: ")
    email = input("Digite seu e-mail: ")
    senha = input("Digite sua senha de acesso: ")
    
    if not nick or not email or not senha:
        print("❌ Todos os campos são obrigatórios!\n")
        return

    try:
        banco = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="folheando"
        )
        cursor = banco.cursor()
        
        cursor.execute("SELECT id FROM usuarios WHERE nome = %s;", (nick,))
        if cursor.fetchone():
            print("❌ Este nickname já está em uso! Escolha outro.\n")
            cursor.close()
            banco.close()
            return
            
        comando_sql = """
        INSERT INTO usuarios (nome, email, senha) 
        VALUES (%s, %s, %s);
        """
        cursor.execute(comando_sql, (nick, email, senha))
        banco.commit()
        
        print(f"🎉 Conta para '{nick}' criada com sucesso! Agora você já pode fazer login.\n")
        
        cursor.close()
        banco.close()
    except Exception as erro:
        print(f"❌ Erro ao cadastrar usuário: {erro}\n")

def adicionar_nova_leitura():
    print(f"\n📝 === ADICIONAR NOVA LEITURA (Logado como: {usuario_logado}) ===")
    
    try:
        banco = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="folheando"
        )
        cursor = banco.cursor()
        
        # 1. Pegar o ID do usuário logado
        cursor.execute("SELECT id FROM usuarios WHERE nome = %s;", (usuario_logado,))
        id_usuario = cursor.fetchone()[0]
        
        # 2. Listar livros cadastrados
        cursor.execute("SELECT id, titulo, autor FROM livros;")
        livros = cursor.fetchall()
        
        print("\n📚 Livros cadastrados no sistema:")
        for livro in livros:
            print(f"[ {livro[0]} ] {livro[1]} (Autor: {livro[2]})")
        print("[ 0 ] Cadastrar um NOVO livro que não está na lista")
        
        escolha_livro = int(input("\nEscolha o número do livro ou 0 para cadastrar um novo: "))
        id_livro = escolha_livro
        
        # Se escolheu cadastrar um novo livro
        if escolha_livro == 0:
            print("\n--- Cadastro de Livro Novo ---")
            titulo_livro = input("Digite o título do livro: ")
            autor_livro = input("Digite o autor do livro: ")
            genero_livro = input("Digite o gênero do livro: ")
            link_livro = input("Digite o link oficial (or deixe em branco): ")
            
            comando_cadastro_livro = """
            INSERT INTO livros (titulo, autor, genero, link_oficial) 
            VALUES (%s, %s, %s, %s);
            """
            cursor.execute(comando_cadastro_livro, (titulo_livro, autor_livro, genero_livro, link_livro))
            banco.commit()
            
            id_livro = cursor.lastrowid
            print(f"📖 Livro '{titulo_livro}' cadastrado com sucesso!")

        # 3. Listar e escolher o Status da Leitura
        cursor.execute("SELECT id, nome FROM status_leitura;")
        status_opcoes = cursor.fetchall()
        
        print("\n📌 Status da sua leitura:")
        for status in status_opcoes:
            print(f"[ {status[0]} ] {status[1]}")
            
        id_status = int(input("Escolha o status: "))
        
        # 4. Definir a Nota
        nota_input = input("Digite uma nota de 1 a 5 (ou deixe em branco caso não tenha terminado): ")
        nota = int(nota_input) if nota_input.strip() != "" else None
        
        # 5. Adicionar Resenha / Comentário escrito
        resenha = input("Escreva uma breve resenha/comentário sobre este livro (ou deixe em branco): ")
        if resenha.strip() == "":
            resenha = None
            
        # 6. Salvar na tabela 'leituras' com a nova coluna 'resenha'
        comando_leitura = """
        INSERT INTO leituras (id_usuario, id_livro, id_status, nota, resenha)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(comando_leitura, (id_usuario, id_livro, id_status, nota, resenha))
        banco.commit()
        
        print("\n✅ Sucesso! Sua leitura e resenha foram salvas e vinculadas ao seu perfil.\n")
        
        cursor.close()
        banco.close()
    except Exception as erro:
        print(f"❌ Erro ao registrar leitura: {erro}\n")


# === MENU PRINCIPAL ===
while True:
    if usuario_logado:
        print(f"✨ === SISTEMA FOLHEANDO (Usuário: {usuario_logado}) ===")
    else:
        print("✨ === SISTEMA FOLHEANDO (Modo Visitante) ===")
        
    print("[ 1 ] Ver Relatório de Leituras 📊")
    print("[ 2 ] Fazer Login 🔑")
    print("[ 3 ] Cadastrar Novo Leitor 👤")
    print("[ 4 ] Adicionar/Vincular Nova Leitura (Requer Login) 📚")
    print("[ 5 ] Fazer Logout (Sair da Conta) 🚪")
    print("[ 6 ] Sair do Sistema ❌")
    print("============================")
    
    opcao = input("Escolha uma opção: ")
    
    if opcao == '1':
        puxar_relatorio()
    elif opcao == '2':
        fazer_login()
    elif opcao == '3':
        cadastrar_novo_usuario()
    elif opcao == '4':
        if usuario_logado is None:
            print("\n🚨 Opa! Acesso negado. Você precisa fazer login primeiro (Opção 2)!\n")
        else:
            adicionar_nova_leitura()
    elif opcao == '5':
        fazer_logout()
    elif opcao == '6':
        print("\n👋 Obrigado por usar o Folheando! Até mais!")
        break
    else:
        print("\n❌ Opção inválida! Digite de 1 a 6.\n")