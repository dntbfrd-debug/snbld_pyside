from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, send_file, make_response

from datetime import datetime, timedelta

import secrets

import os

import hashlib

import sys

import requests

import json

import uuid

import io

from flask_cors import CORS

from config import (SELECTEL_ACCESS_KEY, SELECTEL_SECRET_KEY)


from models import User, BannedHWID, Key, Session, init_db, db


app = Flask(__name__)

CORS(app)


# ===== Конфигурация БД =====

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "users.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


init_db(app)


# ===== Настройки Telegram =====

BOT_TOKEN = "8716164046:AAGHHmqjUZKoOL_7bl1D6e4gyWkIcxSJKO4"

ADMIN_CHAT_ID = "2114966435"

GROUP_CHAT_ID = -1003669812066

DOWNLOAD_URL = "https://snbld.ru/webapp"

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), 'downloads')



def _find_latest_zip():

    """Находит самый новый onedir ZIP в downloads/"""

    if not os.path.exists(DOWNLOADS_DIR):

        return None

    files = [f for f in os.listdir(DOWNLOADS_DIR)

             if f.startswith('snbld_resvap_') and f.endswith('.zip')]

    if not files:

        return None

    return sorted(files)[-1]

# =============================


# ------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ -------------------


def generate_token():

    return secrets.token_urlsafe(32)



def generate_session_id():

    return secrets.token_hex(32)



def is_hwid_banned(hwid):

    if not hwid:

        return False

    return BannedHWID.query.filter_by(hwid=hwid).first() is not None



def send_telegram_message(chat_id, text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    try:

        requests.post(url, data=data, timeout=5)

    except Exception as e:

        sys.stderr.write(f"Ошибка отправки в Telegram: {e}\n")



def generate_key(key_type, source='tribute'):

    return str(uuid.uuid4()).replace('-', '')[:16].upper()



def get_key_type_by_price(price_kopecks):

    mapping = {

        60000: '30d',

        300000: '180d',

        630000: '365d',

        1000000: 'permanent'

    }

    return mapping.get(price_kopecks)



def get_key_type_by_name(name):

    mapping = {

        'ну затестить чисто': '30d',

        'работяга': '180d',

        'ПАПА': '365d',

        'че?реально?': 'permanent'

    }

    return mapping.get(name)



def get_expiry_date(key_type):

    if key_type == 'test':

        return datetime.utcnow() + timedelta(days=1)

    elif key_type == '30d':

        return datetime.utcnow() + timedelta(days=30)

    elif key_type == '180d':

        return datetime.utcnow() + timedelta(days=180)

    elif key_type == '365d':

        return datetime.utcnow() + timedelta(days=365)

    else:

        return None



def get_active_key_for_hwid(hwid):

    if not hwid:

        return None

    return Key.query.filter_by(used_by=hwid, is_active=True).first()



def check_key_validity_for_hwid(hwid):

    key = get_active_key_for_hwid(hwid)

    if not key:

        return False

    if key.expires_at and key.expires_at < datetime.utcnow():

        key.is_active = False

        db.session.commit()

        return False

    return True



def generate_invite_link():

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createChatInviteLink"

    data = {"chat_id": GROUP_CHAT_ID, "member_limit": 1, "expire_date": None}

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


# ------------------- ЭНДПОИНТЫ ДЛЯ КЛИЕНТОВ (ОБЫЧНЫЕ) -------------------


@app.route('/register', methods=['POST'])

def register():

    data = request.json

    username = data.get('username')

    password = data.get('password')

    hwid = data.get('hwid')

    if not username or not password or not hwid:

        return jsonify({'error': 'Логин, пароль и HWID обязательны'}), 400

    if User.query.filter_by(login=username).first():

        return jsonify({'error': 'Пользователь уже существует'}), 400

    if is_hwid_banned(hwid):

        return jsonify({'error': 'Этот компьютер заблокирован. Регистрация невозможна.'}), 403

    token = generate_token()

    new_user = User(login=username, hwid=hwid, token=token)

    new_user.set_password(password)

    db.session.add(new_user)

    db.session.commit()

    return jsonify({'message': 'Регистрация успешна', 'token': token}), 200



@app.route('/login', methods=['POST'])

def login():

    data = request.json

    username = data.get('username')

    password = data.get('password')

    hwid = data.get('hwid')

    if not username or not password or not hwid:

        return jsonify({'error': 'Логин, пароль и HWID обязательны'}), 400

    user = User.query.filter_by(login=username).first()

    if not user:

        return jsonify({'error': 'Пользователь не найден'}), 404

    if is_hwid_banned(hwid):

        return jsonify({'error': 'Этот компьютер заблокирован. Вход невозможен.'}), 403

    if user.status != 'Активен':

        return jsonify({'error': 'Аккаунт заблокирован'}), 403

    if not user.check_password(password):

        return jsonify({'error': 'Неверный пароль'}), 401

    if user.hwid and user.hwid != hwid:

        return jsonify({'error': 'HWID не совпадает'}), 403

    token = generate_token()

    user.token = token

    user.last_login = datetime.utcnow()

    user.last_seen = datetime.utcnow()

    db.session.commit()

    return jsonify({'message': 'Вход выполнен', 'token': token}), 200



@app.route('/check_token', methods=['POST'])

def check_token():

    data = request.json

    token = data.get('token')

    if not token:

        return jsonify({'error': 'Токен не предоставлен'}), 400

    user = User.query.filter_by(token=token).first()

    if not user:

        return jsonify({'error': 'Токен недействителен'}), 404

    if user.status != 'Активен':

        return jsonify({'error': 'Пользователь заблокирован или удалён'}), 403

    if user.hwid and is_hwid_banned(user.hwid):

        return jsonify({'error': 'Ваш компьютер заблокирован'}), 403

    if user.hwid:

        if not check_key_validity_for_hwid(user.hwid):

            return jsonify({'error': 'У вас нет активного ключа или срок его действия истёк'}), 403

    else:

        return jsonify({'error': 'HWID не привязан к пользователю'}), 403

    user.last_seen = datetime.utcnow()

    db.session.commit()

    return jsonify({'message': 'Токен действителен'}), 200



@app.route('/activate_key', methods=['POST'])

def activate_key():

    """Старая активация (для webapp/бота)"""

    data = request.json

    key_str = data.get('key')

    hwid = data.get('hwid')

    telegram_id = data.get('telegram_id')

    if not key_str:

        return jsonify({'error': 'Ключ обязателен'}), 400

    key = Key.query.filter_by(key=key_str).first()

    if not key:

        return jsonify({'error': 'Ключ не найден'}), 404

    if not key.is_active:

        return jsonify({'error': 'Ключ заблокирован или деактивирован'}), 403

    if key.used_by:

        return jsonify({'error': 'Ключ уже использован'}), 403

    if key.expires_at and key.expires_at < datetime.utcnow():

        key.is_active = False

        db.session.commit()

        return jsonify({'error': 'Срок действия ключа истёк'}), 403

    if hwid:

        if is_hwid_banned(hwid):

            return jsonify({'error': 'Ваш компьютер заблокирован'}), 403

        key.used_by = hwid

    elif telegram_id:

        key.used_by = telegram_id

    else:

        return jsonify({'error': 'Не указан HWID или Telegram ID'}), 400

    key.used_at = datetime.utcnow()

    if not key.expires_at and key.key_type != 'permanent':

        key.expires_at = get_expiry_date(key.key_type)

    db.session.commit()

    send_telegram_message(ADMIN_CHAT_ID, f"🔑 Ключ {key.key_type} активирован на {key.used_by}")

    return jsonify({'message': 'Ключ успешно активирован'}), 200


# ------------------- API ДЛЯ МИНИ-ПРИЛОЖЕНИЯ -------------------


@app.route('/webapp')

def webapp():

    return render_template('webapp.html')



@app.route('/api/auth', methods=['POST'])

def auth():

    data = request.json

    init_data = data.get('initData')

    if not init_data:

        return jsonify({'error': 'No initData'}), 400

    import urllib.parse

    params = urllib.parse.parse_qs(init_data)

    user_str = params.get('user', [''])[0]

    if user_str:

        user_info = json.loads(user_str)

        telegram_id = str(user_info.get('id'))

        return jsonify({'telegram_id': telegram_id})

    return jsonify({'error': 'No user data'}), 400



@app.route('/api/check_hwid', methods=['POST'])

def api_check_hwid():

    try:
        data = request.json

        if not data:
            return jsonify({'error': 'Некорректные данные запроса'}), 400

        hwid = data.get('hwid')

        if not hwid:

            return jsonify({'error': 'HWID required'}), 400

        key = Key.query.filter_by(used_by=hwid, is_active=True).first()

        if not key:

            return jsonify({'valid': False, 'error': 'No active key'}), 200

        if key.expires_at and key.expires_at < datetime.utcnow():

            key.is_active = False

            db.session.commit()

            return jsonify({'valid': False, 'error': 'Key expired'}), 200

        return jsonify({

            'valid': True,

            'key_type': key.key_type,

            'expires_at': key.expires_at.isoformat() if key.expires_at else None,

        }), 200
        
    except Exception as e:
        import sys
        sys.stderr.write(f"Ошибка в api_check_hwid: {e}\n")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500




@app.route('/api/get_key_by_telegram', methods=['POST'])

def get_key_by_telegram():

    data = request.json

    telegram_id = data.get('telegram_id')

    if not telegram_id:

        return jsonify({'error': 'telegram_id required'}), 400

    key = Key.query.filter_by(used_by=telegram_id, is_active=True).first()

    if not key:

        key = Key.query.filter_by(purchaser_tg_id=telegram_id, is_active=True).first()

    if key:

        return jsonify({

            'key': key.key,

            'key_type': key.key_type,

            'expires_at': key.expires_at.isoformat() if key.expires_at else None,

        }), 200

    else:

        return jsonify({'error': 'No key found'}), 404



# ==================== API ДЛЯ ПРОГРАММЫ ====================


@app.route('/api/check_key', methods=['POST'])

def api_check_key():

    """Проверить ключ активации (для программы)"""

    data = request.json

    key_str = data.get('key')

    hwid = data.get('hwid')


    if not key_str:

        return jsonify({'valid': False, 'error': 'Key required'}), 400


    key = Key.query.filter_by(key=key_str).first()

    if not key:

        return jsonify({'valid': False, 'error': 'Key not found', 'blocked': False}), 200


    # Ключ заблокирован (вручную в админке)

    if not key.is_active:

        return jsonify({

            'valid': False,

            'error': 'Key is inactive',

            'blocked': True,

            'activated': key.activated_at is not None

        }), 200


    # Проверяем HWID — защита от передачи ключа другому
    if key.activated_at and key.used_by:
        if not hwid or key.used_by != hwid:
            return jsonify({
                'valid': False,
                'error': 'HWID mismatch',
                'blocked': True,
                'activated': True
            }), 200


    if key.expires_at and key.expires_at < datetime.utcnow():

        key.is_active = False

        db.session.commit()

        return jsonify({'valid': False, 'error': 'Key expired', 'blocked': False}), 200


    return jsonify({

        'valid': True,

        'key_type': key.key_type,

        'expires_at': key.expires_at.isoformat() if key.expires_at else None,

        'activated': key.activated_at is not None,

        'blocked': False

    }), 200



@app.route('/api/activate_key', methods=['POST'])

def api_activate_key():

    """Активация ключа для программы (привязка к HWID)"""

    data = request.json

    key_str = data.get('key')

    hwid = data.get('hwid')


    if not key_str:

        return jsonify({'error': 'Key required'}), 400


    key = Key.query.filter_by(key=key_str).first()

    if not key:

        return jsonify({'error': 'Key not found'}), 404


    # Если ключ был заблокирован, но потом разблокирован — разрешаем повторную активацию

    if not key.is_active:

        # Ключ заблокирован — нельзя активировать

        return jsonify({'error': 'Key is inactive'}), 403


    if key.expires_at and key.expires_at < datetime.utcnow():

        key.is_active = False

        db.session.commit()

        return jsonify({'error': 'Key expired'}), 403


    # Если ключ уже активирован — проверяем HWID

    if key.activated_at:

        if hwid and key.used_by == hwid:

            # Тот же HWID — создаём новую сессию (переустановка/повторный вход)

            pass

        else:

            return jsonify({'error': 'Key already activated on another device'}), 403


    # Помечаем ключ как активированный (или повторно активируем после разблокировки)
    if not hwid:
        return jsonify({'error': 'HWID is required for activation'}), 400
    
    key.used_by = hwid

    key.activated_at = datetime.utcnow()

    db.session.commit()


    # Создаём сессию

    session_id = generate_session_id()

    session = Session(

        session_id=session_id,

        key_id=key.id,

        key=key_str,

        ip_address=request.remote_addr

    )

    db.session.add(session)

    db.session.commit()


    send_telegram_message(ADMIN_CHAT_ID, f"🔑 Ключ {key.key_type} активирован (HWID: {hwid[:8] if hwid else 'N/A'}...)")


    return jsonify({

        'success': True,

        'session_id': session_id,

        'key_type': key.key_type,

        'expires_at': key.expires_at.isoformat() if key.expires_at else None,

        'message': 'Ключ успешно активирован'

    }), 200



@app.route('/api/check_session', methods=['POST'])

def api_check_session():

    try:
        data = request.json

        if not data:
            return jsonify({'error': 'Некорректные данные запроса'}), 400

        session_id = data.get('session_id')

        hwid = data.get('hwid')

        
        if not session_id:

            return jsonify({'valid': False, 'error': 'Session ID required'}), 400

        
        session = Session.query.filter_by(session_id=session_id, is_active=True).first()

        if not session:

            return jsonify({'valid': False, 'error': 'Session not found', 'blocked': False}), 200

        
        # Проверяем что ключ ещё валиден

        key = Key.query.get(session.key_id)

        if not key:

            session.is_active = False

            db.session.commit()

            return jsonify({'valid': False, 'error': 'Key deleted', 'blocked': True}), 200

        
        # Ключ заблокирован в админке

        if not key.is_active:

            session.is_active = False

            db.session.commit()

            return jsonify({

                'valid': False,

                'error': 'Key is no longer active',

                'blocked': True,

                'activated': key.activated_at is not None

            }), 200

        
        if key.expires_at and key.expires_at < datetime.utcnow():

            key.is_active = False

            session.is_active = False

            db.session.commit()

            return jsonify({'valid': False, 'error': 'Key expired', 'blocked': False}), 200

        
        # Проверяем HWID (защита от копирования)

        if hwid and key.used_by and key.used_by != hwid and key.used_by != "activated":

            return jsonify({'valid': False, 'error': 'HWID mismatch', 'blocked': False}), 403

        
        # Обновляем last_seen

        session.last_seen = datetime.utcnow()

        db.session.commit()

        
        return jsonify({

            'valid': True,

            'key_type': key.key_type,

            'expires_at': key.expires_at.isoformat() if key.expires_at else None,

            'activated': key.activated_at is not None,

            'blocked': False

        }), 200
        
    except Exception as e:
        import sys
        sys.stderr.write(f"Ошибка в api_check_session: {e}\n")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500


# ==================== ПОЛУЧЕНИЕ ТОКЕНОВ ====================


@app.route('/api/get_tokens', methods=['POST'])

def api_get_tokens():

    """Получить токены для активированной программы (Telegram, Selectel)"""

    try:
        data = request.json

        if not data:
            return jsonify({'error': 'Некорректные данные запроса'}), 400

        session_id = data.get('session_id')

        key_str = data.get('key')

        
        # Определяем ключ через сессию или напрямую

        key = None

        if session_id:

            session = Session.query.filter_by(session_id=session_id, is_active=True).first()

            if session:

                key = Key.query.get(session.key_id)

        elif key_str:

            key = Key.query.filter_by(key=key_str, is_active=True).first()

        
        if not key:

            return jsonify({'error': 'Ключ не найден или неактивен'}), 404

        
        # Проверяем что ключ активирован

        if not key.activated_at:

            return jsonify({'error': 'Ключ не активирован'}), 403

        
        # Проверяем срок действия

        if key.expires_at and key.expires_at < datetime.utcnow():

            return jsonify({'error': 'Ключ истёк'}), 403

        
        # Возвращаем токены (из конфига)

        tokens = {

            'TELEGRAM_BOT_TOKEN': BOT_TOKEN,

            'TELEGRAM_CHAT_ID': ADMIN_CHAT_ID,

            'SELECTEL_ACCESS_KEY': SELECTEL_ACCESS_KEY,

            'SELECTEL_SECRET_KEY': SELECTEL_SECRET_KEY

        }

        
        return jsonify({

            'tokens': tokens,

            'expires_in': 3600  # 1 час

        }), 200
        
    except Exception as e:
        import sys
        sys.stderr.write(f"Ошибка в api_get_tokens: {e}\n")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500



# ------------------- СКАЧИВАНИЕ ПРОГРАММЫ -------------------


@app.route('/media/<path:filename>')

def media(filename):

    return send_from_directory('media', filename)



@app.route('/video_bg_webm')

def serve_video_webm():

    return video_bg_webm()



@app.route('/video_bg_mp4')

def serve_video_mp4():

    return video_bg_mp4()



@app.route('/static/IMG_0004.MP4')

def video_bg_mp4():

    static_path = os.path.join(os.path.dirname(__file__), 'static', 'IMG_0004.MP4')

    if os.path.exists(static_path):

        response = make_response(send_file(static_path, mimetype='video/mp4'))

        response.headers['Access-Control-Allow-Origin'] = '*'

        response.headers['Accept-Ranges'] = 'bytes'

        return response

    return "File not found", 404



@app.route('/static/background.webm')

def video_bg_webm():

    # Отладочная информация

    app_dir = os.path.dirname(__file__)

    
    # Попробовать разные пути

    possible_paths = [

        os.path.join(app_dir, 'static', 'background.webm'),

        os.path.join(app_dir, '..', 'static', 'background.webm'),

        os.path.join(app_dir, '../myapp/static', 'background.webm'),

        '/var/www/snbld/data/www/snbld.ru/myapp/static/background.webm',

    ]

    
    for static_path in possible_paths:

        if os.path.exists(static_path):

            print(f"Found video at: {static_path}")

            response = make_response(send_file(static_path, mimetype='video/webm'))

            response.headers['Access-Control-Allow-Origin'] = '*'

            response.headers['Accept-Ranges'] = 'bytes'

            return response

    
    # Вернуть отладочную информацию если файл не найден

    return jsonify({

        'error': 'File not found',

        'checked_paths': possible_paths,

        'app_dir': app_dir,

        'static_exists': os.path.exists(os.path.join(app_dir, 'static')),

        'static_files': os.listdir(os.path.join(app_dir, 'static')) if os.path.exists(os.path.join(app_dir, 'static')) else []

    }), 404



@app.route('/debug/static_files')

def debug_static_files():

    """Отладка: показать список файлов в папке static"""

    import os

    static_path = os.path.join(os.path.dirname(__file__), 'static')

    if os.path.exists(static_path):

        files = os.listdir(static_path)

        return {'static_folder': static_path, 'files': files}

    return {'error': 'static folder not found'}



@app.route('/download/<key>')

def download_program(key):

    """Скачать программу с ключом активации (ZIP: актуальный exe + key.txt)"""

    key_obj = Key.query.filter_by(key=key).first()

    if not key_obj:

        return "❌ Ключ не найден", 404


    if not key_obj.is_active:

        return "❌ Ключ заблокирован", 403


    if key_obj.expires_at and key_obj.expires_at < datetime.utcnow():

        key_obj.is_active = False

        db.session.commit()

        return "❌ Ключ истёк", 403


    if not key_obj.activated_at:

        key_obj.activated_at = datetime.utcnow()

        db.session.commit()


    if key_obj.download_count >= 3:

        return "❌ Лимит скачиваний исчерпан. Обратитесь в поддержку", 400


    exe_name = 'snbld_resvap_v1.4.0_setup.exe'

    exe_path = os.path.join(DOWNLOADS_DIR, exe_name)

    
    if not os.path.exists(exe_path):

        return '❌ Программа не найдена на сервере. Обратитесь к администратору.', 500

    
    key_obj.download_count += 1

    db.session.commit()

    
    try:

        import zipfile

        output = io.BytesIO()

        
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as dst_zip:

            dst_zip.write(exe_path, exe_name)

            dst_zip.writestr('activation.key', key_obj.key)

        
        output.seek(0)

        
        return send_file(

            output,

            mimetype='application/zip',

            as_attachment=True,

            download_name='snbld_resvap_setup.zip'

        )

    except Exception as e:

        sys.stderr.write(f"Ошибка создания архива: {e}\n")

        return "❌ Ошибка при создании архива", 500



@app.route('/tribute_webhook', methods=['POST'])
def tribute_webhook():

    body = request.get_data(as_text=True)

    sys.stderr.write(f"Webhook received: {body}\n")

    try:

        data = json.loads(body)

    except Exception as e:

        sys.stderr.write(f"Ошибка парсинга JSON: {e}\n")

        return "OK", 200


    if data.get('name') == 'new_subscription':

        payload = data.get('payload', {})

        tg_user_id = payload.get('telegram_user_id')

        tg_username = payload.get('telegram_username', 'нет юзернейма')

        price = payload.get('price')

        sub_name = payload.get('subscription_name')

        if not tg_user_id or not price:

            sys.stderr.write("Отсутствует tg_user_id или price\n")

            return "OK", 200


        key_type = get_key_type_by_price(price)

        if not key_type:

            key_type = get_key_type_by_name(sub_name)


        if key_type:

            key_str = generate_key(key_type, source='tribute')

            new_key = Key(

                key=key_str,

                key_type=key_type,

                source='tribute',

                is_active=True,

                expires_at=get_expiry_date(key_type),

                purchaser_tg_id=str(tg_user_id),

                purchaser_username=tg_username

            )

            db.session.add(new_key)

            db.session.commit()


            user_msg = f"✅ Спасибо за покупку!\nВаш ключ: <code>{key_str}</code>\n\nСсылка для автоматической привязки: https://snbld.ru/webapp?key={key_str}"

            send_telegram_message(tg_user_id, user_msg)

            admin_msg = f"🔑 Ключ {key_type} отправлен пользователю @{tg_username} (ID: {tg_user_id})"

            send_telegram_message(ADMIN_CHAT_ID, admin_msg)


            invite_link = generate_invite_link()

            if invite_link:

                group_msg = f"🎉 А теперь присоединяйтесь к нашему закрытому клубу!\n{invite_link}"

                send_telegram_message(tg_user_id, group_msg)

                send_telegram_message(ADMIN_CHAT_ID, f"🔗 Пользователь @{tg_username} получил ссылку в группу")


            download_msg = f"📥 Скачать программу можно по ссылке: {DOWNLOAD_URL}"

            send_telegram_message(tg_user_id, download_msg)

            sys.stderr.write(f"Ключ {key_type} отправлен пользователю {tg_user_id}\n")

        else:

            sys.stderr.write(f"Неизвестный тип подписки: цена={price}, имя={sub_name}\n")

            send_telegram_message(ADMIN_CHAT_ID, f"❌ Неизвестный тип подписки: цена={price}, имя={sub_name}")


    return "OK", 200


# ------------------- ВЕБХУК БОТА -------------------


@app.route('/telegram_webhook', methods=['POST'])

def telegram_webhook():

    data = request.get_json()

    if not data:

        return "OK", 200


    if 'message' in data:

        message = data['message']

        chat_id = message['chat']['id']

        text = message.get('text', '')

        if text.startswith('/start'):

            parts = text.split(maxsplit=1)

            args = parts[1] if len(parts) > 1 else ''

            if args and args.startswith('bind_'):

                hwid = args[5:]

                webapp_url = f"https://snbld.ru/webapp?hwid={hwid}&action=bind"

                reply_markup = {

                    "inline_keyboard": [[{

                        "text": "Привязать компьютер",

                        "web_app": {"url": webapp_url}

                    }]]

                }

                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

                payload = {

                    "chat_id": chat_id,

                    "text": "Нажмите кнопку, чтобы привязать компьютер к вашей подписке.",

                    "reply_markup": reply_markup

                }

                requests.post(url, json=payload, timeout=5)

            elif args == 'buy':

                # Покупка подписки через личные сообщения

                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

                payload = {

                    "chat_id": chat_id,

                    "text": (

                        "💳 <b>Покупка подписки</b>\n\n"

                        "Напишите мне для покупки:\n"

                        "👤 @rtmnklvch\n\n"

                        "Я рассчитаю стоимость и выставлю счёт!\n\n"

                        "💰 Цены:\n"

                        "• 30 дней — 600₽\n"

                        "• 180 дней — 3000₽\n"

                        "• 365 дней — 6300₽\n"

                        "• Навсегда — 10000₽"

                    ),

                    "parse_mode": "HTML"

                }

                requests.post(url, json=payload, timeout=5)

            else:

                reply_markup = {

                    "inline_keyboard": [[{

                        "text": "Личный кабинет",

                        "web_app": {"url": "https://snbld.ru/webapp"}

                    }]]

                }

                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

                payload = {

                    "chat_id": chat_id,

                    "text": "Добро пожаловать! Нажмите кнопку, чтобы открыть личный кабинет.",

                    "reply_markup": reply_markup

                }

                requests.post(url, json=payload, timeout=5)


    return "OK", 200


# ------------------- АДМИН-ПАНЕЛЬ (ПОЛЬЗОВАТЕЛИ) -------------------


@app.route('/admin')

def admin_panel():

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    users = User.query.all()

    banned_hwids = BannedHWID.query.all()

    
    # Получаем все активированные ключи с HWID

    activated_keys = Key.query.filter(Key.used_by.isnot(None), Key.used_by != 'activated').all()

    
    # Создаём словарь {user_id: hwid} для ключей с purchaser_tg_id

    key_hwids = {}

    for k in activated_keys:

        if k.purchaser_tg_id:

            key_hwids[k.purchaser_tg_id] = k.used_by

    
    return render_template('admin.html', users=users, banned_hwids=banned_hwids, pwd=pwd, key_hwids=key_hwids)



@app.route('/admin/block/<int:user_id>')

def block_user(user_id):

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    user = User.query.get_or_404(user_id)

    if user.hwid:

        existing = BannedHWID.query.filter_by(hwid=user.hwid).first()

        if not existing:

            banned = BannedHWID(hwid=user.hwid)

            db.session.add(banned)

    user.status = 'Заблокирован'

    db.session.commit()

    return redirect(url_for('admin_panel', pwd=pwd))



@app.route('/admin/unblock/<int:user_id>')

def unblock_user(user_id):

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    user = User.query.get_or_404(user_id)

    if user.hwid:

        banned = BannedHWID.query.filter_by(hwid=user.hwid).first()

        if banned:

            db.session.delete(banned)

    user.status = 'Активен'

    db.session.commit()

    return redirect(url_for('admin_panel', pwd=pwd))



@app.route('/admin/reset_hwid/<int:user_id>')

def reset_hwid(user_id):

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    user = User.query.get_or_404(user_id)

    user.hwid = None

    db.session.commit()

    return redirect(url_for('admin_panel', pwd=pwd))



@app.route('/admin/delete/<int:user_id>')

def delete_user(user_id):

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    user = User.query.get_or_404(user_id)

    db.session.delete(user)

    db.session.commit()

    return redirect(url_for('admin_panel', pwd=pwd))



@app.route('/admin/unban_hwid/<int:ban_id>')

def unban_hwid(ban_id):

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    banned = BannedHWID.query.get_or_404(ban_id)

    db.session.delete(banned)

    db.session.commit()

    return redirect(url_for('admin_panel', pwd=pwd))


# ------------------- АДМИН-ПАНЕЛЬ (КЛЮЧИ) -------------------


@app.route('/admin/keys')

def admin_keys():

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    keys = Key.query.order_by(Key.created_at.desc()).all()

    return render_template('admin_keys.html', keys=keys, pwd=pwd)



@app.route('/admin/key/block/<int:key_id>')

def block_key(key_id):

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    key = Key.query.get_or_404(key_id)

    key.is_active = False

    db.session.commit()

    return redirect(url_for('admin_keys', pwd=pwd))



@app.route('/admin/key/unblock/<int:key_id>')

def unblock_key(key_id):

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    key = Key.query.get_or_404(key_id)

    key.is_active = True

    
    # Восстанавливаем все сессии этого ключа

    sessions = Session.query.filter_by(key_id=key.id, is_active=False).all()

    for s in sessions:

        s.is_active = True

    
    db.session.commit()

    return redirect(url_for('admin_keys', pwd=pwd))



@app.route('/admin/key/delete/<int:key_id>')

def delete_key(key_id):

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    key = Key.query.get_or_404(key_id)

    
    # Удаляем все сессии этого ключа (чтобы избежать ошибки FK)

    sessions = Session.query.filter_by(key_id=key.id).all()

    for s in sessions:

        db.session.delete(s)

    db.session.commit()

    
    db.session.delete(key)

    db.session.commit()

    return redirect(url_for('admin_keys', pwd=pwd))



@app.route('/admin/key/reset_activation/<int:key_id>')

def reset_activation(key_id):

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    key = Key.query.get_or_404(key_id)

    key.activated_at = None

    key.used_by = None

    key.used_at = None

    db.session.commit()

    send_telegram_message(ADMIN_CHAT_ID, f"🔄 Активация ключа {key.key} сброшена")

    return redirect(url_for('admin_keys', pwd=pwd))



@app.route('/admin/generate_gift_key', methods=['POST'])

def generate_gift_key():

    pwd = request.args.get('pwd')

    if pwd != '05509054753f':

        return "Доступ запрещён", 403

    key_type = request.form.get('key_type')

    if key_type not in ['test', '30d', '180d', '365d', 'permanent']:

        return "Неверный тип ключа", 400

    key_str = generate_key(key_type, source='admin_gift')

    new_key = Key(

        key=key_str,

        key_type=key_type,

        source='admin_gift',

        is_active=True,

        expires_at=get_expiry_date(key_type)

    )

    db.session.add(new_key)

    db.session.commit()

    send_telegram_message(ADMIN_CHAT_ID, f"🎁 Создан подарочный ключ {key_type}: {key_str}")

    return redirect(url_for('admin_keys', pwd=pwd))


# ------------------- ЗАПУСК -------------------


if __name__ == '__main__':

    app.run()