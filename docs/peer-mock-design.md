# Peer Mock MVP 设计文档

状态：**设计稿第 2.1 版**（2026-09-29），已按第一轮审查意见修改，并补入 Q1、Q18 的决定。本阶段不含代码和 migration。

标注约定：
- 关于现有代码或外部服务的结论，标 **VERIFIED**（读过代码、实际运行过或查到了官方说明）、**INFERRED**（根据结构推断）或 **UNKNOWN**（需要什么才能确定会写明）。
- 设计假设编号为 **A#**，决定事项编号为 **Q#**（第 10 节）。
- 标 **〔v1.1〕** 的内容保留在文档中，但不在 v1 的开发范围内。

---

## 0. 概览

### 0.1 产品闭环（v1）
1. 注册并验证邮箱（已有）。
2. 用邀请码完成首次资料填写：显示名、时区、面试类型和方向、邮件偏好、同意隐私条款。
3. 每周提交可用时间段。
4. 截止后批量匹配。
5. 发出匹配通知，附 `.ics`。
6. 双方确认，主持人（seat 1）确认时要填写会议链接；任一方都可以取消。
7. 前一天提醒，提醒邮件里附会议链接。
8. 面试结束后确认到场并评分。
9. 更新爽约记录和信誉。

整个过程中，用户可以随时举报或屏蔽搭档、删除账号。所有状态变化都写入事件日志。

### 0.2 v1 与 v1.1 的范围
| 功能 | v1 | 〔v1.1〕 |
|---|---|---|
| 搭档取消后 | 留下的一方下一轮优先匹配（报名状态 `partner_cancelled`，streak 加 1） | 在本轮找替补：ReplacementOffer 表、`reoffer_sweep` 任务、测试 T16 和 T16b（4.7） |
| 改期 | 不支持，只能取消 | RescheduleProposal 改期提议（4.8） |
| 信誉 | 计数加暂停规则 | 衰减规则（4.6） |

### 0.3 与现有系统的关系
- **新代码**全部放在 `gateai/peer_mock/`：模型、服务、视图、任务、测试。现有的 3 个 stub 视图会被替换（VERIFIED：`peer_mock/views.py` 没有模型，`sessions/` 固定返回 `[]`）。
- **User 表**：peer mock 的数据都通过外键关联 `users.User`，不在 User 表上加字段（A1）。
- **不依赖** `decision_slots` 的 HTTP 路由，也不依赖它的模型。v1 不使用 `sys_claim` / ResourceLock，理由见 3.8（Q3，已确定）。
- **Bus**：
  - 所有接口都在 `/api/v1/peer-mock/` 下，由 PEER_MOCK_BUS 控制；
  - 所有定时任务使用 `@bus_gated_task('PEER_MOCK_BUS')`；
  - PEER_MOCK_BUS 在上线前一直保持 OFF（VERIFIED：默认 OFF）。
  - 例外：删除账号的接口放在 `/api/v1/users/me/` 下（KERNEL_CORE）。这是账号级的操作，peer mock 关闭时也必须能用。见 2.7。
- **路由收紧**（Q15，已同意）：
  - `resolve_bus` 目前把路径中含有 `/peer`、`/mock` 子串的请求都归到 PEER_MOCK_BUS（VERIFIED：`bus_power.py:113-114`）。改为只匹配前缀 `/api/v1/peer-mock/`，同时删除 `PATH_TO_FEATURE['/peer/']`。
  - PR1 开始时，先把受影响的现有测试列出来给你确认，再修改。

### 0.4 全局假设
| # | 假设 | 依据 |
|---|---|---|
| A1 | 时区、显示名、邮件偏好放在新建的 `PeerProfile` 上，不改 User 表 | Q17，已确定 |
| A2 | 每人每轮最多 1 个有效场次 | Q3，已确定 |
| A3 | 场次 60 分钟，双方各当 30 分钟面试官；时长作为 Round 的参数 | Q2，已确定 |
| A4 | 面试类型是硬约束，方向是软约束；每次报名只选 1 个类型 | Q4，已确定 |
| A5 | 运营时区为 `America/New_York`，作为配置项 `PEER_MOCK_OPS_TZ`；界面上的截止时间、匹配时间、场次时间都按用户自己的时区显示 | Q1，已确定。用户以美国、加拿大为主，另有伦敦等校区的学生 |
| A6 | 只有验证过邮箱的用户能使用 peer mock 接口 | 登录本身不检查 `email_verified`（VERIFIED：`LoginSerializer`），所以由 peer mock 的权限类 `IsEmailVerified` 把关 |
| A7 | 默认不向搭档展示邮箱；用户可以选择对已确认的搭档公开 | Q6，已确定 |
| A8 | 邮件服务的免费档为每天 100 封、每月 3,000 封 | 免费档的常见限制（INFERRED；上线前要对照所选服务商的实际条款） |
| A9 | 所有 URL 中的对象 id 都用不可枚举的 UUID（`public_id`），另外每次都做对象级权限检查 | 纵深防御 |
| A10 | 首批用户必须有邀请码才能完成资料填写 | Q12，已确定。在 peer mock 这一侧校验，不改注册接口 |

---

## 1. 数据模型

所有表都在 `peer_mock` app 内，表名前缀为 `peer_mock_`。时间字段一律使用 `DateTimeField`（`USE_TZ=True`，存储为 UTC；VERIFIED：`settings_base.py` 中 `TIME_ZONE='UTC'`、`USE_TZ=True`）。

### 1.1 表结构

#### `InviteCode`：邀请码（v1）
| 字段 | 类型 | 约束 / 说明 |
|---|---|---|
| `code_hash` | Char(64) | unique，存邀请码的 sha256，不存明文 |
| `label` | Char(64) | 比如「群 A 第一批」，用来统计渠道 |
| `max_uses` / `uses` | PositiveInt | `CHECK(uses <= max_uses)` |
| `expires_at` | DateTime，null | |
| `active` | Bool | |
| `created_at` | DateTime | |

- 使用邀请码时，对该行 `select_for_update`，`uses` 加 1，所以并发使用时不会超过上限。
- 邀请码由管理命令 `peer_invite_codes create --label … --max-uses …` 生成，明文只在命令输出里显示一次。
- 以后要开放注册时，只需要把 settings 里的 `PEER_MOCK_INVITE_REQUIRED` 改为 False。

#### `PeerProfile`：用户的 peer mock 资料（与 User 一对一）
| 字段 | 类型 | 约束 / 说明 |
|---|---|---|
| `user` | OneToOne → User | `on_delete=CASCADE`，主键 |
| `actor_ref` | UUID | unique，默认 uuid4。事件日志里使用的化名 id，见 6.1 |
| `invite_code` | FK → InviteCode，null | SET_NULL；用来统计渠道 |
| `display_name` | Char(40) | 必填，搭档能看到 |
| `timezone` | Char(64) | 必填，必须在 `zoneinfo.available_timezones()` 中 |
| `default_interview_type` / `default_direction` | Char | 用于预填 |
| `email_round_invites` | Bool | 默认 **False**，每周征集邮件需要用户主动勾选 |
| `share_email_with_partner` | Bool | 默认 False |
| `terms_version` / `terms_accepted_at` | Char(16) / DateTime | 同意的条款和隐私说明的版本及时间，是处理依据（用户同意）的证据 |
| `adult_confirmed_at` | DateTime | 用户确认自己年满 18 岁的时间（条款要求，Q18） |
| `completed_count` / `no_show_count` / `late_cancel_count` / `dispute_count` | PositiveInt | 信誉计数的缓存，可以从场次表重新算出（见 4.6） |
| `suspended_until_round` | FK → Round，null | 这一轮（含）之前不参与匹配 |
| `needs_review` | Bool | True 时不参与匹配，直到管理员处理 |
| `email_bouncing` | Bool | 邮件永久性发送失败时设为 True |
| `created_at` / `updated_at` | DateTime | |

#### `Round`：每周一轮
| 字段 | 类型 | 约束 / 说明 |
|---|---|---|
| `id` | BigAuto | |
| `public_id` | UUID | unique |
| `week_key` | Date | **unique**，场次窗口开始那天在运营时区里的日期 |
| `invite_at` / `submission_deadline` / `matching_at` | DateTime | 都由运营时区换算得到，已处理夏令时（5.1） |
| `window_start` / `window_end` | DateTime | 场次窗口，左闭右开 |
| `earliest_session_start` | DateTime | 等于 `matching_at + LEAD`，默认 LEAD = 48h |
| `session_minutes` | PositiveSmallInt | 默认 60 |
| `status` | Char | `open` → `matching` → `matched` → `finished`，另有 `cancelled` |
| `matched_at` | DateTime，null | |
| `algorithm_version` / `input_digest` | Char | 匹配算法的版本，以及输入的 sha256，用来证明结果可以复现 |
| `invites_enqueued_at` | DateTime，null | 保证征集邮件只入队一次 |

- 约束：`CHECK(window_start < window_end)`，`CHECK(submission_deadline <= matching_at <= earliest_session_start)`。
- 索引：`(status, matching_at)`。

#### `Registration`：某用户参加某一轮
| 字段 | 类型 | 约束 / 说明 |
|---|---|---|
| `round` | FK → Round | CASCADE |
| `user` | FK → User | CASCADE |
| `interview_type` / `direction` | Char | |
| `standby_ok` | Bool | 默认 True。〔v1.1〕没匹配上时，愿意作为替补 |
| `status` | Char | `active` / `withdrawn` / `matched` / `unmatched` / `partner_cancelled`（搭档取消了）/ `dropped`（没在截止前确认） |
| `created_at` / `updated_at` | DateTime | |

- 约束：`UniqueConstraint(round, user)`。
- 索引：`(round, interview_type, status)`。

#### `AvailabilityWindow`：可用时间段
| 字段 | 类型 | 约束 / 说明 |
|---|---|---|
| `registration` | FK → Registration | CASCADE |
| `start_utc` / `end_utc` | DateTime | 用于匹配的唯一依据 |
| `local_start` / `local_end` | naive DateTime | 用户提交时的当地时间，用于回显 |
| `tz_name` | Char(64) | 提交时使用的时区 |

- 约束：`CHECK(start_utc < end_utc)`；时长在 60 分钟到 12 小时之间（在服务层检查）；窗口必须落在 `[round.earliest_session_start, round.window_end)` 以内，超出的部分截掉。
- 写入时，同一个 registration 下重叠或首尾相接的窗口会合并；每人每轮最多 20 个窗口。
- 索引：`(registration, start_utc)`。

#### `Session`：一场面试
| 字段 | 类型 | 约束 / 说明 |
|---|---|---|
| `public_id` | UUID | unique |
| `round` | FK → Round | CASCADE |
| `interview_type` / `direction` | Char | |
| `start_utc` / `end_utc` | DateTime | `CHECK(start_utc < end_utc)` |
| `status` | Char | v1：`matched` / `confirmed` / `cancelled` / `expired` / `closed`；〔v1.1〕增加 `reopened` |
| `outcome` | Char，null | `closed` 时填写：`completed` / `no_show_one` / `no_show_both` / `disputed` / `unknown` |
| `confirm_deadline` | DateTime | |
| `finalize_after` | DateTime | 默认 `end + 72h`；有爽约指控时可能延后（4.6） |
| `video_url` | URL，null | 由用户填写，只接受白名单域名（5.5） |
| `video_set_by_seat` | SmallInt，null | 链接是谁填的 |
| `ics_uid` / `ics_sequence` | UUID / PositiveInt | 取消时 `ics_sequence` 加 1 |
| `relaxed_repeat` | Bool | 这场是否来自补匹配阶段（3.3） |
| `created_at` / `updated_at` / `closed_at` | DateTime | |
| 〔v1.1〕`origin`、`reschedule_count` | | 替补和改期用 |

- 索引：`(status, start_utc)`、`(round, status)`、`(status, finalize_after)`。

#### `SessionParticipant`：场次的参与者（每场 2 个座位）
| 字段 | 类型 | 约束 / 说明 |
|---|---|---|
| `session` | FK → Session | CASCADE |
| `user` | FK → User，null | **SET_NULL**：用户删除账号后，搭档那边的历史记录显示为「已删除的用户」 |
| `round` | FK → Round | 冗余字段，供下面的约束使用 |
| `seat` | PositiveSmallInt | `CHECK(seat IN (1,2))`。seat 1 是主持人，负责提供会议链接（5.5） |
| `status` | Char | `pending` / `confirmed` / `cancelled` / `expired`；〔v1.1〕增加 `replaced` |
| `confirmed_at` / `cancelled_at` | DateTime，null | |
| `cancel_reason` | Char(24) | 只存取消原因的代码，不存自由文本 |
| `late_cancel` | Bool | 距开始不到 24 小时取消 |
| `self_attendance` | Char | `unknown` / `attended` / `missed` |
| `partner_attendance` | Char | `unknown` / `attended` / `no_show` / `late` |
| `accused_at` | DateTime，null | 搭档报告本人 no_show 的时间，用来发通知、计算申诉期限 |
| `appeal_note` | Text(500)，null | 被指控者的申诉说明，只有管理员能看到 |
| `final_attendance` | Char | 结算时写入：`attended` / `no_show` / `disputed` / `unknown` |

约束（**防止重复匹配由数据库保证**）：
- `uniq_active_participation_per_round`：`UniqueConstraint(user, round, condition=Q(status__in=['pending','confirmed']))`。同一个用户在同一轮最多只有一个有效场次。各轮的场次窗口互不重叠（由 Round 的生成规则保证，并有测试 T25 覆盖），所以同一时间段内也最多只有一个场次。
- `uniq_active_seat`：`UniqueConstraint(session, seat, condition=Q(status__in=['pending','confirmed']))`。每个座位最多一个有效参与者，所以每场最多 2 人。
- `uniq_user_per_session`：`UniqueConstraint(session, user)`。同一个人不能同时占两个座位。
- 以上三个都是部分唯一约束，SQLite 和 Postgres 上都生效（与 M2 的 `uniq_active_resource_lock` 做法相同）。

#### `Feedback`：场后评分
| 字段 | 说明 |
|---|---|
| `session`（FK）、`rater`（FK → SessionParticipant，CASCADE） | |
| `ratee` | FK → User，null，SET_NULL |
| `rating` | `CHECK(rating BETWEEN 1 AND 5)` |
| `comment` | Text，最多 1,000 字 |
| `created_at` | |

- 约束：`UniqueConstraint(session, rater)`。
- 可见性（Q8，已确定）：
  - 评论采用双盲：双方都提交后，或者到场次结算时，才对被评价人公开；
  - 评分数字只在累计收到 ≥ 3 条后，以平均值的形式展示。

#### `Block`：屏蔽
- 字段：`blocker`、`blocked`（都是 FK → User，CASCADE）、`created_at`。
- 约束：`UniqueConstraint(blocker, blocked)`，`CHECK(blocker <> blocked)`。
- 屏蔽对双方都生效：只要任意一方屏蔽了另一方，两人就不会再被匹配。

#### `Report`：举报
| 字段 | 说明 |
|---|---|
| `public_id` | |
| `reporter` / `reported` | FK → User，null，SET_NULL |
| `session` | FK，null |
| `category` | `no_show` / `harassment` / `inappropriate` / `spam` / `other` |
| `details` | Text，最多 2,000 字 |
| `status` | `open` / `actioned` / `dismissed` |
| `resolution` / `handled_by` / `handled_at` | 管理员的处理结果 |
| `created_at` | |

- 举报时会自动创建一条 `Block`（举报人屏蔽被举报人）。

#### `EmailOutbox`：待发送的邮件（见 5.2）
| 字段 | 说明 |
|---|---|
| `user` | FK → User，null，SET_NULL |
| `kind` | 邮件种类 |
| `context` | JSON，**只存对象 id**，不存邮件正文和地址 |
| `priority` | SmallInt |
| `send_after` / `send_before` | 发送窗口 |
| `status` | `queued` / `sending` / `sent` / `failed` / `expired` / `cancelled` |
| `attempts` / `next_attempt_at` / `last_error` | `last_error` 截断到 200 字符，不含地址 |
| `provider_message_id` / `sent_at` | |
| `dedupe_key` | Char(128)，**unique** |

- 索引：`(status, next_attempt_at, priority)`、`(sent_at)`。

#### `PeerEvent`：事件日志（见第 6 节）

#### `PreRegistration`：预注册表单导入（Q11，已确定：只用于注册时预填，不代替用户创建账号）
- 字段：`email`（unique）、`display_name`、`interview_type`、`direction`、`timezone`、`consent_at`、`invited_at`、`claimed_by`（FK → User，null）。
- 用户注册并验证邮箱后，如果邮箱匹配，首次资料填写页会预填这些数据。

#### 〔v1.1〕`RescheduleProposal`：改期提议
- 字段：`public_id`、`session`（FK，CASCADE）、`proposer`（FK → SessionParticipant）、`new_start_utc`、`status`（`pending` / `accepted` / `declined` / `expired` / `withdrawn`）、`expires_at = min(提出时间 + 24h, 原开始时间 − 12h)`。
- 约束：`UniqueConstraint(session, condition=Q(status='pending'))`。

#### 〔v1.1〕`ReplacementOffer`：替补邀请
- 字段：`public_id`、`session`（FK）、`candidate`（FK → User，CASCADE）、`seat`、`status`（`open` / `accepted` / `superseded` / `expired` / `declined`）、`expires_at`。
- 约束：`UniqueConstraint(session, candidate)`。

### 1.2 与 User 的关系汇总
| 表 | 删除用户时的外键行为 |
|---|---|
| PeerProfile、Registration → AvailabilityWindow、Block、〔v1.1〕ReplacementOffer | CASCADE（删除） |
| SessionParticipant、Feedback.ratee、Report.reporter/reported、EmailOutbox、PeerEvent.user、PreRegistration.claimed_by | SET_NULL（匿名保留） |
| Feedback（作为评分人） | 随着 participant 行保留，评论文字会被清空（见 1.4） |

现有代码中，User 的外键没有一个使用 `PROTECT`（VERIFIED：grep 结果为 0），所以硬删除 User 不会被外键挡住。各旧模块的外键是 CASCADE 还是 SET_NULL 没有逐个核对（INFERRED），需要在 PR6 的删除测试中覆盖。

### 1.3 个人信息字段清单（只收集 MVP 需要的）
| 字段 | 位置 | 用途 | 谁能看到 |
|---|---|---|---|
| 邮箱 | User.email（已有） | 登录、通知 | 本人和系统；只有本人选择公开时，已确认的搭档才能看到 |
| 用户名、密码哈希 | User（已有） | 登录 | 本人 |
| first_name / last_name / phone / location / avatar | User（已有） | **MVP 不需要**：前端不收集，也不展示 | — |
| 显示名 | PeerProfile | 让搭档知道和谁面试 | 本人、搭档 |
| 时区 | PeerProfile、AvailabilityWindow.tz_name | 时间换算和显示 | 本人（搭档只看到按自己时区显示的时间） |
| 面试类型、方向 | Registration | 匹配 | 本人、搭档 |
| 可用时间段 | AvailabilityWindow | 匹配 | 本人 |
| 匹配历史、确认和取消记录 | Session / SessionParticipant | 避免重复配对、信誉、展示 | 本人；搭档只看到共同的场次 |
| 会议链接 | Session.video_url | 开会 | 场次的双方 |
| 到场情况、申诉说明 | SessionParticipant | 信誉、指标、争议处理 | 本人、管理员（申诉说明只有管理员能看） |
| 评分、评论 | Feedback | 帮搭档改进、质量监控 | 按 Q8 的规则 |
| 屏蔽关系 | Block | 排除匹配 | 屏蔽人本人 |
| 举报内容 | Report | 安全审核 | 举报人本人、管理员 |
| 同意记录、年满 18 岁的确认、邀请码渠道 | PeerProfile | 处理依据和年龄要求的证据、渠道统计 | 系统 |
| 预注册数据 | PreRegistration | 注册时预填 | 系统；60 天内没有认领的会被删除 |
| 邮件发送记录 | EmailOutbox（不存地址和正文） | 重试、限额、排错 | 系统 |
| 事件 | PeerEvent（只存化名 id） | 指标 | 管理员 |
| 基础设施日志：nginx 访问日志里的 IP，以及 Sentry | 已有 | 运维 | 运维人员；保留期限需要写进隐私说明（UNKNOWN：Sentry 是否开启了 `send_default_pii` 还没检查） |

### 1.4 删除账号：哪些删除，哪些匿名保留（Q14，已确定）
删除在一个事务里完成（PR6）。

| 数据 | 处理方式 |
|---|---|
| User 行、PeerProfile、Registration、AvailabilityWindow、Block（双向） | **删除** |
| 未来的有效场次 | 先按「一方取消」的流程处理（4.3），不计入晚取消；搭档会收到通知，下一轮优先匹配 |
| 该用户所有 `queued` 的邮件 | 改为 `cancelled` |
| SessionParticipant（历史场次） | 保留，`user` 置为 NULL，`appeal_note` 清空。搭档的历史显示「已删除的用户」 |
| 他给出的 Feedback | 保留评分数字，**清空评论文字** |
| 他收到的 Feedback | `ratee` 置为 NULL，评论文字清空 |
| Report | 保留 180 天用于安全审核，涉及他的 `reporter`/`reported` 置为 NULL，之后由清理任务删除 |
| PreRegistration | 以他的邮箱为 key 的那一行一并删除 |
| PeerEvent | 保留，`user` 置为 NULL，**`actor_ref` 保留**。profile 删除后，`actor_ref` 已经无法再关联到真实身份，但同一个人的事件之间仍然可以关联，所以复约率之类的统计不会失真。另外写入一条 `account_deleted` 事件 |
| 数据库备份 | 保留 14 天后自然过期，写进隐私说明（需要和实际的备份策略保持一致；UNKNOWN：生产环境的备份策略还没定） |

---

## 2. 接口清单

### 2.1 通用规则
- 前缀 `/api/v1/peer-mock/`，归属 PEER_MOCK_BUS。bus 关闭时，中间件返回 404（VERIFIED：现有的中间件行为）。
- **每个视图都显式声明 `permission_classes`**，不依赖全局默认值。基础组合是：
  `P = [IsAuthenticated, FeatureVisibility, IsEmailVerified]`（FeatureVisibility 放在前面：功能被隐藏时，对所有人都是 404，包括未验证邮箱的用户）
  - `IsEmailVerified`：新增，要求 `request.user.email_verified`，否则返回 403，`code=email_not_verified`；
  - `HasPeerProfile`：新增，要求已经完成资料填写，否则返回 409，`code=onboarding_required`；
  - `IsSuperuser`：新增，只看 `is_superuser`。
- **对象级权限**：queryset 一律先按 `request.user` 过滤，不属于自己的对象返回 **404**，与 FeatureVisibility 的「拒绝即 404」语义一致。请求体中的 `user` 等身份字段一律忽略，序列化器里这些字段都是只读的。
- **错误格式**：沿用 DRF 默认格式 `{"detail": ..., "code": ...}`，字段级错误为 `{"field": [{"message":..., "code":...}]}`。
- **幂等**：状态迁移类接口（confirm、cancel）重复调用时，返回 200 和相同的结果，并且只产生一条事件。
- **限流**：写接口按用户限流，默认 `peer_write: 60/hour`；邮件退订接口按 IP 限流；使用邀请码的接口单独限流（`peer_invite: 10/hour`），防止猜码。
- 时间一律用 ISO 8601 UTC（带 `Z`）返回。需要展示的时间，另外返回按用户时区换算好的 `*_local` 字段和时区缩写，前端直接显示。

### 2.2 资料
| 方法 | 路径 | 权限 | 请求 → 返回 |
|---|---|---|---|
| GET | `me/profile/` | P | → `{display_name, timezone, default_interview_type, default_direction, email_round_invites, share_email_with_partner, terms_version, reputation:{...}}`；还没填写时返回 404，`code=no_profile`，同时附上 `prefill`（来自 PreRegistration） |
| PUT | `me/profile/` | P | `{display_name, timezone, default_interview_type?, default_direction?, email_round_invites, share_email_with_partner, accept_terms_version, confirm_adult, invite_code?}` → 同上。第一次调用时创建 profile，必须同时满足：带有效的邀请码（`PEER_MOCK_INVITE_REQUIRED=True` 时），否则返回 400 `invalid_invite_code`；`accept_terms_version` 等于当前版本，否则返回 400 `terms_not_accepted`；`confirm_adult=true`，否则返回 400 `adult_confirmation_required`。成功后写入 `onboarded` 事件 |
| GET | `meta/` | P | → `{interview_types:[...], directions:{type:[...]}, terms_version, invite_required, limits:{max_windows, min_window_minutes}, video_domains:[...]}` |

### 2.3 轮次和可用时间
| 方法 | 路径 | 权限 | 请求 → 返回 |
|---|---|---|---|
| GET | `rounds/current/` | P + HasPeerProfile | → `{id, status, submission_deadline, window_start, window_end, earliest_session_start, *_local, my_registration: {...} \| null}` |
| GET | `rounds/{id}/registration/` | 同上 | → 我的报名，没有则返回 404 |
| PUT | `rounds/{id}/registration/` | 同上 | 见下文示例。**整体替换**。只在 `round.status=open` 且截止前可以调用，否则返回 409 `round_closed` |
| DELETE | `rounds/{id}/registration/` | 同上 | 截止前退出，返回 204。status 改为 `withdrawn`，保留记录用于统计 |

`PUT` 请求：
```json
{
  "interview_type": "coding",
  "direction": "backend",
  "windows": [
    {"date": "2026-03-10", "start": "18:00", "end": "20:00"},
    {"date": "2026-03-12", "start": "23:00", "end": "01:00"}
  ]
}
```
- `end <= start` 表示结束时间在第二天。
- 时间粒度为 15 分钟。
- 使用的时区是 profile 里的时区。

返回（200）：
```json
{
  "id": "…", "interview_type": "coding", "direction": "backend",
  "windows": [
    {"local": "2026-03-10 18:00–20:00 EDT", "start_utc": "2026-03-10T22:00:00Z", "end_utc": "2026-03-11T00:00:00Z"}
  ],
  "warnings": [
    {"code": "ambiguous_local_time", "window": 1, "message": "2026-11-01 01:30 出现两次，按第一次（EDT，05:30Z）处理"},
    {"code": "clipped", "window": 0, "message": "早于最早可开始时间的部分已去掉"}
  ]
}
```

错误（400）：
- `nonexistent_local_time`：落在夏令时开始时跳过的那一小时里；
- `window_too_short`；
- `outside_round`；
- `too_many_windows`。

### 2.4 场次
| 方法 | 路径 | 权限 | 请求 → 返回 |
|---|---|---|---|
| GET | `sessions/?scope=upcoming\|past` | P | → `[SessionSummary]` |
| GET | `sessions/{sid}/` | P，只限参与者 | → SessionDetail（见下文） |
| POST | `sessions/{sid}/confirm/` | 同上 | `{video_url?}`。**seat 1 确认时，如果场次还没有链接，必须提供 `video_url`**，否则返回 400 `video_url_required`。→ SessionDetail；幂等 |
| POST | `sessions/{sid}/cancel/` | 同上 | `{reason: "schedule_conflict"\|"no_longer_needed"\|"other"}` → SessionDetail；幂等 |
| PUT | `sessions/{sid}/video-link/` | 同上，场次状态为 matched 或 confirmed | `{url}`，只接受白名单域名（5.5）→ SessionDetail。任一方都可以修改 |
| GET | `sessions/{sid}/calendar.ics` | 同上 | → `text/calendar`，包含最新的时间和链接 |
| POST | `sessions/{sid}/attendance/` | 同上，只在场次开始后到结算前可用 | `{self: "attended"\|"missed", partner: "attended"\|"no_show"\|"late", appeal_note?}`；结算前可以修改。被指控者提交 `self=attended` 就等于申诉（4.6） |
| POST | `sessions/{sid}/feedback/` | 同上，且场次已经开始 | `{rating: 1..5, comment?}` → 201；重复提交返回 409 |
| GET | `sessions/{sid}/feedback/` | 同上 | → `{given: {...}\|null, received: {...}\|null}`，其中 `received` 按 Q8 的规则公开 |
| 〔v1.1〕POST | `sessions/{sid}/reschedule/`、`…/reschedule/{pid}/accept\|decline\|withdraw/` | 同上 | 见 4.8 |

SessionDetail 的格式：
```json
{
  "id": "…", "status": "confirmed", "phase": "upcoming",
  "interview_type": "coding", "direction": "backend",
  "start_utc": "…", "end_utc": "…", "start_local": "Tue Mar 10, 19:00 EDT",
  "confirm_deadline": "…",
  "me": {"seat": 1, "is_host": true, "status": "confirmed", "can_cancel": true, "late_cancel_if_now": false},
  "partner": {"display_name": "Alex", "status": "pending", "email": null},
  "video": {"url": "https://meet.google.com/abc-defg-hij", "needs_link": false},
  "attendance": {"accused": false, "appeal_deadline": null}
}
```

### 2.5 〔v1.1〕替补邀请
| 方法 | 路径 | 权限 | 请求 → 返回 |
|---|---|---|---|
| GET | `offers/` | P + HasPeerProfile | → 我的 `open` 邀请 |
| POST | `offers/{oid}/accept/` | 同上，**只限被邀请人** | 成功 → SessionDetail；座位已被别人拿走或邀请已过期 → 409 `offer_unavailable` |
| POST | `offers/{oid}/decline/` | 同上 | → 200 |

### 2.6 屏蔽和举报
| 方法 | 路径 | 权限 | 请求 → 返回 |
|---|---|---|---|
| GET | `blocks/` | P | → `[{id, display_name, created_at}]` |
| POST | `blocks/` | P | `{session_id}`：屏蔽该场次的搭档。**请求里不接受 user id**，只能屏蔽和自己同场过的人 → 201；重复屏蔽返回 200 |
| DELETE | `blocks/{bid}/` | P，只限屏蔽人本人 | → 204 |
| GET | `reports/` | P | → 我提交的举报 |
| POST | `reports/` | P | `{session_id, category, details}` → 201，同时自动屏蔽对方 |

### 2.7 账号、邮件、信誉
| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `me/reputation/` | P | → `{completed, no_shows, late_cancels, disputes, reliability, suspended_until, needs_review}` |
| GET / POST | `email/unsubscribe/?t=<signed>` | `[AllowAny, FeatureVisibility]` + 签名令牌 + IP 限流 | 关闭 `email_round_invites`；POST 用于支持 RFC 8058 的一键退订。令牌使用 `TimestampSigner`，有效期 90 天 |
| DELETE | `/api/v1/users/me/` | `[IsAuthenticated, FeatureVisibility]` | `{password}`（需要再次输入密码）→ 204。放在 users 模块（KERNEL_CORE），通过 `peer_mock` 注册的删除钩子完成 1.4 的处理 |

### 2.8 管理（只限 superuser；Q13，已确定：v1 只做接口和命令，不做前端页面）
| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `admin/reports/?status=open` | `[IsAuthenticated, IsSuperuser, FeatureVisibility]` | 举报审核队列 |
| POST | `admin/reports/{rid}/resolve/` | 同上 | `{action: "dismiss"\|"warn"\|"suspend_1_round"\|"flag_review", note}` |
| GET | `admin/reviews/` | 同上 | `needs_review` 的用户，以及争议场次和申诉说明 |
| POST | `admin/profiles/{actor_ref}/clear-review/` | 同上 | 解除 `needs_review` |
| POST | `admin/rounds/{id}/run-matching/?dry_run=1` | 同上 | 手动触发匹配。dry run 只返回结果，不写入数据库 |
| GET | `admin/metrics/?from=&to=` | 同上 | 返回第 6 节定义的指标 |

管理命令（运维用，不依赖 HTTP）：
- `peer_run_matching`：支持从数据库或 CSV 读取输入（见 3.9）
- `peer_invite_codes create|list|disable`
- `peer_import_preregistrations <csv>`
- `peer_metrics --weeks 4`

---

## 3. 匹配算法

以规格 §6（v1：贪心，确定性）为基础，下面列出调整的地方。

### 3.1 输入
- `round`：窗口、`earliest_session_start`、`session_minutes`，以及作为参数传入的 `now`（算法内部不读系统时钟）。
- 本轮 `status=active` 的每条报名：`user_id`、`interview_type`、`direction`、窗口列表（UTC，已排序、已合并）。
- 历史数据，全部从数据库计算（CSV 模式则从历史文件读取，见 3.9）：
  - `pair_count(u,v)`：两人双方都确认过的场次数；
  - `rounds_since_paired(u,v)`：距离上次配对过了几轮，没配对过则为 ∞；
  - `unmatched_streak(u)`：最近连续多少次报名以 `unmatched` 或 `partner_cancelled` 结束（中间没报名的轮次跳过不计；只要有一场真正完成的场次，就清零）；
  - 屏蔽关系（任意方向）；
  - 暂停状态（`suspended_until_round >= round`，或 `needs_review`）。

### 3.2 约束
- **始终是硬约束**（两个阶段都不放宽）：
  1. 面试类型相同；
  2. 两人窗口的交集中，存在一段长度 ≥ `session_minutes`、开始时间 ≥ `earliest_session_start` 的区间；
  3. 双方之间没有任何方向的屏蔽；
  4. 双方都不在暂停状态；
  5. 每人每轮最多一场。这一条由数据库约束 `uniq_active_participation_per_round` 兜底，不只靠算法保证。
- **第一阶段额外的硬约束**：上一轮刚配对过的不能再配（`rounds_since_paired = 1`，即 **K=1**）。补匹配阶段放宽这一条。
- **软约束**（候选人排序，依次比较）：
  1. 同方向优先；
  2. `repeat_penalty` 小的优先：上一轮配对过记 2（只会在补匹配阶段出现），两轮前配对过记 1，其余记 0；
  3. `pair_count` 小的优先。
- **起始时间**：在交集中找最早的可行开始时间，**按 UTC 15 分钟对齐**（:00/:15/:30/:45）。规格原来是 30 分钟对齐，这里改为 15 分钟，见 3.7 中 T12 的说明。

### 3.3 算法（按面试类型分组，各组分别运行）
```
eligible = 本类型的有效报名，去掉处于暂停状态的用户
tiebreak(u) = sha256(f"{round_key}:{u.user_id}")   # 同一轮内稳定，换一轮就轮换

def build_edges(users, allow_last_round_repeat):
    for 每一对 (u, v)，按 user_id 升序遍历:      # 保证确定性
        overlap = 两个有序区间列表的归并求交          # O(w)
        若满足硬约束（按 allow_last_round_repeat 决定是否排除上一轮的搭档）:
            连边, slot(u,v) = 最早可行的 15 分钟对齐起点

def greedy(users, edges):
    degree(u) = u 在 edges 中的边数
    # 连续没匹配上的人排在最前（公平性），其次才按约束程度排
    order = sort(users, key = (-min(streak(u), 3), degree(u), tiebreak(u)))
    matched = set(); pairs = []
    for u in order:
        if u in matched: continue
        candidates = [v for v in neighbours(u) if v not in matched]
        if not candidates: continue
        v = min(candidates, key = (direction(u) != direction(v),   # 同方向优先
                                   repeat_penalty(u, v),
                                   pair_count(u, v),
                                   -min(streak(v), 3),              # 也优先照顾对方
                                   degree(v),                       # 优先选约束多的搭档
                                   slot(u, v),
                                   tiebreak(v)))
        pairs.append((u, v, slot(u, v))); matched |= {u, v}
    return pairs, users - matched

# 第一阶段：上一轮的搭档是硬约束
pairs1, left = greedy(eligible, build_edges(eligible, allow_last_round_repeat=False))
# 第二阶段（补匹配）：只在剩余用户之间运行，允许上一轮的搭档
pairs2, left = greedy(left, build_edges(left, allow_last_round_repeat=True))
# pairs2 的场次标记 relaxed_repeat = True
leftover = left → Registration.status = unmatched
```
- 整个匹配在**一个事务**里完成，只写入一次。
- 输入先序列化成规范的 JSON（按 id 排序），计算 sha256 后存为 `input_digest`。

### 3.4 奇数人数、剩余用户和重复配对
- **剩余用户**：两个阶段之后，仍然没有可配对象的人，或者奇数人数时多出来的那个人。他们：
  1. 状态标为 `unmatched`，`streak` 加 1，下一轮排在最前面；
  2. 收到一封「本轮未匹配」的低优先级邮件，在应用内也能看到；
  3. 〔v1.1〕进入本轮的替补名单（4.7）。
- **管理员凑数**：v1 不启用（Q16，已确定）。
- **重复配对**（Q16，已确定）：
  - 上一轮配对过：第一阶段硬性排除，补匹配阶段允许，但排在最后考虑；
  - 两轮前配对过：软约束，降低优先级；
  - 更早以前配对过：按 `pair_count` 降低优先级。

### 3.5 多轮之间的公平性
**问题**：规格原来的排序键是 `(degree ASC, streak DESC, tiebreak)`，`streak` 只在度数相同时起作用。结果是，度数最高的人每轮都排在最后处理。如果人数是奇数，每轮剩下的往往都是同一个人。

**调整一：排序的第一关键字改为 `streak DESC`**，最多按 3 封顶。

**性质**：设 u 上一轮没匹配上（streak ≥ 1），本轮至少有一个可配对象，并且本轮 streak ≥ 1 的其他人没有把 u 的全部候选人都占走。那么 u 本轮**一定能匹配上**。
- 原因：在 streak 相同的一组人里，u 之前处理的每个人最多占走一个候选人；
- 这就是测试 T4b 和 T20 的依据。

**调整二：补匹配**。人数少的时候，「上一轮搭档不能再配」这条限制本身就可能造成没人可配（比如某种类型只有 2–3 个人，上一轮刚好互相配过）。第二阶段只在剩余用户之间放宽这一条，屏蔽和暂停仍然是硬约束。因为第二阶段只处理剩余的人，所以不会改变第一阶段已经产生的任何配对。

**代价与兜底**：
- streak 用户先挑，可能占走某个低度数用户唯一的搭档，匹配总数可能因此变少。首批人数少，每轮 streak ≥ 1 的人通常只有每种类型 0–1 个，影响有限（INFERRED）。
- 离线对比：用 blossom 算法（`networkx.max_weight_matching(maxcardinality=True)`）计算最大匹配数，作为测试基准，只在测试里使用。
- 规则：如果贪心算法在真实数据上的匹配数比 blossom 少 5% 以上，就改用带权重的 blossom（规格 L4）。

### 3.6 确定性和复杂度
- **确定性**：
  - 所有遍历都按 `user_id` 或排序键进行，不依赖 dict 或 set 的顺序，不读系统时钟；
  - 输入相同、`round_key` 相同时，结果逐字节相同，`input_digest` 也相同；
  - 所有排序键都以 `tiebreak`（sha256 的结果）结尾，所以不存在未定义的平局。
- **复杂度**（每种类型 n 人，每人 w 个窗口，w ≤ 20）：
  - 建边：O(n² · w)；补匹配阶段只处理剩余的 r 人，是 O(r² · w)，r 通常很小；
  - 排序：O(n log n)；
  - 贪心：O(Σ d log d) ≤ O(n² log n)；
  - n = 2,000、w = 5 时，约 400 万次区间归并，Python 里是秒级（T19：< 10 s）；
  - 首批几十到一两百人时，是毫秒级。

### 3.7 对照规格中的 19 个测试用例
| # | 用例 | 处理 | 说明 |
|---|---|---|---|
| T1 | 2 人同类型，交集 90 分钟 | **沿用** | 期望的开始时间改为「最早的 15 分钟对齐起点」，并且要 ≥ `earliest_session_start`（测试中注入 `now`） |
| T2 | 交集 59 分钟 | 沿用 | |
| T3 | 交集 60 分钟但类型不同 | 沿用 | |
| T4 | 3 人两两兼容 | **调整** | 1 场匹配 + 1 人未匹配，streak = 1。新增 **T4b**：下一轮同样 3 个人，上一轮的剩余者**一定**能匹配上（原规格只要求优先） |
| T5 | A–B 上轮配对过，边为 A–B、C–D、A–C、B–D | 沿用 | 期望 A–C、B–D，都在第一阶段产生，补匹配阶段没有剩余用户。新增 **T5b**：A–B 上一轮配对过，并且两人只和对方有交集。第一阶段两人都匹配不上，补匹配阶段让他们配成一对，`relaxed_repeat = True` |
| T6 | 星形图 | 沿用 | 所有人 streak = 0 时，排序等同于原规格，期望 L3–H、L1–L2 |
| T7 | 同一输入跑两次 | 沿用 | 另外断言 `input_digest` 相同 |
| T8 | 同一输入，换一个 round_key | 沿用 | |
| T9 | 纽约 2026-03-08 02:30（夏令时跳过的时间） | 沿用 | 断言 400 `nonexistent_local_time` 和错误信息 |
| T10 | 纽约 2026-11-01 01:30（出现两次的时间） | 沿用 | 按 fold=0 处理，结果是 05:30Z，并通过 `warnings` 回显 |
| T11 | 纽约 18:00–20:00 与伦敦 23:00–01:00（2026-03-10） | 沿用 | 同时覆盖「结束时间在第二天」。期望 23:00Z；纽约显示 19:00 EDT，伦敦显示 23:00 GMT |
| T12 | Asia/Kolkata（+05:30）的 :30 对齐 | **调整** | 改为 15 分钟对齐后仍然成立。新增 **T12b**：Asia/Kathmandu（+05:45）当地 10:00–11:00 = 04:15–05:15Z，按 30 分钟对齐会找不到起点，按 15 分钟对齐得到 04:15Z |
| T13 | 唯一的交集属于一对屏蔽关系 | 沿用 | 加上反向屏蔽的用例；**补匹配阶段也不能配成** |
| T14 | 因爽约被暂停的用户 | 沿用 | 暂停的定义见 4.6；加上 `needs_review` 的用例；补匹配阶段同样排除 |
| T15 | 并发：两个线程为同一 (round, user) 插入参与者 | **调整** | 约束现在是**部分**唯一约束（只针对 `pending`/`confirmed`）。补充：已取消的行不妨碍插入新的有效行 |
| T16 | 并发：两个替补同时接受同一个座位 | **〔v1.1〕** | 替补流程在 v1.1 实现 |
| T17 | 两个匹配任务并发运行同一轮 | **调整** | 改用 Round 行的 `select_for_update(skip_locked=True)`，代替 advisory lock。代码与数据库无关，在 Postgres 上有效 |
| T18 | confirm ×2、cancel ×2 | 沿用 | 每种都只有一条事件；〔v1.1〕扩展到改期和替补的 accept、decline |
| T19 | 性能：2,000 人，每人 5 个窗口 | 沿用 | < 10 s。另外加一个 2,000 人、每人 20 个窗口的用例，只记录耗时 |

新增的测试：
- **T20**：公平性。
  - **T20a**（中等规模）：固定一组奇数人数的用户，连续跑 10 轮，任何有 ≥ 2 个可配对象的人都不会连续两轮没匹配上。
  - **T20b**（小规模，验证补匹配的作用）：每种类型 5–8 人，用固定随机种子生成 50 组场景，每组连续跑 8 轮（把每轮的结果写回历史，作为下一轮的输入）。分别在关闭和开启补匹配的情况下统计「连续两轮未匹配」的次数。断言：
    1. 每组场景里，开启后的次数 ≤ 关闭时的次数；
    2. 50 组的总次数，开启后严格更少；
    3. 另有一个手工构造的 6 人场景：关闭补匹配时，一定会有人连续未匹配；开启后没有。
- **T21**：早于 `earliest_session_start` 的可行时间会被忽略。
- **T22**：软约束的顺序：同方向优先；两轮前配对过的排在从未配对的后面；补匹配阶段里，上一轮的搭档排在最后。
- **T23**：跨过夏令时切换的窗口。纽约 2026-11-01 00:30–02:30 当地时间 = 04:30Z–07:30Z，实际长 3 小时；3 月切换日同理。
- **T24**：用户提交后修改了时区，已存的 UTC 窗口不变，只有显示随之改变。
- **T25**：Round 的生成横跨夏令时切换的那一周，相邻两轮的窗口首尾相接、不重叠；那一周长 167 或 169 小时。
- **T26**：CSV 模式（3.9）与数据库模式对同一份输入给出完全相同的结果。

### 3.8 为什么 v1 不使用 `sys_claim` / ResourceLock（Q3，已确定）
- `sys_claim` 保证的是「**每个资源**只有一个持有者」，并且锁带有 TTL。peer mock 要保证的不变式是「**每个用户**每轮只有一个有效场次」，场次也不会因为超时而失效。这正好是一个部分唯一约束能直接表达的。
- 如果用 `sys_claim` 来实现，每场匹配要为两个用户各 claim 一次（资源为 (user, round)）。每次都会写审计记录和幂等记录，还要在 `decision_slots` 里新增一个资源类型（需要 migration）。换来的保证和约束完全一样，所以不划算。
- v1 各个流程的仲裁方式：
  - 匹配：Round 行加锁，在一个事务里完成；
  - 确认、取消、填写链接、到场报告：对 Session 行 `select_for_update`。
- 这些都在 Postgres CI 上用 M2 的方法做并发测试。

### 3.9 CSV 输入：上线前手动跑第一轮
`peer_run_matching` 有两种输入方式：
- `--round <id>`：从数据库读取；
- `--csv <file>`：从 CSV 读取，**只做 dry run**，不读写数据库里的任何业务表。
  - 这样在应用上线前，就可以用预注册表单的导出数据，跑一轮手动匹配。
  - 两种方式调用同一个 `matching.py` 纯函数（T26）。

命令格式：
```
python manage.py peer_run_matching --csv registrations.csv \
    --round-key 2026-10-04 \
    --window-start "2026-10-04 00:00" --window-end "2026-10-11 00:00" \
    --earliest-start "2026-10-04 09:00" \
    [--ops-tz America/New_York] [--session-minutes 60] \
    [--history history.csv] [--blocks blocks.csv] \
    --out matches.csv [--strict]
```
- 所有时间参数都按 `--ops-tz` 解释。
- `--round-key` 在 CSV 模式下代替 `round.id`，用于计算 tiebreak。
- CSV 模式下，user_id 由 `sha256(小写的 email)` 生成，所以同一个人跨轮保持稳定。

**`registrations.csv`**（UTF-8，第一行是列名。表单导出后，只需要改列名即可）：
| 列 | 必填 | 格式 | 示例 |
|---|---|---|---|
| `email` | 是 | 邮箱，不区分大小写，用于去重 | `alex@example.edu` |
| `display_name` | 是 | ≤ 40 字 | `Alex` |
| `timezone` | 是 | IANA 时区名 | `America/New_York` |
| `interview_type` | 是 | `coding` / `behavioral` / `system_design` | `coding` |
| `direction` | 否 | 见 Q4 的取值；为空视为 `general` | `backend` |
| `windows` | 是 | 用分号分隔的当地时间段，格式为 `YYYY-MM-DD HH:MM-HH:MM`；结束时间 ≤ 开始时间表示第二天 | `2026-10-05 18:00-20:00; 2026-10-07 23:00-01:00` |
| `consent` | 是 | `yes`，否则这一行不参与匹配 | `yes` |

**`history.csv`**（可选，用于之前几轮手动匹配的结果）：
| 列 | 说明 |
|---|---|
| `round_key` | 那一轮的日期，比如 `2026-09-27` |
| `email` | 参与者 |
| `partner_email` | 搭档；没匹配上时为空 |
| `outcome` | `matched` / `unmatched` / `partner_cancelled` / `completed` |

从这个文件计算 `pair_count`、`rounds_since_paired` 和 `unmatched_streak`。

**`blocks.csv`**（可选）：`email, blocked_email`，两列。

**校验**：
- 时区非法、时间落在夏令时的空档里、窗口太短或超出范围、同一个邮箱出现多次（取最后一行）、缺少同意，都会报出行号和原因。
- 默认跳过出错的行并继续；加上 `--strict` 时，只要有一行出错就整体退出（退出码非 0）。
- 出现两次的当地时间按 fold=0 处理，并在输出里给出警告。

**输出**：
- `matches.csv`：`session_no, interview_type, direction_a, direction_b, start_utc, email_a, name_a, start_local_a, email_b, name_b, start_local_b, relaxed_repeat`。
- `unmatched.csv`（和 `--out` 放在同一目录）：`email, interview_type, reason`，其中 reason 为 `no_candidates`、`odd_one_out` 或 `excluded_suspended`。
- 标准输出只打印汇总：每种类型的人数、匹配数、剩余人数、补匹配数、`input_digest`。**不打印邮箱**。
- 输出文件含个人信息，只写到 `--out` 指定的路径。如果这个路径在仓库目录内且没有被 git 忽略，命令会拒绝执行。

---

## 4. 状态机

### 4.1 Session（v1）
```
matcher ──► matched ──(两人都确认)──► confirmed ──(finalize_after 之后结算)──► closed{outcome}
              │                          │
              │ 任一方取消                │ 任一方取消
              ▼                          ▼
          cancelled ◄─────────────────────┘

matched ──(confirm_deadline 时有人没确认)──► expired
```
- 「提醒」和「进行中」**不作为存储的状态**：
  - 提醒是参与者上的发送记录，靠 `EmailOutbox` 的去重键保证只发一次；
  - 「进行中」「待反馈」由 `now` 相对 `start_utc` / `end_utc` 的位置推算出来，在 API 返回的 `phase` 字段里给出（`upcoming` / `in_progress` / `awaiting_feedback` / `closed`）。
  - 这样定时任务晚跑了也不会出现状态错误。

| 转换 | 触发 | 前置条件（在 Session 行锁内检查） | 副作用 |
|---|---|---|---|
| → matched | 匹配任务 | 数据库约束通过 | 2 个 participant（pending）；匹配结果邮件入队；`matched` 事件 |
| matched → confirmed | 第二个人确认 | 两个座位都是 confirmed，并且已经有会议链接 | `confirmed` 事件 |
| matched/confirmed → cancelled | 任一方取消 | 场次还没开始 | 取消方的 participant → cancelled（距开始不到 24h 时记 `late_cancel`）；另一方收到通知，报名 → `partner_cancelled`，下一轮优先；`.ics` 取消邮件入队 |
| matched → expired | 到了 `confirm_deadline`，有人没确认 | — | 没确认的人：participant → expired，报名 → `dropped`（不获得优先，不计 strike）；已确认的一方：报名 → `partner_cancelled`（下一轮优先），并收到通知 |
| confirmed → closed | 结算任务，`now ≥ finalize_after` | — | 计算 outcome（4.5），更新信誉计数（4.6） |

### 4.2 确认
- **确认截止时间**：`confirm_deadline = start − 24h`。因为 LEAD = 48h，这个时间一定 ≥ 匹配时间 + 24h。
- **会议链接**：seat 1（主持人）确认时，如果还没有链接，必须同时提供链接。所以到截止时间时，所有 confirmed 的场次都一定有链接（5.5）。
- **催促**：在 `max(匹配时间 + 12h, deadline − 12h)` 之后，只给**还没确认的人**发一次催促邮件。如果场次还没有链接，给 seat 1 的催促邮件会特别提醒他填写。

### 4.3 一方取消后，另一方怎么处理
**v1**：
1. 取消方的 participant → `cancelled`。如果距开始不到 24 小时，记 `late_cancel = true`（计入信誉，见 4.6）。
2. 场次 → `cancelled`。
3. 留下的一方收到高优先级通知：「搭档取消了这一场，你不会受到任何影响；下一轮会优先为你匹配。」报名状态 → `partner_cancelled`，streak 加 1。
4. 给双方发 `.ics` 取消邮件（`STATUS:CANCELLED`）。为了节省额度，取消方的这封邮件优先级较低。

〔v1.1〕加入替补流程，见 4.7。

### 4.4 删除账号时的未来场次
按 4.3 处理，但不记 `late_cancel`；搭档收到的通知里不透露对方是删除了账号。

### 4.5 结算：每个人的到场结果
场次开始后，每个参与者回答两个问题：
1. 我是否参加了；
2. 搭档是否到场：到了 / 没来 / 迟到超过 15 分钟。

`finalize_after` 之后统一结算，每个人的结果如下：
| 本人自报 | 搭档说他 | 结果 |
|---|---|---|
| missed | 任意 | **no_show**（本人承认） |
| attended 或 unknown | attended / late | attended |
| attended | no_show | **disputed** |
| unknown | no_show | **no_show**（已通知本人，但本人在申诉期内没有申诉） |
| unknown | unknown | unknown（不计入任何计数） |

**场次结果**：
- 两人都 attended → `completed`；
- 一人 no_show → `no_show_one`；
- 两人都 no_show → `no_show_both`；
- 有 disputed → `disputed`；
- 否则 → `unknown`。

### 4.6 爽约指控、申诉和信誉
**爽约指控与申诉**（v1）：
- 某人被搭档报告为 `no_show` 时，**立即**给他入队一封最高优先级的通知：
  - 告诉他搭档报告他未到场；
  - 说明可以申诉：在场次页面确认「我参加了」，并可以附上说明（`appeal_note`，只有管理员能看到）；
  - 给出申诉截止时间。
- 同一场次里，这封通知只发一次（去重键 `accused:{session}:{user}`）。指控人改回「到了」再改成「没来」，不会重复发送。
- **申诉期**：通知发出后至少 48 小时。`finalize_after = max(end + 72h, accused_at + 48h)`，所以临近结算才提出的指控，也会给被指控者留出完整的申诉时间。
- 被指控者申诉后，这个人的结果是 `disputed`。

**争议的计数**：一次争议同时给**被指控者和指控者**的 `dispute_count` 各加 1。任一方累计 2 次争议，就进入 `needs_review`，由管理员在 `admin/reviews/` 里查看双方的报告和申诉说明，然后决定：解除、警告，或暂停。

**信誉规则**（v1：只有计数和暂停；Q7，已确定）：
- 1 次爽约 = 1 个 strike；2 次晚取消（开场前不到 24 小时）= 1 个 strike。
- 到确认截止时间还没确认：**不计** strike，只把报名标为 `dropped`。
- 累计 2 个 strike：暂停下一轮（`suspended_until_round`）。
- 累计 3 个 strike：`needs_review`。
- 累计 2 次争议：`needs_review`。
- 〔v1.1〕衰减：连续完成 3 场（本人 attended）后，抵消 1 个 strike。

**信誉分**：只给本人看，v1 不影响匹配排序。
```
reliability = round(100 × (completed + 1) / (completed + no_show + 0.5 × late_cancel + 1))
```
加 1 是贝叶斯平滑，新用户默认 100。

### 4.7 〔v1.1〕替补
- **候选人**：满足以下全部条件的人：
  - 本轮报名状态为 `unmatched` 或 `partner_cancelled`，并且 `standby_ok`；
  - **不包括** `dropped` 的用户（他们没有在截止前确认）；
  - 面试类型相同；
  - 窗口**完整覆盖**这个场次的时间；
  - 满足全部硬约束（屏蔽、暂停、上一轮没和留下的一方配对过）；
  - 本轮没有有效场次（由数据库约束保证）。
- **流程**：
  1. 一方取消（或到截止时间未确认），并且距开始 > 12h 时，场次 → `reopened`；
  2. 按 `(streak DESC, 同方向优先, tiebreak)` 排序，同时邀请前 K=2 名候选人，邀请的过期时间为 `min(发出时间 + 6h, start − 12h)`；
  3. 过期后，依次邀请接下来的 2 个人；
  4. 到了 `start − 12h` 仍然没有替补：场次 → `cancelled`，留下的一方按 v1 规则处理。
- **接受**：
  1. 对 Session 行 `select_for_update`；
  2. 检查场次仍然是 `reopened`，并且这个座位还空着；
  3. 插入 participant（直接为 confirmed）；这时如果候选人刚好在另一场里也被接受，部分唯一约束会拦下，返回 409；
  4. 把其他人的邀请改为 superseded；
  5. **如果留下的一方仍是 pending**，给他新的确认截止时间：`confirm_deadline = min(now + 12h, start − 12h)`，并发一封催促邮件；否则场次直接 → confirmed。
- `reopened` 状态下**不允许发起改期**。
- 测试：T16（并发接受同一座位）、T16b（同一人并发接受两场）、候选人筛选（包括 `partner_cancelled`，排除 `dropped`）、新确认截止时间的计算。

### 4.8 〔v1.1〕改期
- 任意一方可以提议一个新时间。新时间要在 round 窗口以内、≥ `now + 12h`、按 15 分钟对齐。API 会给出两人可用时间交集中的建议起点。
- 提议只有在对方接受后才生效，在那之前原时间仍然有效。每场最多改期 2 次。
- **接受之后**：
  - `start_utc` 和 `end_utc` 更新，`ics_sequence` 加 1；
  - 双方都视为已确认；
  - 已经入队但还没发出的提醒邮件改为 `cancelled`，按新时间重新入队；
  - 给双方发新的 `.ics`。
- 拒绝或过期：原时间保持不变。
- 并发：改期接受和取消同时发生时，由 Session 行锁串行化。

### 4.9 Round
- 状态流转：`open` → `matching`（到了 `matching_at`，匹配任务拿到行锁时）→ `matched` → `finished`（`window_end` 之后，并且所有场次都已结算）。
- `cancelled` 只由管理员手动设置。
- 匹配失败时，事务回滚，状态回到 `open`，由下一次任务运行时重试（5.1）。

---

## 5. 定时任务与邮件

### 5.1 定时任务（全部使用 `@bus_gated_task('PEER_MOCK_BUS')`，bus 关闭时直接返回）
**设计原则**：
- beat 只负责按固定间隔触发，**所有「几点做什么」都作为数据存在 Round、Session 和 Outbox 上**（按运营时区换算，已处理夏令时）；
- 每个任务都是「扫描到期的记录，然后推进它们的状态」，天然幂等；
- beat 停机一段时间后，只会造成延迟，不会漏掉；
- celery beat 的 crontab 默认按 UTC 计算，所以不用 crontab 表达「每周一 10:00 纽约时间」。

| 任务 | 间隔 | 做什么 | 失败了怎么办 |
|---|---|---|---|
| `peer_ensure_rounds` | 每小时 | 确保未来 2 周的 Round 都已存在：按运营时区生成各个时间点，靠 `week_key` 唯一约束保证幂等 | 下次运行时补上；轮次缺失时，`rounds/current/` 返回 404，前端显示「下一轮即将开放」 |
| `peer_enqueue_round_invites` | 15 分钟 | 到 `invite_at` 后，给 `email_round_invites=True` 且本轮还没报名的用户各入队一封征集邮件（低优先级）。完成后记 `invites_enqueued_at` | 靠去重键 `invite:{round}:{user}` 保证不重复 |
| `peer_run_due_matching` | 15 分钟 | 找出 `status=open` 且 `now ≥ matching_at` 的轮次：`select_for_update(skip_locked=True)` → 匹配 → 写入结果 → 结果邮件入队。整个过程在一个事务里 | 异常时整体回滚，下次重试。连续 3 次失败会触发 Sentry 告警（`matching_failed` 事件）。可以用管理命令手动运行，也可以先 dry run |
| `peer_confirmation_sweep` | 15 分钟 | 催促邮件入队；到截止时间按 4.1 的 expired 规则处理 | 幂等，下次继续 |
| `peer_enqueue_reminders` | 15 分钟 | 对 confirmed 的场次，在 `[start − 26h, start − 12h]` 窗口内入队提醒邮件（邮件里附会议链接），去重键 `remind24:{session}:{user}:{ics_sequence}` | 同上；发送时再检查一次场次状态，已取消的不发 |
| `peer_enqueue_feedback_requests` | 30 分钟 | 场次结束 1 小时后，入队反馈请求（`send_before = end + 48h`） | 同上 |
| `peer_finalize_sessions` | 每小时 | 结算 `now ≥ finalize_after`、仍是 confirmed 的场次：outcome → 信誉计数 → 暂停和 review 规则 → Round 进入 finished | 每场一个事务，单场失败不影响其他场次 |
| `peer_dispatch_email` | 2 分钟 | 按 5.2 的规则在每日限额内发送 | 见 5.2 |
| `peer_purge` | 每天 | 删除：超过 30 天的已发送或失败邮件记录；超过 180 天的已处理举报；超过 60 天仍未认领的预注册数据 | 下次继续 |
| 〔v1.1〕`peer_reoffer_sweep` | 15 分钟 | 处理过期的替补邀请，邀请下一批候选人；到 `start − 12h` 仍无替补时取消场次 | 同上 |

爽约指控的通知不需要单独的任务：提交到场报告的接口在同一个事务里直接入队。

beat 调度表写在 `CELERY_BEAT_SCHEDULE` 里（和现有做法一致，VERIFIED：`settings_base.py:96`），`peer_mock.tasks` 加入 `CELERY_IMPORTS`。

**默认的周节奏**（运营时区 America/New_York，Q1 已确定）：
| 时间 | 事件 |
|---|---|
| 周一 10:00 | 征集邮件（只发给订阅了的用户；群里同时发帖） |
| 周四 23:59 | 提交截止 |
| 周五 09:00 | 匹配；当天发结果邮件，发不完的顺延到周六 |
| 周日 09:00 起（周五 09:00 + 48h） | 最早的场次可以开始 |
| 周日 00:00 – 下周六 24:00 | 场次窗口 |

这样安排，征集邮件和结果邮件分别在不同的日子发，提醒和反馈邮件会分散到整周。

上表只是运营时区里的定义。界面和邮件里，这些时间都按**用户自己的时区**显示。比如对伦敦的用户，「周四 23:59 截止」显示为「周五 04:59 BST」（夏令时切换前后的那几周，差值会变）。

### 5.2 邮件队列（EmailOutbox）
- **入队**：业务代码只调用 `enqueue(kind, user, context_ids, priority, send_after, send_before, dedupe_key)`，并且**和状态变化在同一个事务里**提交。事务回滚了，邮件也不会留下。
- **渲染**：在**发送时**才渲染邮件。每次都读取最新的场次数据（比如最新的会议链接），同时检查邮件是否仍然有效；已经无效的（比如场次已取消）直接改为 `cancelled`。
- **发送**（`peer_dispatch_email`）：
  1. 计算今日剩余额度：`quota = DAILY_LIMIT − AUTH_RESERVE − 今天已经 sent 的数量`。「今天」按服务商的计数日计算，默认是 UTC 日（UNKNOWN：要核对服务商的规则）。
  2. `SELECT … FOR UPDATE SKIP LOCKED`，取出 `status=queued`、`next_attempt_at ≤ now` 的记录，按 `(priority, send_before, id)` 排序（优先级优先，其次截止时间早的优先），最多取 `min(quota, 20)` 条，标记为 `sending`。
  3. 逐封通过 SMTP 发送（沿用 M3 的 SMTP 配置）：
     - 成功 → `sent`，写入 `email_sent` 事件；
     - 临时性错误（4xx、超时）→ 按 5m、30m、2h、6h 退避重试，最多 5 次；
     - 永久性错误（5xx，比如地址无效）→ `failed`，写入 `email_failed` 事件，并给 profile 标记 `email_bouncing`，应用内提示用户检查邮箱。
  4. 超过 `send_before` 还没发出的邮件 → `expired`，写入事件。比如开场以后才发出提醒就没有意义了。
  5. 卡在 `sending` 超过 15 分钟的记录（worker 崩溃）会重新放回 `queued`。
     - 这意味着投递语义是「**至少一次**」：极少数情况下可能重复发送，但不会漏发。
- **优先级**（数字越小越优先）：

  | 优先级 | 邮件 |
  |---|---|
  | 0 | 爽约指控通知、搭档取消通知 |
  | 1 | 匹配结果（含 `.ics`） |
  | 2 | 前一天提醒 |
  | 3 | 确认催促 |
  | 4 | 反馈请求、取消方的 `.ics` 取消邮件 |
  | 5 | 「本轮未匹配」通知 |
  | 6 | 征集邮件 |

  额度不够时，低优先级的邮件自然往后推；超过 `send_before` 就放弃。所有内容在应用内都能看到，邮件只是通知。
- **认证邮件**：注册验证和重置密码的邮件目前由 users 模块直接调用 `send_mail` 同步发送，不经过这个队列（VERIFIED：`users/serializers.py`）。它们同样占用服务商的每日额度，所以预留 `AUTH_RESERVE = 20` 封/天（Q9，已确定）。
- **退订**：所有非事务性邮件（征集邮件）都带 `List-Unsubscribe` 和一键退订链接。事务性邮件（匹配、提醒、取消、爽约通知）是用户报名后服务本身的一部分；不想再收，可以退出本轮或者删除账号。
- 邮件里的所有链接都指向应用页面，需要登录；不做免登录的「确认 / 取消」签名链接（Q19，已确定）。

### 5.3 邮件量估算（每天 100 封的免费档）
设一轮有 P 个参与者：

| 邮件 | 每轮数量（估计） |
|---|---|
| 征集邮件 | C（只发给订阅者，每次最多 60 封，超出的部分只在群里通知） |
| 匹配结果 | ≈ P |
| 确认催促 | ≈ 0.3P |
| 前一天提醒 | ≈ P |
| 反馈请求 | ≈ P |
| 取消 / 未匹配 / 爽约通知 | ≈ 0.2P |
| **合计** | **≈ 3.5P + C** |

- **每周容量**：(100 − 20) × 7 = 560 封。按 C = 60 计算，**P ≲ 140**。
- **每月上限**：3,000 封 ÷ 4.3 周 ≈ 700 封/周。所以真正的瓶颈是每日上限，而不是每月上限。
- **高峰日（周五匹配日）**：P = 140 时，当天最多发 80 封结果邮件，其余 60 封按 EDF 顺延到周六。场次最早在周日开始，确认截止最早在周六 09:00，所以最紧的那批（周日场次）会最先发出。
- **1 小时前的提醒不发邮件**：改由 `.ics` 里的 `VALARM`（`TRIGGER:-PT1H`）让日历应用自己提醒（Q9，已确定）。
- **扩容时机**：P 连续两轮超过 120 时，升级到付费档，或者把反馈请求改成只在应用内提示。
- 首批活跃用户预计是几十到一两百人，处在免费档能承受的边缘，**上线前需要确认服务商和额度**。

### 5.4 日历邀请（.ics）
- 格式：`METHOD:PUBLISH`（**不写 ATTENDEE**，以免把搭档的邮箱放进邀请里）。
- 内容：
  - `UID:{ics_uid}@<domain>`；
  - 取消时 `SEQUENCE` 加 1；
  - `DTSTART` / `DTEND` 用 UTC（`…Z`）；
  - `SUMMARY`：`Peer mock: coding (with Alex)`；
  - `LOCATION`：**场次页面的 URL**。匹配结果邮件发出时，会议链接通常还没填，所以不写会议链接；
  - `DESCRIPTION`：场次页面的链接，并说明「会议链接和最新时间以此页面为准，前一天的提醒邮件也会附上链接」；
  - `VALARM -PT1H`。
- 从场次页面下载的 `calendar.ics` 是实时生成的，会包含已经填好的会议链接。
- 取消时发一封 `STATUS:CANCELLED` 的 `.ics`，`SEQUENCE` 加 1。
- **UNKNOWN**：`PUBLISH` 方式下，Gmail、Outlook、Apple Calendar 是否会按同一个 UID 取消已有的日程。上线前需要在这三个客户端上实际测试。如果不行，就在取消邮件的正文里明确说明，请用户手动删除日程。邮件里同时附上「添加到 Google 日历」链接作为备用。

### 5.5 视频链接
**meet.jit.si 实测结果（2026-09-29）：要求登录。**
- 公共实例 meet.jit.si 从 2023-08-24 起，不再允许匿名创建房间：第一个进入的人（主持人）必须用 Google、GitHub 或 Facebook 账号登录，其他人可以直接加入（VERIFIED：Jitsi 官方博客 [Authentication on meet.jit.si](https://jitsi.org/blog/authentication-on-meet-jit-si/)）。
- 当前线上的客户端配置也一致：`https://meet.jit.si/config.js` 里配置了 `tokenAuthUrl`（登录页）和访客域 `anonymousdomain: 'guest.meet.jit.si'`，也就是「创建房间需要认证，访客匿名加入」的结构（VERIFIED：2026-09-29 用 curl 读取）。
- 没有在浏览器里实际开会（本机环境做不到）。「谁先进入谁就要登录」这一点，依据的是官方说明和配置（INFERRED 为当前行为）。
- 结论：自动生成 Jitsi 链接后，仍然要求其中一方有 Google、GitHub 或 Facebook 账号并登录，而且谁先进入会议谁就会被要求登录。这对用户是一个意外的障碍，也会造成「进不去会议」式的爽约。

**两种方案的对比（更新后）**：
| | ① 自动生成 Jitsi 链接 | ② 主持人自己填写 Google Meet 或 Zoom 链接 |
|---|---|---|
| 可用时间 | 匹配时就有 | 主持人确认时填写（确认的前提条件），所以所有 confirmed 的场次都一定有链接 |
| 操作负担 | 先进入会议的人必须登录第三方账号，事先无法控制是谁 | 主持人需要创建一个会议并粘贴链接（`meet.google.com/new` 一步即可） |
| 成本 | 0 | 0。Google Meet 个人免费版的一对一会议时长足够；Zoom 免费版的多人会议限 40 分钟（都是 INFERRED，需要核对当前条款），所以页面上推荐 Meet |
| 安全 | 房间名随机，无法猜到，但有链接的人都能进 | 链接是用户输入的，**必须限制域名白名单**，防止被用来给搭档发钓鱼链接 |
| 依赖 | 公共实例的政策和可用性不受我们控制 | 依赖用户自己的账号 |

**推荐：方案 ②，由主持人填写链接，推荐使用 Google Meet**（Q5，按你的指示更新）。
- seat 1 是主持人：同一场中 tiebreak 较小的一方，确定性可复现。
- 主持人确认时必须填写链接；另一方也可以修改链接。
- 白名单：只接受 https 链接，域名限于 `meet.google.com`、`zoom.us`、`*.zoom.us`、`teams.microsoft.com`、`teams.live.com`、`meet.jit.si`。meet.jit.si 保留在白名单里，给愿意登录的用户使用。
- 修改链接不会额外发邮件，以节省额度。链接出现在：场次页面、实时生成的 `calendar.ics`，以及前一天的提醒邮件（提醒在发送时才渲染）。
- 如果主持人一直不确认，到截止时间按 4.1 的 expired 规则处理，留下的一方下一轮优先。

---

## 6. 事件日志与指标

### 6.1 结构（`PeerEvent`）
| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | BigAuto | |
| `occurred_at` | DateTime | 默认 now，建索引 |
| `event_type` | Char(40) | 取值见下 |
| `user` | FK → User，null，SET_NULL | 删除账号后置为 NULL |
| `actor_ref` | UUID，null | 来自 PeerProfile.actor_ref。删除账号后保留，用来在统计中关联同一个人的事件 |
| `actor_kind` | Char(8) | `user` / `system` / `admin` |
| `round_id` / `session_id` | BigInt，null | 普通整数列，不加外键，所以删除场次也不会影响日志 |
| `metadata` | JSON | **不放个人信息**：比如 `{"interview_type":"coding","rating":4,"reason":"schedule_conflict","late":true}` |
| `idempotency_key` | Char(128)，unique，null | 防止重复写入，比如 `confirmed:{session}:{user}` |

- 索引：`(event_type, occurred_at)`、`(actor_ref, occurred_at)`、`(round_id, event_type)`。
- 写入方式：`emit(...)` 和状态变化在**同一个事务**里写入。遇到 `idempotency_key` 冲突时，在 savepoint 里静默忽略。
- 事件日志只追加：模型不提供 update 和 delete 接口，唯一的例外是删除账号时把 `user` 置为 NULL。

**事件类型**（v1）：
- `signup`：User 创建时，由 `post_save` 信号在 peer_mock 这边记录
- `email_verified`、`onboarded`（metadata 含邀请码的 label）
- `round_opened`、`invite_enqueued`
- `availability_submitted`（metadata 含窗口数、总时长）、`registration_withdrawn`
- `matching_run`（metadata 含 n、matches、补匹配数、耗时、`input_digest`）
- `matched`（每人一条，metadata 含 `relaxed_repeat`）、`unmatched`（每人一条）
- `confirmed`、`confirm_expired`、`cancelled`（含 late 标记）、`partner_cancelled`
- `video_link_set`（metadata 只记域名）
- `reminded`
- `attendance_reported`、`no_show_reported`、`appeal_submitted`
- `session_closed`（metadata 含 outcome）
- `attendance_final`（每人一条，metadata 含本人的最终结果）
- `rated`
- `blocked`、`reported`、`report_resolved`
- `suspended`、`review_flagged`、`review_cleared`
- `email_sent`、`email_failed`、`email_expired`（metadata 含 kind）
- `account_deleted`

〔v1.1〕增加 `reoffer_sent`、`reoffer_accepted`、`rescheduled`、`reschedule_declined`。

### 6.2 核心指标的计算方式
按周（Round）统计，用 SQL 视图或 `admin/metrics/` 接口计算。

| 指标 | 定义 | 计算（示意） |
|---|---|---|
| 注册数 | 期间内新注册的人数；另外单独统计完成资料填写的人数，并按邀请码渠道拆分 | `count(distinct actor_ref) where event_type='signup'`（`onboarded` 同理） |
| 提交率 | 某轮提交了可用时间的人数 ÷ 截止时已完成资料填写且未删除的用户数（Q10，已确定）；另外附上「÷ 收到征集邮件的人数」作为参考 | `count(distinct actor_ref) where type='availability_submitted' and round_id=R` 减去最终退出的人，再除以 `count(distinct actor_ref) where type='onboarded' and occurred_at < deadline(R)` |
| 匹配成功率 | 本轮被匹配的人数 ÷ 截止时仍有效的报名人数；另外单独报告补匹配贡献的比例 | `matched(R) / (matched(R) + unmatched(R))`，两者都按人计 |
| 确认率 | 截止前双方都确认的场次数 ÷ 匹配的场次数 | `confirmed` 事件按 session 分组，数出人数为 2 的场次 |
| 到场率 | outcome 为 `completed` 的场次数 ÷ 应当进行的场次数（进入 closed 的场次）。同时报告 `unknown` 和 `disputed` 的占比 | `session_closed.metadata.outcome` |
| 复约率 | 在第 R 轮完成过场次的人中，在 R+1 轮（或者 R+1 到 R+2 轮）又提交了可用时间的比例 | 集合 A = 第 R 轮 `attendance_final` 且结果为 attended、所在场次 outcome = completed 的 actor_ref；集合 B = R+1 轮 `availability_submitted` 的人；结果为 \|A∩B\|/\|A\| |
| 连续未匹配 | 连续两轮都是 unmatched 或 partner_cancelled 的人数（验证 3.5 的公平性） | 按 actor_ref 排列各轮的 `unmatched` / `partner_cancelled` 事件 |
| 平均评分 | 平均评分 | `avg((metadata->>'rating')::int) where type='rated'` |
| 邮件健康度 | 每天发送、失败、过期的数量 | `email_*` 事件按天统计 |

- 以上计算都**只用 `actor_ref`**，不 join User 表。所以删除账号不会让历史指标变化。

---

## 7. 前端页面清单
新页面全部放在 `/peer/*` 下。前端是 nginx 提供的静态文件，不经过 Django 的 bus 控制（INFERRED：由部署结构推断）。上线时导航只显示 peer mock 相关的入口，其他模块的入口隐藏（路由代码保留）。

| 页面 | 路径 | 调用的接口 |
|---|---|---|
| 注册 / 登录 / 验证邮箱（已有） | `/register`、`/login`、`/email-verification` | `users/register`、`login`、`verify-email`、`resend-verification` |
| 首次资料填写 | `/peer/onboarding` | `GET meta/`、`GET me/profile/`（拿到预填数据）、`PUT me/profile/`（带邀请码）。时区默认取 `Intl.DateTimeFormat().resolvedOptions().timeZone`；展示隐私说明和条款，要求分别勾选「同意条款和隐私说明」和「我已年满 18 岁」 |
| 首页 | `/peer` | `GET rounds/current/`、`GET sessions/?scope=upcoming`，显示待办：确认、填写会议链接、反馈、申诉 |
| 提交可用时间 | `/peer/rounds/:id/availability` | `GET rounds/{id}/registration/`、`PUT`、`DELETE`。按当地时间显示周视图，提交后回显 UTC 时间，并把 `warnings` 和夏令时相关的错误显示在对应的时间段上 |
| 我的场次 | `/peer/sessions` | `GET sessions/?scope=upcoming\|past` |
| 场次详情 | `/peer/sessions/:id` | `GET sessions/{sid}/`、`confirm`（主持人要同时填写链接）、`cancel`（晚取消时二次确认）、`PUT video-link`、`calendar.ics`、`POST blocks/`、`POST reports/` |
| 场后反馈与申诉 | `/peer/sessions/:id/feedback` | `POST attendance/`（被指控时显示申诉说明框和截止时间）、`POST feedback/`、`GET feedback/` |
| 设置 | `/peer/settings` | `GET/PUT me/profile/`、`GET me/reputation/`、`GET blocks/`、`DELETE blocks/{id}`、`GET reports/` |
| 删除账号 | `/peer/settings/delete` | `DELETE /api/v1/users/me/`（需要输入密码），完成后清除本地的 token |
| 邮件退订 | `/peer/unsubscribe?t=` | `POST email/unsubscribe/` |
| 隐私说明 / 条款（已有页面，内容需要重写） | `/privacy`、`/terms` | 无（静态页面） |
| 〔v1.1〕替补邀请 | `/peer/offers` | `GET offers/`、`accept`、`decline` |
| 〔v1.1〕改期 | 在场次详情页内 | `reschedule/*` |

前端的时间显示统一使用接口返回的 `*_local` 字段。只有在周视图编辑时，才在前端把时间拆成日期和时刻；不在前端自己做时区换算，换算的唯一来源是服务端。

---

## 8. 测试计划
所有新测试放在 `peer_mock/tests/`，CI 的 `backend-postgres` job 会运行它们（VERIFIED：M4 以后，这个 job 已经是合并闸门）。

### 8.1 单元测试（不访问数据库，或只用 SimpleTestCase）
- **匹配核心** `peer_mock/matching.py` 是纯函数，输入输出都是 dataclass：T1–T14、T19–T22，以及 T4b、T5b、T12b。另有离线的 blossom 对照测试，用 `@skipUnless(networkx)` 跳过，所以 networkx 不会加进运行时依赖。
- **CSV 输入**：3.9 的每一种校验错误；`--strict`；同一个邮箱重复出现；输出文件路径的检查；T26。
- **时区换算** `peer_mock/timeutil.py`：见 8.4。
- **状态机**：
  - 每个转换都要测前置条件、副作用、事件和邮件入队；
  - 所有不合法的转换都返回 409，状态不变；
  - 主持人确认时不填链接返回 400。
- **结算和信誉**：
  - 4.5 表中的每一行；
  - 爽约指控：立即入队最高优先级的通知，而且只发一次；`finalize_after` 按 `accused_at + 48h` 延后；
  - 申诉后结果为 disputed，双方的 `dispute_count` 都加 1；任一方到 2 次就进入 `needs_review`；
  - strike 阈值和暂停规则；信誉分公式的边界值。
- **邮件**：
  - 额度计算，含 AUTH_RESERVE 和日界线；
  - 优先级和 EDF 排序；
  - 重试退避；
  - 永久性错误；
  - `send_before` 过期；
  - `sending` 卡住后回收；
  - 去重键；
  - 发送时发现场次已取消，改为 cancelled；
  - `.ics` 的内容：UTC、UID、SEQUENCE、VALARM、不含 ATTENDEE。
- **视频链接**：白名单通过和拒绝的用例，包括 `javascript:`、`http://`、`zoom.us.evil.com`、`evil.com/zoom.us`、`meet.google.com@evil.com`。
- **邀请码**：错误、过期、停用、用完的邀请码都被拒绝；邀请码只存哈希。
- **Bus 门禁**：
  - PEER_MOCK_BUS 为 OFF 时，每个 peer mock 接口都返回 404；
  - 每个任务都带有 `required_bus == 'PEER_MOCK_BUS'`，bus 关闭时直接返回。
  - 做法和 `chat/test_chat_bus.py` 相同。

### 8.2 IDOR 测试（`peer_mock/tests/test_object_access.py`）
- 准备：用户 A、B、C。A 和 B 同场，C 与 A、B 都无关。请求用 C 的身份（有时也用 A 的身份），去访问属于别人的资源。
- 断言：
  - 读取返回 404；
  - 修改返回 404，**并且数据库里的数据不变**；
  - 事件表和邮件队列里没有新增记录。
- 按接口逐个列出矩阵，每个接口都要有至少一条用例：

| 资源 | 攻击 |
|---|---|
| 报名和可用时间 | C 通过 `rounds/{id}/registration/` 只能读写自己的报名；请求体里带 `user=A` 会被忽略 |
| 场次 | C 对 A–B 场次的 GET、confirm、cancel、video-link、calendar.ics、attendance、feedback |
| 到场和申诉 | B 不能改 A 的 `self_attendance`；A 的 `appeal_note` 不会出现在 B 能看到的任何返回里 |
| 评分 | C 看不到 A、B 的 feedback；A 在 Q8 规定的公开时间之前看不到 B 对他的评价 |
| 屏蔽 | C 不能删除 A 的屏蔽；不能用别人场次的 session_id 去屏蔽；列表里只出现自己的屏蔽记录 |
| 举报 | C 看不到 A 的举报；非 superuser 访问 `admin/*` 一律返回 404 |
| 资料和信誉 | 只能访问 `me/`，接口里没有任何按 id 取别人资料的路径（用测试断言路由表） |
| 删除账号 | A 删除账号后，B 看到的历史里 partner 显示为「已删除的用户」，接口返回里不出现 A 的邮箱或 id |
| 〔v1.1〕改期和替补 | 提议人不能自己 accept；发给 B 的替补邀请，C 不能 accept |

另外为 `IsEmailVerified` 和 `HasPeerProfile` 各写一条拒绝用例。

### 8.3 并发测试（Postgres，沿用 M2 的方法：`TransactionTestCase`、多线程、每个线程独立连接、Barrier 同时起跑、重复 100 次以上）
| # | 场景 | 断言 |
|---|---|---|
| T15 | N 个线程为同一个 (round, user) 插入有效 participant | 恰好 1 个成功，N−1 个 IntegrityError；已取消的行不妨碍插入 |
| T17 | 两个匹配任务同时运行同一轮 | 恰好一个运行，另一个返回 `skipped`；场次数等于单独运行一次的结果 |
| T18c | 同一场次上，confirm 和 cancel 并发；双方同时 cancel | 最终状态一定是合法的组合，每个动作最多产生一条事件 |
| I1 | 同一个邀请码剩最后一次使用机会时，N 个人同时使用 | 恰好 1 个成功 |
| E1 | 两个 dispatch 同时运行 | 每封邮件只被取出一次（SKIP LOCKED）；发送总数不超过额度 |
| 〔v1.1〕T16 / T16b | 替补并发接受 | 见 4.7 |

在 PR 描述里报告 peer_mock 的覆盖率（`coverage` 已经接入 CI）。

### 8.4 时区测试
- T9、T10、T11、T12、T12b、T23、T24、T25（见 3.7）。
- **显示**：同一个场次在纽约、伦敦、上海、加尔各答四个时区显示的时间和时区缩写。
- **边界**：
  - 窗口跨过午夜；
  - 窗口跨过 round 窗口边界时被截掉；
  - 窗口早于 `earliest_session_start`；
  - 运营时区本身在切换夏令时的那一周。
- **`.ics`**：`DTSTART` 一定是 UTC 格式（以 Z 结尾）。
- **非法时区**：`Mars/Olympus` 或空字符串返回 400。
- 测试**不依赖运行机器的时区**：CI 中另外用 `TZ=Asia/Tokyo` 再跑一次时区相关的测试，证明结果和机器时区无关。

### 8.5 集成测试与前端
- **后端完整流程**：注册 → 验证 → 用邀请码填写资料 → 提交 → 匹配 → 确认（主持人填写链接）→ 提醒入队 → 到场 → 评分 → 结算，一个测试走完。
- **前端 jest**（M5 以后 CI 会运行 jest）：
  - 可用时间页面能显示夏令时相关的错误和 warnings；
  - 场次详情页的按钮随状态变化；主持人确认时要求填写链接；
  - 晚取消时有二次确认；
  - 被指控时能看到申诉入口和截止时间；
  - 删除账号时有确认流程。

---

## 9. 开发顺序（可以独立合并的 PR）
每个 PR 都有自己的分支，CI 全绿后以 merge commit 合并。每个 bug 固定是「一个失败测试的 commit + 一个修复的 commit」；小的 lint 和命名修改，在推送前用 `--amend` 合并进去。纯依赖和纯文档的 PR 用 squash 合并。

**整个开发期间 PEER_MOCK_BUS 保持 OFF**：每个 PR 合并后，生产环境的行为都不变；新功能在测试里，以及开发环境里手动打开 bus 后，都可以使用和验证。

### v1
| PR | 范围 | 验收标准 |
|---|---|---|
| **PR1 基础：资料、邀请码、轮次、可用时间** | 开始前先列出 `resolve_bus` 收紧会影响的现有测试，等你确认。模型：InviteCode、PeerProfile、Round、Registration、AvailabilityWindow、PeerEvent、PreRegistration 和 migration；`timeutil`（当地时间 ↔ UTC、round 时间点的生成）；权限类 IsEmailVerified、HasPeerProfile（IsSuperuser 在 PR5 随管理接口一起加入）；2.2、2.3 的接口；`peer_ensure_rounds` 任务；`peer_invite_codes` 命令；`resolve_bus` 前缀收紧。**旧的 stub 视图保留**：`health/`、`status/` 继续保留（`FeatureVisibilityForJwtUsersTest` 用它们作测试接口，见 LATER）；`sessions/` 在 PR2 中由真实接口替换，届时列出 `PeerMockAccessTest` 需要的修改；运营时区配置项 `PEER_MOCK_OPS_TZ`（默认 America/New_York，非法值启动时报错）；本文档第 10 节 Q1、Q18 的更新 | T9–T12b、T23–T25 通过；不同意条款或不确认年满 18 岁时无法完成资料填写；`PEER_MOCK_OPS_TZ` 换成 Europe/London 时，Round 时间点按新时区生成；邀请码用例和 I1 通过；2.2、2.3 的 IDOR 用例通过；bus 关闭时返回 404；`makemigrations --check` 干净 |
| **PR2 匹配与 CSV 试运行** | `matching.py` 纯函数（两阶段）；Session、SessionParticipant 模型和三个部分唯一约束；`peer_run_due_matching` 任务；`peer_run_matching` 命令，支持数据库和 CSV 两种输入（3.9）；`GET sessions/`、`GET sessions/{sid}/`（只读） | T1–T8、T4b、T5b、T13、T14、T19–T22、T26 通过；**T20b 通过**；Postgres 上 T15、T17 通过；用一份样例 CSV 跑 dry run，输出 `matches.csv` 和 `unmatched.csv`，标准输出不含邮箱 |
| **PR3 邮件队列与匹配通知** | EmailOutbox、dispatch、额度、重试；邮件模板（纯文本 + HTML）；`.ics`；匹配结果、未匹配、征集邮件；退订接口 | 8.1 的邮件用例和 E1 通过；在开发环境用 console backend 走一遍：匹配 → 两封带 `.ics` 的邮件 |
| **PR4 场次生命周期（v1）** | confirm（主持人要同时填写链接）、cancel、video-link（白名单）；`confirmation_sweep`、`enqueue_reminders` 任务；取消和催促邮件；搭档取消后的 `partner_cancelled` 优先规则 | 4.1 的所有转换都有测试；T18、T18c 在 Postgres 上通过；视频链接白名单用例通过；2.4 的 IDOR 用例通过；取消后下一轮的匹配结果里，留下的一方排在最前面（端到端测试） |
| **PR5 场后：到场、申诉、评分、信誉、屏蔽、举报** | attendance（爽约指控通知、申诉、`finalize_after` 延后）、feedback（双盲）、结算任务、计数和暂停规则、争议计数和 needs_review；Block、Report；2.8 的管理接口和命令；反馈请求邮件 | 4.5 的规则表逐行有测试；指控通知立即入队且只发一次；申诉期至少 48 小时；双方的争议计数都正确；屏蔽后两个阶段都不会再匹配（端到端测试）；2.6、2.8 的 IDOR 用例通过 |
| **PR6 删除账号与数据保留** | `DELETE /api/v1/users/me/` 和 peer_mock 的删除钩子；`peer_purge` 任务；按 GDPR 水平编写的隐私说明和条款（同时覆盖 UK GDPR、加拿大 PIPEDA，见第 10 节 Q18），更新前端的 `/privacy`、`/terms` 页面，条款版本号随之更新 | 1.4 表中的每一行都有断言；删除后指标不变（用 actor_ref 统计）；删除用户时，所有旧模块的外键都不报错 |
| **PR7 前端 A：主流程** | onboarding（邀请码）、首页、提交可用时间、我的场次、场次详情（确认、填写链接、取消）；导航只保留 peer mock | jest 用例通过；在开发环境打开 bus 后，手动走完「提交 → 匹配 → 确认」 |
| **PR8 前端 B：其余页面** | 场后反馈和申诉、设置、屏蔽和举报、删除账号、退订页 | jest 用例通过；手动走完全流程 |
| **PR9 上线准备** | 指标（`admin/metrics/` 或 SQL 视图）和 `peer_metrics` 命令；`peer_import_preregistrations`；运维文档（每周的运营检查清单、手动匹配、处理举报和 review）；governance seed 确认 PEER_MOCK 功能开关 | 用种子数据跑出第 6 节的全部指标；导入命令能处理重复和格式错误的行 |

PR 之间的依赖：PR1 → PR2 → PR3 → PR4 → PR5 → PR6。PR7 在 PR4 之后就可以开始，PR8 在 PR5 之后，PR9 最后。**PR2 合并后，就可以用 CSV 模式跑手动的第一轮。**

**LATER**：`kernel/tests/test_m12_routing.py::FeatureVisibilityForJwtUsersTest` 改用一个专门的测试接口，不再依赖 peer mock 的 stub；之后 `health/`、`status/` 两个 stub 可以删除。

**上线本身不是一个 PR**：由你按照 PEER_MOCK_BUS 的上线清单（安全审查、邮件域名 SPF/DKIM、`.ics` 在三个客户端上的实测、隐私说明上线、**买好域名后把隐私说明里的 `privacy@<DOMAIN>` 换成真实地址并确认能收信**、生成首批邀请码）逐项确认后，手动打开 bus。

### 〔v1.1〕
| PR | 范围 | 验收标准 |
|---|---|---|
| PR10 替补 | ReplacementOffer、`reoffer_sweep`、`offers/*` 接口、替补邀请邮件、前端替补页面；Session 增加 `reopened` 状态 | 4.7 的全部规则：候选人包括 `partner_cancelled`、排除 `dropped`；留下的一方仍是 pending 时，新的确认截止时间为 `min(now + 12h, start − 12h)`；`reopened` 时不能改期；T16、T16b 在 Postgres 上通过 |
| PR11 改期 | RescheduleProposal、`reschedule/*` 接口、改期邮件和新的 `.ics` | 4.8 的全部规则；改期接受和取消的并发测试；改期后提醒会重新入队 |
| PR12 信誉衰减 | 连续完成 3 场抵消 1 个 strike | 衰减的边界测试；计数可以从场次表重新算出 |

---

## 10. 决定事项
| # | 问题 | 决定 |
|---|---|---|
| Q1 | 运营时区和每周节奏 | 已定：America/New_York，作为配置项 `PEER_MOCK_OPS_TZ`；节奏见 5.1。用户以美国、加拿大为主，另有伦敦等校区的学生，所以界面上的截止时间、匹配时间都按**用户自己的时区**显示（接口返回 `*_local` 字段） |
| Q2 | 场次时长 | 已定：60 分钟（各 30 分钟），参数放在 Round 上 |
| Q3 | 每人每轮场次数；是否走 `sys_claim` | 已定：每人每轮 1 场，用部分唯一约束保证；不走 `sys_claim`（3.8） |
| Q4 | 方向的取值和约束 | 已定：coding 下分 `general_swe` / `frontend` / `backend` / `data_ml` / `mobile`；system design 下分 `general` / `infra`；behavioral 没有方向。方向是软约束；每次报名只选 1 个类型 |
| Q5 | 视频链接 | 已定（按实测结果更新）：meet.jit.si 要求登录，所以改为主持人自己填写链接，推荐 Google Meet（5.5） |
| Q6 | 搭档的联系方式 | 已定：默认不公开；用户可以选择对已确认的搭档公开邮箱 |
| Q7 | 信誉规则 | 已定：按 4.6（v1 只有计数和暂停，争议双方都计数，衰减放到 v1.1） |
| Q8 | 评论的可见性 | 已定：双盲公开；评分数字只在收到 ≥ 3 条后显示平均值 |
| Q9 | 邮件预算 | 已定：为认证邮件预留 20 封/天；1 小时提醒只靠 VALARM；征集邮件只发给订阅者 |
| Q10 | 提交率的分母 | 已定：完成资料填写的用户数；附上收到征集邮件的人数作为参考 |
| Q11 | 预注册数据 | 已定：只导入 PreRegistration 用于预填；只给首批 100–150 人发邀请邮件，分 2 天发完 |
| Q12 | 准入 | 已定：首批使用邀请码（A10） |
| Q13 | 举报审核 | 已定：v1 只做管理接口和命令 |
| Q14 | 删除后的数据处理 | 已定：按 1.4 |
| Q15 | 收紧 `resolve_bus` | 已同意；PR1 开始时先列出受影响的测试 |
| Q16 | 重复配对 | 已定：上一轮配对过的硬性排除（K=1），两轮前的作为软约束；剩余用户补匹配时放宽；不启用管理员凑数 |
| Q17 | 时区的位置 | 已定：PeerProfile |
| Q18 | 隐私和年龄 | 已定：隐私说明按 GDPR 水平编写，同时覆盖 UK GDPR 和加拿大 PIPEDA，在 PR6 中完成，内容包括：<br>1. 用户权利：查看、更正、删除。更正通过设置页完成，删除通过「删除账号」完成；v1 的查看和导出通过邮件申请、人工处理：联系邮箱暂用占位符 `privacy@<DOMAIN>`，**承诺 30 天内答复**（满足 GDPR 和 PIPEDA）；<br>2. 数据存放在美国，属于跨境存储；<br>3. 保存期限，引用 1.4 节；<br>4. 处理依据是用户同意，在首次填写资料时勾选（`terms_version` / `terms_accepted_at`）；<br>5. 条款要求用户年满 18 岁，首次填写资料时要单独确认（`adult_confirmed_at`，在 PR1 实现）。 |
| Q19 | 免登录签名链接 | 已定：不做 |

---

## 附：规格原文与本设计的差异汇总
1. 公平性：排序的第一关键字改为 `streak DESC`，并增加补匹配阶段（3.3、3.5）。
2. 重复配对：硬性排除从 2 轮改为 1 轮，两轮前的作为软约束（3.2）。
3. 起始时间改为按 UTC 15 分钟对齐（T12b）。
4. 最早开始时间从「now + 24h」改为「匹配时间 + 48h」，给确认留出一天（4.2）。
5. 并发匹配的互斥从 advisory lock 改为 Round 行的 `SKIP LOCKED`（T17）。
6. participant 的唯一约束改为部分唯一约束（T15）。
7. 1 小时前的提醒改由 `.ics` 的 VALARM 负责，不发邮件（5.3）。
8. 视频链接改为主持人自己填写，不自动生成 Jitsi 链接（5.5）。
9. 事件日志增加 `actor_ref` 化名，删除账号后指标不失真（6.1）。
10. 替补流程和改期放到 v1.1；v1 中搭档取消后，留下的一方下一轮优先（0.2）。
