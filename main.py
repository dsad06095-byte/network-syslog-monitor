#!/usr/bin/env python3
from loguru import logger
from src.syslog_server import SyslogServer
from src.rule_engine import RuleEngine
from src.alert_sender import AlertSender

# 全局实例
rule_engine = RuleEngine()
alert_sender = AlertSender()

def process_log(device_ip, message, timestamp):
    """处理接收到的日志"""
    matched = rule_engine.match(device_ip, message, timestamp)
    
    if matched:
        # 添加设备信息
        for alert in matched:
            alert['device_ip'] = device_ip
            alert['timestamp'] = timestamp.isoformat()
        
        # 批量发送告警（已在 AlertSender 内部做批量处理）
        alert_sender.send(matched)

def main():
    logger.info("网络设备日志分析告警系统启动")
    
    server = SyslogServer(host='0.0.0.0', port=514)
    
    try:
        server.start(callback=process_log)
    except KeyboardInterrupt:
        logger.info("服务停止")
        server.stop()

if __name__ == "__main__":
    main()
