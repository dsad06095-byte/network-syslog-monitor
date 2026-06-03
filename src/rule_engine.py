#!/usr/bin/env python3
import re
import yaml
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

class RuleEngine:
    def __init__(self, rules_file: str = "config/rules.yaml"):
        self.rules_file = Path(rules_file)
        self.rules = self._load_rules()
        # 计数缓存：key -> 时间戳列表
        self.event_cache = defaultdict(list)
        #  告警冷却缓存：规则+设备 -> 上次告警时间
        self.last_alert_time = defaultdict(datetime)
        #  冷却时间（秒），避免重复告警刷屏
        self.cooldown_seconds = 300  # 5分钟
        
    def _load_rules(self):
        with open(self.rules_file, encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('rules', [])
    
    def _is_in_cooldown(self, device_ip: str, rule_name: str, current_time: datetime) -> bool:
        """检查是否在冷却期内"""
        key = f"{device_ip}:{rule_name}"
        last_time = self.last_alert_time.get(key)
        if last_time:
            if (current_time - last_time).total_seconds() < self.cooldown_seconds:
                return True
        return False
    
    def match(self, device_ip: str, message: str, timestamp: datetime):
        """匹配日志，返回匹配的规则列表"""
        matched = []
        
        for rule in self.rules:
            pattern = rule.get('pattern')
            if not pattern:
                continue
                
            if re.search(pattern, message, re.IGNORECASE):
                rule_name = rule['name']
                severity = rule.get('severity', 'info')
                count_threshold = rule.get('count_threshold')
                
                #  检查冷却期
                if self._is_in_cooldown(device_ip, rule_name, timestamp):
                    logger.debug(f"{device_ip} {rule_name} 在冷却期内，跳过告警")
                    continue
                
                if count_threshold:
                    # 计数类规则
                    key = f"{device_ip}:{rule_name}"
                    self.event_cache[key].append(timestamp)
                    
                    # 清理过期记录
                    time_window = rule.get('time_window', 60)
                    cutoff = timestamp - timedelta(seconds=time_window)
                    self.event_cache[key] = [
                        t for t in self.event_cache[key] if t > cutoff
                    ]
                    
                    if len(self.event_cache[key]) >= count_threshold:
                        matched.append({
                            'name': rule_name,
                            'severity': severity,
                            'count': len(self.event_cache[key]),
                            'message': message[:200]
                        })
                        #  记录告警时间（用于冷却）
                        self.last_alert_time[key] = timestamp
                        #  清理缓存，但保留最近1条避免完全丢失
                        self.event_cache[key] = self.event_cache[key][-1:]
                else:
                    # 单次匹配规则
                    matched.append({
                        'name': rule_name,
                        'severity': severity,
                        'message': message[:200]
                    })
                    #  单次规则也需要冷却
                    key = f"{device_ip}:{rule_name}"
                    self.last_alert_time[key] = timestamp
        
        return matched
