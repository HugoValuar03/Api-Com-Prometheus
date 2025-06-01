import time
import random
import copy  # Importar para fazer cópias de dados

from app.metrics import (
    ORDERS_CREATED_TOTAL,
    ORDER_PROCESSING_LATENCY,
    APP_ERRORS_TOTAL,
    INVENTORY_LEVEL_GAUGE
)
from config.config import Config

# Banco de dados simulado de produtos e estoque
_products_db = {
    "Mouse": {"name": "Mouse", "stock": 100, "price": 59.99},  # Atualizado name
    "Teclado": {"name": "Teclado", "stock": 250, "price": 249.99},  # Atualizado name
    "Monitor": {"name": "Monitor", "stock": 200, "price": 259.99},  # Atualizado name
    "Cadeira": {"name": "Cadeira", "stock": 150, "price": 279.99},
    "Notebook": {"name": "Notebook", "stock": 300, "price": 1500.00},
}

# Novo: Banco de dados simulado para armazenar pedidos
_orders_db = {}

def initialize_inventory_gauges():
    for product_id, data in _products_db.items():
        INVENTORY_LEVEL_GAUGE.labels(product_id=product_id).set(data["stock"])


def process_order_creation(order_data: dict) -> dict:
    start_time = time.time()
    order_status = "failure"
    payment_status = "denied"
    error_message = None
    order_id = None  # Inicializa order_id

    try:
        if not order_data.get("items") or not isinstance(order_data["items"], list):
            error_message = "Dados do pedido inválidos: 'items' é obrigatório e deve ser uma lista."
            APP_ERRORS_TOTAL.labels(endpoint='/orders', error_type='validation_error').inc()
            return {"success": False, "message": error_message, "status_code": 400}

        customer_id = order_data.get("customer_id", "UNKNOWN_CUSTOMER")
        total_amount = 0.0
        processed_items = []

        for item_data in order_data["items"]:
            product_id = item_data.get("product_id")
            quantity = item_data.get("quantity", 0)

            if product_id not in _products_db:
                error_message = f"Produto '{product_id}' não encontrado."
                APP_ERRORS_TOTAL.labels(endpoint='/orders', error_type='product_not_found').inc()
                return {"success": False, "message": error_message, "status_code": 404}

            if quantity <= 0:
                error_message = f"Quantidade inválida ({quantity}) para o produto '{product_id}'."
                APP_ERRORS_TOTAL.labels(endpoint='/orders', error_type='invalid_quantity').inc()
                return {"success": False, "message": error_message, "status_code": 400}

            if random.random() < Config.STOCK_VALIDATION_FAILURE_CHANCE:
                error_message = f"Estoque insuficiente para o produto '{product_id}' (simulado)."
                APP_ERRORS_TOTAL.labels(endpoint='/orders', error_type='insufficient_stock_simulated').inc()
                return {"success": False, "message": error_message, "status_code": 400}

            # Simula decremento de estoque APENAS SE FOR PRODUTO VÁLIDO E QUANTIDADE OK
            if _products_db[product_id]["stock"] < quantity:  # Verificação adicional de estoque
                error_message = f"Estoque real insuficiente para o produto '{product_id}'."
                APP_ERRORS_TOTAL.labels(endpoint='/orders', error_type='real_insufficient_stock').inc()
                return {"success": False, "message": error_message, "status_code": 400}

            _products_db[product_id]["stock"] -= quantity
            INVENTORY_LEVEL_GAUGE.labels(product_id=product_id).set(_products_db[product_id]["stock"])

            total_amount += _products_db[product_id]["price"] * quantity
            processed_items.append({
                "product_id": product_id,
                "name": _products_db[product_id]["name"],  # Adiciona o nome do produto
                "quantity": quantity,
                "price_unit": _products_db[product_id]["price"]
            })

        time.sleep(random.uniform(0.1, 0.4))
        if random.random() < Config.PAYMENT_GATEWAY_FAILURE_CHANCE:
            payment_status = "denied"
            order_status = "failure"
            error_message = "Pagamento negado pelo gateway (simulado)."
            APP_ERRORS_TOTAL.labels(endpoint='/orders', error_type='payment_denied_simulated').inc()
            return {"success": False, "message": error_message, "status_code": 402}

        payment_status = "approved"
        order_status = "success"
        order_id = f"ORDER-{int(time.time() * 1000)}-{random.randint(100, 999)}"

        # Novo: Salva o pedido no banco de dados simulado
        _orders_db[order_id] = {
            "customer_id": customer_id,
            "items": processed_items,
            "total_amount": total_amount,
            "status": "pending",  # Status inicial
            "created_at": time.time(),
            "last_updated_at": time.time()
        }

        time.sleep(random.uniform(Config.ORDER_PROCESSING_MIN_LATENCY_SECONDS, Config.ORDER_PROCESSING_MAX_LATENCY_SECONDS))

        return {"success": True, "message": f"Pedido {order_id} criado com sucesso!", "order_id": order_id, "status_code": 201}

    except Exception as e:
        error_message = f"Erro inesperado na criação do pedido: {str(e)}"
        APP_ERRORS_TOTAL.labels(endpoint='/orders', error_type='unexpected_error_creation').inc()
        return {"success": False, "message": error_message, "status_code": 500}
    finally:
        latency = time.time() - start_time
        ORDER_PROCESSING_LATENCY.labels(order_type='create').observe(latency)
        ORDERS_CREATED_TOTAL.labels(status=order_status, payment_status=payment_status).inc()


def get_order_details(order_id: str) -> dict:
    """
    Simula a recuperação de detalhes de um pedido, buscando no DB simulado.
    """
    time.sleep(random.uniform(0.05, 0.2))
    order_data = _orders_db.get(order_id)  # Busca o pedido no DB simulado

    if order_data:
        # Retorna uma CÓPIA dos dados para evitar modificações externas diretas
        details = copy.deepcopy(order_data)
        details["success"] = True
        details["status_code"] = 200
        return details
    APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>', error_type='order_not_found').inc()
    return {"success": False, "message": "Pedido não encontrado.", "status_code": 404}


def update_order_status(order_id: str, new_status: str) -> dict:
    """
    Simula a atualização do status de um pedido no DB simulado.
    """
    start_time = time.time()
    order_status_result = "failure"
    error_message = None

    try:
        if not order_id.startswith("ORDER-"):
            error_message = "ID de pedido inválido."
            APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>/status', error_type='invalid_order_id').inc()
            return {"success": False, "message": error_message, "status_code": 400}

        order_to_update = _orders_db.get(order_id)
        if not order_to_update:
            error_message = "Pedido não encontrado para atualização."
            APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>/status', error_type='order_not_found_for_update').inc()
            return {"success": False, "message": error_message, "status_code": 404}

        if new_status not in ["shipped", "delivered", "cancelled", "returned", "processed"]:  # Adicionado "processed"
            error_message = "Status inválido para atualização. Escolha entre shipped, delivered, cancelled, returned, processed."
            APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>/status', error_type='invalid_status_update').inc()
            return {"success": False, "message": error_message, "status_code": 400}

        if random.random() < 0.05:
            raise Exception("Falha interna simulada na atualização do pedido.")

        # Novo: Atualiza o status e a data de última atualização no DB simulado
        order_to_update["status"] = new_status
        order_to_update["last_updated_at"] = time.time()

        order_status_result = "success"
        return {"success": True, "message": f"Status do pedido {order_id} atualizado para {new_status}.", "status_code": 200}

    except Exception as e:
        error_message = f"Erro inesperado na atualização do pedido: {str(e)}"
        APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>/status', error_type='unexpected_error_update').inc()
        return {"success": False, "message": error_message, "status_code": 500}
    finally:
        latency = time.time() - start_time
        ORDER_PROCESSING_LATENCY.labels(order_type='update').observe(latency)


def get_all_orders() -> dict:
    """
    Simula a recuperação de todos os pedidos no sistema.
    Retorna uma lista de todos os pedidos armazenados no DB simulado,
    incluindo o order_id dentro de cada objeto de pedido.
    """
    time.sleep(random.uniform(0.05, 0.2)) # Simula latência de busca

    # Criar uma lista onde cada pedido inclui seu próprio order_id
    all_orders_with_ids = []
    for order_id, order_data in _orders_db.items():
        # Criar uma cópia profunda para evitar modificações acidentais
        order_copy = copy.deepcopy(order_data)
        order_copy["order_id"] = order_id # Adiciona o order_id ao dicionário do pedido
        all_orders_with_ids.append(order_copy)

    if all_orders_with_ids:
        return {"success": True, "orders": all_orders_with_ids, "status_code": 200}

    # Se não houver pedidos, retorna uma lista vazia
    return {"success": True, "orders": [], "message": "Nenhum pedido encontrado.", "status_code": 200}


def update_order_generic(order_id: str, update_data: dict) -> dict:
    """
    Simula a atualização genérica de dados de um pedido.
    Permite mudar campos como customer_id, status, etc.
    """
    start_time = time.time()
    order_status_result = "failure"
    error_message = None

    try:
        if not order_id.startswith("ORDER-"):
            error_message = "ID de pedido inválido."
            APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>', error_type='invalid_order_id_generic_update').inc()
            return {"success": False, "message": error_message, "status_code": 400}

        order_to_update = _orders_db.get(order_id)
        if not order_to_update:
            error_message = "Pedido não encontrado para atualização genérica."
            APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>', error_type='order_not_found_generic_update').inc()
            return {"success": False, "message": error_message, "status_code": 404}

        # Campos permitidos para atualização (simulação)
        allowed_fields = ["customer_id", "status", "notes"]  # Exemplo: pode adicionar mais campos aqui

        for key, value in update_data.items():
            if key in allowed_fields:
                if key == "status" and value not in ["shipped", "delivered", "cancelled", "returned", "processed"]:
                    error_message = f"Status inválido para atualização: '{value}'."
                    APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>', error_type='invalid_status_generic_update').inc()
                    return {"success": False, "message": error_message, "status_code": 400}
                order_to_update[key] = value
            else:
                error_message = f"Campo '{key}' não pode ser atualizado."
                APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>', error_type='invalid_field_for_update').inc()
                return {"success": False, "message": error_message, "status_code": 400}

        # Simula um erro interno aleatório na atualização
        if random.random() < 0.05:  # 5% de chance de erro interno
            raise Exception("Falha interna simulada na atualização genérica do pedido.")

        order_to_update["last_updated_at"] = time.time()  # Atualiza o timestamp

        order_status_result = "success"
        return {"success": True, "message": f"Pedido {order_id} atualizado com sucesso.", "status_code": 200}

    except Exception as e:
        error_message = f"Erro inesperado na atualização genérica do pedido: {str(e)}"
        APP_ERRORS_TOTAL.labels(endpoint='/orders/<id>', error_type='unexpected_error_generic_update').inc()
        return {"success": False, "message": error_message, "status_code": 500}
    finally:
        latency = time.time() - start_time
        # Podemos reutilizar a métrica de latência de processamento de pedido
        # ou criar uma nova específica para atualizações genéricas se for relevante
        ORDER_PROCESSING_LATENCY.labels(order_type='generic_update').observe(latency)


# Chama a função para inicializar os gauges de estoque assim que o módulo é carregado
initialize_inventory_gauges()
