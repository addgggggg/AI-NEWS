# LLM Provider 配置说明

总结模块已经做成通用版，不绑定 GPT。

## 支持模式

```text
openai_compatible：标准 /v1/chat/completions，推荐默认值，需要显式配置 base_url
openai：OpenAI 兼容模式，base_url 默认 https://api.openai.com/v1
ollama：本地 Ollama /api/chat
none：不调用模型，使用降级摘要
```

## 默认配置

`config.yaml`：

```yaml
summary:
  provider: openai_compatible
  model: ""
  model_env: LLM_MODEL
  api_key_env: LLM_API_KEY
  base_url_env: LLM_BASE_URL
  timeout_seconds: 60
  max_items: 40
```

`.env`：

```text
LLM_API_KEY=
LLM_MODEL=
LLM_BASE_URL=
```

## OpenAI 示例

```text
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4.1-mini
LLM_BASE_URL=https://api.openai.com/v1
```

## DeepSeek 示例

```text
LLM_API_KEY=你的 DeepSeek Key
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
```

## 其他 OpenAI 兼容服务

只要服务商提供 `/v1/chat/completions` 兼容接口，就填：

```text
LLM_API_KEY=服务商 Key
LLM_MODEL=服务商模型名
LLM_BASE_URL=服务商 /v1 地址
```

## Ollama 示例

`config.yaml`：

```yaml
summary:
  provider: ollama
  model: qwen2.5:7b
  base_url: http://localhost:11434
```

Ollama 默认不需要 `LLM_API_KEY`。

## 不调用模型

`config.yaml`：

```yaml
summary:
  provider: none
```

系统会使用降级摘要，适合测试采集、去重、推送链路。
