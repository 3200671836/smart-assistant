# Smart Assistant CI/CD 流水线文档

## 1. 项目概述

这是一个基于 FastAPI + RAG 的智能助手项目，已配置完整的 CI/CD 流水线。

## 2. CI/CD 流水线架构

### 2.1 持续集成 (CI) 流程
```
代码提交 → 代码质量检查 → 自动化测试 → Docker构建验证 → 安全扫描
```

### 2.2 持续部署 (CD) 流程
```
CI通过 → 构建Docker镜像 → 推送镜像 → 部署到K8s/Swarm → 健康检查 → 通知监控
```

## 3. 文件结构说明

```
smart-assistant/
├── .github/workflows/          # GitHub Actions 工作流
│   ├── ci.yml                  # CI 流水线
│   └── cd.yml                  # CD 流水线
├── k8s/                        # Kubernetes 部署配置
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── docker-compose.yml          # 开发环境配置
├── docker-compose.prod.yml     # 生产环境配置
├── Dockerfile                  # Docker 构建配置
├── Makefile                    # 开发命令工具
├── prometheus.yml              # 监控配置
└── README.md                   # 项目文档
```

## 4. 使用说明

### 4.1 本地开发
```bash
# 安装依赖
make install

# 运行测试
make test

# 代码格式化
make format

# 本地运行
make run
```

### 4.2 Docker 开发
```bash
# 构建镜像
make build

# 启动服务
make run-docker

# 查看日志
make logs
```

### 4.3 部署到 Kubernetes
```bash
# 部署到 K8s
make deploy-k8s

# 部署到 Swarm
make deploy-swarm
```

## 5. CI/CD 工作流说明

### 5.1 CI 工作流 (.github/workflows/ci.yml)
- **触发条件**: push 到 main/develop 分支或创建 PR
- **包含任务**:
  1. 🔍 Lint & Type Check: Ruff + Black 代码检查
  2. 🧪 Unit & Integration Tests: 单元测试 + 集成测试
  3. 🐳 Docker Build: Docker 镜像构建验证
  4. 🔒 Security Scan: Bandit 安全扫描

### 5.2 CD 工作流 (.github/workflows/cd.yml)
- **触发条件**: push 到 main 分支或创建版本标签
- **包含任务**:
  1. 🐳 Build & Push Docker Image: 构建并推送镜像到 GitHub Container Registry
  2. 🚀 Deploy to Kubernetes: 部署到 Kubernetes 集群
  3. 🐳 Deploy to Docker Swarm: 部署到 Docker Swarm 集群
  4. 📢 Notify & Monitor: 发送通知并创建部署记录

## 6. 监控和告警

### 6.1 监控组件
- **Prometheus**: 指标收集和存储
- **Grafana**: 数据可视化仪表板
- **Redis Exporter**: Redis 监控
- **Node Exporter**: 节点资源监控
- **cAdvisor**: 容器监控

### 6.2 访问地址
- 应用: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## 7. 环境变量配置

### 7.1 开发环境 (.env)
```bash
DATABASE_URL=sqlite:///./data.db
REDIS_HOST=localhost
REDIS_PORT=6379
DASHSCOPE_API_KEY=your_api_key
ENVIRONMENT=development
```

### 7.2 生产环境 (Kubernetes Secret)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: smart-assistant-secret
type: Opaque
stringData:
  DASHSCOPE_API_KEY: "your_production_api_key"
```

## 8. 演示准备

### 8.1 演示场景
1. **代码提交触发 CI**: 展示代码提交后自动运行测试
2. **PR 合并触发 CD**: 展示代码合并后自动部署
3. **健康检查**: 展示应用健康状态
4. **监控仪表板**: 展示 Prometheus + Grafana 监控
5. **回滚演示**: 展示部署失败时的自动回滚

### 8.2 演示步骤
1. 修改代码并提交到 GitHub
2. 查看 GitHub Actions 运行状态
3. 验证测试通过和代码质量检查
4. 查看 Docker 镜像构建和推送
5. 验证生产环境部署
6. 访问应用验证功能
7. 查看监控仪表板

## 9. 故障排除

### 9.1 常见问题
1. **CI 失败**: 检查测试用例、代码规范
2. **Docker 构建失败**: 检查 Dockerfile 和依赖
3. **部署失败**: 检查 K8s 配置和网络连接
4. **健康检查失败**: 检查应用启动和依赖服务

### 9.2 调试命令
```bash
# 查看 CI 日志
gh run list
gh run view <run_id> --log

# 查看容器日志
kubectl logs -f deployment/smart-assistant -n smart-assistant

# 检查服务状态
kubectl get all -n smart-assistant
```

---

## 10. 加分项 (CD 部分)

✅ **已实现的 CD 功能**:
1. 多环境部署 (Kubernetes + Docker Swarm)
2. 蓝绿部署策略
3. 自动回滚机制
4. 完整的监控告警体系
5. 通知系统 (Slack/GitHub)
6. 健康检查和就绪探针
7. 资源限制和自动扩缩容
8. TLS 证书自动管理
9. 持久化存储配置
10. 服务网格集成准备