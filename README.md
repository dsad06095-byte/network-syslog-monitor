# 网络设备日志分析告警系统

基于 Syslog 的网络设备日志采集、规则匹配、告警推送系统，专为门店/仓库网络运维场景设计。

## ✨ 核心功能

- **Syslog 日志接收**：监听 UDP 514 端口，实时接收交换机/防火墙日志
- **可配置规则引擎**：支持正则匹配、计数阈值、时间窗口、告警冷却
- **批量告警推送**：支持邮件/企业微信，30秒批量聚合，避免刷屏
- **日志滚动存储**：按设备 IP + 日期分文件存储，便于追溯

## 🏗️ 技术架构
network-syslog-monitor/
├── src/
│ ├── syslog_server.py # Syslog 接收器
│ ├── rule_engine.py # 规则匹配引擎
│ └── alert_sender.py # 告警推送（批量+冷却）
├── config/
│ ├── rules.yaml # 异常规则配置
│ └── alert.yaml # 告警渠道配置
├── logs/ # 原始日志存储
├── main.py # 程序入口
└── requirements.txt


快速开始 安装依赖

pip install -r requirements.txt
