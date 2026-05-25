#!/bin/bash

# 测试 Docker 构建和启动
echo "1. 构建 Docker 镜像..."
docker build -t smart-assistant-test .

echo "2. 启动 Redis 容器..."
docker run -d --name redis-test -p 6379:6379 redis:7-alpine
sleep 5

echo "3. 启动应用容器..."
docker run -d --name app-test \
  -e DASHSCOPE_API_KEY=test \
  -e REDIS_HOST=host.docker.internal \
  -e REDIS_PORT=6379 \
  -e DATABASE_URL=sqlite:///./data.db \
  -p 8000:8000 \
  smart-assistant-test

echo "4. 等待应用启动..."
for i in {1..30}; do
  if curl -s -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "应用启动成功！"
    break
  fi
  echo "等待应用启动... ($i/30)"
  sleep 1
done

echo "5. 测试健康检查..."
if curl -s -f http://localhost:8000/api/health; then
  echo "✅ 健康检查通过"
else
  echo "❌ 健康检查失败"
  echo "容器日志："
  docker logs app-test
  exit 1
fi

echo "6. 清理..."
docker stop app-test redis-test
docker rm app-test redis-test
docker rmi smart-assistant-test