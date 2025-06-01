import os
from dotenv import load_dotenv

load_dotenv() # Carrega as variáveis de ambiente do arquivo .env

class Config:
    # Configurações da aplicação Flask
    FLASK_APP_PORT = int(os.getenv('FLASK_APP_PORT', 5000))
    FLASK_DEBUG = True # Mudar para False em produção!

    # Configurações de terceiros (Prometheus, etc.)
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', 9090))
    GRAFANA_PORT = int(os.getenv('GRAFANA_PORT', 3001))

    # Configurações para simulação de e-commerce
    ORDER_PROCESSING_MIN_LATENCY_SECONDS = 0.1
    ORDER_PROCESSING_MAX_LATENCY_SECONDS = 0.5
    PAYMENT_GATEWAY_FAILURE_CHANCE = 0.15 # 15% de chance de falha no pagamento
    STOCK_VALIDATION_FAILURE_CHANCE = 0.05 # 5% de chance de falha na validação de estoque
    API_KEY_REQUIRED = os.getenv('API_KEY_REQUIRED', 'minha_chave_secreta_empresa') # Chave de API para autenticação simulada