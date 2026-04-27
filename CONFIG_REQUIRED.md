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
