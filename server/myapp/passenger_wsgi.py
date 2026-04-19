import sys
import os

INTERP = "/home/s/snbld/snbld.beget.tech/myapp/venv/bin/python"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

# Инициализируем БД через models
from models import db
from app import app

with app.app_context():
    db.create_all()

from app import app as application
