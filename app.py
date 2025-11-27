from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pyairtable import Api
import os

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', 'Produtos')

api = None
table = None

def get_airtable_table():
    global api, table
    if table is None:
        if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
            raise Exception("Credenciais do Airtable nao configuradas. Configure AIRTABLE_API_KEY e AIRTABLE_BASE_ID.")
        api = Api(AIRTABLE_API_KEY)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
    return table

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
        "titulo": fields.get('titulo', ''),
        "descricao": fields.get('descricao', ''),
        "preco": float(fields.get('preco', 0)),
        "categoria": fields.get('categoria', ''),
        "agricultor_id": fields.get('agricultor_id', 99)
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
    try:
        airtable = get_airtable_table()
        records = airtable.all()
        produtos = [airtable_record_to_produto(r) for r in records]
        return jsonify(produtos), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/produtos', methods=['POST'])
def criar_produto():
    dados_produto = request.get_json()
    
    if not dados_produto:
        return jsonify({"valido": False, "erros": ["Dados do produto nao fornecidos."]}), 400
    
    erros = validar_dados_produto(dados_produto)
    if erros:
        return jsonify({"valido": False, "erros": erros}), 400
    
    try:
        airtable = get_airtable_table()
        
        novo_registro = {
            "titulo": dados_produto['titulo'],
            "descricao": dados_produto.get('descricao', ''),
            "preco": float(dados_produto['preco']),
            "categoria": dados_produto['categoria'],
            "agricultor_id": dados_produto.get('agricultor_id', 99)
        }
        
        record = airtable.create(novo_registro)
        produto = airtable_record_to_produto(record)
        return jsonify(produto), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/produtos/<string:id>', methods=['GET'])
def obter_produto(id):
    try:
        airtable = get_airtable_table()
        record = airtable.get(id)
        produto = airtable_record_to_produto(record)
        return jsonify(produto), 200
    except Exception as e:
        return jsonify({"mensagem": "Produto nao encontrado"}), 404

@app.route('/produtos/<string:id>', methods=['PUT', 'PATCH'])
def atualizar_produto(id):
    dados_atualizacao = request.get_json()
    
    if not dados_atualizacao:
        return jsonify({"valido": False, "erros": ["Dados de atualizacao nao fornecidos."]}), 400
    
    try:
        airtable = get_airtable_table()
        
        record_atual = airtable.get(id)
        fields_atuais = record_atual.get('fields', {})
        
        dados_para_validar = {
            "titulo": dados_atualizacao.get('titulo', fields_atuais.get('titulo', '')),
            "preco": dados_atualizacao.get('preco', fields_atuais.get('preco', 0)),
            "categoria": dados_atualizacao.get('categoria', fields_atuais.get('categoria', ''))
        }

        erros = validar_dados_produto(dados_para_validar)
        if erros:
            return jsonify({"valido": False, "erros": erros}), 400
        
        campos_atualizar = {}
        for key in ['titulo', 'descricao', 'categoria']:
            if key in dados_atualizacao:
                campos_atualizar[key] = dados_atualizacao[key]
        if 'preco' in dados_atualizacao:
            campos_atualizar['preco'] = float(dados_atualizacao['preco'])
        
        record = airtable.update(id, campos_atualizar)
        produto = airtable_record_to_produto(record)
        return jsonify(produto), 200
    except Exception as e:
        return jsonify({"mensagem": "Produto nao encontrado"}), 404

@app.route('/produtos/<string:id>', methods=['DELETE'])
def deletar_produto(id):
    try:
        airtable = get_airtable_table()
        airtable.delete(id)
        return '', 204
    except Exception as e:
        return jsonify({"mensagem": "Produto nao encontrado"}), 404

@app.route('/categorias', methods=['GET'])
def listar_categorias():
    return jsonify(CATEGORIAS_PERMITIDAS), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
