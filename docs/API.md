# CareerBridge API 文档

## 概述

CareerBridge API 是一个 RESTful API，提供 AI 驱动的职业发展平台功能。

## 基础信息

- **Base URL**: `http://localhost:8001/api/v1/`
- **认证**: JWT Token
- **格式**: JSON
- **版本**: v1

## 认证

### 获取 Token

```http
POST /api/v1/users/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123"
}
```

### 使用 Token

```http
Authorization: Bearer <your_token>
```

## 端点概览

### 用户管理
- `POST /api/v1/users/register/` - 用户注册
- `POST /api/v1/users/login/` - 用户登录
- `POST /api/v1/users/logout/` - 用户登出
- `GET /api/v1/users/profile/` - 获取用户资料
- `PUT /api/v1/users/profile/` - 更新用户资料

### 简历管理
- `GET /api/v1/resumes/` - 获取简历列表
- `POST /api/v1/resumes/` - 上传简历
- `GET /api/v1/resumes/{id}/` - 获取简历详情
- `PUT /api/v1/resumes/{id}/` - 更新简历
- `DELETE /api/v1/resumes/{id}/` - 删除简历
- `POST /api/v1/resumes/{id}/analyze/` - 分析简历

### 导师服务
- `GET /api/v1/mentors/` - 获取导师列表
- `GET /api/v1/mentors/{id}/` - 获取导师详情
- `POST /api/v1/mentors/` - 申请成为导师

### 预约管理
- `GET /api/v1/appointments/` - 获取预约列表
- `POST /api/v1/appointments/` - 创建预约
- `GET /api/v1/appointments/{id}/` - 获取预约详情
- `PUT /api/v1/appointments/{id}/` - 更新预约
- `DELETE /api/v1/appointments/{id}/` - 取消预约

### 支付管理
- `POST /api/v1/payments/create-payment-intent/` - 创建支付意图
- `POST /api/v1/payments/confirm-payment/` - 确认支付
- `GET /api/v1/payments/history/` - 获取支付历史

### 外部服务集成
- `GET /api/v1/resumes/external/job-crawler/` - 外部工作爬取
- `POST /api/v1/resumes/external/resume-matcher/` - 外部简历匹配
- `GET /api/v1/resumes/external/health/` - 外部服务健康检查

## 响应格式

### 成功响应

```json
{
    "status": "success",
    "data": {
        // 响应数据
    },
    "message": "操作成功"
}
```

### 错误响应

```json
{
    "status": "error",
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": {}
    }
}
```

## 状态码

- `200` - 成功
- `201` - 创建成功
- `400` - 请求错误
- `401` - 未认证
- `403` - 权限不足
- `404` - 资源不存在
- `500` - 服务器错误

## 分页

支持分页的端点返回格式：

```json
{
    "count": 100,
    "next": "http://localhost:8001/api/v1/resumes/?page=2",
    "previous": null,
    "results": [
        // 数据列表
    ]
}
```

## 示例

### 上传简历

```bash
curl -X POST http://localhost:8001/api/v1/resumes/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@resume.pdf" \
  -F "title=My Resume"
```

### 分析简历

```bash
curl -X POST http://localhost:8001/api/v1/resumes/1/analyze/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "technology",
    "job_title": "software engineer"
  }'
```

## 错误处理

### 常见错误码

- `INVALID_CREDENTIALS` - 无效的认证信息
- `PERMISSION_DENIED` - 权限不足
- `RESOURCE_NOT_FOUND` - 资源不存在
- `VALIDATION_ERROR` - 数据验证错误
- `EXTERNAL_SERVICE_ERROR` - 外部服务错误

### 重试策略

对于外部服务调用，建议实现指数退避重试策略：

```python
import time
import requests

def api_call_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            return response
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # 指数退避
```

## 速率限制

- 认证端点: 5 次/分钟
- 一般端点: 100 次/分钟
- 文件上传: 10 次/分钟

## 支持

如有问题，请联系开发团队或查看项目文档。 