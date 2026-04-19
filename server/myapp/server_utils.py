# -*- coding: utf-8 -*-
"""
utils.py
Вспомогательные функции серверной части snbld resvap
"""

import uuid
import hashlib
import secrets
import sys
import requests
from datetime import datetime, timedelta

from config import (
    BOT_TOKEN, ADMIN_CHAT_ID, GROUP_CHAT_ID,
    KEY_TYPES, PRICES, SUBSCRIPTION_NAMES, KEY_LENGTH
)
from models import db, Key, BannedHWID, User


def generate_token():
    """Генерирует токен сессии"""
    return secrets.token_urlsafe(32)


def generate_key_string():
    """Генерирует строку ключа активации"""
    return str(uuid.uuid4()).replace('-', '')[:KEY_LENGTH].upper()


def get_key_type_by_price(price_kopecks):
    """Определяет тип ключа по цене"""
    return PRICES.get(price_kopecks)


def get_key_type_by_name(name):
    """Определяет тип ключа по названию подписки"""
    return SUBSCRIPTION_NAMES.get(name)


def get_expiry_date(key_type):
    """Возвращает дату истечения для типа ключа"""
    if key_type not in KEY_TYPES:
        return None
    
    days = KEY_TYPES[key_type].get('days')
    if days is None:  # permanent
        return None
    return datetime.utcnow() + timedelta(days=days)


def is_hwid_banned(hwid):
    """Проверяет, заблокирован ли HWID"""
    if not hwid:
        return False
    return BannedHWID.query.filter_by(hwid=hwid).first() is not None


def get_active_key_for_hwid(hwid):
    """Получает активный ключ для HWID"""
    if not hwid:
        return None
    return Key.query.filter_by(used_by=hwid, is_active=True).first()


def check_key_validity_for_hwid(hwid):
    """Проверяет валидность ключа для HWID"""
    key = get_active_key_for_hwid(hwid)
    if not key:
        return False
    if key.expires_at and key.expires_at < datetime.utcnow():
        key.is_active = False
        db.session.commit()
        return False
    return True


def send_telegram_message(chat_id, text, parse_mode='HTML'):
    """Отправляет сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    try:
        response = requests.post(url, data=data, timeout=5)
        return response.json()
    except Exception as e:
        sys.stderr.write(f"Ошибка отправки в Telegram: {e}\n")
        return None


def generate_invite_link():
    """Генерирует ссылку-приглашение в группу"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createChatInviteLink"
    data = {
        "chat_id": GROUP_CHAT_ID,
        "member_limit": 1,
        "expire_date": None
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        if result.get("ok"):
            return result["result"]["invite_link"]
        else:
            sys.stderr.write(f"Ошибка создания ссылки: {result}\n")
            return None
    except Exception as e:
        sys.stderr.write(f"Ошибка при создании ссылки: {e}\n")
        return None


def create_key(key_type, source='tribute', purchaser_tg_id=None, purchaser_username=None):
    """Создаёт новый ключ активации"""
    if key_type not in KEY_TYPES:
        return None
    
    key_str = generate_key_string()
    expires_at = get_expiry_date(key_type)
    
    new_key = Key(
        key=key_str,
        key_type=key_type,
        source=source,
        is_active=True,
        expires_at=expires_at,
        purchaser_tg_id=str(purchaser_tg_id) if purchaser_tg_id else None,
        purchaser_username=purchaser_username
    )
    
    db.session.add(new_key)
    db.session.commit()
    
    return new_key


def activate_key(key_str, hwid=None, telegram_id=None):
    """
    Активирует ключ
    :return: (success, message, key_data)
    """
    if not key_str:
        return False, 'Ключ обязателен', None
    
    key = Key.query.filter_by(key=key_str).first()
    if not key:
        return False, 'Ключ не найден', None
    
    if not key.is_active:
        return False, 'Ключ заблокирован или деактивирован', None
    
    if key.used_by:
        return False, 'Ключ уже использован', None
    
    if key.expires_at and key.expires_at < datetime.utcnow():
        key.is_active = False
        db.session.commit()
        return False, 'Срок действия ключа истёк', None
    
    if hwid:
        if is_hwid_banned(hwid):
            return False, 'Ваш компьютер заблокирован', None
        key.used_by = hwid
    elif telegram_id:
        key.used_by = telegram_id
    else:
        return False, 'Не указан HWID или Telegram ID', None
    
    key.used_at = datetime.utcnow()
    
    if not key.expires_at and key.key_type != 'permanent':
        key.expires_at = get_expiry_date(key.key_type)
    
    db.session.commit()
    
    # Уведомляем админа
    send_telegram_message(
        ADMIN_CHAT_ID,
        f"🔑 Ключ {key.key_type} активирован на {key.used_by}"
    )
    
    return True, 'Ключ успешно активирован', key.to_dict()


def hash_password(password):
    """Хеширует пароль"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_telegram_init_data(init_data):
    """
    Проверяет initData от Telegram WebApp
    :return: (valid, user_data)
    """
    import urllib.parse
    import hmac
    import hashlib
    
    try:
        params = urllib.parse.parse_qs(init_data)
        
        # Получаем hash
        received_hash = params.get('hash', [''])[0]
        if not received_hash:
            return False, None
        
        # Удаляем hash из параметров
        params.pop('hash', None)
        
        # Сортируем параметры
        data_check_arr = []
        for key, value in params.items():
            if value:
                data_check_arr.append(f"{key}={value[0]}")
        data_check_arr.sort()
        data_check_string = '\n'.join(data_check_arr)
        
        # Вычисляем hash
        secret_key = hmac.new(
            b'WebAppData',
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            return False, None
        
        # Извлекаем user data
        user_str = params.get('user', [''])[0]
        if user_str:
            import json
            user_info = json.loads(user_str)
            return True, user_info
        
        return False, None
        
    except Exception as e:
        sys.stderr.write(f"Ошибка проверки initData: {e}\n")
        return False, None
