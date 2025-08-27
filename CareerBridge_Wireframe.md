# CareerBridge Website Wireframe

## 🎯 网站概述
CareerBridge 是一个职业导师匹配平台，连接学生与经验丰富的职业导师。

---

## 📱 1. 首页 (Landing Page)
```
┌─────────────────────────────────────────────────────────────┐
│                    Header Navigation                        │
├─────────────────────────────────────────────────────────────┤
│  [Logo] CareerBridge    [Features] [API] [Admin] [Docs]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    Hero Section                             │
│                                                             │
│              🚀 CareerBridge                                │
│        Connect with Career Mentors                          │
│                                                             │
│        [Admin Panel] [API Documentation]                    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    Features Grid                            │
│                                                             │
│  👥 Mentor     📅 Appointment    📄 Resume                 │
│  Matching      Booking          Analysis                   │
│                                                             │
│  💳 Payments   🔔 Notifications  📊 Progress               │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    API Section                              │
│                                                             │
│  [API Root] [Swagger] [ReDoc] [Admin Panel]                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 2. 登录页面 (Login Page)
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    Login Form                               │
│                                                             │
│              🔐 Welcome Back                                │
│                                                             │
│        ┌─────────────────────────────┐                     │
│        │ Username/Email              │                     │
│        └─────────────────────────────┘                     │
│                                                             │
│        ┌─────────────────────────────┐                     │
│        │ Password                    │                     │
│        └─────────────────────────────┘                     │
│                                                             │
│        [Login Button]                                      │
│                                                             │
│        [Forgot Password?] [Register]                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 3. 仪表板 (Dashboard)
```
┌─────────────────────────────────────────────────────────────┐
│  Sidebar Navigation                                         │
├─────────────────────────────────────────────────────────────┤
│  [Logo] CareerBridge                                        │
│                                                             │
│  📊 Dashboard                                               │
│  👥 Mentors                                                 │
│  📅 Appointments                                            │
│  📄 Resumes                                                 │
│  ⚙️  Settings                                               │
│  👤 Profile                                                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Top Bar                                                    │
│  Welcome, [Username]!  [🔔] [👤]                           │
├─────────────────────────────────────────────────────────────┤
│                    Main Content                             │
│                                                             │
│  📈 Statistics Cards                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Upcoming│ │ Resumes │ │ Sessions│ │ Views   │           │
│  │   3     │ │   5     │ │   12    │ │   45    │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                             │
│  📋 Recent Activity                    🚀 Quick Actions    │
│  ┌─────────────────────────┐ ┌─────────────────────────┐   │
│  │ • Booked session with   │ │ [Upload Resume]         │   │
│  │   John Smith            │ │ [Book Appointment]      │   │
│  │ • Resume analyzed       │ │ [Find Mentor]           │   │
│  │ • Profile updated       │ │                         │   │
│  └─────────────────────────┘ └─────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 👥 4. 导师列表页面 (Mentor List)
```
┌─────────────────────────────────────────────────────────────┐
│  Sidebar Navigation                                         │
├─────────────────────────────────────────────────────────────┤
│                    Main Content                             │
│                                                             │
│  🔍 Search & Filters                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [Search mentors...] [Filter] [Clear]                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📋 Mentor Cards Grid                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ [Avatar]    │ │ [Avatar]    │ │ [Avatar]    │           │
│  │ John Smith  │ │ Sarah Jones │ │ Mike Davis  │           │
│  │ Software    │ │ Marketing   │ │ Data Science│           │
│  │ Engineer    │ │ Manager     │ │ Lead        │           │
│  │ ⭐⭐⭐⭐⭐ (15) │ │ ⭐⭐⭐⭐ (8)   │ │ ⭐⭐⭐⭐⭐ (22) │           │
│  │ $80/hr      │ │ $65/hr      │ │ $95/hr      │           │
│  │ [View] [Book]│ │ [View] [Book]│ │ [View] [Book]│           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ [Avatar]    │ │ [Avatar]    │ │ [Avatar]    │           │
│  │ Lisa Chen   │ │ Tom Wilson  │ │ Emma Brown  │           │
│  │ Product     │ │ UX Designer │ │ HR Manager  │           │
│  │ Manager     │ │             │ │             │           │
│  │ ⭐⭐⭐⭐ (12)  │ │ ⭐⭐⭐⭐⭐ (18) │ │ ⭐⭐⭐⭐ (9)   │           │
│  │ $75/hr      │ │ $70/hr      │ │ $60/hr      │           │
│  │ [View] [Book]│ │ [View] [Book]│ │ [View] [Book]│           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 👤 5. 导师详情页面 (Mentor Detail)
```
┌─────────────────────────────────────────────────────────────┐
│  Sidebar Navigation                                         │
├─────────────────────────────────────────────────────────────┤
│                    Main Content                             │
│                                                             │
│  👤 Mentor Profile                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [Large Avatar] John Smith                            │   │
│  │ Software Engineer at Google                          │   │
│  │ ⭐⭐⭐⭐⭐ (15 reviews) • 8 years experience           │   │
│  │ $80/hour • Available for sessions                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📋 Content Tabs                                           │
│  [About] [Experience] [Reviews] [Booking]                  │
│                                                             │
│  📝 About Section                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Experienced software engineer with expertise in     │   │
│  │ Python, JavaScript, and cloud technologies...       │   │
│  │                                                      │   │
│  │ 🏷️ Skills: Python, JavaScript, AWS, React, Node.js  │   │
│  │ 🎓 Education: Stanford University, Computer Science │   │
│  │ 💼 Experience: Google (5 years), Microsoft (3 years)│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📅 Booking Section                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Select Date: [Calendar Widget]                       │   │
│  │ Select Time: [Time Slots]                            │   │
│  │ Session Type: [Career Advice] [Technical Review]     │   │
│  │ Duration: [30 min] [60 min] [90 min]                 │   │
│  │                                                      │   │
│  │ [Book Session - $80]                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📄 6. 简历管理页面 (Resume Management)
```
┌─────────────────────────────────────────────────────────────┐
│  Sidebar Navigation                                         │
├─────────────────────────────────────────────────────────────┤
│                    Main Content                             │
│                                                             │
│  📄 My Resumes                                             │
│  [Upload Resume]                                           │
│                                                             │
│  📋 Resume Cards                                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Software    │ │ Marketing   │ │ Data Science│           │
│  │ Engineer    │ │ Specialist  │ │ Resume      │           │
│  │ Resume.pdf  │ │ Resume.pdf  │ │ Resume.pdf  │           │
│  │ Uploaded:   │ │ Uploaded:   │ │ Uploaded:   │           │
│  │ 2024-08-15  │ │ 2024-08-10  │ │ 2024-08-05  │           │
│  │ Status: ✅   │ │ Status: ✅   │ │ Status: ⏳   │           │
│  │ Analyzed    │ │ Analyzed    │ │ Analyzing   │           │
│  │ [Download]  │ │ [Download]  │ │ [Download]  │           │
│  │ [View] [AI] │ │ [View] [AI] │ │ [View] [AI] │           │
│  │ [Delete]    │ │ [Delete]    │ │ [Delete]    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                             │
│  📊 Analysis Results                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Overall Score: 85/100                                │   │
│  │                                                      │   │
│  │ ✅ Strengths:                                        │   │
│  │ • Clear structure and formatting                     │   │
│  │ • Relevant skills highlighted                        │   │
│  │                                                      │   │
│  │ ⚠️ Areas for Improvement:                            │   │
│  │ • Add more quantifiable achievements                 │   │
│  │ • Include industry-specific keywords                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📅 7. 预约管理页面 (Appointment Management)
```
┌─────────────────────────────────────────────────────────────┐
│  Sidebar Navigation                                         │
├─────────────────────────────────────────────────────────────┤
│                    Main Content                             │
│                                                             │
│  📅 My Appointments                                        │
│  [Create Appointment]                                      │
│                                                             │
│  📋 Appointment List                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🔵 Upcoming Sessions                                 │   │
│  │ ┌─────────────────────────────────────────────────┐ │   │
│  │ │ John Smith - Software Engineer                  │ │   │
│  │ │ Aug 20, 2024 • 2:00 PM • 60 min                 │ │   │
│  │ │ Career advice session                           │ │   │
│  │ │ [Reschedule] [Cancel] [Join]                    │ │   │
│  │ └─────────────────────────────────────────────────┘ │   │
│  │                                                      │   │
│  │ ┌─────────────────────────────────────────────────┐ │   │
│  │ │ Sarah Jones - Marketing Manager                 │ │   │
│  │ │ Aug 22, 2024 • 10:00 AM • 30 min                │ │   │
│  │ │ Resume review session                           │ │   │
│  │ │ [Reschedule] [Cancel] [Join]                    │ │   │
│  │ └─────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📊 Past Sessions                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✅ Completed Sessions                                │   │
│  │ ┌─────────────────────────────────────────────────┐ │   │
│  │ │ Mike Davis - Data Science Lead                  │ │   │
│  │ │ Aug 15, 2024 • 3:00 PM • 90 min                 │ │   │
│  │ │ Technical interview prep                         │ │   │
│  │ │ [View Notes] [Rate Session]                      │ │   │
│  │ └─────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 8. 管理后台 (Admin Dashboard)
```
┌─────────────────────────────────────────────────────────────┐
│  Admin Header                                              │
├─────────────────────────────────────────────────────────────┤
│  [Logo] Admin Panel    [Health] [Settings] [Logout]        │
├─────────────────────────────────────────────────────────────┤
│  Sidebar Navigation                                         │
├─────────────────────────────────────────────────────────────┤
│  📊 Dashboard                                               │
│  👥 User Management                                         │
│  🎓 Mentor Applications                                     │
│  📅 Appointment Management                                  │
│  ⚙️ System Settings                                         │
│  📈 Analytics                                               │
├─────────────────────────────────────────────────────────────┤
│                    Main Content                             │
│                                                             │
│  📊 System Overview                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Total   │ │ Active  │ │ Pending │ │ Revenue │           │
│  │ Users   │ │ Mentors │ │ Apps    │ │ This    │           │
│  │ 1,234   │ │ 89      │ │ 12      │ │ Month   │           │
│  │         │ │         │ │         │ │ $15,420 │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                             │
│  📋 Recent Activity                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • New user registration: john.doe@email.com        │   │
│  │ • Mentor application approved: Sarah Johnson       │   │
│  │ • Payment processed: $80 for session booking       │   │
│  │ • System backup completed successfully             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🚨 System Health                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✅ Database: Healthy                                 │   │
│  │ ✅ API Services: Operational                         │   │
│  │ ✅ Email Service: Active                             │   │
│  │ ⚠️ Payment Gateway: Minor delays                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 9. 移动端响应式设计
```
┌─────────────────────────────────────────┐
│ Mobile Header                           │
├─────────────────────────────────────────┤
│ [Menu] CareerBridge [🔔] [👤]           │
├─────────────────────────────────────────┤
│                                         │
│  📱 Mobile Dashboard                    │
│                                         │
│  📊 Stats (Stacked)                     │
│  ┌─────────────────────────────────────┐ │
│  │ Upcoming: 3                          │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │ Resumes: 5                           │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │ Sessions: 12                         │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  🚀 Quick Actions                       │
│  [Upload Resume]                        │
│  [Book Appointment]                     │
│  [Find Mentor]                          │
│                                         │
│  📋 Recent Activity                     │
│  ┌─────────────────────────────────────┐ │
│  │ • Booked session with John Smith    │ │
│  │ • Resume analyzed                   │ │
│  │ • Profile updated                   │ │
│  └─────────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🎨 10. 设计系统 (Design System)

### 颜色方案 (Color Palette)
```
Primary Colors:
- Primary Blue: #1976d2
- Secondary Purple: #dc004e
- Success Green: #4caf50
- Warning Orange: #ff9800
- Error Red: #f44336

Background Colors:
- Primary Background: #f5f5f5
- Card Background: #ffffff
- Dark Background: #333333

Text Colors:
- Primary Text: #212121
- Secondary Text: #757575
- Light Text: #ffffff
```

### 字体系统 (Typography)
```
Headings:
- H1: 2.5rem, Bold (700)
- H2: 2rem, Semi-bold (600)
- H3: 1.75rem, Semi-bold (600)
- H4: 1.5rem, Semi-bold (600)

Body Text:
- Body 1: 1rem, Regular (400)
- Body 2: 0.875rem, Regular (400)
- Button: 0.875rem, Semi-bold (600)
```

### 间距系统 (Spacing)
```
- XS: 4px
- S: 8px
- M: 16px
- L: 24px
- XL: 32px
- XXL: 48px
```

### 圆角系统 (Border Radius)
```
- Small: 4px
- Medium: 8px
- Large: 12px
- Extra Large: 16px
```

---

## 🔄 11. 用户流程 (User Flows)

### 新用户注册流程
```
1. 访问首页 → 2. 点击注册 → 3. 填写信息 → 4. 邮箱验证 → 5. 登录成功
```

### 导师申请流程
```
1. 用户登录 → 2. 申请成为导师 → 3. 填写资料 → 4. 提交申请 → 5. 管理员审核 → 6. 批准/拒绝
```

### 预约流程
```
1. 浏览导师 → 2. 选择导师 → 3. 查看详情 → 4. 选择时间 → 5. 确认预约 → 6. 支付 → 7. 预约成功
```

### 简历分析流程
```
1. 上传简历 → 2. AI分析 → 3. 查看结果 → 4. 获取建议 → 5. 优化简历
```

---

## 📋 12. 功能优先级

### 高优先级 (P0)
- ✅ 用户认证系统
- ✅ 导师列表和详情
- ✅ 预约管理系统
- ✅ 简历上传和分析
- ✅ 管理后台

### 中优先级 (P1)
- 🔄 实时聊天功能
- 🔄 支付系统集成
- 🔄 通知系统
- 🔄 评价和反馈

### 低优先级 (P2)
- 📅 视频会议集成
- 📅 学习路径推荐
- 📅 社区论坛
- 📅 移动应用

---

这个线框图展示了 CareerBridge 网站的完整结构和用户界面设计，涵盖了所有主要功能和页面布局。 