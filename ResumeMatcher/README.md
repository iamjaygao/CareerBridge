# Resume Matcher API Service

一个独立的简历匹配 API 服务，为 CareerBridge 平台提供 AI 驱动的简历与职位匹配功能。

## 🚀 项目概述

Resume Matcher API Service 是一个基于 FastAPI 的独立微服务，专门负责使用 AI 技术分析简历与职位描述的匹配度，并提供详细的匹配分析和建议。

## ✨ 主要功能

- **智能简历匹配**: 使用 AI 技术分析简历与职位描述的匹配度
- **语义分析**: 基于自然语言处理进行深度语义匹配
- **技能匹配**: 智能识别和匹配技能要求
- **匹配评分**: 提供详细的匹配分数和解释
- **批量匹配**: 支持批量简历与职位匹配
- **反馈学习**: 基于用户反馈持续改进匹配算法

## 🛠 技术栈

- **Web 框架**: FastAPI
- **AI/ML**: OpenAI GPT, Sentence Transformers, spaCy
- **数据库**: PostgreSQL + Redis
- **向量数据库**: Pinecone / Weaviate (可选)
- **任务队列**: Celery
- **文档**: Swagger UI / ReDoc
- **监控**: Prometheus + Grafana
- **日志**: structlog

## 📦 安装

### 1. 克隆项目
```bash
git clone <repository-url>
cd ResumeMatcher
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
createdb resume_matcher_db

# 运行迁移
alembic upgrade head
```

## 🚀 运行

### 开发模式
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### 生产模式
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8002
```

### Docker 运行
```bash
docker-compose up -d
```

## 📚 API 文档

启动服务后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## 🔗 API 端点

### 健康检查
- `GET /health/` - 基本健康检查
- `GET /health/detailed` - 详细健康检查

### 简历匹配
- `POST /match` - 单个简历匹配
- `POST /batch-match` - 批量简历匹配
- `GET /matches/{match_id}` - 获取匹配详情
- `GET /matches/{match_id}/analysis` - 获取详细分析

### 反馈和学习
- `POST /matches/{match_id}/feedback` - 提交匹配反馈
- `GET /analytics/accuracy` - 获取匹配准确率统计

### 模型管理
- `GET /models/status` - 获取模型状态
- `POST /models/retrain` - 触发模型重训练

## 🔧 配置

### 环境变量

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/resume_matcher_db
REDIS_URL=redis://localhost:6379

# API 配置
API_KEY=your-api-key
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8001"]

# AI 服务配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2

# 向量数据库 (可选)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX=resume-matcher

# 匹配配置
CONFIDENCE_THRESHOLD=0.7
MAX_TOKENS=2000
TEMPERATURE=0.3
```

## 🧪 测试

### 运行测试
```bash
pytest
```

### 运行特定测试
```bash
pytest tests/test_matching.py
```

### 覆盖率测试
```bash
pytest --cov=app tests/
```

## 📊 监控

### 健康检查
```bash
curl http://localhost:8002/health/
```

### 指标监控
```bash
curl http://localhost:8002/metrics
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
docker build -t resume-matcher .
docker run -p 8002:8002 resume-matcher
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

Resume Matcher 通过 RESTful API 与 CareerBridge 集成：

```python
# CareerBridge 中的调用示例
import requests

response = requests.post(
    "http://resume-matcher:8002/match",
    json={
        "resume_text": "resume content...",
        "job_description": "job description...",
        "job_title": "Software Engineer",
        "company": "Tech Corp"
    },
    headers={"Authorization": "Bearer your-api-key"}
)
```

## 📝 开发指南

### 添加新的匹配算法
1. 在 `app/services/matchers/` 中创建新的匹配器类
2. 实现 `BaseMatcher` 接口
3. 在 `app/services/matching_service.py` 中注册新匹配器
4. 添加相应的测试

### 添加新的 API 端点
1. 在 `app/api/routes/` 中创建新的路由文件
2. 在 `app/main.py` 中注册路由
3. 添加相应的 schemas 和测试

## 🐛 故障排除

### 常见问题

1. **AI 模型加载失败**
   - 检查 OpenAI API 密钥配置
   - 确保网络连接正常
   - 检查模型文件路径

2. **数据库连接失败**
   - 检查 DATABASE_URL 配置
   - 确保 PostgreSQL 服务运行中

3. **匹配准确率低**
   - 检查训练数据质量
   - 调整匹配参数
   - 收集更多用户反馈

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如有问题，请联系开发团队。 