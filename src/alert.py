#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claw-ex 警告通知模块
支持阈值告警（CPU/内存/任务失败等）
通知渠道：邮件、Webhook、飞书
"""

import sys
import os
import json
import time
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'

def c_cyan(s): return f"{Colors.CYAN}{s}{Colors.RESET}"
def c_yellow(s): return f"{Colors.YELLOW}{s}{Colors.RESET}"
def c_green(s): return f"{Colors.GREEN}{s}{Colors.RESET}"
def c_red(s): return f"{Colors.RED}{s}{Colors.RESET}"
def c_gray(s): return f"{Colors.GRAY}{s}{Colors.RESET}"
def c_bold(s): return f"{Colors.BOLD}{s}{Colors.RESET}"

# 路径配置
OPENCLAW_HOME = Path(os.environ.get('OPENCLAW_HOME', Path.home() / '.openclaw'))
ALERT_CONFIG_FILE = OPENCLAW_HOME / 'alert-config.json'
ALERT_HISTORY_FILE = OPENCLAW_HOME / 'alert-history.json'

class AlertChannel(Enum):
    EMAIL = 'email'
    WEBHOOK = 'webhook'
    FEISHU = 'feishu'

class AlertSeverity(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

@dataclass
class AlertRule:
    id: str
    name: str
    metric: str  # cpu, memory, task_failure, disk, etc.
    threshold: float
    operator: str  # gt, lt, eq, gte, lte
    channel: str
    channel_config: Dict[str, Any]
    severity: str
    enabled: bool = True
    cooldown_minutes: int = 15
    created_at: str = ''
    last_triggered: str = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

def generate_alert_id(name: str) -> str:
    """生成唯一的告警 ID"""
    timestamp = datetime.now().isoformat()
    return hashlib.md5(f"{name}-{timestamp}".encode()).hexdigest()[:12]

def load_alerts() -> List[AlertRule]:
    """加载告警配置"""
    if not ALERT_CONFIG_FILE.exists():
        return []
    
    try:
        with open(ALERT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [AlertRule.from_dict(r) for r in data.get('rules', [])]
    except Exception as e:
        print(c_yellow(f'⚠️  加载告警配置失败：{e}'))
        return []

def save_alerts(alerts: List[AlertRule]):
    """保存告警配置"""
    ALERT_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        'version': '1.0',
        'updated_at': datetime.now().isoformat(),
        'rules': [a.to_dict() for a in alerts]
    }
    with open(ALERT_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_alert_history() -> List[Dict]:
    """加载告警历史"""
    if not ALERT_HISTORY_FILE.exists():
        return []
    
    try:
        with open(ALERT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_alert_history(history: List[Dict]):
    """保存告警历史"""
    ALERT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def send_email_notification(to: str, subject: str, body: str, smtp_config: Dict) -> bool:
    """发送邮件通知"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = smtp_config.get('from', smtp_config.get('username'))
        msg['To'] = to
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(smtp_config['host'], smtp_config.get('port', 587))
        server.starttls()
        server.login(smtp_config['username'], smtp_config['password'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(c_red(f'✗ 邮件发送失败：{e}'))
        return False

def send_webhook_notification(url: str, payload: Dict, headers: Dict = None) -> bool:
    """发送 Webhook 通知"""
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers or {'Content-Type': 'application/json'},
            timeout=10
        )
        return response.status_code in [200, 201, 204]
    except Exception as e:
        print(c_red(f'✗ Webhook 发送失败：{e}'))
        return False

def send_feishu_notification(webhook_url: str, title: str, content: str, severity: str) -> bool:
    """发送飞书通知"""
    try:
        # 飞书机器人消息格式
        color_map = {
            'low': 'blue',
            'medium': 'orange',
            'high': 'red',
            'critical': 'red'
        }
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🚨 {title}"
                    },
                    "template": color_map.get(severity, 'blue')
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": content
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"触发时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(c_red(f'✗ 飞书通知发送失败：{e}'))
        return False

def send_notification(rule: AlertRule, metric_value: float, context: Dict = None) -> bool:
    """发送通知"""
    title = f"告警：{rule.name}"
    content = f"""**告警规则**: {rule.name}
**监控指标**: {rule.metric}
**当前值**: {metric_value}
**阈值**: {rule.operator} {rule.threshold}
**严重程度**: {rule.severity.upper()}

{context.get('message', '') if context else ''}"""
    
    channel = rule.channel
    config = rule.channel_config
    
    if channel == 'email':
        return send_email_notification(
            config.get('to'),
            title,
            content,
            config.get('smtp', {})
        )
    elif channel == 'webhook':
        return send_webhook_notification(
            config.get('url'),
            {
                'alert': rule.name,
                'metric': rule.metric,
                'value': metric_value,
                'threshold': rule.threshold,
                'severity': rule.severity,
                'time': datetime.now().isoformat()
            },
            config.get('headers')
        )
    elif channel == 'feishu':
        return send_feishu_notification(
            config.get('webhook_url'),
            title,
            content,
            rule.severity
        )
    else:
        print(c_red(f'✗ 不支持的通知渠道：{channel}'))
        return False

def check_alerts(metrics: Dict[str, float], context: Dict = None):
    """检查并触发告警"""
    alerts = load_alerts()
    history = load_alert_history()
    now = datetime.now()
    triggered = []
    
    for rule in alerts:
        if not rule.enabled:
            continue
        
        # 检查冷却时间
        if rule.last_triggered:
            last_trigger = datetime.fromisoformat(rule.last_triggered)
            if (now - last_trigger).total_seconds() < rule.cooldown_minutes * 60:
                continue
        
        # 获取指标值
        metric_value = metrics.get(rule.metric)
        if metric_value is None:
            continue
        
        # 检查阈值
        triggered_flag = False
        if rule.operator == 'gt' and metric_value > rule.threshold:
            triggered_flag = True
        elif rule.operator == 'lt' and metric_value < rule.threshold:
            triggered_flag = True
        elif rule.operator == 'eq' and metric_value == rule.threshold:
            triggered_flag = True
        elif rule.operator == 'gte' and metric_value >= rule.threshold:
            triggered_flag = True
        elif rule.operator == 'lte' and metric_value <= rule.threshold:
            triggered_flag = True
        
        if triggered_flag:
            # 发送通知
            if send_notification(rule, metric_value, context):
                rule.last_triggered = now.isoformat()
                history.append({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'metric': rule.metric,
                    'value': metric_value,
                    'threshold': rule.threshold,
                    'severity': rule.severity,
                    'channel': rule.channel,
                    'triggered_at': now.isoformat(),
                    'status': 'sent'
                })
                triggered.append(rule.name)
                print(c_green(f'✓ 告警已发送：{rule.name}'))
            else:
                history.append({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'metric': rule.metric,
                    'value': metric_value,
                    'threshold': rule.threshold,
                    'severity': rule.severity,
                    'channel': rule.channel,
                    'triggered_at': now.isoformat(),
                    'status': 'failed'
                })
                print(c_red(f'✗ 告警发送失败：{rule.name}'))
    
    # 保存更新
    save_alerts(alerts)
    save_alert_history(history[-1000:])  # 保留最近 1000 条
    
    return triggered

def cmd_alert_list(args: List[str]):
    """列出所有告警规则"""
    alerts = load_alerts()
    
    print(c_cyan('\n🔔 告警规则:\n'))
    
    if not alerts:
        print(c_gray('  （无告警规则）\n'))
        return
    
    headers = ['ID', '名称', '指标', '条件', '渠道', '严重性', '状态']
    rows = []
    
    for alert in alerts:
        status = '🟢' if alert.enabled else '🔴'
        rows.append([
            alert.id[:8],
            alert.name[:20],
            alert.metric,
            f"{alert.operator} {alert.threshold}",
            alert.channel,
            alert.severity,
            status
        ])
    
    # 表格输出
    col_widths = [max(len(h), max(len(str(row[i])) for row in rows)) + 2 for i, h in enumerate(headers)]
    
    line = '┌' + '┬'.join('─' * w for w in col_widths) + '┐'
    sep = '├' + '┼'.join('─' * w for w in col_widths) + '┤'
    end = '└' + '┴'.join('─' * w for w in col_widths) + '┘'
    
    header_row = '│' + '│'.join(h.ljust(w) for h, w in zip(headers, col_widths)) + '│'
    
    output = [line, header_row, sep]
    for row in rows:
        padded_row = list(row) + [''] * (len(headers) - len(row))
        row_str = '│' + '│'.join(str(cell).ljust(w) for cell, w in zip(padded_row, col_widths)) + '│'
        output.append(row_str)
    output.append(end)
    
    print('\n'.join(output))
    print(f"\n共 {len(alerts)} 条规则\n")

def cmd_alert_create(args: List[str]):
    """创建告警规则"""
    if len(args) < 8:
        print(c_red('❌ 参数不足'))
        print('用法：claw-ex alert create <name> <metric> <operator> <threshold> <channel> <channel_config> [选项]')
        print('示例:')
        print('  claw-ex alert create "CPU 高负载" cpu gt 80 feishu \'{"webhook_url":"https://..."}\'')
        print('  claw-ex alert create "内存不足" memory gt 90 email \'{"to":"admin@example.com","smtp":{...}}\'')
        print('  claw-ex alert create "任务失败" task_failure gt 5 webhook \'{"url":"https://..."}\'')
        print('\n指标：cpu, memory, disk, task_failure, session_count, etc.')
        print('操作符：gt, lt, eq, gte, lte')
        print('渠道：email, webhook, feishu')
        print('选项：--severity low|medium|high|critical --cooldown <minutes> --no-enabled')
        sys.exit(1)
    
    name = args[2]
    metric = args[3]
    operator = args[4]
    
    try:
        threshold = float(args[5])
    except ValueError:
        print(c_red('❌ 阈值必须是数字'))
        sys.exit(1)
    
    channel = args[6]
    
    try:
        channel_config = json.loads(args[7])
    except json.JSONDecodeError:
        print(c_red('❌ 渠道配置必须是有效的 JSON'))
        sys.exit(1)
    
    # 解析选项
    severity = 'medium'
    cooldown = 15
    enabled = True
    
    if '--severity' in args:
        idx = args.index('--severity')
        if idx + 1 < len(args):
            severity = args[idx + 1]
    
    if '--cooldown' in args:
        idx = args.index('--cooldown')
        if idx + 1 < len(args):
            try:
                cooldown = int(args[idx + 1])
            except ValueError:
                pass
    
    if '--no-enabled' in args:
        enabled = False
    
    # 验证参数
    if operator not in ['gt', 'lt', 'eq', 'gte', 'lte']:
        print(c_red(f'❌ 不支持的操作符：{operator}'))
        sys.exit(1)
    
    if channel not in ['email', 'webhook', 'feishu']:
        print(c_red(f'❌ 不支持的渠道：{channel}'))
        sys.exit(1)
    
    if severity not in ['low', 'medium', 'high', 'critical']:
        print(c_red(f'❌ 不支持的严重性：{severity}'))
        sys.exit(1)
    
    # 创建规则
    rule = AlertRule(
        id=generate_alert_id(name),
        name=name,
        metric=metric,
        threshold=threshold,
        operator=operator,
        channel=channel,
        channel_config=channel_config,
        severity=severity,
        enabled=enabled,
        cooldown_minutes=cooldown,
        created_at=datetime.now().isoformat()
    )
    
    # 保存
    alerts = load_alerts()
    alerts.append(rule)
    save_alerts(alerts)
    
    print(c_green(f'\n✅ 告警规则已创建:\n'))
    print(f"  ID:        {c_bold(rule.id)}")
    print(f"  名称：     {rule.name}")
    print(f"  指标：     {rule.metric}")
    print(f"  条件：     {rule.operator} {rule.threshold}")
    print(f"  渠道：     {rule.channel}")
    print(f"  严重性：   {rule.severity}")
    print(f"  冷却时间：{rule.cooldown_minutes} 分钟")
    print(f"  状态：     {'🟢 已启用' if rule.enabled else '🔴 已禁用'}\n")

def cmd_alert_delete(args: List[str]):
    """删除告警规则"""
    if len(args) < 3:
        print(c_red('❌ 缺少告警 ID 或名称'))
        print('用法：claw-ex alert delete <id|name> [--confirm]')
        sys.exit(1)
    
    identifier = args[2]
    confirm = '--confirm' in args
    
    alerts = load_alerts()
    
    # 查找告警
    found = None
    for alert in alerts:
        if alert.id == identifier or alert.name == identifier:
            found = alert
            break
    
    if not found:
        print(c_red(f'❌ 未找到告警规则：{identifier}'))
        sys.exit(1)
    
    if not confirm:
        print(c_yellow(f'⚠️  确定要删除告警规则 "{found.name}" 吗？'))
        print('使用 --confirm 确认删除')
        sys.exit(1)
    
    alerts = [a for a in alerts if a.id != found.id]
    save_alerts(alerts)
    
    print(c_green(f'✅ 告警规则已删除：{found.name}\n'))

def cmd_alert_run(args: List[str]):
    """手动触发告警检查"""
    print(c_cyan('\n🔍 检查告警...\n'))
    
    # 模拟指标数据（实际应从监控系统获取）
    try:
        import psutil
        metrics = {
            'cpu': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent
        }
    except ImportError:
        metrics = {
            'cpu': 50.0,
            'memory': 60.0,
            'disk': 40.0
        }
    
    print(f"当前指标:")
    for k, v in metrics.items():
        print(f"  {k}: {v}%")
    print()
    
    triggered = check_alerts(metrics, {'message': '手动触发检查'})
    
    if triggered:
        print(c_green(f'\n✅ 触发了 {len(triggered)} 条告警:'))
        for name in triggered:
            print(f"  - {name}")
    else:
        print(c_gray('\n没有触发告警\n'))

def cmd_alert_history(args: List[str]):
    """查看告警历史"""
    history = load_alert_history()
    
    print(c_cyan('\n📜 告警历史 (最近 20 条):\n'))
    
    if not history:
        print(c_gray('  （无历史记录）\n'))
        return
    
    # 显示最近 20 条
    recent = history[-20:][::-1]
    
    headers = ['时间', '规则', '指标', '值', '状态']
    rows = []
    
    for entry in recent:
        time_str = datetime.fromisoformat(entry['triggered_at']).strftime('%m-%d %H:%M')
        status_icon = '✓' if entry['status'] == 'sent' else '✗'
        rows.append([
            time_str,
            entry['rule_name'][:15],
            entry['metric'],
            entry['value'],
            status_icon
        ])
    
    col_widths = [max(len(h), max(len(str(row[i])) for row in rows)) + 2 for i, h in enumerate(headers)]
    
    line = '┌' + '┬'.join('─' * w for w in col_widths) + '┐'
    sep = '├' + '┼'.join('─' * w for w in col_widths) + '┤'
    end = '└' + '┴'.join('─' * w for w in col_widths) + '┘'
    
    header_row = '│' + '│'.join(h.ljust(w) for h, w in zip(headers, col_widths)) + '│'
    
    output = [line, header_row, sep]
    for row in rows:
        padded_row = list(row) + [''] * (len(headers) - len(row))
        row_str = '│' + '│'.join(str(cell).ljust(w) for cell, w in zip(padded_row, col_widths)) + '│'
        output.append(row_str)
    output.append(end)
    
    print('\n'.join(output))
    print(f"\n共 {len(history)} 条历史记录\n")

def cmd_alert_test(args: List[str]):
    """测试告警通知"""
    if len(args) < 5:
        print(c_red('❌ 参数不足'))
        print('用法：claw-ex alert test <channel> <config> [message]')
        print('示例:')
        print('  claw-ex alert test feishu \'{"webhook_url":"https://..."}\' "测试消息"')
        sys.exit(1)
    
    channel = args[2]
    
    try:
        config = json.loads(args[3])
    except json.JSONDecodeError:
        print(c_red('❌ 配置必须是有效的 JSON'))
        sys.exit(1)
    
    message = args[4] if len(args) > 4 else "这是一条测试告警消息"
    
    # 创建临时规则
    rule = AlertRule(
        id='test',
        name='测试告警',
        metric='test',
        threshold=0,
        operator='gt',
        channel=channel,
        channel_config=config,
        severity='low',
        enabled=True,
        cooldown_minutes=0,
        created_at=datetime.now().isoformat()
    )
    
    print(c_cyan(f'\n📤 发送测试通知到 {channel}...\n'))
    
    if send_notification(rule, 0, {'message': message}):
        print(c_green('✅ 测试通知发送成功!\n'))
    else:
        print(c_red('❌ 测试通知发送失败!\n'))
        sys.exit(1)
