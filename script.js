// URL base da nossa API em Flask
const API_URL = "https://folheando-api.onrender.com";

// Variável para guardar o usuário logado na sessão do navegador
let usuarioLogado = null;

// Executa assim que a página é carregada
document.addEventListener("DOMContentLoaded", () => {
    carregarRelatorio();
});

// 1. FUNÇÃO PARA NAVEGAR ENTRE AS SEÇÕES (TELAS)
function mostrarSecao(idSecao) {
    const secoes = document.querySelectorAll('.tela-secao');
    secoes.forEach(secao => {
        secao.classList.add('oculto');
    });

    const secaoAtiva = document.getElementById(idSecao);
    if (secaoAtiva) {
        secaoAtiva.classList.remove('oculto');
    }

    if (idSecao === 'secao-relatorio') {
        carregarRelatorio();
    } else if (idSecao === 'secao-nova-leitura') {
        carregarLivrosNoSelect();
    }
}

// 2. BUSCAR E EXIBIR O RELATÓRIO DE LEITURAS (Atualizado com Formatação de Data!)
async function carregarRelatorio() {
    const listaLeituras = document.getElementById('lista-leituras');
    listaLeituras.innerHTML = '<p class="carregando">Carregando leituras...</p>';

    const filtroTipo = document.getElementById('filtro-tipo').value;
    let url = `${API_URL}/relatorio`;

    if (filtroTipo === 'meu' && usuarioLogado) {
        url += `?usuario=${encodeURIComponent(usuarioLogado.nome)}`;
    }

    try {
        const resposta = await fetch(url);
        const dados = await resposta.json();

        if (!resposta.ok) {
            throw new Error(dados.erro || 'Erro ao carregar dados do servidor.');
        }

        listaLeituras.innerHTML = '';

        if (dados.length === 0) {
            listaLeituras.innerHTML = '<p class="carregando">Nenhuma leitura registrada ainda. Seja o primeiro!</p>';
            return;
        }

        dados.forEach(leitura => {
            const cartao = document.createElement('div');
            cartao.className = 'cartao-leitura';

            const nota = leitura.nota ? `⭐ ${leitura.nota}/5` : 'Sem nota';
            const resenha = leitura.resenha ? `<p class="resenha-texto">✍️ "${leitura.resenha}"</p>` : '';

            // --- CÓDIGO NOVO: Tratamento e Formatação da Data ---
            let dataFormatada = "";
            if (leitura.data_registro) {
                const dataObj = new Date(leitura.data_registro);
                // Converte a data para o padrão de data do Brasil: DD/MM/AAAA
                dataFormatada = dataObj.toLocaleDateString('pt-BR');
            }
            // ----------------------------------------------------

            cartao.innerHTML = `
                <div class="leitura-topo">
                    <span class="leitor-nome">👤 ${leitura.leitor}</span>
                    <!-- Mostramos a data ao lado da nota no cabeçalho do cartão -->
                    <span>${nota} | 📅 ${dataFormatada}</span>
                </div>
                <h3 class="leitura-titulo">${leitura.titulo}</h3>
                <div class="leitura-info">
                    <span class="status-badge">${leitura.status}</span>
                </div>
                ${resenha}
            `;
            listaLeituras.appendChild(cartao);
        });

    } catch (erro) {
        listaLeituras.innerHTML = `<p class="carregando" style="color: red;">❌ Não foi possível carregar as leituras: ${erro.message}</p>`;
    }
}

// 3. FAZER LOGIN
async function realizarLogin(event) {
    event.preventDefault();

    const nick = document.getElementById('login-nick').value;
    const senha = document.getElementById('login-senha').value;

    try {
        const resposta = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nick, senha })
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            alert(dados.erro || 'Erro ao fazer login.');
            return;
        }

        usuarioLogado = dados.usuario;
        document.getElementById('usuario-status').innerText = `Melhor leitor(a): ${usuarioLogado.nome} 📖`;
        
        document.getElementById('btn-logout').classList.remove('oculto');
        document.getElementById('btn-nav-login').classList.add('oculto');
        document.getElementById('btn-nav-cadastro').classList.add('oculto');
        document.getElementById('btn-nav-nova-leitura').classList.remove('oculto');
        document.getElementById('filtro-relatorio-container').classList.remove('oculto');

        alert(`Seja muito bem-vinda, ${usuarioLogado.nome}!`);
        document.getElementById('form-login').reset();
        mostrarSecao('secao-relatorio');

    } catch (erro) {
        alert('Erro de conexão com o servidor Back-end.');
    }
}

// 4. FAZER LOGOUT
function deslogar() {
    usuarioLogado = null;
    document.getElementById('usuario-status').innerText = 'Modo Visitante 👤';
    
    document.getElementById('btn-logout').classList.add('oculto');
    document.getElementById('btn-nav-login').classList.remove('oculto');
    document.getElementById('btn-nav-cadastro').classList.remove('oculto');
    document.getElementById('btn-nav-nova-leitura').classList.add('oculto');
    document.getElementById('filtro-relatorio-container').classList.add('oculto');
    document.getElementById('filtro-tipo').value = 'todos';

    alert('Até logo! Você voltou para o modo visitante.');
    mostrarSecao('secao-relatorio');
}

// 5. CADASTRAR NOVO USUÁRIO
async function realizarCadastro(event) {
    event.preventDefault();

    const nick = document.getElementById('cadastro-nick').value;
    const email = document.getElementById('cadastro-email').value;
    const senha = document.getElementById('cadastro-senha').value;

    try {
        const resposta = await fetch(`${API_URL}/cadastrar_usuario`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nick, email, senha })
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            alert(dados.erro || 'Erro ao cadastrar.');
            return;
        }

        alert(dados.mensagem);
        document.getElementById('form-cadastro').reset();
        mostrarSecao('secao-login');

    } catch (erro) {
        alert('Erro ao se conectar com o servidor.');
    }
}

// 6. BUSCAR LIVROS CADASTRADOS PARA O MENU SELEÇÃO
async function carregarLivrosNoSelect() {
    const selectLivros = document.getElementById('leitura-livro');
    selectLivros.innerHTML = '<option value="">Carregando livros...</option>';

    try {
        const resposta = await fetch(`${API_URL}/livros`);
        const livros = await resposta.json();

        selectLivros.innerHTML = '<option value="">-- Escolha um livro --</option>';
        
        livros.forEach(livro => {
            const opcao = document.createElement('option');
            opcao.value = {id: livro.id}.id; // Mantendo o padrão do id obtido
            opcao.innerText = `${livro.titulo} (Autor: ${livro.autor})`;
            selectLivros.appendChild(opcao);
        });

        const opcaoNovo = document.createElement('option');
        opcaoNovo.value = "0";
        opcaoNovo.innerText = "➕ Cadastrar um NOVO livro...";
        selectLivros.appendChild(opcaoNovo);

    } catch (erro) {
        selectLivros.innerHTML = '<option value="">Erro ao carregar livros</option>';
    }
}

// Mostrar/Esconder os campos extras de livro novo dependendo da escolha
function verificarNovoLivro() {
    const select = document.getElementById('leitura-livro');
    const containerNovoLivro = document.getElementById('campos-novo-livro');
    const inputsNovos = containerNovoLivro.querySelectorAll('input');

    if (select.value === "0") {
        containerNovoLivro.classList.remove('oculto');
        inputsNovos.forEach(input => input.required = true);
    } else {
        containerNovoLivro.classList.add('oculto');
        inputsNovos.forEach(input => {
            input.required = false;
            input.value = '';
        });
    }
}

// 7. SALVAR NOVA LEITURA
async function salvarLeitura(event) {
    event.preventDefault();

    if (!usuarioLogado) {
        alert("Erro: Você precisa estar logado para salvar uma leitura.");
        return;
    }

    const id_livro = document.getElementById('leitura-livro').value;
    const id_status = document.getElementById('leitura-status').value;
    const nota = document.getElementById('leitura-nota').value || null;
    const resenha = document.getElementById('leitura-resenha').value || null;

    const corpoRequisicao = {
        id_usuario: usuarioLogado.id,
        id_livro: id_livro,
        id_status: id_status,
        nota: nota,
        resenha: resenha
    };

    if (id_livro === "0") {
        corpoRequisicao.novo_titulo = document.getElementById('novo-titulo').value;
        corpoRequisicao.novo_autor = document.getElementById('novo-autor').value;
        corpoRequisicao.novo_genero = document.getElementById('novo-genero').value;
    }

    try {
        const resposta = await fetch(`${API_URL}/adicionar_leitura`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(corpoRequisicao)
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            alert(dados.erro || 'Erro ao registrar leitura.');
            return;
        }

        alert("🎉 Leitura registrada com sucesso!");
        document.getElementById('form-leitura').reset();
        document.getElementById('campos-novo-livro').classList.add('oculto');
        mostrarSecao('secao-relatorio');

    } catch (erro) {
        alert('Erro de conexão ao salvar leitura.');
    }
}