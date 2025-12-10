#!/bin/bash

echo "🚀 启动 CareerBridge 服务..."

# 检查并启动前端服务
echo "📱 启动前端服务 (3000)..."
cd frontend/build
if ! lsof -i :3000 > /dev/null 2>&1; then
    nohup python3 -m http.server 3000 > /tmp/frontend_server.log 2>&1 &
    echo "✅ 前端服务已启动"
else
    echo "✅ 前端服务已在运行"
fi

# 检查并启动后端服务
echo "🔧 启动后端服务 (8001)..."
cd ../../careerbridge
if ! lsof -i :8001 > /dev/null 2>&1; then
    nohup python3 manage.py runserver 8001 > /tmp/backend_server.log 2>&1 &
    echo "✅ 后端服务已启动"
else
    echo "✅ 后端服务已在运行"
fi

# 检查并启动 JobCrawler
echo "🔍 启动 JobCrawler (8000)..."
cd ../JobCrawler
if ! lsof -i :8000 > /dev/null 2>&1; then
    nohup python3 real_job_crawler.py > /tmp/jobcrawler_server.log 2>&1 &
    echo "✅ JobCrawler 已启动"
else
    echo "✅ JobCrawler 已在运行"
fi

# 检查并启动 ResumeMatcher
echo "🤖 启动 ResumeMatcher (8002)..."
cd ../ResumeMatcher
if ! lsof -i :8002 > /dev/null 2>&1; then
    nohup python3 simple_resume_matcher.py > /tmp/resumematcher_server.log 2>&1 &
    echo "✅ ResumeMatcher 已启动"
else
    echo "✅ ResumeMatcher 已在运行"
fi

echo ""
echo "🎉 所有服务启动完成！"
echo ""
echo "🌐 访问地址:"
echo "   • 前端应用: http://localhost:3000"
echo "   • 测试页面: http://localhost:3000/test-login.html"
echo "   • 后端 API: http://localhost:8001"
echo "   • JobCrawler: http://localhost:8000"
echo "   • ResumeMatcher: http://localhost:8002"
echo ""
echo "📋 Admin 账号:"
echo "   • iamjaygao / admin123"
echo "   • admin / admin123"
