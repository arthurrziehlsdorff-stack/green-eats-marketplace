from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', 'Produtos')

airtable_table = None
airtable_enabled = False

produtos_local = [
    {
        "id": "a1b2c3d4",
        "titulo": "Tomate Cereja Organico",
        "descricao": "Tomates cereja doces, perfeitos para saladas.",
        "preco": 12.50,
        "categoria": "Legume",
        "agricultor_id": 1
    },
    {
        "id": "e5f6g7h8",
        "titulo": "Alface Crespa",
        "descricao": "Alface fresca, colhida na manha.",
        "preco": 4.99,
        "categoria": "Verdura",
        "agricultor_id": 2
    },
    {
        "id": "i9j0k1l2",
        "titulo": "Banana Prata Organica",
        "descricao": "Bananas maduras e doces, cultivadas sem agrotoxicos.",
        "preco": 8.90,
        "categoria": "Fruta",
        "agricultor_id": 1
    }
]

def init_airtable():
    global airtable_table, airtable_enabled
    if AIRTABLE_API_KEY and AIRTABLE_BASE_ID:
        try:
            from pyairtable import Api
            api = Api(AIRTABLE_API_KEY)
            airtable_table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
            airtable_table.all()
            airtable_enabled = True
            print("Airtable conectado com sucesso!")
        except Exception as e:
            print("Airtable nao disponivel, usando armazenamento local. Erro: " + str(e))
            airtable_enabled = False
    else:
        print("Credenciais Airtable nao configuradas, usando armazenamento local.")
        airtable_enabled = False

CATEGORIAS_PERMITIDAS = ['Fruta', 'Legume', 'Verdura']

def validar_dados_produto(dados_produto):
    erros = []
    
    try:
        preco = float(dados_produto.get('preco', 0))
        if preco <= 0:
            erros.append("O preco deve ser maior que zero.")
    except (ValueError, TypeError):
        erros.append("O preco deve ser um valor numerico valido.")

    titulo = dados_produto.get('titulo', '')
    if len(str(titulo).strip()) < 5:
        erros.append("O titulo do produto deve ter no minimo 5 caracteres.")
        
    categoria = dados_produto.get('categoria', '')
    if categoria not in CATEGORIAS_PERMITIDAS:
        erros.append("A categoria '" + str(categoria) + "' nao e permitida. Use: " + ', '.join(CATEGORIAS_PERMITIDAS) + ".")
    
    return erros

def airtable_record_to_produto(record):
    fields = record.get('fields', {})
    return {
        "id": record.get('id'),
        "titulo": fields.get('Titulo', fields.get('titulo', '')),
        "descricao": fields.get('Descricao', fields.get('descricao', '')),
        "preco": float(fields.get('Preco', fields.get('preco', 0)) or 0),
        "categoria": fields.get('Categoria', fields.get('categoria', '')),
        "agricultor_id": fields.get('Agricultor_id', fields.get('agricultor_id', 99))
    }

def produto_to_airtable_fields(dados):
    return {
        "Titulo": dados.get('titulo', ''),
        "Descricao": dados.get('descricao', ''),
        "Preco": float(dados.get('preco', 0)),
        "Categoria": dados.get('categoria', ''),
        "Agricultor_id": dados.get('agricultor_id', 99)
    }

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/validar-produto', methods=['POST'])
def validar_produto():
    dados_produto = request.get_json()
    
    if not dados_produto:
        return jsonify({"valido": False, "erros": ["Dados do produto nao fornecidos."]}), 400
    
    erros = validar_dados_produto(dados_produto)

    if erros:
        return jsonify({"valido": False, "erros": erros}), 400
    
    return jsonify({"valido": True, "mensagem": "Produto validado com sucesso!"}), 200

@app.route('/produtos', methods=['GET'])
def listar_produtos():
    if airtable_enabled and airtable_table:
        try:
            records = airtable_table.all()
            produtos = [airtable_record_to_produto(r) for r in records]
            return jsonify(produtos), 200
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
    else:
        return jsonify(produtos_local), 200

@app.route('/produtos', methods=['POST'])
def criar_produto():
    global produtos_local
    dados_produto = request.get_json()
    
    if not dados_produto:
        return jsonify({"valido": False, "erros": ["Dados do produto nao fornecidos."]}), 400
    
    erros = validar_dados_produto(dados_produto)
    if erros:
        return jsonify({"valido": False, "erros": erros}), 400
    
    if airtable_enabled and airtable_table:
        try:
            campos = produto_to_airtable_fields(dados_produto)
            record = airtable_table.create(campos)
            produto = airtable_record_to_produto(record)
            return jsonify(produto), 201
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
    else:
        import uuid
        novo_produto = {
            "id": str(uuid.uuid4()),
            "titulo": dados_produto['titulo'],
            "descricao": dados_produto.get('descricao', ''),
            "preco": float(dados_produto['preco']),
            "categoria": dados_produto['categoria'],
            "agricultor_id": dados_produto.get('agricultor_id', 99)
        }
        produtos_local.append(novo_produto)
        return jsonify(novo_produto), 201

@app.route('/produtos/<string:id>', methods=['GET'])
def obter_produto(id):
    if airtable_enabled and airtable_table:
        try:
            record = airtable_table.get(id)
            produto = airtable_record_to_produto(record)
            return jsonify(produto), 200
        except Exception:
            return jsonify({"mensagem": "Produto nao encontrado"}), 404
    else:
        produto = next((p for p in produtos_local if p["id"] == id), None)
        if produto:
            return jsonify(produto), 200
        return jsonify({"mensagem": "Produto nao encontrado"}), 404

@app.route('/produtos/<string:id>', methods=['PUT', 'PATCH'])
def atualizar_produto(id):
    global produtos_local
    dados_atualizacao = request.get_json()
    
    if not dados_atualizacao:
        return jsonify({"valido": False, "erros": ["Dados de atualizacao nao fornecidos."]}), 400
    
    if airtable_enabled and airtable_table:
        try:
            record_atual = airtable_table.get(id)
            fields_atuais = record_atual.get('fields', {})
            
            dados_para_validar = {
                "titulo": dados_atualizacao.get('titulo', fields_atuais.get('Titulo', fields_atuais.get('titulo', ''))),
                "preco": dados_atualizacao.get('preco', fields_atuais.get('Preco', fields_atuais.get('preco', 0))),
                "categoria": dados_atualizacao.get('categoria', fields_atuais.get('Categoria', fields_atuais.get('categoria', '')))
            }

            erros = validar_dados_produto(dados_para_validar)
            if erros:
                return jsonify({"valido": False, "erros": erros}), 400
            
            campos_atualizar = {}
            if 'titulo' in dados_atualizacao:
                campos_atualizar['Titulo'] = dados_atualizacao['titulo']
            if 'descricao' in dados_atualizacao:
                campos_atualizar['Descricao'] = dados_atualizacao['descricao']
            if 'categoria' in dados_atualizacao:
                campos_atualizar['Categoria'] = dados_atualizacao['categoria']
            if 'preco' in dados_atualizacao:
                campos_atualizar['Preco'] = float(dados_atualizacao['preco'])
            
            record = airtable_table.update(id, campos_atualizar)
            produto = airtable_record_to_produto(record)
            return jsonify(produto), 200
        except Exception:
            return jsonify({"mensagem": "Produto nao encontrado"}), 404
    else:
        try:
            produto_index = next(i for i, p in enumerate(produtos_local) if p["id"] == id)
        except StopIteration:
            return jsonify({"mensagem": "Produto nao encontrado"}), 404

        produto_atual = produtos_local[produto_index]
        
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
    global produtos_local
    
    if airtable_enabled and airtable_table:
        try:
            airtable_table.delete(id)
            return '', 204
        except Exception:
            return jsonify({"mensagem": "Produto nao encontrado"}), 404
    else:
        tamanho_original = len(produtos_local)
        produtos_local = [p for p in produtos_local if p["id"] != id]
        
        if len(produtos_local) < tamanho_original:
            return '', 204
        return jsonify({"mensagem": "Produto nao encontrado"}), 404

@app.route('/categorias', methods=['GET'])
def listar_categorias():
    return jsonify(CATEGORIAS_PERMITIDAS), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "airtable_enabled": airtable_enabled,
        "storage": "Airtable" if airtable_enabled else "Local (memoria)"
    }), 200

init_airtable()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
