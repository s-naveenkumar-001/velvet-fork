from flask import Flask, jsonify, render_template, request

import chat_service
import config
import restaurant_info
from api import api
from db import SessionLocal, init_db
from db_models import MenuItem
from seed_data import seed

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
app.register_blueprint(api)

init_db()
seed()


@app.teardown_appcontext
def remove_session(exception=None):
    SessionLocal.remove()


@app.get("/")
def index_get():
    session = SessionLocal()
    items = (
        session.query(MenuItem)
        .filter(MenuItem.is_available.is_(True))
        .order_by(MenuItem.category, MenuItem.name)
        .all()
    )
    categories = sorted({item.category for item in items})
    return render_template("index.html", menu_items=items, categories=categories, info=restaurant_info)


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("message") or "").strip()
    if not text:
        return jsonify({"error": "empty_message", "message": "Message cannot be empty."}), 400

    session_id = chat_service.get_or_create_session_id()
    answer = chat_service.get_response(session_id, text)
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(debug=config.FLASK_DEBUG)
