# CareerBridge 开发环境设置指南

## 系统要求

- Python 3.8+
- Node.js 16+
- PostgreSQL (可选，开发环境可使用 SQLite)
- Redis (可选，用于缓存和 Celery)

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd CareerBridge
```

### 2. 后端设置

#### 创建虚拟环境

```bash
cd careerbridge
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

#### 安装依赖

```bash
pip install -r requirements.txt
```

#### 环境配置

```bash
cp env_template.txt .env
# 编辑 .env 文件，配置必要的环境变量
```

#### 数据库迁移

```bash
python manage.py migrate
```

#### 创建超级用户

```bash
python manage.py createsuperuser
```

#### 启动开发服务器

```bash
python manage.py runserver 8001
```

### 3. 前端设置

#### 安装依赖

```bash
cd frontend
npm install
```

#### 启动开发服务器

```bash
npm start
```

### 4. Job Crawler 服务

#### 启动独立服务

```bash
cd JobCrawler
python3 start.py
```

## 环境变量配置

### 必需的环境变量

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_ENV=development

# 数据库
DATABASE_URL=sqlite:///db.sqlite3

# 外部服务
OPENAI_API_KEY=your-openai-api-key
JOB_CRAWLER_BASE_URL=http://localhost:8000
JOB_CRAWLER_API_KEY=dev-api-key

# 支付
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 可选的环境变量

```bash
# Redis
REDIS_URL=redis://localhost:6379

# 邮件
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# 监控
SENTRY_DSN=your-sentry-dsn
```

## 开发工具

### 代码格式化

```bash
# 安装开发工具
pip install black isort flake8

# 格式化代码
black .
isort .

# 检查代码质量
flake8 .
```

### 测试

```bash
# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html

# 运行特定测试
pytest tests/test_resumes.py
```

### 数据库管理

```bash
# 创建迁移
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 查看迁移状态
python manage.py showmigrations

# 重置数据库
python manage.py flush
```

## 项目结构

```
CareerBridge/
├── careerbridge/          # Django 后端
│   ├── careerbridge/     # 项目配置
│   ├── resumes/          # 简历管理
│   ├── mentors/          # 导师服务
│   ├── appointments/     # 预约管理
│   ├── payments/         # 支付管理
│   ├── users/            # 用户管理
│   └── ...
├── frontend/             # React 前端
│   ├── src/
│   ├── public/
│   └── ...
├── JobCrawler/           # 独立爬虫服务
└── docs/                 # 文档
```

## 开发工作流

### 1. 功能开发

```bash
# 创建新分支
git checkout -b feature/new-feature

# 开发功能
# ...

# 运行测试
pytest

# 提交代码
git add .
git commit -m "feat: add new feature"

# 推送分支
git push origin feature/new-feature
```

### 2. 代码审查

- 创建 Pull Request
- 确保所有测试通过
- 代码审查通过后合并

### 3. 部署

```bash
# 生产环境部署
docker-compose -f docker-compose.prod.yml up -d
```

## 调试技巧

### Django 调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 ipdb (更好的调试体验)
pip install ipdb
import ipdb; ipdb.set_trace()
```

### 前端调试

```javascript
// 在浏览器控制台中使用
console.log('Debug info');
debugger; // 断点
```

### 数据库调试

```bash
# 进入 Django shell
python manage.py shell

# 查询数据库
from resumes.models import Resume
Resume.objects.all()
```

## 常见问题

### 1. 依赖安装失败

```bash
# 升级 pip
pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -r requirements.txt --no-cache-dir
```

### 2. 数据库连接问题

```bash
# 检查数据库配置
python manage.py check

# 重置数据库
python manage.py flush
```

### 3. 前端构建失败

```bash
# 清理 node_modules
rm -rf node_modules package-lock.json
npm install

# 清理缓存
npm cache clean --force
```

### 4. 外部服务连接问题

```bash
# 检查 Job Crawler 服务
curl http://localhost:8000/health/

# 检查 Redis
redis-cli ping
```

## 性能优化

### 数据库优化

```python
# 使用 select_related 和 prefetch_related
resumes = Resume.objects.select_related('user').prefetch_related('skills')

# 使用数据库索引
class Resume(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
```

### 缓存优化

```python
# 使用缓存装饰器
from django.core.cache import cache

@cache_page(60 * 15)  # 缓存15分钟
def expensive_view(request):
    # ...
```

### 前端优化

```javascript
// 使用 React.memo 优化组件
const OptimizedComponent = React.memo(({ data }) => {
    return <div>{data}</div>;
});

// 使用 useMemo 和 useCallback
const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
```

## 贡献指南

### 代码规范

- 遵循 PEP 8 (Python)
- 使用 ESLint (JavaScript)
- 编写测试用例
- 添加文档注释

### 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建过程或辅助工具的变动
```

## 支持

如有问题，请：

1. 查看项目文档
2. 搜索现有 Issues
3. 创建新的 Issue
4. 联系开发团队 