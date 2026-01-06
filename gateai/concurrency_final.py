import os
import django
import threading
from django.utils import timezone
from datetime import timedelta

# 1. 初始化 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateai.settings_base')
django.setup()

from decision_slots.models import ResourceLock

# 清理一下之前的测试数据，确保环境纯净
ResourceLock.objects.filter(resource_id=999).delete()

results = []
barrier = threading.Barrier(2)

def worker(label):
    # 2. 屏障同步：让两个线程像短跑运动员一样在起跑线等待
    barrier.wait()  
    try:
        # 3. 核心竞争：尝试锁定同一个 Resource (ID=999)
        # 只有数据库层面的 Unique Constraint 才能挡住这种微秒级的冲突
        ResourceLock.objects.create(
            decision_id=f"smoke-{label}-{timezone.now().timestamp()}",
            resource_type="APPOINTMENT",
            resource_id=999,
            owner_id=label,
            expires_at=timezone.now() + timedelta(seconds=30)
        )
        results.append(f"{label}:SUCCESS")
    except Exception:
        results.append(f"{label}:FAIL")

print("\n🚀 Starting Real Concurrency Probe...")
t1 = threading.Thread(target=worker, args=(1,))
t2 = threading.Thread(target=worker, args=(2,))

t1.start()
t2.start()
t1.join()
t2.join()

print("\n--- CONCURRENCY RESULT ---")
print(f"Outcome: {results}")
print("--------------------------")

# 4. 判别逻辑
if "1:SUCCESS" in results and "2:SUCCESS" in results:
    print("❌ CRITICAL FAILURE: Double lock detected! Kernel is UNSAFE.")
elif "1:SUCCESS" in results or "2:SUCCESS" in results:
    print("✅ PASS: Integrity maintained. Only one winner.")
else:
    print("⚠️ WARNING: No one succeeded. Check DB connection.")