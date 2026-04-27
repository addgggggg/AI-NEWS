# AI News Agent 实现状态

## 当前已完成

```text
项目骨架
配置加载
日志系统
SQLite 初始化
job_runs / dedupe_hashes / health_checks 表
健康检查命令
清理命令
联网后每日一次自动运行模式
Bilibili 关键词采集器
抖音指定账号采集器骨架
标准化 pipeline
AI 关键词过滤
7 天 hash 去重
基础排序
通用 LLM 总结调用
支持 OpenAI 兼容接口和 Ollama
LLM 未配置时的降级摘要
飞书 webhook 推送
发送成功删除日报
发送失败保留日报 24 小时
Dockerfile
docker-compose.yml
单元测试
```

## 当前验证结果

已通过：

```text
python -m unittest discover -s tests -p "test_*.py"
python run.py init-db
python run.py healthcheck
python run.py cleanup
python run.py dry-run --collector bilibili
python run.py dry-run --collector douyin
python run.py dry-run --summary
```

完整任务 `python run.py once` 已验证：

```text
Bilibili 采集成功
LLM 未配置时自动使用降级摘要
飞书未配置时发送失败
发送失败后日报保留在 tmp/reports/YYYY-MM-DD/
job_runs 正确记录 failed 状态
```

## 当前需要用户配置

复制 `.env.example` 为 `.env`：

```powershell
Copy-Item .env.example .env
```

填写：

```text
LLM_API_KEY=你的模型服务 API Key
LLM_MODEL=你的模型名
LLM_BASE_URL=你的模型服务地址
FEISHU_WEBHOOK=你的飞书机器人 webhook
```

配置抖音账号：

```text
config/douyin_accounts.yaml
```

示例：

```yaml
accounts:
  - name: 机器之心
    profile_url: "https://www.douyin.com/user/实际账号ID"
    sec_uid: ""
    weight: 1.0
    enabled: true
```

第一版至少需要：

```text
name
profile_url
enabled: true
```

## 注意事项

### Bilibili

Bilibili 采集器使用公开搜索接口，已经做了：

```text
浏览器请求头
首页 warmup
单关键词失败跳过
低频请求
```

如果平台返回 412，系统会记录日志并跳过该关键词，不会中断整次任务。

### 抖音

抖音第一版只做指定账号公开主页监控。由于抖音页面结构经常变化，当前解析器只提取公开页面中可见的视频链接。后续如果你提供实际账号 URL，需要用 dry-run 验证返回效果：

```powershell
python run.py dry-run --collector douyin
```

不实现：

```text
验证码绕过
签名逆向
登录态抓取
高频访问
```

如果 dry-run 日志出现 `douyin_account_blocked_by_captcha`，说明当前环境拿到的是验证码中间页，系统会跳过该账号，不会尝试绕过。

## 下一步建议

```text
1. 配置 .env 的 FEISHU_WEBHOOK
2. 运行 python run.py dry-run --delivery
3. 配置 5-10 个抖音账号
4. 运行 python run.py dry-run --collector douyin
5. 配置 LLM_API_KEY / LLM_MODEL / LLM_BASE_URL
6. 运行 python run.py once
7. 确认飞书收到日报
8. 再启动 python run.py schedule
```
