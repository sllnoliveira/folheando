// URL base da nossa API em Flask
const API_URL = "https://folheando.onrender.com";


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
    } else if (idSecao === 'secao-biblioteca') {
        carregarBiblioteca();
    } else if (idSecao === 'secao-nova-leitura') {
        carregarLivrosNoSelect();
    }
}

// 2. BUSCAR E EXIBIR O RELATÓRIO DE LEITURAS
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

            let dataFormatada = "";
            if (leitura.data_registro) {
                const dataObj = new Date(leitura.data_registro);
                dataFormatada = dataObj.toLocaleDateString('pt-BR');
            }

            let botaoEditar = "";
            if (usuarioLogado && leitura.leitor === usuarioLogado.nome) {
                botaoEditar = `<button class="btn-secundario" onclick="abrirModalEdicao(${leitura.id}, '${leitura.status}')">✏️ Atualizar Leitura</button>`;
            }

            cartao.innerHTML = `
                <div class="leitura-topo">
                    <span class="leitor-nome">👤 ${leitura.leitor}</span>
                    <span>${nota} | 📅 ${dataFormatada}</span>
                </div>
                <h3 class="leitura-titulo">${leitura.titulo}</h3>
                <div class="leitura-info">
                    <span class="status-badge">${leitura.status}</span>
                </div>
                ${resenha}
                <div style="margin-top: 10px;">${botaoEditar}</div>
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
            opcao.value = livro.id;
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
        corpoRequisicao.novo_link = document.getElementById('novo-link').value;
    } else {
        corpoRequisicao.novo_titulo = null;
        corpoRequisicao.novo_autor = null;
        corpoRequisicao.novo_genero = null;
        corpoRequisicao.novo_link = null;
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
        alert('Erro de conexão ao salvar leitura: ' + erro.message);
    }
}

function verificarStatusLeitura() {
    const selectStatus = document.getElementById('leitura-status');
    const blocoAvaliacao = document.getElementById('bloco-avaliacao');
    const inputNota = document.getElementById('leitura-nota');
    const inputResenha = document.getElementById('leitura-resenha');

    if (!selectStatus || !blocoAvaliacao) return;

    if (selectStatus.value === "2") {
        blocoAvaliacao.style.display = "block";
        inputNota.required = true;
        inputResenha.required = true;

        let avisoChamada = document.getElementById('aviso-chamada-avaliacao');
        if (!avisoChamada) {
            avisoChamada = document.createElement('div');
            avisoChamada.id = 'aviso-chamada-avaliacao';
            avisoChamada.style.color = '#d63384';
            avisoChamada.style.fontWeight = 'bold';
            avisoChamada.style.margin = '10px 0';
            avisoChamada.innerHTML = '✨ Oba! Já que terminou de ler, qual é a sua nota e resenha para este livro?';
            blocoAvaliacao.insertBefore(avisoChamada, blocoAvaliacao.firstChild);
        }
    } else {
        blocoAvaliacao.style.display = "none";
        inputNota.required = false;
        inputResenha.required = false;
        inputNota.value = '';
        inputResenha.value = '';

        const avisoChamada = document.getElementById('aviso-chamada-avaliacao');
        if (avisoChamada) {
            avisoChamada.remove();
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const selectStatus = document.getElementById('leitura-status');
    if (selectStatus) {
        selectStatus.addEventListener('change', verificarStatusLeitura);
        verificarStatusLeitura();
    }
});

async function abrirModalEdicao(idLeitura, statusAtual) {
    let novoStatusId = prompt("Digite o novo ID do status (1: Lendo, 2: Lido, 3: Quero Ler, 4: Abandonado):", "2");
    if (!novoStatusId) return;

    let novaNota = prompt("Digite a nova nota (1 a 5):", "5");
    let novaResenha = prompt("Digite a nova resenha:", "");

    try {
        const resposta = await fetch(`${API_URL}/atualizar_leitura/${idLeitura}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id_status: parseInt(novoStatusId),
                nota: novaNota ? parseInt(novaNota) : null,
                resenha: novaResenha
            })
        });

        const resultado = await resposta.json();

        if (resposta.ok) {
            alert(resultado.mensagem);
            carregarRelatorio();
        } else {
            alert("Erro: " + resultado.erro);
        }
    } catch (erro) {
        console.error("Erro na requisição:", erro);
        alert("Não foi possível conectar ao servidor.");
    }
}

// 7. BUSCAR E EXIBIR A BIBLIOTECA DE LIVROS (Com Média de Notas, Resenhas e Restrição de Links)
async function carregarBiblioteca() {
    const listaBiblioteca = document.getElementById('lista-biblioteca');
    listaBiblioteca.innerHTML = '<p class="carregando">Carregando livros da biblioteca...</p>';

    try {
        const resposta = await fetch(`${API_URL}/livros`);
        const livros = await resposta.json();

        if (!resposta.ok) {
            throw new Error(livros.erro || 'Erro ao carregar a biblioteca.');
        }

        listaBiblioteca.innerHTML = '';

        if (livros.length === 0) {
            listaBiblioteca.innerHTML = '<p class="carregando">Nenhum livro cadastrado na biblioteca ainda.</p>';
            return;
        }

        livros.forEach(livro => {
            const cartao = document.createElement('div');
            cartao.className = 'cartao-leitura';

            let mediaFormatada = "Sem avaliações";
            if (livro.media_notas && parseFloat(livro.media_notas) > 0) {
                mediaFormatada = `⭐ ${parseFloat(livro.media_notas).toFixed(1)} / 5`;
            }

            let conteudoExtra = "";
            if (usuarioLogado && livro.link) {
                conteudoExtra = `<a href="${livro.link}" target="_blank" class="btn-secundario" style="display: inline-block; margin-top: 10px; text-decoration: none; text-align: center;">🔗 Acessar Livro / PDF</a>`;
            } else if (usuarioLogado && !livro.link) {
                conteudoExtra = `<p style="font-size: 0.9em; color: #777; margin-top: 10px;">Sem link externo cadastrado</p>`;
            } else {
                conteudoExtra = `
                    <div style="margin-top: 10px; padding: 8px; background-color: #fdf2f4; border-radius: 5px; text-align: center;">
                        <p style="font-size: 0.8em; color: #d63384; margin-bottom: 4px;">🔒 Faça login para ver os links de leitura!</p>
                        <button class="btn-secundario" onclick="mostrarSecao('secao-login')" style="font-size: 0.75em; padding: 4px 8px;">Entrar</button>
                    </div>
                `;
            }

            let secaoResenhas = "";
            if (livro.resenhas) {
                const listaResenhas = livro.resenhas.split('|||');
                let itensHtml = listaResenhas.map(r => `<p style="font-size: 0.85em; margin: 5px 0; background: #fff; padding: 6px; border-radius: 4px; border-left: 3px solid #d63384;">✍️ "${r}"</p>`).join('');
                
                secaoResenhas = `
                    <details style="margin-top: 10px; font-size: 0.9em; cursor: pointer;">
                        <summary style="font-weight: bold; color: #d63384;">💬 Ver Avaliações e Resenhas (${listaResenhas.length})</summary>
                        <div style="margin-top: 8px; max-height: 120px; overflow-y: auto;">
                            ${itensHtml}
                        </div>
                    </details>
                `;
            } else {
                secaoResenhas = `<p style="font-size: 0.85em; color: #888; margin-top: 10px;">💬 Nenhuma resenha cadastrada ainda.</p>`;
            }

            cartao.innerHTML = `
                <div class="leitura-topo">
                    <span class="leitor-nome">📖 Gênero: ${livro.genero || 'Não informado'}</span>
                    <span style="font-weight: bold; color: #e65c00;">${mediaFormatada}</span>
                </div>
                <h3 class="leitura-titulo">${livro.titulo}</h3>
                <div class="leitura-info">
                    <span class="status-badge">Autor: ${livro.autor}</span>
                </div>
                ${secaoResenhas}
                ${conteudoExtra}
            `;
            listaBiblioteca.appendChild(cartao);
        });

    } catch (erro) {
        listaBiblioteca.innerHTML = `<p class="carregando" style="color: red;">❌ Não foi possível carregar a biblioteca: ${erro.message}</p>`;
    }
}