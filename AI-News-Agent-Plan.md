# AI News Agent 实施方案

## 目标

每天固定时间自动从抖音和 Bilibili 收集最新 AI 相关内容，清洗、去重、排序、总结后推送给用户。系统不长期保存原始内容或日报正文，只保留运行状态和 7 天去重 hash。

## 一、核心流程

```text
每日定时触发
  ↓
采集 Bilibili + 抖音
  ↓
内存中清洗、标准化
  ↓
生成去重 hash
  ↓
过滤最近 7 天已出现内容
  ↓
AI 相关性过滤
  ↓
重要性评分排序
  ↓
选取 Top 内容
  ↓
生成日报临时文件
  ↓
发送到邮箱/飞书/企业微信
  ↓
发送成功：立即删除日报临时文件
  ↓
发送失败：保留 24 小时
  ↓
记录任务状态
  ↓
清理过期 hash 和临时文件
```

## 二、采集范围

### Bilibili

```text
关键词搜索
指定 UP 主
科技区/AI 相关标签
```

### 抖音

```text
指定 AI/科技账号
厂商官方账号
公开可访问内容
开放平台授权数据，后续可扩展
```

### 不做的内容

```text
绕验证码
逆向签名
高频匿名访问
抓取登录后私有数据
保存视频/图片/完整页面快照
```

## 三、关键词初版

```text
AI
人工智能
大模型
AIGC
OpenAI
ChatGPT
Claude
Gemini
DeepSeek
Kimi
豆包
通义千问
智谱
文生图
视频生成
AI Agent
智能体
机器人
英伟达
GPU
算力
自动驾驶
```

## 四、数据存储策略

最终采用折中方案：

```text
原始内容：不保存
清洗内容：不保存
视频/图片：不保存
日报正文：发送成功后删除
发送失败日报：保留 24 小时
去重信息：只保存 hash，保留 7 天
运行记录：只保存状态、数量、错误信息
```

本地目录：

```text
ai-news-agent/
  tmp/
    reports/
      2026-04-25/
        daily_report.md
        daily_report.html

  logs/
    scheduler.log
    collector.log
```

发送成功后删除：

```text
tmp/reports/2026-04-25/
```

失败时保留，超过 24 小时自动删除。

## 五、数据库设计

只保留两张核心表。

### job_runs

```sql
CREATE TABLE job_runs (
  id BIGSERIAL PRIMARY KEY,
  job_date DATE NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL,
  items_collected_count INT DEFAULT 0,
  items_selected_count INT DEFAULT 0,
  delivered BOOLEAN DEFAULT FALSE,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### dedupe_hashes

```sql
CREATE TABLE dedupe_hashes (
  id BIGSERIAL PRIMARY KEY,
  hash_value TEXT NOT NULL UNIQUE,
  platform TEXT,
  first_seen_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL
);
```

`expires_at`：

```text
first_seen_at + 7 days
```

## 六、去重策略

生成 hash 的字段：

```text
platform + external_id
url
normalized_title
normalized_title + author
```

优先级：

```text
1. external_id hash
2. url hash
3. 标题 hash
4. 标题 + 作者 hash
```

只存 hash，不存原文。

保留周期：

```text
7 天
```

## 七、评分策略

```text
final_score =
  ai_relevance * 0.35 +
  freshness * 0.20 +
  engagement * 0.25 +
  source_weight * 0.10 +
  novelty * 0.10
```

过滤掉：

```text
纯带货
课程广告
明显标题党
重复搬运
无实质信息的工具合集
非 AI 内容
```

优先保留：

```text
模型发布
产品更新
公司动态
监管政策
产业融资
技术突破
重要观点解读
官方账号发布
```

## 八、日报格式

```markdown
# AI 新闻日报 - 2026-04-25

## 今日重点
1. xxx
2. xxx
3. xxx

## 产品与模型动态
- xxx

## 国内 AI 动态
- xxx

## 海外 AI 动态
- xxx

## 热门视频
| 平台 | 标题 | 作者 | 链接 |
|---|---|---|---|

## 值得继续关注
- xxx
```

日报发送渠道：

```text
邮箱
飞书 webhook
企业微信 webhook
```

建议第一版先做一个渠道，例如飞书或邮箱。

## 九、LLM 总结 Prompt

```text
你是一个 AI 行业新闻分析师。

请根据下面的视频和新闻条目，生成一份中文 AI 新闻日报。

要求：
1. 不要逐条复述，要合并相同事件。
2. 优先关注模型发布、产品更新、公司动态、监管政策、产业融资、技术突破。
3. 过滤营销、带货、重复搬运和低信息密度内容。
4. 每条重点新闻说明为什么重要。
5. 保留来源链接。
6. 如果信息不足，要标注“待确认”。

输出结构：
- 今日重点
- 产品与模型动态
- 国内 AI 动态
- 海外 AI 动态
- 热门视频
- 值得继续关注
```

## 十、项目结构

```text
ai-news-agent/
  app/
    collectors/
      base.py
      bilibili.py
      douyin.py

    pipeline/
      normalize.py
      filter.py
      dedupe.py
      rank.py
      summarize.py

    delivery/
      email.py
      feishu.py
      wecom.py

    db/
      models.py
      session.py

    prompts/
      daily_summary.md

    config.py
    scheduler.py
    main.py

  migrations/
  tests/
  tmp/
  logs/
  docker-compose.yml
  Dockerfile
  .env.example
  README.md
```

## 十一、配置示例

```yaml
schedule:
  timezone: Asia/Shanghai
  daily_run_at: "08:30"

storage:
  persist_raw: false
  persist_normalized: false
  persist_reports: false
  temp_report_dir: ./tmp/reports
  delete_after_success: true
  keep_failed_tmp_hours: 24

dedupe:
  enabled: true
  retention_days: 7
  store_only_hash: true

keywords:
  - AI
  - 人工智能
  - 大模型
  - AIGC
  - OpenAI
  - ChatGPT
  - DeepSeek
  - Kimi
  - 豆包
  - 通义千问
  - 智能体
  - 视频生成
  - 英伟达

bilibili:
  enabled: true
  max_results_per_keyword: 20
  target_authors: []

douyin:
  enabled: true
  mode: account_watch
  target_accounts:
    - 示例AI账号1
    - 示例科技账号2

delivery:
  email:
    enabled: true
    to: you@example.com

  feishu:
    enabled: false
    webhook_url: ""

  wecom:
    enabled: false
    webhook_url: ""

cleanup:
  enabled: true
  run_after_job: true
  log_retention_days: 14
```

## 十二、部署方式

使用 Docker Compose：

```yaml
services:
  agent:
    build: .
    env_file: .env
    depends_on:
      - postgres
    volumes:
      - ./tmp:/app/tmp
      - ./logs:/app/logs
    restart: unless-stopped

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ai_news
      POSTGRES_USER: ai_news
      POSTGRES_PASSWORD: change_me
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## 十三、清理任务

每日任务结束后执行：

```text
1. 如果日报发送成功，删除当日报告目录
2. 如果日报发送失败，保留临时文件 24 小时
3. 删除超过 24 小时的失败日报临时目录
4. 删除 expires_at < now() 的 dedupe_hashes
5. 删除超过 14 天的日志
```

## 十四、实施阶段

### 阶段 1：MVP，1-2 天

```text
Bilibili 关键词采集
抖音指定账号采集
内存清洗
7 天 hash 去重
通用 LLM 总结
邮箱或飞书推送
发送成功后删除日报文件
失败保留 24 小时
记录 job_runs
```

### 阶段 2：稳定版，3-5 天

```text
Docker 部署
PostgreSQL 持久化 job_runs 和 dedupe_hashes
失败重试
日志和异常告警
黑名单/白名单
来源权重
热度评分
```

### 阶段 3：增强版，1-2 周

```text
事件合并
个性化排序
每周趋势报告
历史问答，但需要额外保存摘要或 embedding
更多推送渠道
开放平台授权接入
```

注意：如果后续需要历史问答或趋势分析，就必须额外保存摘要、事件 ID 或 embedding。当前方案为了隐私和轻量化，不支持深度历史查询。

## 十五、验收标准

### MVP

```text
每天自动执行一次
可采集 Bilibili AI 相关内容
可采集抖音指定账号内容
可过滤最近 7 天重复内容
可生成 AI 新闻日报
可成功推送
发送成功后不保留日报正文
失败日报 24 小时后自动删除
数据库不保存新闻正文
```

### 稳定版

```text
连续运行 7 天不中断
重复内容明显减少
明显无关内容比例低于 20%
每日报告生成时间小于 10 分钟
单个平台失败不影响整体日报生成
```

## 最终推荐第一版范围

```text
Bilibili 关键词采集
抖音指定账号监控
PostgreSQL 只存 job_runs + dedupe_hashes
临时 Markdown/HTML 日报
飞书或邮箱推送
成功后删除日报
失败保留 24 小时
7 天 hash 去重
Docker Compose 部署
```

这版可以比较快落地，也符合“不保存原始文件，发送完删除，只保留 7 天去重信息”的要求。
