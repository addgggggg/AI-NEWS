# AI News Agent 代码实现计划

## 当前实现选择

```text
运行模式：联网后每日一次 auto 模式
推送渠道：飞书 webhook
数据库：SQLite
抖音：指定账号公开主页监控
抖音渲染：Playwright
LLM：通用 provider，不绑定 GPT
日报：发送成功删除，失败保留 24 小时
去重 hash：SQLite 保留 7 天
自我迭代任务：不实现
```

## 命令

```text
python run.py init-db
python run.py once
python run.py auto
python run.py healthcheck
python run.py cleanup
python run.py dry-run --collector bilibili
python run.py dry-run --collector rss
python run.py dry-run --collector douyin
python run.py dry-run --summary
python run.py dry-run --delivery
```

面向非开发用户的 PowerShell 脚本：

```text
scripts/install.ps1
scripts/healthcheck.ps1
scripts/run_once.ps1
scripts/run_auto.ps1
scripts/dry_run_douyin.ps1
scripts/install_startup_task.ps1
scripts/start_startup_task.ps1
scripts/startup_task_status.ps1
scripts/uninstall_startup_task.ps1
scripts/install_startup_shortcut.ps1
scripts/uninstall_startup_shortcut.ps1
scripts/switch_model.ps1
scripts/test_model.ps1
```

## 日志规划

日志目录：

```text
logs/
  app.log
  collector.log
  summary.log
  delivery.log
  healthcheck.log
```

日志不记录：

```text
完整新闻正文
完整日报正文
完整页面内容
敏感 token
飞书 webhook
```

## 检测任务

### healthcheck

检查：

```text
config.yaml 是否存在
.env 是否存在
FEISHU_WEBHOOK 是否配置
LLM_API_KEY 是否配置
LLM_MODEL 是否配置
LLM_BASE_URL 是否配置
SQLite 是否可写
tmp/ 是否可写
logs/ 是否可写
关键词是否为空
抖音账号列表是否为空
```

### dry-run collector

检查：

```text
采集器是否能启动
平台是否能访问
返回字段是否能标准化
不生成日报
不推送
```

### dry-run summary

检查：

```text
总结模块是否可用
LLM 不可用时是否能降级生成简报
```

### dry-run delivery

检查：

```text
飞书 webhook 是否可用
发送一条测试消息
不包含真实新闻内容
```

### cleanup

处理：

```text
删除超过 24 小时的失败日报临时目录
删除过期 dedupe_hashes
删除超过 14 天的日志
```

## 抖音账号配置

本地配置文件：

```text
config/douyin_accounts.local.yaml
```

仓库模板：

```text
config/douyin_accounts.yaml
```

格式：

```yaml
accounts:
  - name: 账号名称
    profile_url: "https://www.douyin.com/user/..."
    sec_uid: ""
    weight: 1.0
    enabled: true
```

## 后续可选增强

```text
更多来源平台
更精细的来源权重
更严格的标题党过滤
本地 outbox 补发队列
Windows 开机自启动脚本
```
