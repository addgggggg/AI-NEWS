# AI News Agent 代码实现计划

## 已确认技术选择

```text
推送渠道：飞书 webhook
数据库：SQLite
抖音：指定账号监控
项目目录：当前项目根目录
原始内容：不落盘
日报：发送成功删除，失败保留 24 小时
去重 hash：SQLite 保留 7 天
自我迭代任务：不实现
```

## 代码阶段范围

第一版目标是 MVP：

```text
1. 可通过命令行运行一次任务
2. 可通过定时器每天运行
3. 可检查配置、数据库、目录、飞书 webhook
4. 可采集 Bilibili 关键词内容
5. 可按配置监控抖音指定账号
6. 可生成日报并推送到飞书
7. 发送成功后删除日报临时文件
8. 发送失败后保留日报 24 小时
9. 只在 SQLite 保存 job_runs、dedupe_hashes、health_checks
```

## 命令设计

```text
python run.py init-db
python run.py once
python run.py schedule
python run.py healthcheck
python run.py cleanup
python run.py dry-run --collector bilibili
python run.py dry-run --collector douyin
python run.py dry-run --summary
python run.py dry-run --delivery
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

日志保留策略：

```text
默认 14 天
单文件最大 10MB
最多保留 5 个轮转文件
```

日志记录：

```text
任务开始/结束
采集平台
采集数量
过滤数量
去重数量
入选日报数量
发送状态
错误类型
耗时
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
Prompt 是否输出基本栏目
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

检查并处理：

```text
删除超过 24 小时的失败日报临时目录
删除过期 dedupe_hashes
删除超过 14 天的日志
```

## 抖音账号配置方式

抖音账号列表独立放在：

```text
config/douyin_accounts.yaml
```

格式：

```yaml
accounts:
  - name: 机器之心
    profile_url: "https://www.douyin.com/user/REPLACE_ME"
    sec_uid: ""
    weight: 1.0
    enabled: true
```

第一版要求至少填写：

```text
name
profile_url
```

`sec_uid` 可以先留空，后续由程序解析或人工补充。

## 第一轮实现顺序

```text
1. 项目骨架 + 配置加载
2. 日志系统
3. SQLite 初始化
4. 清理任务
5. 飞书推送
6. Bilibili 采集器
7. 抖音指定账号采集器
8. 标准化 pipeline
9. hash 去重
10. 相关性过滤和排序
11. 通用 LLM 总结
12. run.py 命令入口
13. healthcheck / dry-run
14. README 使用说明
```
