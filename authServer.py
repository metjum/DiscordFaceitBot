import base64
import os
import sqlite3
from dotenv import load_dotenv
from flask import Flask, request, redirect
import requests

load_dotenv()

faceit_client_id = os.getenv("APP_CLIENT_ID")
faceit_client_secret = os.getenv("APP_CLIENT_SECRET")
faceit_redirect_url = os.getenv("APP_REDIRECT_URL")
faceit_token_endpoint = os.getenv("APP_ENDPOINT_TOKEN")

app = Flask(__name__)


@app.route('/')
def index():

    return "You can now close this window!"


@app.route('/callback')
def callback():
    print("Accessed")
    code = request.args.get('code')
    userid = request.args.get('state')

    data = {
        "code": code,
        "grant_type": "authorization_code"
    }
    encoded_auth = base64.b64encode(f"{faceit_client_id}:{faceit_client_secret}".encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_auth}"
    }
    response = requests.post(f"{os.getenv('APP_ENDPOINT_TOKEN')}", headers=headers, data=data)
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        id_token = response.json()["id_token"]

        conn = sqlite3.connect("tokenDatabase.sqlite")
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO tokens (user_id, access_token, id_token) VALUES (?, ?, ?)""", (userid, access_token, id_token))
        conn.commit()
        conn.close()

        return redirect("/")
    else:
        return f"Error: {response.text}"
