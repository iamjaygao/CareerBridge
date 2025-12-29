# Job Crawler API Service

一个独立的职位爬虫 API 服务，为 CareerBridge 平台提供工作数据。

## 🚀 项目概述

Job Crawler API Service 是一个基于 FastAPI 的独立微服务，专门负责从多个来源爬取工作信息，并提供 RESTful API 接口供其他服务调用。

## ✨ 主要功能

- **多源工作爬取**: 从 Indeed、LinkedIn、Glassdoor 等平台爬取工作信息
- **智能搜索**: 支持关键词、地点、公司等多维度搜索
- **市场分析**: 提供薪资数据、技能需求分析
- **工作推荐**: 基于用户技能和经验的工作推荐
- **实时数据**: 定期更新工作数据，保持信息新鲜度

## 🛠 技术栈

- **Web 框架**: FastAPI
- **数据库**: PostgreSQL + Redis
- **爬虫框架**: Scrapy + Selenium
- **任务队列**: Celery
- **文档**: Swagger UI / ReDoc
- **监控**: Prometheus + Grafana
- **日志**: structlog

## 📦 安装

### 1. 克隆项目
```bash
git clone <repository-url>
cd JobCrawler
```

### 2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 环境配置
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、API 密钥等
```

### 5. 数据库设置
```bash
# 创建数据库
createdb job_crawler_db

# 运行迁移
alembic upgrade head
```

## 🚀 运行

### 开发模式
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产模式
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker 运行
```bash
docker-compose up -d
```

## 📚 API 文档

启动服务后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔗 API 端点

### 健康检查
- `GET /health/` - 基本健康检查
- `GET /health/detailed` - 详细健康检查

### 工作搜索
- `GET /jobs/search` - 搜索工作
- `GET /jobs/{job_id}` - 获取工作详情
- `GET /jobs/trending/list` - 获取热门工作
- `GET /jobs/recommendations/list` - 获取工作推荐

### 市场数据
- `GET /market/salary` - 获取薪资数据
- `GET /market/skills` - 获取技能需求分析
- `GET /market/trends` - 获取市场趋势

## 🔧 配置

### 环境变量

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/job_crawler_db
REDIS_URL=redis://localhost:6379

# API 配置
API_KEY=your-api-key
CORS_ORIGINS=["http://localhost:3000"]

# 爬虫配置
SCRAPER_TIMEOUT=30
SCRAPER_DELAY=1

# 外部 API
INDEED_API_KEY=your-indeed-api-key
LINKEDIN_API_KEY=your-linkedin-api-key
```

## 🧪 测试

### 运行测试
```bash
pytest
```

### 运行特定测试
```bash
pytest tests/test_jobs.py
```

### 覆盖率测试
```bash
pytest --cov=app tests/
```

## 📊 监控

### 健康检查
```bash
curl http://localhost:8000/health/
```

### 指标监控
```bash
curl http://localhost:8000/metrics
```

## 🔒 安全

- API 密钥认证
- CORS 配置
- 请求限流
- 输入验证
- SQL 注入防护

## 📈 部署

### Docker 部署
```bash
docker build -t job-crawler .
docker run -p 8000:8000 job-crawler
```

### Docker Compose 部署
```bash
docker-compose up -d
```

### Kubernetes 部署
```bash
kubectl apply -f k8s/
```

## 🤝 与 CareerBridge 集成

Job Crawler 通过 RESTful API 与 CareerBridge 集成：

```python
# CareerBridge 中的调用示例
import requests

response = requests.get(
    "http://job-crawler:8000/jobs/search",
    params={"keywords": "python", "location": "San Francisco"},
    headers={"Authorization": "Bearer your-api-key"}
)
```

## 📝 开发指南

### 添加新的爬虫源
1. 在 `app/services/scrapers/` 中创建新的爬虫类
2. 实现 `BaseScraper` 接口
3. 在 `app/services/crawler.py` 中注册新爬虫
4. 添加相应的测试

### 添加新的 API 端点
1. 在 `app/api/routes/` 中创建新的路由文件
2. 在 `app/main.py` 中注册路由
3. 添加相应的 schemas 和测试

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 DATABASE_URL 配置
   - 确保 PostgreSQL 服务运行中

2. **Redis 连接失败**
   - 检查 REDIS_URL 配置
   - 确保 Redis 服务运行中

3. **爬虫超时**
   - 调整 SCRAPER_TIMEOUT 配置
   - 检查网络连接

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如有问题，请联系开发团队。 