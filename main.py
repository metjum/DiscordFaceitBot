import authServer
import discordBot

import sqlite3
from waitress import serve
import multiprocessing
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if __name__ == '__main__':
    discordBot.tree.add_command(discordBot.setup)

    conn = sqlite3.connect("tokenDatabase.sqlite")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (user_id text PRIMARY KEY, access_token text, id_token text)''')
    conn.commit()
    conn.close()

    t1 = multiprocessing.Process(target=serve, args=(authServer.app,), kwargs={'host': os.getenv("LISTEN_IP_ADDRESS"), 'port': os.getenv("LISTEN_PORT")})
    t1.start()

    discordBot.bot.run(TOKEN)

    t1.join()
