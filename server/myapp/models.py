# -*- coding: utf-8 -*-
"""
models.py
Модели базы данных для snbld resvap
ОБНОВЛЁННАЯ ВЕРСИЯ - без HWID, с сессиями
"""

from datetime import datetime
import hashlib
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Пользователь системы"""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    hwid = db.Column(db.String(256), nullable=True)  # ← Оставлен для обратной совместимости (не используется)
    token = db.Column(db.String(256), unique=True, nullable=False)
    telegram_id = db.Column(db.String(64), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    reg_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Активен')
    last_seen = db.Column(db.DateTime, nullable=True)

    # Связи
    keys = db.relationship('Key', backref='owner', lazy='dynamic')

    def set_password(self, password):
        """Хеширует пароль"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        """Проверяет пароль"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def to_dict(self):
        """Преобразует в словарь"""
        return {
            'id': self.id,
            'login': self.login,
            'hwid': self.hwid,
            'telegram_id': self.telegram_id,
            'status': self.status,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'reg_date': self.reg_date.isoformat() if self.reg_date else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }

    def __repr__(self):
        return f'<User {self.login}>'


class BannedHWID(db.Model):
    """Заблокированные HWID (для обратной совместимости)"""
    __tablename__ = 'banned_hwid'

    id = db.Column(db.Integer, primary_key=True)
    hwid = db.Column(db.String(256), unique=True, nullable=False)
    banned_at = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        """Преобразует в словарь"""
        return {
            'id': self.id,
            'hwid': self.hwid,
            'banned_at': self.banned_at.isoformat() if self.banned_at else None,
            'reason': self.reason
        }

    def __repr__(self):
        return f'<BannedHWID {self.hwid}>'


class Key(db.Model):
    """Ключи активации"""
    __tablename__ = 'key'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    key_type = db.Column(db.String(20), nullable=False)
    source = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    used_by = db.Column(db.String(256), nullable=True)  # ← Теперь хранит "activated" вместо HWID
    used_at = db.Column(db.DateTime, nullable=True)
    activated_at = db.Column(db.DateTime, nullable=True)  # ← Дата первой активации
    download_count = db.Column(db.Integer, default=0)  # ← Сколько раз скачан
    is_active = db.Column(db.Boolean, default=True)
    purchaser_tg_id = db.Column(db.String(64), nullable=True)
    purchaser_username = db.Column(db.String(128), nullable=True)

    # Связи
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    sessions = db.relationship('Session', backref='session_key', lazy='dynamic')

    @property
    def time_left(self):
        """Оставшееся время действия"""
        if not self.expires_at:
            return "бессрочно"
        delta = self.expires_at - datetime.utcnow()
        if delta.total_seconds() <= 0:
            return "истёк"
        days = delta.days
        hours = delta.seconds // 3600
        return f"{days}д {hours}ч"

    def is_valid(self):
        """Проверяет валидность ключа"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def to_dict(self):
        """Преобразует в словарь"""
        return {
            'id': self.id,
            'key': self.key,
            'key_type': self.key_type,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used_by': self.used_by,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'download_count': self.download_count,
            'is_active': self.is_active,
            'time_left': self.time_left
        }

    def __repr__(self):
        return f'<Key {self.key} ({self.key_type})>'


class Session(db.Model):
    """Сессии активации (НОВАЯ МОДЕЛЬ)"""
    __tablename__ = 'session'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    key_id = db.Column(db.Integer, db.ForeignKey('key.id'), nullable=False)
    key = db.Column(db.String(64), nullable=False)  # Дублирование для быстрого поиска
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45), nullable=True)

    def to_dict(self):
        """Преобразует в словарь"""
        return {
            'session_id': self.session_id,
            'key': self.key,
            'key_id': self.key_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<Session {self.session_id}>'


def init_db(app):
    """Инициализирует базу данных"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
