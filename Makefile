.PHONY: help install test lint format build run deploy clean

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov httpx ruff black

test: ## 运行测试
	pytest tests/ -v --tb=short --cov=app --cov-report=html --cov-report=term --timeout=60

test-unit: ## 运行单元测试
	pytest tests/ -v -m "not integration" --tb=short

test-integration: ## 运行集成测试
	pytest tests/ -v -m "integration" --tb=short

lint: ## 代码质量检查
	ruff check app/
	black --check app/

format: ## 代码格式化
	black app/
	ruff check app/ --fix

build: ## 构建 Docker 镜像
	docker build -t smart-assistant:latest -t smart-assistant:$(shell git rev-parse --short HEAD) .

run: ## 本地运行
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-docker: ## Docker 运行
	docker-compose up -d

stop-docker: ## 停止 Docker
	docker-compose down

logs: ## 查看日志
	docker-compose logs -f app

deploy-k8s: ## 部署到 Kubernetes
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secret.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/ingress.yaml

deploy-swarm: ## 部署到 Docker Swarm
	docker stack deploy -c docker-compose.prod.yml smart-assistant

clean: ## 清理临时文件
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml test-results.xml