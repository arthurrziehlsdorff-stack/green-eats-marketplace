from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import uuid
import os

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

produtos = [
    {
        "id": "a1b2c3d4",
        "titulo": "Tomate Cereja Orgânico",
        "descricao": "Tomates cereja doces, perfeitos para saladas.",
        "preco": 12.50,
        "categoria": "Legume",
        "agricultor_id": 1
    },
    {
        "id": "e5f6g7h8",
        "titulo": "Alface Crespa",
        "descricao": "Alface fresca, colhida na manhã.",
        "preco": 4.99,
        "categoria": "Verdura",
        "agricultor_id": 2
    },
    {
        "id": "i9j0k1l2",
        "titulo": "Banana Prata Orgânica",
        "descricao": "Bananas maduras e doces, cultivadas sem agrotóxicos.",
        "preco": 8.90,
        "categoria": "Fruta",
        "agricultor_id": 1
    }
]

CATEGORIAS_PERMITIDAS = ['Fruta', 'Legume', 'Verdura']

def validar_dados_produto(dados_produto):
    """Função auxiliar para validar os dados do produto."""
    erros = []
    
    try:
        preco = float(dados_produto.get('preco', 0))
        if preco <= 0:
            erros.append("O preço deve ser maior que zero.")
    except (ValueError, TypeError):
        erros.append("O preço deve ser um valor numérico válido.")

    titulo = dados_produto.get('titulo', '')
    if len(str(titulo).strip()) < 5:
        erros.append("O título do produto deve ter no mínimo 5 caracteres.")
        
    categoria = dados_produto.get('categoria', '')
    if categoria not in CATEGORIAS_PERMITIDAS:
        erros.append(f"A categoria '{categoria}' não é permitida. Use: {', '.join(CATEGORIAS_PERMITIDAS)}.")
    
    return erros

@app.route('/')
def index():
    """Serve a página principal."""
    return send_from_directory('static', 'index.html')

@app.route('/validar-produto', methods=['POST'])
def validar_produto():
    """Endpoint para validar os dados do produto antes de criar/atualizar."""
    dados_produto = request.get_json()
    
    if not dados_produto:
        return jsonify({"valido": False, "erros": ["Dados do produto não fornecidos."]}), 400
    
    erros = validar_dados_produto(dados_produto)

    if erros:
        return jsonify({"valido": False, "erros": erros}), 400
    
    return jsonify({"valido": True, "mensagem": "Produto validado com sucesso!"}), 200

@app.route('/produtos', methods=['GET'])
def listar_produtos():
    """Lista todos os produtos (CRUD: Read All)."""
    return jsonify(produtos), 200

@app.route('/produtos', methods=['POST'])
def criar_produto():
    """Cria um novo produto após validação (CRUD: Create)."""
    dados_produto = request.get_json()
    
    if not dados_produto:
        return jsonify({"valido": False, "erros": ["Dados do produto não fornecidos."]}), 400
    
    erros = validar_dados_produto(dados_produto)
    if erros:
        return jsonify({"valido": False, "erros": erros}), 400
        
    novo_produto = {
        "id": str(uuid.uuid4()),
        "titulo": dados_produto['titulo'],
        "descricao": dados_produto.get('descricao', ''),
        "preco": float(dados_produto['preco']),
        "categoria": dados_produto['categoria'],
        "agricultor_id": dados_produto.get('agricultor_id', 99)
    }
    
    produtos.append(novo_produto)
    return jsonify(novo_produto), 201

@app.route('/produtos/<string:id>', methods=['GET'])
def obter_produto(id):
    """Busca um produto pelo ID (CRUD: Read One)."""
    produto = next((p for p in produtos if p["id"] == id), None)
    if produto:
        return jsonify(produto), 200
    return jsonify({"mensagem": "Produto não encontrado"}), 404

@app.route('/produtos/<string:id>', methods=['PUT', 'PATCH'])
def atualizar_produto(id):
    """Atualiza um produto existente (CRUD: Update)."""
    dados_atualizacao = request.get_json()
    
    if not dados_atualizacao:
        return jsonify({"valido": False, "erros": ["Dados de atualização não fornecidos."]}), 400
    
    try:
        produto_index = next(i for i, p in enumerate(produtos) if p["id"] == id)
    except StopIteration:
        return jsonify({"mensagem": "Produto não encontrado"}), 404

    produto_atual = produtos[produto_index]
    
    dados_para_validar = {
        "titulo": dados_atualizacao.get('titulo', produto_atual['titulo']),
        "preco": dados_atualizacao.get('preco', produto_atual['preco']),
        "categoria": dados_atualizacao.get('categoria', produto_atual['categoria'])
    }

    erros = validar_dados_produto(dados_para_validar)
    if erros:
        return jsonify({"valido": False, "erros": erros}), 400
    
    for key in ['titulo', 'descricao', 'preco', 'categoria']:
        if key in dados_atualizacao:
            if key == 'preco':
                produto_atual[key] = float(dados_atualizacao[key])
            else:
                produto_atual[key] = dados_atualizacao[key]
    
    return jsonify(produto_atual), 200

@app.route('/produtos/<string:id>', methods=['DELETE'])
def deletar_produto(id):
    """Deleta um produto (CRUD: Delete)."""
    global produtos
    tamanho_original = len(produtos)
    produtos = [p for p in produtos if p["id"] != id]
    
    if len(produtos) < tamanho_original:
        return '', 204
    return jsonify({"mensagem": "Produto não encontrado"}), 404

@app.route('/categorias', methods=['GET'])
def listar_categorias():
    """Lista todas as categorias permitidas."""
    return jsonify(CATEGORIAS_PERMITIDAS), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
