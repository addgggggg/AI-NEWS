# 需要填写的配置

安装完成后，需要填写两个文件。

## 1. `.env`

从 `.env.example` 自动复制生成。填写：

```text
LLM_API_KEY=你的模型服务 API Key
LLM_MODEL=你的模型名
LLM_BASE_URL=你的模型服务地址
FEISHU_WEBHOOK=你的飞书机器人 webhook
AI_NEWS_CONFIG=config.yaml
```

示例，DeepSeek：

```text
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
AI_NEWS_CONFIG=config.yaml
```

示例，通义千问兼容模式：

```text
LLM_API_KEY=sk-xxx
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
AI_NEWS_CONFIG=config.yaml
```

## 2. `config/douyin_accounts.local.yaml`

从 `config/douyin_accounts.yaml` 自动复制生成。填写要监控的抖音账号主页。

必须是账号主页链接，包含 `/user/`，不要填搜索页。

```yaml
accounts:
  - name: 账号名称
    profile_url: "https://www.douyin.com/user/实际账号ID"
    sec_uid: ""
    weight: 1.0
    enabled: true
```

可以添加多个账号：

```yaml
accounts:
  - name: 账号A
    profile_url: "https://www.douyin.com/user/xxxx"
    sec_uid: ""
    weight: 1.0
    enabled: true

  - name: 账号B
    profile_url: "https://www.douyin.com/user/yyyy"
    sec_uid: ""
    weight: 1.0
    enabled: true
```

## 验证

```powershell
scripts\healthcheck.ps1
scripts\dry_run_douyin.ps1
```

## 运行

手动跑一次：

```powershell
scripts\run_once.ps1
```

联网后每日自动跑一次：

```powershell
scripts\run_auto.ps1
```

## 快速切换模型

查看可用模型模板：

```powershell
scripts\switch_model.ps1 -List
```

切换到某个模板：

```powershell
scripts\switch_model.ps1 -Profile deepseek
```

常用模板：

```text
deepseek
deepseek-v4-flash
kimi
zhipu
qwen-plus
openai
ollama-qwen
```

切换后仍需要确认 `.env` 里的 `LLM_API_KEY` 是对应服务商的 key。

测试模型：

```powershell
scripts\test_model.ps1
```

## 开机/登录后自动运行

安装 Windows 登录自启动，推荐不需要管理员权限的启动文件夹方式：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_startup_shortcut.ps1
```

卸载启动文件夹自启动：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\uninstall_startup_shortcut.ps1
```

如需使用 Windows 计划任务，可以尝试：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_startup_task.ps1
```

部分系统注册计划任务需要管理员权限。

```powershell
scripts\uninstall_startup_task.ps1
```

## 简报格式

系统会让模型输出纯文字版简报，不使用表格或复杂 Markdown。格式包括：

```text
AI 新闻简报（日期）
一、今日重点
二、产品与模型动态
三、国内 AI 动态
四、海外 AI 动态
五、值得关注的视频
六、继续关注
```

如果模型响应较慢，可以在 `config.yaml` 中调大：

```yaml
summary:
  timeout_seconds: 180
```
