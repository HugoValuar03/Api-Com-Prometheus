from prometheus_client import generate_latest, Counter, Histogram, Gauge
from flask import request, jsonify
import time

# --- Definição das Métricas ---

# Requisições HTTP
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total de requisições HTTP para a API.',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'api_request_latency_seconds',
    'Latência de requisições HTTP da API em segundos.',
    ['method', 'endpoint']
)

# Erros da Aplicação (de Lógica de Negócio ou Internos)
APP_ERRORS_TOTAL = Counter(
    'api_errors_total',
    'Total de erros internos e de lógica de negócio da API.',
    ['endpoint', 'error_type']
)

# Métricas Específicas do Negócio (Gerenciamento de Pedidos)
ORDERS_CREATED_TOTAL = Counter(
    'ecommerce_orders_created_total',
    'Total de pedidos criados no sistema.',
    ['status', 'payment_status']  # status: success/failure, payment_status: approved/denied
)

ORDER_PROCESSING_LATENCY = Histogram(
    'ecommerce_order_processing_latency_seconds',
    'Latência para processar (criar ou atualizar) um pedido.',
    ['order_type']  # create, update
)

ACTIVE_SESSIONS_GAUGE = Gauge(
    'ecommerce_active_sessions_gauge',
    'Número de sessões de usuário ativas na plataforma.'
)

INVENTORY_LEVEL_GAUGE = Gauge(
    'ecommerce_inventory_level_gauge',
    'Nível de estoque atual de um produto específico.',
    ['product_id']
)


# --- Funções de Inicialização e Middleware ---

def init_metrics_and_middleware(app):
    """
    Inicializa todas as métricas Prometheus e registra os middlewares
    na aplicação Flask.
    """

    @app.before_request
    def before_request_hook():
        request.start_time = time.time()
        ACTIVE_SESSIONS_GAUGE.inc()  # Incrementa sessões ativas

    @app.after_request
    def after_request_hook(response):
        latency = time.time() - request.start_time

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.path
        ).observe(latency)

        ACTIVE_SESSIONS_GAUGE.dec()  # Decrementa sessões ativas
        return response

    @app.errorhandler(500)
    def handle_500_error(e):
        """
        Registra erros 500 (Internal Server Error) globais.
        """
        APP_ERRORS_TOTAL.labels(endpoint=request.path, error_type='internal_server_error').inc()
        response = jsonify({"error": "Ocorreu um erro interno no servidor."})
        response.status_code = 500
        return response

    @app.route('/metrics')
    def prometheus_metrics():
        """
        Endpoint para o Prometheus coletar as métricas.
        """
        return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}
