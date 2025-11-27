# GreenEats - Sistema de Gestão de Produtos Orgânicos

## Visão Geral
MVP do Módulo de Gestão de Produtos para a startup GreenEats, que conecta produtores locais de alimentos orgânicos a consumidores urbanos.

## Stack Tecnológica
- **Backend**: Python 3.11 + Flask
- **Frontend**: HTML5, CSS3, JavaScript Vanilla
- **Armazenamento**: Lista em memória (simulação de banco de dados para MVP)

## Estrutura do Projeto
```
/
├── app.py                 # Backend Flask - API RESTful
├── static/
│   ├── index.html         # Frontend - Interface administrativa
│   └── style.css          # Estilos CSS
├── .gitignore             # Arquivos ignorados pelo Git
└── replit.md              # Documentação do projeto
```

## Modelo de Dados - Produto

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | string (UUID) | Identificador único do produto |
| titulo | string | Nome do produto (mín. 5 caracteres) |
| descricao | string | Descrição detalhada do produto |
| preco | float | Preço em reais (deve ser > 0) |
| categoria | string | Uma das: 'Fruta', 'Legume', 'Verdura' |
| agricultor_id | integer | ID do agricultor responsável |

## API Endpoints

### Validação
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/validar-produto` | Valida dados antes de criar/atualizar |

### CRUD de Produtos
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/produtos` | Lista todos os produtos |
| POST | `/produtos` | Cria um novo produto |
| GET | `/produtos/{id}` | Busca produto por ID |
| PUT/PATCH | `/produtos/{id}` | Atualiza produto existente |
| DELETE | `/produtos/{id}` | Remove um produto |

### Auxiliares
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/categorias` | Lista categorias permitidas |
| GET | `/` | Serve página principal |

## Regras de Validação
1. **Preço**: Deve ser maior que zero
2. **Título**: Mínimo de 5 caracteres
3. **Categoria**: Deve ser uma das permitidas: Fruta, Legume, Verdura

## User Stories do MVP

### US01 - Cadastro Básico de Produtos
**Como** agricultor,
**quero** cadastrar meus produtos orgânicos com título, descrição, preço e categoria,
**para que** os consumidores possam visualizar minha oferta.

### US02 - Validação de Dados do Produto
**Como** administrador do sistema,
**quero** que o sistema valide os dados do produto antes do cadastro,
**para que** evitemos erros de contabilidade com preços negativos ou informações incompletas.

### US03 - Visualização do Catálogo
**Como** consumidor,
**quero** ver a lista de produtos disponíveis com seus preços e categorias,
**para que** possa escolher os alimentos orgânicos que desejo comprar.

## Integração Frontend-Backend

A requisição aos dados da API é feita no evento `DOMContentLoaded` do JavaScript, que é o momento ideal pois garante que:
1. O DOM está completamente carregado
2. Os elementos HTML já existem para receber os dados
3. A interface está pronta para exibir os resultados

### Exemplo de código de integração:
```javascript
async function carregarProdutos() {
    try {
        const resposta = await fetch(`${API_BASE_URL}/produtos`);
        if (!resposta.ok) {
            throw new Error(`Erro: ${resposta.status}`);
        }
        const produtos = await resposta.json();
        renderizarProdutos(produtos);
    } catch (erro) {
        console.error("Falha na integração:", erro);
    }
}

document.addEventListener('DOMContentLoaded', carregarProdutos);
```

## Como Executar
O servidor Flask inicia automaticamente na porta 5000 com o comando:
```bash
python app.py
```

## Próximas Fases
- Implementar autenticação de agricultores
- Adicionar persistência com PostgreSQL
- Criar módulo de encomendas/pedidos
- Dashboard administrativo com estatísticas
