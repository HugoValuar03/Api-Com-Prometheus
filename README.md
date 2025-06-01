# Protótipo de API de Gerenciamento de Pedidos com Monitoramento (Prometheus & Grafana)

Este projeto demonstra uma API de e-commerce simulada com instrumentação de métricas robusta, utilizando Flask para a API, Prometheus para coleta e Grafana para visualização. Desenvolvido como um protótipo empresarial para monitoramento de aplicações.

## Funcionalidades da API

A API simula as seguintes operações de gerenciamento de pedidos:

* **Criação de Pedidos:** `POST /orders`
    * Simula validação de dados, verificação de estoque e processamento de pagamento.
    * Pode retornar sucesso (201), falha de validação (400), produto não encontrado (404), pagamento negado (402), ou erro interno (500).
    * Requer `X-API-Key` no cabeçalho para autenticação simulada (valor configurado em `.env`).
* **Consulta de Pedidos:** `GET /orders/{order_id}`
* **Atualização de Status de Pedidos:** `PUT /orders/{order_id}/status`
    * Simula atualização de status (ex: "shipped", "delivered").
    * Pode simular erros internos.
* **Health Check:** `GET /health` - Retorna o status operacional da API.
* **Métricas Prometheus:** `GET /metrics` - Endpoint para o Prometheus coletar dados.

## Métricas Coletadas

As seguintes métricas são expostas e monitoradas:

* `api_requests_total`: Contador de todas as requisições HTTP, categorizadas por método, endpoint e status HTTP (2xx, 4xx, 5xx).
* `api_request_latency_seconds`: Histograma da latência de todas as requisições HTTP, por método e endpoint.
* `api_errors_total`: Contador de erros específicos da aplicação, categorizados por endpoint e tipo de erro (ex: `validation_error`, `payment_denied_simulated`, `unauthorized_access`, `internal_server_error`).
* `ecommerce_orders_created_total`: Contador de pedidos criados, categorizados por status final do pedido (`success`/`failure`) e status do pagamento (`approved`/`denied`).
* `ecommerce_order_processing_latency_seconds`: Histograma da latência de operações de criação/atualização de pedidos.
* `ecommerce_active_sessions_gauge`: Gauge que estima o número de usuários ativos (requisições em andamento).
* `ecommerce_inventory_level_gauge`: Gauge mostrando o nível de estoque atual de produtos específicos (`product_id`).

## Requisitos

* Python 3.x
* `pip` (gerenciador de pacotes Python)
* Prometheus
* Grafana

## Configuração e Execução

Siga os passos abaixo para configurar e executar o protótipo.

### 1. Preparar o Ambiente Python

1.  **Crie um Ambiente Virtual (opcional, mas recomendado):**
    ```bash
    python -m venv .venv
    ```
2.  **Ative o Ambiente Virtual:**
    * **Windows:** `.\.venv\Scripts\activate`
    * **macOS/Linux:** `source ./.venv/bin/activate`
3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
````python
    FLASK_APP_PORT=5000
    PROMETHEUS_PORT=9090
    GRAFANA_PORT=3001
    API_KEY_REQUIRED=minha_chave_secreta_empresa # Mude para uma chave segura para o protótipo
````

### 3. Iniciar a API Flask

No terminal (com o ambiente virtual ativado) e na raiz do projeto:

```bash
    python run.py
```