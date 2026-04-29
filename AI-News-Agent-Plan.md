# AI News Agent 实施方案

## 目标

在程序运行期间自动检测联网状态。只要网络可用，并且当天还没有成功发送过日报，系统就自动采集 Bilibili 和抖音指定账号的 AI 相关内容，调用配置的通用 LLM 生成摘要，然后推送到飞书。当天成功发送后不再重复发送。

系统不长期保存原始内容或日报正文，只保留运行状态和 7 天去重 hash。

## 核心流程

```text
启动 auto 模式
  ↓
循环检测网络
  ↓
检查今天是否已成功发送
  ↓
未发送且联网：采集 Bilibili + RSS + 抖音
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
调用通用 LLM 总结
  ↓
生成日报临时文件
  ↓
发送到飞书
  ↓
发送成功：删除日报临时文件，当天不再重复发送
  ↓
发送失败：保留 24 小时，下次联网检查继续重试
  ↓
清理过期 hash 和临时文件
```

## 运行模式

推荐运行：

```powershell
python run.py auto
```

辅助命令：

```powershell
python run.py init-db
python run.py once
python run.py healthcheck
python run.py cleanup
python run.py dry-run --collector bilibili
python run.py dry-run --collector douyin
python run.py dry-run --summary
python run.py dry-run --delivery
```

`auto` 模式由 `job_runs` 表判断当天是否已经成功发送。只有 `status='success'` 且 `delivered=1` 的记录才会阻止当天重复运行。

## 采集范围

### Bilibili

```text
关键词搜索
按发布时间排序
单关键词失败不影响整体任务
```

### RSS

```text
官方模型/公司博客
研究论文源
开源和开发者源
```

默认启用：

```text
OpenAI Blog
Google DeepMind Blog
Hugging Face Blog
NVIDIA Blog AI
Microsoft AI Blog
arXiv cs.AI / cs.CL / cs.LG
```

### 抖音

```text
指定账号主页
公开可访问内容
Playwright 浏览器渲染
仅提取页面中出现的公开视频链接
```

不做：

```text
绕验证码
逆向签名
登录态抓取
高频访问
保存视频/图片/完整页面快照
```

如果抖音返回验证码中间页，系统记录 `douyin_account_blocked_by_captcha` 并跳过该账号。

## 存储策略

```text
原始内容：不保存
清洗内容：不保存
视频/图片：不保存
日报正文：发送成功后删除
发送失败日报：保留 24 小时
去重信息：只保存 hash，保留 7 天
运行记录：只保存状态、数量、错误信息
```

目录：

```text
tmp/reports/
logs/
```

## 数据库

使用 SQLite：

```text
ai_news.db
```

核心表：

```text
job_runs
dedupe_hashes
health_checks
```

`job_runs` 用于记录每日运行和发送状态。

`dedupe_hashes` 只保存 URL/标题/ID 的 hash，不保存正文，7 天后清理。

`health_checks` 保存健康检查结果。

## 通用 LLM

总结模块不绑定 GPT。支持：

```text
openai_compatible：标准 /v1/chat/completions
openai：OpenAI 默认地址
ollama：本地 Ollama /api/chat
none：不调用模型，使用降级摘要
```

通过 `.env` 配置：

```text
LLM_API_KEY=
LLM_MODEL=
LLM_BASE_URL=
FEISHU_WEBHOOK=
AI_NEWS_CONFIG=config.yaml
```

## 飞书推送

只支持飞书 webhook。发送成功后日报临时文件立即删除。

如果飞书发送失败：

```text
job_runs 记录 failed
日报临时文件保留 24 小时
auto 模式后续继续重试
```

## 配置

关键配置在 `config.yaml`：

```yaml
runtime:
  timezone: Asia/Shanghai

auto_run:
  check_interval_seconds: 1800
  start_delay_seconds: 0
  network_check_timeout_seconds: 8
  network_check_urls:
    - https://www.bilibili.com
    - https://open.feishu.cn
```

抖音账号配置使用本地文件：

```text
config/douyin_accounts.local.yaml
```

该文件被 Git 忽略，避免把账号列表提交到 GitHub。仓库中保留模板：

```text
config/douyin_accounts.yaml
```

## 项目结构

```text
app/
  collectors/
    base.py
    bilibili.py
    douyin.py
  db/
    models.py
    session.py
  delivery/
    feishu.py
  pipeline/
    dedupe.py
    filter.py
    normalize.py
    rank.py
    summarize.py
  cleanup.py
  config.py
  healthcheck.py
  logging_config.py

tests/
config/
填写配置/
run.py
config.yaml
Dockerfile
docker-compose.yml
requirements.txt
README.md
```

## 验收标准

```text
healthcheck 通过
Bilibili dry-run 可返回内容
抖音 dry-run 在公开视频可访问时可返回内容
once 可完成采集、总结、飞书推送
auto 模式当天成功后不重复发送
发送成功后不保留日报正文
数据库不保存新闻正文
```
