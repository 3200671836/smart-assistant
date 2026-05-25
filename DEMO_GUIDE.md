# Smart Assistant CI/CD 演示脚本

## 演示目标
展示完整的 CI/CD 流水线，包括代码提交、自动化测试、Docker 构建、部署到生产环境、监控和告警。

## 演示步骤

### 第 1 步：环境准备
```bash
# 1.1 克隆项目
git clone https://github.com/3200671836/smart-assistant.git
cd smart-assistant/backend

# 1.2 安装依赖
make install

# 1.3 运行本地测试
make test

# 1.4 启动本地服务
make run
```

### 第 2 步：代码提交触发 CI
```bash
# 2.1 创建新功能分支
git checkout -b feature/add-ci-cd-demo

# 2.2 添加演示文件
echo "# CI/CD Demo Feature" >> app/demo.py

# 2.3 提交代码
git add .
git commit -m "feat: add CI/CD demo feature"

# 2.4 推送到 GitHub
git push origin feature/add-ci-cd-demo
```

### 第 3 步：创建 Pull Request
1. 访问 GitHub 仓库
2. 创建 Pull Request: feature/add-ci-cd-demo → main
3. 观察 GitHub Actions 自动运行 CI

### 第 4 步：CI 流程演示
在 GitHub Actions 页面展示：
1. **Lint & Type Check**: Ruff + Black 代码检查通过
2. **Unit & Integration Tests**: 测试覆盖率 ≥60%
3. **Docker Build**: Docker 镜像构建成功
4. **Security Scan**: Bandit 安全扫描无高危漏洞

### 第 5 步：合并 PR 触发 CD
1. 在 GitHub 上批准并合并 PR
2. 观察 CD 流水线自动启动
3. 展示以下阶段：
   - ✅ Docker 镜像构建和推送
   - ✅ 部署到 Kubernetes
   - ✅ 健康检查通过
   - ✅ 通知发送

### 第 6 步：验证部署
```bash
# 6.1 检查 Kubernetes 部署状态
kubectl get all -n smart-assistant

# 6.2 访问应用
curl https://smart-assistant.example.com/api/health

# 6.3 查看应用日志
kubectl logs -f deployment/smart-assistant -n smart-assistant
```

### 第 7 步：监控演示
1. **访问 Prometheus**: http://localhost:9090
   - 查看应用指标
   - 查看 Redis 指标
   - 查看节点资源使用率

2. **访问 Grafana**: http://localhost:3000 (admin/admin)
   - 展示应用监控仪表板
   - 展示 Redis 监控仪表板
   - 展示系统资源仪表板

### 第 8 步：故障注入和恢复演示
```bash
# 8.1 模拟应用故障
kubectl delete pod -n smart-assistant -l app=smart-assistant

# 8.2 观察自动恢复
kubectl get pods -n smart-assistant -w

# 8.3 验证健康检查
curl -f https://smart-assistant.example.com/api/health
```

### 第 9 步：回滚演示
```bash
# 9.1 部署一个有问题的版本
# (修改 deployment.yaml 中的镜像标签)

# 9.2 观察部署失败
kubectl rollout status deployment/smart-assistant -n smart-assistant

# 9.3 执行回滚
kubectl rollout undo deployment/smart-assistant -n smart-assistant

# 9.4 验证回滚成功
kubectl get pods -n smart-assistant
```

### 第 10 步：演示总结
1. **CI 成果**:
   - 代码质量保证
   - 自动化测试覆盖
   - 安全扫描
   - Docker 镜像验证

2. **CD 成果**:
   - 自动部署到生产环境
   - 多环境支持 (K8s + Swarm)
   - 健康检查和自动恢复
   - 完整的监控体系
   - 通知和告警

## 演示要点记录表

| 阶段 | 演示内容 | 预期结果 | 实际结果 |
|------|----------|----------|----------|
| 代码提交 | 创建 PR 触发 CI | CI 流水线自动运行 | ✅ |
| CI 检查 | 代码质量检查 | Ruff/Black 通过 | ✅ |
| CI 测试 | 自动化测试 | 测试覆盖率 ≥60% | ✅ |
| CI 构建 | Docker 构建 | 镜像构建成功 | ✅ |
| CI 安全 | 安全扫描 | 无高危漏洞 | ✅ |
| CD 部署 | 合并 PR 触发 CD | 自动部署到 K8s | ✅ |
| CD 验证 | 健康检查 | 应用可访问 | ✅ |
| 监控 | Prometheus/Grafana | 指标正常显示 | ✅ |
| 故障恢复 | 删除 Pod | 自动重建 | ✅ |
| 回滚 | 部署失败回滚 | 回滚到上一版本 | ✅ |

## 演示脚本文件

创建演示脚本文件：

```bash
#!/bin/bash
# demo.sh - Smart Assistant CI/CD 演示脚本

set -e

echo "=== Smart Assistant CI/CD 演示 ==="
echo "开始时间: $(date)"

# 1. 环境检查
echo -e "\n1. 检查环境..."
python --version
docker --version
kubectl version --short
make --version

# 2. 运行测试
echo -e "\n2. 运行自动化测试..."
make test

# 3. 代码质量检查
echo -e "\n3. 代码质量检查..."
make lint

# 4. 构建 Docker 镜像
echo -e "\n4. 构建 Docker 镜像..."
make build

# 5. 启动本地服务
echo -e "\n5. 启动本地服务..."
make run-docker &
sleep 10

# 6. 健康检查
echo -e "\n6. 应用健康检查..."
curl -f http://localhost:8000/api/health || {
    echo "健康检查失败"
    exit 1
}

# 7. 访问 API 文档
echo -e "\n7. API 文档可访问..."
curl -s http://localhost:8000/docs | grep -q "FastAPI" || {
    echo "API 文档不可访问"
    exit 1
}

# 8. 停止服务
echo -e "\n8. 停止本地服务..."
make stop-docker

# 9. 演示完成
echo -e "\n=== 演示完成 ==="
echo "结束时间: $(date)"
echo "所有检查通过！CI/CD 流水线工作正常。"
```

## 演示注意事项

1. **网络要求**: 确保可以访问 GitHub 和 Docker Hub
2. **权限要求**: 需要 GitHub 仓库的写权限和 K8s 集群的部署权限
3. **时间安排**: 完整演示约需 15-20 分钟
4. **故障预案**: 准备离线演示方案
5. **Q&A 准备**: 准备常见问题解答

## 演示评分标准

| 评分项 | 权重 | 说明 |
|--------|------|------|
| CI 流程完整性 | 30% | 代码检查、测试、构建、安全扫描 |
| CD 流程完整性 | 40% | 自动部署、健康检查、监控、回滚 |
| 演示效果 | 20% | 流程清晰、结果可视、故障恢复 |
| 文档完整性 | 10% | README、演示脚本、故障排除 |

**总分: 100分 (CD 部分为加分项)**

---

## 快速开始演示

```bash
# 1. 下载演示脚本
curl -O https://raw.githubusercontent.com/3200671836/smart-assistant/main/demo.sh

# 2. 赋予执行权限
chmod +x demo.sh

# 3. 运行演示
./demo.sh

# 4. 查看演示结果
cat demo.log
```

## 联系信息

如有问题，请联系：
- 项目仓库: https://github.com/3200671836/smart-assistant
- CI/CD 配置: `.github/workflows/`
- 部署配置: `k8s/` 和 `docker-compose.prod.yml`
- 监控配置: `prometheus.yml`