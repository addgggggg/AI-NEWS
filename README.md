# AI News Agent

每日从 Bilibili 和抖音指定账号采集 AI 相关内容，生成日报并推送到飞书。系统不保存原始内容，日报发送成功后删除，去重 hash 只保留 7 天。

## 快速开始

一行安装：

```powershell
git clone https://github.com/addgggggg/AI-NEWS.git; cd AI-NEWS; powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

分步安装：

```powershell
git clone https://github.com/addgggggg/AI-NEWS.git
cd AI-NEWS
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

安装完成后，按 [CONFIG_REQUIRED.md](CONFIG_REQUIRED.md) 填写 `.env` 和 `config/douyin_accounts.local.yaml`。

检查配置：

```powershell
scripts\healthcheck.ps1
```

手动跑一次：

```powershell
scripts\run_once.ps1
```

联网后每日自动跑一次：

```powershell
scripts\run_auto.ps1
```

安装 Windows 登录自启动，推荐不需要管理员权限的启动文件夹方式：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_startup_shortcut.ps1
```

卸载启动文件夹自启动：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\uninstall_startup_shortcut.ps1
```

如果你希望使用 Windows 计划任务，可以用下面的脚本；部分系统需要管理员权限：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_startup_task.ps1
```

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
python run.py auto
```

也可以使用 `scripts/` 里的 PowerShell 脚本运行。

`auto` 模式不按固定时间发送。它会循环检查网络和今天是否已经成功发送：

```text
网络不可用：等待下次检查
网络可用且今天未成功发送：采集、总结、推送飞书
今天已成功发送：当天不再重复发送
```

检查间隔在 `config.yaml` 的 `auto_run.check_interval_seconds` 中配置。

## 抖音账号配置

编辑：

```text
config/douyin_accounts.local.yaml
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
`config/douyin_accounts.local.yaml` 会被 Git 忽略，避免把你的账号列表提交到 GitHub。可以从 `config/douyin_accounts.yaml` 复制一份后再填写。

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

## 简报格式

日报会输出为纯文字简报，不使用表格或复杂 Markdown。模型超时时会自动降级为基础纯文字摘要。

## 文档

```text
Implementation-Status.md
Code-Implementation-Plan.md
AI-News-Agent-Plan.md
CONFIG_REQUIRED.md
```
