from flask import Flask, request, jsonify, g
import random
import time
from config.config import Config  # Para acesso à chave de API
from app.services import (
    process_order_creation,
    get_order_details,
    update_order_status,
    get_all_orders,
    update_order_generic
)
from app.metrics import APP_ERRORS_TOTAL  # Para erros específicos de rotas


def init_routes(app: Flask):
    """
    Inicializa todas as rotas da aplicação Flask.
    As rotas agora usam os serviços definidos em app/services.py.
    """

    @app.route('/')
    def home():
        """Endpoint principal da API."""
        time.sleep(random.uniform(0.05, 0.15))
        return "Bem-vindo à API de Gerenciamento de Pedidos! (Protótipo Empresarial)"

    @app.route('/health')
    def health_check():
        """
        Endpoint de Health Check (verificação de saúde).
        Essencial para monitoramento de disponibilidade.
        """
        return jsonify({"status": "healthy", "message": "API de Pedidos está operacional."}), 200

    @app.route('/orders', methods=['POST'])
    def create_order():
        """
        Cria um novo pedido no sistema.
        Simula validações de dados, verificação de estoque e processamento de pagamento.
        """
        # --- Autenticação Simulada com API Key ---
        # Em um cenário real, você teria um middleware de autenticação mais robusto.
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != Config.API_KEY_REQUIRED:
            APP_ERRORS_TOTAL.labels(endpoint='/orders', error_type='unauthorized_access').inc()
            return jsonify({"error": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401

        order_data = request.json
        if not order_data:
            APP_ERRORS_TOTAL.labels(endpoint='/orders', error_type='empty_payload').inc()
            return jsonify({"error": "Requisição inválida. O corpo deve ser um JSON."}), 400

        # Chama a lógica de negócio do serviço
        result = process_order_creation(order_data)
        return jsonify(result), result.get("status_code", 500)

    @app.route('/orders/<string:order_id>', methods=['GET'])
    def get_order(order_id: str):
        """
        Busca detalhes de um pedido específico.
        """
        result = get_order_details(order_id)
        return jsonify(result), result.get("status_code", 500)

    @app.route('/orders/<string:order_id>/status', methods=['PUT'])
    def update_order(order_id: str):
        """
        Atualiza o status de um pedido existente.
        """
        update_data = request.json
        new_status = update_data.get("status")

        if not new_status:
            APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>/status', error_type='missing_status').inc()
            return jsonify({"error": "Status novo é obrigatório no corpo da requisição."}), 400

        # Chama a lógica de negócio do serviço
        result = update_order_status(order_id, new_status)
        return jsonify(result), result.get("status_code", 500)

    @app.route('/orders', methods=['GET'])
    def list_orders():
        """
        Coleta e retorna uma lista de todos os pedidos no sistema.
        """
        result = get_all_orders()
        return jsonify(result), result.get("status_code", 500)

    @app.route('/orders/<string:order_id>', methods=['PATCH'])
    def patch_order(order_id: str):
        """
        Atualiza parcialmente dados de um pedido existente (PATCH).
        Permite mudar customer_id, status, notes, etc.
        """
        # Autenticação simulada com API Key
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != Config.API_KEY_REQUIRED:
            APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>', error_type='unauthorized_access_patch').inc()
            return jsonify({"error": "Acesso não autorizado. Chave de API inválida ou ausente."}), 401

        update_data = request.json
        if not update_data:
            APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>', error_type='empty_patch_payload').inc()
            return jsonify({"error": "Requisição PATCH inválida. O corpo deve ser um JSON com dados a serem atualizados."}), 400

        result = update_order_generic(order_id, update_data)
        return jsonify(result), result.get("status_code", 500)