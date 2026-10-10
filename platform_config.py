"""
平台配置：读取 config/platform.json，敏感项可用环境变量覆盖。

环境变量（优先级高于配置文件）:
  PLATFORM_CONFIG  配置文件路径
  MQTT_HOST / MQTT_PORT / MQTT_USERNAME / MQTT_PASSWORD / MQTT_TLS / MQTT_CA_CERT
  API_TOKEN        接口访问令牌（为空则不校验）
  SECRET_KEY       Flask 密钥
"""

import json
import os
import ssl
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.environ.get('PLATFORM_CONFIG', os.path.join(BASE_DIR, 'config', 'platform.json'))


def load_config():
    with open(CONFIG_PATH, encoding='utf-8') as f:
        cfg = json.load(f)

    mqtt_cfg = cfg.setdefault('mqtt', {})
    env = os.environ
    if env.get('MQTT_HOST'):
        mqtt_cfg['host'] = env['MQTT_HOST']
    if env.get('MQTT_PORT'):
        mqtt_cfg['port'] = int(env['MQTT_PORT'])
    if env.get('MQTT_USERNAME'):
        mqtt_cfg['username'] = env['MQTT_USERNAME']
    if env.get('MQTT_PASSWORD'):
        mqtt_cfg['password'] = env['MQTT_PASSWORD']
    if env.get('MQTT_TLS'):
        mqtt_cfg['tls'] = env['MQTT_TLS'].lower() in ('1', 'true', 'yes')
    if env.get('MQTT_CA_CERT'):
        mqtt_cfg['ca_cert'] = env['MQTT_CA_CERT']
    if env.get('API_TOKEN'):
        cfg['api_token'] = env['API_TOKEN']
    cfg.setdefault('devices', {})
    return cfg


CONFIG = load_config()


def create_mqtt_client(role, mqtt_module):
    """按配置创建 MQTT 客户端：账号密码、TLS、自动重连。调用方负责 connect_async + loop_start。"""
    mqtt_cfg = CONFIG['mqtt']
    client_id = f"{mqtt_cfg.get('client_id_prefix', 'idip')}-{role}-{uuid.uuid4().hex[:6]}"
    try:
        client = mqtt_module.Client(mqtt_module.CallbackAPIVersion.VERSION1, client_id=client_id)
    except AttributeError:  # paho-mqtt < 2.0
        client = mqtt_module.Client(client_id=client_id)
    if mqtt_cfg.get('username'):
        client.username_pw_set(mqtt_cfg['username'], mqtt_cfg.get('password') or None)
    if mqtt_cfg.get('tls'):
        client.tls_set(ca_certs=mqtt_cfg.get('ca_cert') or None, cert_reqs=ssl.CERT_REQUIRED)
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    return client


def mqtt_address():
    return CONFIG['mqtt'].get('host', '127.0.0.1'), int(CONFIG['mqtt'].get('port', 1883)), int(CONFIG['mqtt'].get('keepalive', 60))


def parse_timestamp(raw):
    """把设备上报的时间统一成本地时间（不带时区），与数据库中其它时间一致。
    支持 ISO 字符串（带或不带时区、Z 结尾）和 Unix 秒/毫秒时间戳；无法解析时用当前时间。"""
    if raw is None or isinstance(raw, bool):
        return datetime.now()
    try:
        if isinstance(raw, (int, float)):
            seconds = raw / 1000 if raw > 1e11 else raw
            return datetime.fromtimestamp(seconds)
        ts = datetime.fromisoformat(str(raw).strip().replace('Z', '+00:00'))
        if ts.tzinfo is not None:
            ts = ts.astimezone().replace(tzinfo=None)
        return ts
    except (ValueError, TypeError, OverflowError, OSError):
        return datetime.now()
