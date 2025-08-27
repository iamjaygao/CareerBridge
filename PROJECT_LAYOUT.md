# CareerBridge 项目布局结构

## 📁 项目整体架构

```
CareerBridge/
├── 📁 careerbridge/          # Django 后端
│   ├── 📁 careerbridge/      # Django 项目配置
│   ├── 📁 users/            # 用户管理模块
│   ├── 📁 resumes/          # 简历管理模块
│   ├── 📁 mentors/          # 导师管理模块
│   ├── 📁 appointments/     # 预约管理模块
│   ├── 📁 notifications/    # 通知系统模块
│   ├── 📁 payments/         # 支付系统模块
│   ├── 📁 adminpanel/       # 管理后台模块
│   ├── 📁 chat/            # 实时聊天模块 (P3新增)
│   ├── 📁 external_services/ # 外部服务集成
│   └── 📁 media/           # 媒体文件存储
├── 📁 frontend/            # React 前端
│   ├── 📁 src/
│   │   ├── 📁 components/  # 组件库
│   │   ├── 📁 pages/       # 页面组件
│   │   ├── 📁 services/    # API 服务
│   │   ├── 📁 store/       # Redux 状态管理
│   │   └── 📁 hooks/       # 自定义 Hooks
└── 📁 scripts/             # 部署和测试脚本
```

## 🏗️ 后端架构 (Django)

### 核心应用模块

#### 1. 📁 careerbridge/ (项目配置)
```
careerbridge/
├── settings_base.py        # 基础配置
├── settings_dev.py         # 开发环境配置
├── settings_prod.py        # 生产环境配置
├── urls.py                # 主路由配置
├── asgi.py               # ASGI 配置 (WebSocket支持)
├── wsgi.py               # WSGI 配置
└── celery_app.py         # Celery 异步任务配置
```

#### 2. 📁 users/ (用户管理)
```
users/
├── models.py              # 用户模型
├── views.py              # 用户视图 (21KB, 528行)
├── serializers.py        # 序列化器 (18KB, 459行)
├── urls.py              # 用户路由
├── admin.py             # 管理后台配置
└── backends.py          # 认证后端
```

#### 3. 📁 resumes/ (简历管理) - 核心模块
```
resumes/
├── models.py              # 数据模型 (39KB, 942行)
├── views.py              # 视图层 (58KB, 1498行)
├── serializers.py        # 序列化器 (17KB, 419行)
├── services.py           # 业务逻辑 (17KB, 419行)
├── external_services.py  # 外部服务集成 (15KB, 441行)
├── tasks.py             # Celery 异步任务
├── admin.py             # 管理后台 (8.4KB, 219行)
├── tier_service.py      # 会员等级服务 (12KB, 315行)
├── referral_service.py  # 推荐系统 (12KB, 327行)
├── data_management.py   # 数据管理 (17KB, 436行)
├── legal_disclaimers.py # 法律合规 (14KB, 378行)
└── urls.py              # 路由配置 (5.2KB, 96行)
```

#### 4. 📁 chat/ (实时聊天) - P3新增
```
chat/
├── models.py              # 聊天模型
├── views.py              # 聊天视图
├── serializers.py        # 序列化器
├── consumers.py          # WebSocket 消费者
├── routing.py            # WebSocket 路由
└── urls.py              # REST API 路由
```

#### 5. 📁 mentors/ (导师管理)
```
mentors/
├── models.py              # 导师模型
├── views.py              # 导师视图
├── serializers.py        # 序列化器
├── services.py           # 导师服务
├── tasks.py             # 异步任务
└── urls.py              # 路由配置
```

#### 6. 📁 appointments/ (预约管理)
```
appointments/
├── models.py              # 预约模型
├── views.py              # 预约视图
├── serializers.py        # 序列化器
└── urls.py              # 路由配置
```

#### 7. 📁 payments/ (支付系统)
```
payments/
├── models.py              # 支付模型
├── views.py              # 支付视图
├── serializers.py        # 序列化器
└── urls.py              # 路由配置
```

#### 8. 📁 notifications/ (通知系统)
```
notifications/
├── models.py              # 通知模型
├── views.py              # 通知视图
├── serializers.py        # 序列化器
└── urls.py              # 路由配置
```

#### 9. 📁 adminpanel/ (管理后台)
```
adminpanel/
├── models.py              # 管理模型
├── views.py              # 管理视图
├── serializers.py        # 序列化器
└── urls.py              # 路由配置
```

### 部署和配置文件
```
careerbridge/
├── requirements.txt        # 开发依赖
├── requirements_prod.txt   # 生产依赖
├── docker-compose.yml      # Docker 编排
├── Dockerfile             # Docker 镜像
├── gunicorn.conf.py       # Gunicorn 配置
├── deploy.py              # 部署脚本
├── deployment_config.py   # 部署配置
└── env_template.txt       # 环境变量模板
```

## 🎨 前端架构 (React + TypeScript)

### 核心目录结构

#### 1. 📁 src/components/ (组件库)
```
components/
├── 📁 common/             # 通用组件
│   ├── PageHeader.tsx
│   ├── LoadingSpinner.tsx
│   ├── ErrorAlert.tsx
│   ├── PerformanceMonitor.tsx
│   └── ErrorBoundary.tsx
├── 📁 layout/             # 布局组件
│   └── MainLayout.tsx
├── 📁 chat/              # 聊天组件 (P3新增)
│   └── ChatWindow.tsx
├── 📁 search/            # 搜索组件 (P3新增)
│   └── AdvancedSearch.tsx
├── 📁 mentors/           # 导师组件
│   ├── MentorCard.tsx
│   └── MentorFilterBar.tsx
├── 📁 appointments/      # 预约组件
│   ├── AppointmentCard.tsx
│   └── BookingDialog.tsx
├── 📁 resumes/          # 简历组件
│   └── UploadResumeDialog.tsx
├── 📁 payments/         # 支付组件
│   └── PaymentForm.tsx
├── 📁 forms/            # 表单组件
│   └── FormField.tsx
└── 📁 ui/               # UI 组件
```

#### 2. 📁 src/pages/ (页面组件)
```
pages/
├── 📁 auth/              # 认证页面
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── PasswordResetPage.tsx
│   └── EmailVerificationPage.tsx
├── 📁 dashboard/         # 仪表板
│   └── DashboardPage.tsx
├── 📁 mentors/           # 导师页面
│   ├── MentorListPage.tsx
│   └── MentorDetailPage.tsx
├── 📁 appointments/      # 预约页面
│   ├── AppointmentListPage.tsx
│   └── CreateAppointmentPage.tsx
├── 📁 resumes/          # 简历页面
│   ├── ResumeListPage.tsx
│   ├── UploadResumePage.tsx
│   └── ResumeAnalysisPage.tsx
├── 📁 chat/             # 聊天页面 (P3新增)
│   ├── ChatListPage.tsx
│   └── ChatRoomPage.tsx
├── 📁 payments/         # 支付页面
│   └── PaymentDemoPage.tsx
├── 📁 admin/            # 管理页面
│   ├── AdminDashboardPage.tsx
│   ├── UserManagementPage.tsx
│   ├── MentorApplicationsPage.tsx
│   └── AppointmentManagementPage.tsx
├── 📁 profile/          # 个人资料
│   └── ProfilePage.tsx
├── 📁 settings/         # 设置页面
│   └── SettingsPage.tsx
└── 📁 error/            # 错误页面
    └── NotFoundPage.tsx
```

#### 3. 📁 src/services/ (服务层)
```
services/
├── 📁 api/              # API 服务
│   ├── apiClient.ts
│   ├── authService.ts
│   ├── mentorService.ts
│   ├── appointmentService.ts
│   ├── resumeService.ts
│   ├── chatService.ts   # P3新增
│   ├── paymentService.ts
│   ├── adminService.ts
│   └── searchService.ts
├── 📁 notifications/    # 通知服务 (P3新增)
│   └── notificationService.ts
└── 📁 utils/            # 工具服务
    └── errorHandler.ts
```

#### 4. 📁 src/store/ (状态管理)
```
store/
├── configureStore.ts
├── index.ts
├── rootReducer.ts
└── 📁 slices/
    ├── authSlice.ts
    ├── mentorSlice.ts
    ├── appointmentSlice.ts
    ├── resumeSlice.ts
    └── chatSlice.ts
```

#### 5. 📁 src/hooks/ (自定义 Hooks)
```
hooks/
├── useResponsive.ts
└── useDebounce.ts       # P3新增
```

### 配置文件
```
frontend/
├── package.json          # 依赖配置
├── tsconfig.json         # TypeScript 配置
├── public/
│   ├── manifest.json     # PWA 配置
│   ├── sw.js            # Service Worker (P3新增)
│   └── index.html
└── src/
    ├── App.tsx          # 主应用组件
    ├── index.tsx        # 应用入口
    └── theme/           # 主题配置
```

## 🔧 外部服务集成

### 1. 支付系统 (Stripe)
- PaymentIntents 处理
- Stripe Connect 导师分成
- Webhook 事件处理
- 退款和争议处理

### 2. AI 服务 (OpenAI)
- 简历分析
- 智能建议
- 内容生成

### 3. 外部 API 集成
- ResumeMatcher API
- JobCrawler API
- 邮件服务
- 短信服务

### 4. 监控和日志
- Sentry 错误监控
- Redis 缓存和会话
- Celery 异步任务
- 健康检查

## 📊 项目规模统计

### 后端代码量
- **总行数**: ~15,000+ 行
- **最大模块**: resumes (58KB, 1498行)
- **核心功能**: 用户管理、简历分析、导师系统、支付处理

### 前端代码量
- **总行数**: ~8,000+ 行
- **组件数量**: 50+ 个组件
- **页面数量**: 20+ 个页面
- **服务模块**: 10+ 个服务

### 数据库模型
- **用户相关**: 3 个模型
- **简历相关**: 8 个模型
- **导师相关**: 4 个模型
- **预约相关**: 3 个模型
- **支付相关**: 4 个模型
- **通知相关**: 4 个模型
- **聊天相关**: 3 个模型 (P3新增)

## 🚀 技术栈总结

### 后端技术栈
- **框架**: Django 5.2 + Django REST Framework
- **数据库**: PostgreSQL (生产) / SQLite (开发)
- **缓存**: Redis
- **异步**: Celery + Redis
- **实时通信**: Django Channels + WebSocket
- **支付**: Stripe API
- **AI**: OpenAI API
- **部署**: Docker + Gunicorn

### 前端技术栈
- **框架**: React 19 + TypeScript
- **状态管理**: Redux Toolkit
- **UI 库**: Material-UI (MUI)
- **路由**: React Router
- **HTTP 客户端**: Axios
- **表单**: React Hook Form + Yup
- **实时通信**: WebSocket
- **PWA**: Service Worker
- **构建**: Create React App

## 📈 项目完成度

### ✅ 已完成功能
1. **P1**: 核心功能 (100%)
2. **P2**: 生产环境准备 (100%)
3. **P2扩展**: 性能优化 (100%)
4. **P3**: 前端体验优化 (100%)

### 🎯 当前状态
- **后端**: 生产就绪，包含所有核心功能
- **前端**: 现代化 UI，包含实时功能
- **部署**: Docker 容器化，支持生产环境
- **监控**: 完整的错误监控和性能跟踪

这是一个功能完整、架构清晰、技术栈现代化的全栈职业发展平台！ 