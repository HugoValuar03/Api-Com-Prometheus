import sys
import os

# Adiciona o diretório 'app' ao PATH do Python
# Isso é necessário para que possamos importar módulos de dentro da pasta 'app'
# como 'app.routes' e 'app.metrics'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from flask import Flask
from config.config import Config
from app.routes import init_routes  # Será criado em app/routes.py
from app.metrics import init_metrics_and_middleware # Será criado em app/metrics.py

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa as métricas e o middleware do Prometheus
    init_metrics_and_middleware(app)

    # Inicializa as rotas da aplicação
    init_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    print(f"[*] Starting Flask API on http://localhost:{app.config['FLASK_APP_PORT']}")
    app.run(
        host='0.0.0.0', # Permite acesso de outras máquinas (para Prometheus/Grafana em Docker, por exemplo)
        port=app.config['FLASK_APP_PORT'],
        debug=app.config['FLASK_DEBUG']
    )