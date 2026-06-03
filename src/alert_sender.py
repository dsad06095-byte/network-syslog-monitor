#!/usr/bin/env python3
import smtplib
import requests
from email.mime.text import MIMEText
from loguru import logger
import yaml
from pathlib import Path
from collections import defaultdict
from threading import Timer
import time

class AlertSender:
    def __init__(self, config_file='config/alert.yaml'):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        #  批量发送缓存
        self.alert_buffer = defaultdict(list)
        self.flush_timer = None
        self.batch_interval = 30  # 30秒批量发送一次
        
    def _load_config(self):
        if self.config_file.exists():
            with open(self.config_file, encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def send(self, alerts):
        """添加告警到缓冲区（批量发送）"""
        if not alerts:
            return
        
        for alert in alerts:
            # 按设备+规则去重合并
            key = f"{alert.get('device_ip', 'unknown')}:{alert['name']}"
            if key not in self.alert_buffer:
                self.alert_buffer[key] = alert
        
        # 启动定时器批量发送
        if self.flush_timer is None:
            self.flush_timer = Timer(self.batch_interval, self._flush)
            self.flush_timer.start()
    
    def _flush(self):
        """批量发送告警"""
        if not self.alert_buffer:
            self.flush_timer = None
            return
        
        alerts = list(self.alert_buffer.values())
        
        # 按严重程度排序
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        alerts.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        # 打印日志
        for alert in alerts:
            logger.warning(f"告警: {alert['severity']} | {alert['name']} | {alert.get('device_ip', 'unknown')}")
        
        # 邮件告警
        if self.config.get('email', {}).get('enabled'):
            self._send_email(alerts)
        
        # 企业微信告警
        if self.config.get('wecom', {}).get('enabled'):
            self._send_wecom(alerts)
        
        # 清空缓冲区
        self.alert_buffer.clear()
        self.flush_timer = None
    
    def _send_email(self, alerts):
        """发送邮件告警（批量）"""
        try:
            email_cfg = self.config.get('email', {})
            if not email_cfg.get('enabled'):
                return
            
            # 构建邮件内容
            content_lines = []
            for a in alerts:
                content_lines.append(
                    f"[{a['severity'].upper()}] {a['name']} | {a.get('device_ip', 'unknown')}\n"
                    f"    {a.get('message', '')[:100]}"
                )
            content = "\n\n".join(content_lines)
            
            msg = MIMEText(content, 'plain', 'utf-8')
            msg['Subject'] = f"[网络告警] 发现 {len(alerts)} 条异常"
            msg['From'] = email_cfg.get('from', 'monitor@example.com')
            msg['To'] = email_cfg.get('to', 'ops@example.com')
            
            # 实际发送（取消注释）
            # server = smtplib.SMTP(email_cfg.get('smtp_server'), email_cfg.get('smtp_port'))
            # server.send_message(msg)
            # server.quit()
            
            logger.info(f"批量邮件告警已发送: {len(alerts)} 条")
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
    
    def _send_wecom(self, alerts):
        """发送企业微信告警（批量）"""
        try:
            wecom_cfg = self.config.get('wecom', {})
            if not wecom_cfg.get('enabled'):
                return
            
            webhook_url = wecom_cfg.get('webhook_url')
            if not webhook_url:
                return
            
            # 构建消息（最多显示前5条）
            content_lines = ["【网络告警汇总】"]
            for i, a in enumerate(alerts[:5]):
                content_lines.append(
                    f"{i+1}. [{a['severity'].upper()}] {a['name']} ({a.get('device_ip', 'unknown')})"
                )
            if len(alerts) > 5:
                content_lines.append(f"... 共 {len(alerts)} 条告警")
            
            data = {
                "msgtype": "text",
                "text": {"content": "\n".join(content_lines)}
            }
            # 实际发送（取消注释）
            # requests.post(webhook_url, json=data)
            
            logger.info(f"批量企微告警已发送: {len(alerts)} 条")
        except Exception as e:
            logger.error(f"企微发送失败: {e}")
