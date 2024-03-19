from flask import Flask, request, jsonify, session
from dotenv import load_dotenv
import os
import sqlite3
from DatabaseTables import DatabaseTables
from PasswordHasher import PasswordHasher
from openai import OpenAI
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE = 'database.db'
password_hasher = PasswordHasher()


limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"]
)


def is_logged_in():
    return 'user_id' in session


@app.route('/mock', methods=['GET'])
def mock():
    if(is_logged_in() == False):
      return jsonify({"message": "Not Logged In"}), 401

    return jsonify({"message": "Hello World"}), 200

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({"message": "Name, email, and password are required"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({"message": "User with this email already exists"}), 400

        hashed_password = password_hasher.hash_password(password)
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_password))
        user_id = cursor.lastrowid

    return jsonify({"message": "Signup successful", "user_id": user_id}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json;
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"message": "User not found. Please signup"}), 404

        stored_password = user[3]
        if not password_hasher.verify_password(stored_password, password):
            return jsonify({"message": "Incorrect password"}), 401

    session['user_id'] = user[0]

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE chat_log SET is_active = 0 WHERE user_id = ?", (session.get('user_id'),))

    return jsonify({"message": "Login successful"}), 200


@app.route('/logout', methods=['POST'])
def logout():
    if not is_logged_in():
        return jsonify({"message": "Not Logged In"}), 401

    # Mark chat logs as inactive for the current user session
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE chat_log SET is_active = 0 WHERE user_id = ?", (session.get('user_id'),))
    session.pop('user_id', None)
    return jsonify({"message": "Logout successful"}), 200


@app.route('/openai-completion', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    if not is_logged_in():
        return jsonify({"message": "Not Logged In"}), 401

    user_id = session.get('user_id', None)
    data = request.json
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"message": "Prompt field is required"}), 400

    chat_logs = []
    with sqlite3.connect(DATABASE) as conn:
      cursor = conn.cursor()
      cursor.execute("SELECT * FROM chat_log WHERE user_id = ? AND is_active = 1", (user_id,))
      chat_logs = cursor.fetchall()

    messages = []
    for chat_log in chat_logs:
      currPrompt = chat_log[2]
      cuurResponse = chat_log[3]
      messages.append({"role": "user", "content": currPrompt})
      messages.append({"role": "assistant", "content": cuurResponse})

    messages.append({"role": "user", "content": prompt})

    try:

        client = OpenAI(api_key= OPENAI_API_KEY);

        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages
        )

        responseMessage = response.choices[0].message.content

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO chat_log (user_id, request, response, is_active) VALUES (?, ?, ?, ?)", (user_id, prompt, responseMessage.strip(), True))

        return jsonify({"message": responseMessage}), 200

    except Exception as e:
        return jsonify({"message": f"Error processing request: {str(e)}"}), 500


if __name__ == '__main__':
    DatabaseTables.create_user_table()
    DatabaseTables.create_chat_log_table()
    app.run(debug=True)
