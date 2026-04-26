# AI News Agent

每日从 Bilibili 和抖音指定账号采集 AI 相关内容，生成日报并推送到飞书。系统不保存原始内容，日报发送成功后删除，去重 hash 只保留 7 天。

## 快速开始

```powershell
cd "AI News"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

如果只是本地验证，也可以直接使用系统 Python 运行。

## 配置 LLM

编辑 `.env`：

```text
LLM_API_KEY=你的模型服务 API Key
LLM_MODEL=你的模型名
LLM_BASE_URL=你的模型服务地址
FEISHU_WEBHOOK=你的飞书机器人 webhook
```

默认使用 OpenAI 兼容接口，也就是标准 `/v1/chat/completions`。只要服务商兼容这个接口，就可以接入，不限 GPT。
在 `openai_compatible` 模式下必须显式配置 `LLM_BASE_URL`。

常见配置示例：

```text
# OpenAI
LLM_MODEL=gpt-4.1-mini
LLM_BASE_URL=https://api.openai.com/v1

# DeepSeek
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1

# 其他 OpenAI 兼容服务
LLM_MODEL=服务商提供的模型名
LLM_BASE_URL=服务商提供的 /v1 地址
```

如果使用 Ollama，本地服务默认地址是 `http://localhost:11434`，并在 `config.yaml` 中设置：

```yaml
summary:
  provider: ollama
  model: qwen2.5:7b
```

如需完全不调用模型，可设置：

```yaml
summary:
  provider: none
```

系统会使用降级摘要。

## 初始化和运行

```powershell
python run.py init-db
python run.py healthcheck
python run.py once
python run.py schedule
```

## 抖音账号配置

编辑：

```text
config/douyin_accounts.yaml
```

格式：

```yaml
accounts:
  - name: 机器之心
    profile_url: "https://www.douyin.com/user/实际账号ID"
    sec_uid: ""
    weight: 1.0
    enabled: true
```

第一版至少填写 `name` 和 `profile_url`。

## 检测命令

```powershell
python run.py dry-run --collector bilibili
python run.py dry-run --collector douyin
python run.py dry-run --summary
python run.py dry-run --delivery
python run.py cleanup
```

## 存储策略

```text
原始内容：不保存
清洗内容：不保存
日报正文：发送成功后删除
发送失败日报：保留 24 小时
去重信息：只保存 hash，保留 7 天
运行记录：只保存状态、数量、错误信息
```

## 文档

```text
Implementation-Status.md
Code-Implementation-Plan.md
AI-News-Agent-Plan.md
```
