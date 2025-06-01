from flask import Flask, request, jsonify
from prometheus_client import generate_latest, Counter, Histogram, Gauge
import time
import random

# ----------------------------------------------------------------------
# 1. Configuração da Aplicação Flask
# ----------------------------------------------------------------------
app = Flask(__name__)

# ----------------------------------------------------------------------
# 2. Definição das Métricas Prometheus (Mais Detalhadas)
# ----------------------------------------------------------------------

# Contador de requisições totais:
# Adicionado um label 'status' para diferenciar requisições bem-sucedidas (2xx)
# de erros (4xx, 5xx).
REQUEST_COUNT = Counter(
    'app_requests_total',
    'Requisições totais para a aplicação.',
    ['method', 'endpoint', 'status']
)

# Histograma de latência das requisições:
# Mede a duração das requisições, também com labels para método e endpoint.
REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Latência de requisições da aplicação em segundos.',
    ['method', 'endpoint']
)

# Contador de erros específicos da aplicação:
# Registra erros internos, com um label 'error_type' para categorizar.
APP_ERRORS_TOTAL = Counter(
    'app_errors_total',
    'Erros internos da aplicação.',
    ['endpoint', 'error_type']
)

# Gauge para monitorar o número de usuários ativos (exemplo):
# Um Gauge pode subir e descer. Simula o número de usuários ativos.
ACTIVE_USERS = Gauge(
    'app_active_users',
    'Número de usuários ativos na aplicação.'
)

# Contador para simular itens processados por uma função interna:
# Mostra como instrumentar lógica de negócio específica.
PROCESSED_ITEMS_TOTAL = Counter(
    'app_processed_items_total',
    'Número total de itens processados.',
    ['item_type']
)

# ----------------------------------------------------------------------
# 3. Middleware para Coletar Métricas (Mais Abrangente)
# ----------------------------------------------------------------------

@app.before_request
def before_request():
    request.start_time = time.time()
    # Aumenta o contador de usuários ativos quando uma requisição começa
    ACTIVE_USERS.inc()

@app.after_request
def after_request(response):
    latency = time.time() - request.start_time

    # Incrementa o contador de requisições com o status HTTP da resposta.
    # O `response.status_code` nos dá o código como 200, 404, 500 etc.
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.path
    ).observe(latency)

    # Diminui o contador de usuários ativos quando a requisição termina
    ACTIVE_USERS.dec() # Reduz o gauge
    return response

# Manipulador de erros para capturar exceções não tratadas
@app.errorhandler(500)
def handle_500_error(e):
    """
    Registra erros 500 (Internal Server Error) e retorna uma resposta JSON.
    """
    APP_ERRORS_TOTAL.labels(endpoint=request.path, error_type='internal_server_error').inc()
    response = jsonify({"error": "Ocorreu um erro interno no servidor."})
    response.status_code = 500
    return response

# ----------------------------------------------------------------------
# 4. Funções de Lógica de Negócio Instrumentadas
# ----------------------------------------------------------------------

def process_data_item(item_type: str):
    """
    Simula o processamento de um item de dados.
    Esta função incrementa uma métrica de contador para itens processados.
    """
    time.sleep(random.uniform(0.01, 0.1)) # Simula trabalho
    PROCESSED_ITEMS_TOTAL.labels(item_type=item_type).inc()
    return f"Item do tipo '{item_type}' processado com sucesso!"

# ----------------------------------------------------------------------
# 5. Endpoints da API (Mais Variados)
# ----------------------------------------------------------------------

@app.route('/')
def home():
    """
    Endpoint principal da API.
    """
    time.sleep(random.uniform(0.05, 0.15))
    return "Olá do Parceiro de Programação! Sua API robusta está funcionando!"

@app.route('/hello/<name>')
def hello(name):
    """
    Endpoint de exemplo com um parâmetro de caminho.
    Processa um item de dados ao ser acessado.
    """
    time.sleep(random.uniform(0.1, 0.2))
    result = process_data_item("greeting_request")
    return f"Olá, {name}! {result}"

@app.route('/calculate/<operation>/<a>/<b>')
def calculate(operation, a, b):
    """
    Endpoint que simula uma operação de cálculo e pode falhar.
    Demonstra a métrica de erro.
    """
    try:
        num_a = float(a)
        num_b = float(b)

        if operation == 'divide':
            if num_b == 0:
                # Simula uma divisão por zero que gera um erro
                APP_ERRORS_TOTAL.labels(endpoint=request.path, error_type='division_by_zero').inc()
                return jsonify({"error": "Divisão por zero não é permitida."}), 400
            result = num_a / num_b
        elif operation == 'add':
            result = num_a + num_b
        else:
            APP_ERRORS_TOTAL.labels(endpoint=request.path, error_type='invalid_operation').inc()
            return jsonify({"error": "Operação inválida."}), 400

        # Simula uma falha aleatória para testar a métrica de erro 500
        if random.random() < 0.1: # 10% de chance de erro interno
            raise Exception("Erro interno simulado!")

        time.sleep(random.uniform(0.02, 0.08))
        return jsonify({"result": result})

    except ValueError:
        APP_ERRORS_TOTAL.labels(endpoint=request.path, error_type='invalid_input').inc()
        return jsonify({"error": "Entrada inválida. Certifique-se de que 'a' e 'b' são números."}), 400
    except Exception as e:
        # Erro genérico, será capturado pelo errorhandler(500)
        raise e


@app.route('/users_online')
def users_online():
    """
    Endpoint para demonstrar o Gauge de usuários ativos.
    """
    # Note: o Gauge já é incrementado/decrementado no middleware para cada requisição.
    # Este endpoint serve apenas para mostrar que ele existe.
    return jsonify({"message": "Verifique o painel do Grafana para 'app_active_users'."})


@app.route('/process_items/<item_type>')
def process_items_endpoint(item_type):
    """
    Endpoint que usa a função de lógica de negócio instrumentada.
    """
    time.sleep(random.uniform(0.03, 0.1))
    message = process_data_item(item_type)
    return jsonify({"status": message})


@app.route('/metrics')
def metrics():
    """
    Endpoint que expõe as métricas no formato do Prometheus.
    """
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

# ----------------------------------------------------------------------
# 6. Execução da Aplicação
# ----------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)