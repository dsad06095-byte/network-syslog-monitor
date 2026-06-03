#!/usr/bin/env python3
import socket
import select
from datetime import datetime
from loguru import logger
from pathlib import Path

class SyslogServer:
    def __init__(self, host='0.0.0.0', port=514, log_dir='logs'):
        self.host = host
        self.port = port
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.running = False
        self.sock = None
        
    def start(self, callback=None):
        """启动 Syslog 服务器（非阻塞模式）"""
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1.0)  
        self.sock.bind((self.host, self.port))
        logger.info(f"Syslog 服务器启动，监听 {self.host}:{self.port}")
        
        while self.running:
            try:
                # 使用 select 实现非阻塞（备选方案）
                ready, _, _ = select.select([self.sock], [], [], 1.0)
                if not ready:
                    continue
                    
                data, addr = self.sock.recvfrom(4096)
                
                message = data.decode('utf-8', errors='replace').strip()
                # 清洗不可见字符
                message = ''.join(c for c in message if c.isprintable() or c in '\n\r\t')
                
                timestamp = datetime.now()
                device_ip = addr[0]
                
                # 保存原始日志
                self._save_log(device_ip, timestamp, message)
                
                # 回调处理
                if callback:
                    callback(device_ip, message, timestamp)
                    
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"接收日志失败: {e}")
        
        if self.sock:
            self.sock.close()
    
    def _save_log(self, device_ip, timestamp, message):
        """保存原始日志到文件"""
        date_str = timestamp.strftime("%Y%m%d")
        log_file = self.log_dir / f"{device_ip}_{date_str}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp.isoformat()} {message}\n")
    
    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
