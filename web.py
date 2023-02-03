from logging.config import dictConfig

from flask import Flask
from markupsafe import escape

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "flask.log",
                "formatter": "default",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["console", "file"]},
    }
)
app = Flask(__name__)


@app.route('/user/<username>')
def show_user_profile(username):
    app.logger.info(f"Пришел запрос от пользователля {username}")
    return f'User {escape(username)}'
