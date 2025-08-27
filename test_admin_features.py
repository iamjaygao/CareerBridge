#!/usr/bin/env python3
"""
CareerBridge 管理员功能测试脚本
"""

import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 管理员测试用户凭据
ADMIN_USER = {
    "login": "admin_test",
    "password": "adminpass123"
}

class AdminFeatureTester:
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
    
    def test_admin_login(self):
        """测试管理员登录"""
        print("\n🔐 测试管理员登录...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/users/login/",
                json=ADMIN_USER,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access" in data:
                    self.auth_token = data["access"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("管理员登录", True, f"成功登录管理员: {ADMIN_USER['login']}")
                else:
                    self.log_test("管理员登录", False, "响应中没有访问令牌")
            else:
                self.log_test("管理员登录", False, f"登录失败，状态码: {response.status_code}, 响应: {response.text[:100]}")
        except Exception as e:
            self.log_test("管理员登录", False, f"登录异常: {str(e)}")
    
    def test_admin_health_check(self):
        """测试管理员健康检查"""
        print("\n🏥 测试管理员健康检查...")
        
        if not self.auth_token:
            self.log_test("管理员健康检查", False, "未登录，跳过测试")
            return
        
        try:
            response = self.session.get(f"{API_BASE}/adminpanel/health/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("管理员健康检查", True, "管理员面板健康检查正常")
            else:
                self.log_test("管理员健康检查", False, f"检查失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("管理员健康检查", False, f"检查异常: {str(e)}")
    
    def test_user_management(self):
        """测试用户管理"""
        print("\n👥 测试用户管理...")
        
        if not self.auth_token:
            self.log_test("用户管理", False, "未登录，跳过测试")
            return
        
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
    
    def test_mentor_applications(self):
        """测试导师申请管理"""
        print("\n📝 测试导师申请管理...")
        
        if not self.auth_token:
            self.log_test("导师申请管理", False, "未登录，跳过测试")
            return
        
        try:
            response = self.session.get(f"{API_BASE}/adminpanel/mentors/applications/")
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_test("导师申请管理", True, f"获取到 {len(data['results'])} 个申请")
                else:
                    self.log_test("导师申请管理", True, "获取到申请数据")
            else:
                self.log_test("导师申请管理", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("导师申请管理", False, f"获取异常: {str(e)}")
    
    def test_system_stats(self):
        """测试系统统计"""
        print("\n📊 测试系统统计...")
        
        if not self.auth_token:
            self.log_test("系统统计", False, "未登录，跳过测试")
            return
        
        try:
            response = self.session.get(f"{API_BASE}/adminpanel/stats/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("系统统计", True, "获取到系统统计数据")
            else:
                self.log_test("系统统计", False, f"获取失败，状态码: {response.status_code}")
        except Exception as e:
            self.log_test("系统统计", False, f"获取异常: {str(e)}")
    
    def run_all_tests(self):
        """运行所有管理员功能测试"""
        print("🚀 开始 CareerBridge 管理员功能测试")
        print("=" * 50)
        
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(3)
        
        # 执行所有测试
        self.test_admin_login()
        self.test_admin_health_check()
        self.test_user_management()
        self.test_mentor_applications()
        self.test_system_stats()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📋 管理员功能测试报告")
        print("=" * 50)
        
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
        report_file = f"admin_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
            print("\n🎉 所有管理员功能测试通过！")
        else:
            print(f"\n⚠️ 有 {failed_tests} 个管理员功能测试失败。")

if __name__ == "__main__":
    tester = AdminFeatureTester()
    tester.run_all_tests() 