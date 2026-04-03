"""
你这段配置里，每一个“技术名词”的通俗解释 + 它在你这套 Stage-1 里到底意味着什么（带权威来源引用）。

========================
A) deliverables 里的名词
========================

1) eval/ module
- 含义：你自己实现的一套“离线评测工具/评测框架”，专门用来量化检索/排序/匹配系统到底好不好。
- 在你这里：它不是“模型”，而是“尺子”。给定一批测试 query + 标注的 ground truth（正确答案/正确chunk/正确JD等），跑完后产出数字指标。

1.1) Recall@K
- 含义：在“前 K 个结果”里，你找回了多少比例的“所有相关项”。更偏“覆盖率/找全”。:contentReference[oaicite:0]{index=0}
- 公式直观理解：如果某个 query 一共有 |G| 个正确相关项，你 top-K 结果里命中了 |G ∩ S_k| 个，
  Recall@K = |G ∩ S_k| / |G|。:contentReference[oaicite:1]{index=1}
- 在 RAG/向量检索里：它回答的是“该找的资料，我找全了没？”（找不全，后面生成再强也救不回来）

1.2) MRR (Mean Reciprocal Rank)
- 含义：只看“第一个正确结果”排在第几名；越靠前越好。:contentReference[oaicite:2]{index=2}
- 直觉：第一个正确结果排第 1 名 -> 得分 1；排第 2 名 -> 0.5；排第 3 名 -> 0.333...
  然后对所有 query 取平均。:contentReference[oaicite:3]{index=3}
- 在你这里：MRR 很适合衡量“用户点开第一个命中”的体验（比如 top-1/top-3 的可用性）。

1.3) nDCG (Normalized Discounted Cumulative Gain)
- 含义：一个“排名质量”指标：相关的结果越靠前越好；并且允许“相关度分级”（非常相关/一般相关/不相关）。:contentReference[oaicite:4]{index=4}
- “Discounted”的意思：越往后排名折扣越大；“Normalized”的意思：除以理想最优排序的 DCG，让分数落在 0~1 可比。:contentReference[oaicite:5]{index=5}
- 在你这里：如果你有分级标签（比如 chunk relevance 0/1/2），nDCG 比 MRR 更能体现“整体排序好不好”。

1.4) benchmark CLI
- 含义：命令行工具（CLI = Command Line Interface），你可以在终端一条命令跑评测，比如：
  `make benchmark` 或 `python -m eval.benchmark ...`
- 在你这里：核心是“可重复、可自动化”（CI 里也能跑），输出一份固定格式的 metrics（JSON/console/文件）。

2) docker-compose RAG service
- 含义：用 Docker Compose 把“多容器服务”定义在一个 YAML 文件里，一条命令就能把整套服务拉起来。:contentReference[oaicite:6]{index=6}
- 在你这里：RAG service 不是单一进程，通常至少包含：
  - API 服务（FastAPI）
  - 向量库（Chroma）
  - 可能还有：embedding worker、数据导入脚本、监控等
- 为什么必须 docker-compose：
  - 让“别人 clone 你的 repo 后”能直接 `docker compose up` 跑起来，环境一致。:contentReference[oaicite:7]{index=7}

2.1) RAG service（你这里的“标准服务”含义）
- 含义：把 RAG 从“脚本实验”做成“可部署的服务”：对外提供 HTTP API，内部完成
  (ingest -> embed -> store -> retrieve -> assemble context -> return) 的稳定流程。
- 注意：RAG 本质是“检索增强生成”，但你 Stage-1 这份 deliverables 里提到的是 FastAPI + Chroma，
  这更像是在先把“Retrieval/Context 生成”服务化，后面再接不同 LLM。

2.2) FastAPI
- 含义：Python 的高性能 Web API 框架，用类型标注做参数校验，并能自动生成 OpenAPI 文档。:contentReference[oaicite:8]{index=8}
- 在你这里：它就是 RAG service 的“HTTP 外壳”，提供 endpoints：
  /ingest, /query, /health, /metrics 等。

2.3) Chroma
- 含义：面向 LLM 应用的开源向量数据库，用来存 embedding 并做相似度检索。:contentReference[oaicite:9]{index=9}
- 在你这里：它是 RAG 的“检索引擎/向量索引层”：你把简历/JD/chunks embedding 后写进去，
  query embedding 后 top-k 拉回相关 chunks。

3) GateAI runtime router (retry/fallback/budget)
- 含义：一个“运行时路由器/调度器”，决定一次请求该调用哪个 LLM、失败如何重试、何时降级、成本如何控制。
- 你写的三个关键词分别是：

3.1) retry
- 含义：请求失败后按策略再次尝试（例如：网络超时、5xx、429）。
- 关键点：要有“可控重试”，否则会把错误放大（retry storm）。

3.2) fallback
- 含义：主模型不可用/超预算/延迟过高时，切换到备用模型或备用策略。
- 例子：GPT-4 类失败 -> 切到更便宜/更快的模型；或从“生成”降级为“只返回检索结果摘要”。

3.3) budget
- 含义：预算控制（通常是“token 成本预算”或“每请求最大 token / 每分钟 token 配额”）。
- 在你这里：router 要能在运行时“算账”：如果预计超预算，就走更便宜路径、缩短上下文、或拒绝并返回可解释错误。

4) Latency, token/req, error-rate metrics
- 这三个是典型“可观测性三件套”：性能、成本、可靠性。

4.1) Latency（延迟）
- 含义：一次请求从进来到出结果花了多久（常用 P50/P95/P99）。
- 在你这里：你会关心：
  - 检索耗时（embedding + vector search）
  - LLM 推理耗时
  - 总耗时

4.2) token/req（每请求 token 数）
- 含义：一次请求消耗的 token（输入+输出），它直接决定钱和延迟。
- 在你这里：router 的 budget 控制就需要它作为核心观测量。

4.3) error-rate（错误率）
- 含义：请求中失败的比例（按状态码分类更有用：4xx vs 5xx vs 429）。
- 在你这里：它用来判断“系统是否稳定”、fallback 是否生效、重试是否在制造更多错误。

========================
B) exit_criteria 里的名词
========================

1) make benchmark produces numeric metrics
- 含义：你可以用 `make benchmark` 一键跑评测，并且输出“数字指标”（Recall@K/MRR/nDCG 等），
  不是“感觉不错/打印几行日志”。

2) docker compose up runs full RAG service
- 含义：一条命令把 FastAPI + Chroma（以及你定义的其它服务）全部跑起来，并且能对外提供 API。:contentReference[oaicite:10]{index=10}

3) GateAI can route same query across 2+ LLMs
- 含义：同一个输入 query，router 能根据策略在至少两个模型之间切换/路由（主用 + 备用），
  并且行为是可解释、可验证的（例如：超时 -> fallback；超预算 -> cheaper model）。

4) Metrics visible on /metrics endpoint
- 含义：你的服务暴露一个 HTTP endpoint（通常就是 `/metrics`），用 Prometheus 的文本格式输出指标，
  让监控系统能抓取。:contentReference[oaicite:11]{index=11}
- “/metrics 长什么样”直觉例子：一行一个 metric + 可选 labels。:contentReference[oaicite:12]{index=12}

========================
一句话对齐（你现在这份 Stage-1）
========================
- eval：定义“好”的标准（数字化）
- RAG service：把检索能力服务化并可复现运行
- runtime router：把多模型调用变成可控系统（重试/降级/预算）
- /metrics：把性能/成本/错误率暴露出来，形成可观测闭环
"""
