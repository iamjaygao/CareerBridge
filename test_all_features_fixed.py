#!/usr/bin/env python3
"""
CareerBridge 全面功能测试脚本 (修正版)
测试所有主要功能模块
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta

# 配置
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试用户凭据 - 使用与admin无关的测试用户
TEST_USER = {
    "login": "testuser",
    "password": "testpass123"
}

class CareerBridgeTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}: {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_service_health(self):
        """测试服务健康状态"""
        print("\n🔍 测试服务健康状态...")
        
        # 测试后端API可访问性
        try:
            response = self.session.get(f"{API_BASE}/search/popular/jobs/", timeout=5)
            if response.status_code == 200:
                self.log_test("后端API可访问性", True, "后端API正常运行")
            else:
                self.log_test("后端API可访问性", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("后端API可访问性", False, f"连接失败: {str(e)}")
            
        # 测试前端可访问性
        try:
            response = self.session.get(FRONTEND_URL, timeout=5)
            if response.status_code == 200:
                self.log_test("前端可访问性", True, "前端服务正常运行")
            else:
                self.log_test("前端可访问性", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("前端可访问性", False, f"连接失败: {str(e)}")
    
    def test_user_authentication(self):
        """测试用户认证功能"""
        print("\n🔐 测试用户认证功能...")
        
        # 测试用户登录
        try:
            response = self.session.post(
                f"{API_BASE}/users/login/",
                json=TEST_USER,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access" in data:
                    self.auth_token = data["access"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("用户登录", True, f"成功登录用户: {TEST_USER['login']}")
                else:
                    self.log_test("用户登录", False, "响应中没有访问令牌")
            else:
                self.log_test("用户登录", False, f"登录失败，状态码: {response.status_code}, 响应: {response.text[:100]}")
        except Exception as e:
            self.log_test("用户登录", False, f"登录异常: {str(e)}")
    
    def test_dashboard_functionality(self):
        """测试仪表板功能"""
        print("\n📊 测试仪表板功能...")
        
        if not self.auth_token:
            self.log_test("仪表板统计", False, "未登录，跳过测试")
            return
            
        try:
            response = self.session.get(f"{API_BASE}/users/dashboard/stats/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("仪表板统计", True, f"获取到统计数据: {len(data)} 项")
            else:
                self.log_test("仪表板统计", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("仪表板统计", False, f"获取异常: {str(e)}")
    
    def test_search_functionality(self):
        """测试搜索功能"""
        print("\n🔍 测试搜索功能...")
        
        # 测试热门工作
        try:
            response = self.session.get(f"{API_BASE}/search/popular/jobs/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("热门工作搜索", True, f"获取到 {len(data)} 个热门工作")
            else:
                self.log_test("热门工作搜索", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("热门工作搜索", False, f"获取异常: {str(e)}")
        
        # 测试热门技能
        try:
            response = self.session.get(f"{API_BASE}/search/popular/skills/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("热门技能搜索", True, f"获取到 {len(data)} 个热门技能")
            else:
                self.log_test("热门技能搜索", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("热门技能搜索", False, f"获取异常: {str(e)}")
        
        # 测试热门行业
        try:
            response = self.session.get(f"{API_BASE}/search/popular/industries/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("热门行业搜索", True, f"获取到 {len(data)} 个热门行业")
            else:
                self.log_test("热门行业搜索", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("热门行业搜索", False, f"获取异常: {str(e)}")
    
    def test_mentor_functionality(self):
        """测试导师功能"""
        print("\n👨‍🏫 测试导师功能...")
        
        # 测试导师列表
        try:
            response = self.session.get(f"{API_BASE}/mentors/?page=1")
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_test("导师列表", True, f"获取到 {len(data['results'])} 个导师")
                else:
                    self.log_test("导师列表", True, f"获取到导师数据")
            else:
                self.log_test("导师列表", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("导师列表", False, f"获取异常: {str(e)}")
        
        # 测试导师分页
        try:
            response = self.session.get(f"{API_BASE}/mentors/?page=2")
            if response.status_code == 200:
                data = response.json()
                self.log_test("导师分页", True, "分页功能正常")
            else:
                self.log_test("导师分页", False, f"分页失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("导师分页", False, f"分页异常: {str(e)}")
    
    def test_appointment_functionality(self):
        """测试预约功能"""
        print("\n📅 测试预约功能...")
        
        if not self.auth_token:
            self.log_test("预约列表", False, "未登录，跳过测试")
            return
        
        # 测试预约列表
        try:
            response = self.session.get(f"{API_BASE}/appointments/appointments/?status=upcoming&page=1")
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_test("预约列表", True, f"获取到 {len(data['results'])} 个预约")
                else:
                    self.log_test("预约列表", True, "获取到预约数据")
            else:
                self.log_test("预约列表", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("预约列表", False, f"获取异常: {str(e)}")
    
    def test_resume_functionality(self):
        """测试简历功能"""
        print("\n📄 测试简历功能...")
        
        if not self.auth_token:
            self.log_test("简历列表", False, "未登录，跳过测试")
            return
        
        # 测试简历列表
        try:
            response = self.session.get(f"{API_BASE}/resumes/")
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_test("简历列表", True, f"获取到 {len(data['results'])} 个简历")
                else:
                    self.log_test("简历列表", True, "获取到简历数据")
            else:
                self.log_test("简历列表", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("简历列表", False, f"获取异常: {str(e)}")
    
    def test_admin_functionality(self):
        """测试管理员功能"""
        print("\n⚙️ 测试管理员功能...")
        
        if not self.auth_token:
            self.log_test("管理员健康检查", False, "未登录，跳过测试")
            return
        
        # 测试管理员健康检查
        try:
            response = self.session.get(f"{API_BASE}/adminpanel/health/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("管理员健康检查", True, "管理员面板健康检查正常")
            else:
                self.log_test("管理员健康检查", False, f"检查失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("管理员健康检查", False, f"检查异常: {str(e)}")
        
        # 测试用户管理
        try:
            response = self.session.get(f"{API_BASE}/adminpanel/users/")
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_test("用户管理", True, f"获取到 {len(data['results'])} 个用户")
                else:
                    self.log_test("用户管理", True, "获取到用户数据")
            else:
                self.log_test("用户管理", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("用户管理", False, f"获取异常: {str(e)}")
    
    def test_chat_functionality(self):
        """测试聊天功能"""
        print("\n💬 测试聊天功能...")
        
        if not self.auth_token:
            self.log_test("聊天房间", False, "未登录，跳过测试")
            return
        
        # 测试聊天房间列表
        try:
            response = self.session.get(f"{API_BASE}/chat/rooms/")
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_test("聊天房间列表", True, f"获取到 {len(data['results'])} 个聊天房间")
                else:
                    self.log_test("聊天房间列表", True, "获取到聊天房间数据")
            else:
                self.log_test("聊天房间列表", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("聊天房间列表", False, f"获取异常: {str(e)}")
    
    def test_payment_functionality(self):
        """测试支付功能"""
        print("\n💳 测试支付功能...")
        
        if not self.auth_token:
            self.log_test("支付意图创建", False, "未登录，跳过测试")
            return
        
        # 测试创建支付意图
        try:
            payment_data = {
                "mentor_id": 1,
                "payment_type": "appointment",
                "amount": "10.00",
                "currency": "USD",
                "provider": "stripe",
                "description": "测试支付"
            }
            response = self.session.post(
                f"{API_BASE}/payments/create-intent/",
                json=payment_data,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("支付意图创建", True, "成功创建支付意图")
            else:
                self.log_test("支付意图创建", False, f"创建失败，状态码: {response.status_code}, 响应: {response.text[:100]}")
        except Exception as e:
            self.log_test("支付意图创建", False, f"创建异常: {str(e)}")
    
    def test_swagger_documentation(self):
        """测试API文档"""
        print("\n📚 测试API文档...")
        
        try:
            response = self.session.get(f"{BASE_URL}/swagger/")
            if response.status_code == 200:
                self.log_test("Swagger文档", True, "API文档可访问")
            else:
                self.log_test("Swagger文档", False, f"访问失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("Swagger文档", False, f"访问异常: {str(e)}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始 CareerBridge 全面功能测试 (修正版)")
        print("=" * 60)
        
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(3)
        
        # 执行所有测试
        self.test_service_health()
        self.test_user_authentication()
        self.test_dashboard_functionality()
        self.test_search_functionality()
        self.test_mentor_functionality()
        self.test_appointment_functionality()
        self.test_resume_functionality()
        self.test_admin_functionality()
        self.test_chat_functionality()
        self.test_payment_functionality()
        self.test_swagger_documentation()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📋 测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # 保存详细报告
        report_file = f"test_report_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        if failed_tests == 0:
            print("\n🎉 所有测试通过！CareerBridge 项目功能正常！")
        else:
            print(f"\n⚠️ 有 {failed_tests} 个测试失败，请检查相关功能。")

if __name__ == "__main__":
    tester = CareerBridgeTester()
    tester.run_all_tests() 