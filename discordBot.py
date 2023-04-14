import asyncio
import os
import aiohttp
import sqlite3
import jwt
import urllib.parse
from dotenv import load_dotenv

import discord
from discord import app_commands, ButtonStyle
from discord.ui import View

load_dotenv()

faceit_client_id = os.getenv("APP_CLIENT_ID")
faceit_client_secret = os.getenv("APP_CLIENT_SECRET")
faceit_redirect_url = os.getenv("APP_REDIRECT_URL")
faceit_token_endpoint = os.getenv("APP_ENDPOINT_TOKEN")
faceit_client_api_key = os.getenv("APP_CLIENT_API_KEY")
discord_skill_level_ranks = {
    0: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_0')}",
    1: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_1')}",
    2: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_2')}",
    3: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_3')}",
    4: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_4')}",
    5: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_5')}",
    6: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_6')}",
    7: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_7')}",
    8: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_8')}",
    9: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_9')}",
    10: f"{os.getenv('SKILL_LEVEL_GROUP_NAME_10')}",

}

intents = discord.Intents.all()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


def decode_token(token):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")


async def check_users():
    while True:
        async with aiohttp.ClientSession() as session:
            conn = sqlite3.connect("tokenDatabase.sqlite")
            c = conn.cursor()
            for row in c.execute("SELECT id_token, user_id FROM tokens"):
                id_token = row[0]

                nickname = decode_token(id_token)["nickname"]
                url = f"{os.getenv('APP_ENDPOINT_PLAYER')}?nickname={nickname}"
                headers = {"Authorization": f"Bearer {faceit_client_api_key}"}
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        try:
                            skill_level = data["games"]["csgo"]["skill_level"]
                        except KeyError:
                            skill_level = None

                        if skill_level is not None:
                            guild = bot.get_guild(int(os.getenv("GUILD_ID")))
                            member = await guild.fetch_member(row[1])

                            role_name = discord_skill_level_ranks.get(skill_level)
                            role = discord.utils.get(guild.roles, name=role_name)
                            await member.add_roles(role)
                    else:
                        print(f"Error getting player data for {nickname}: {response.status}")
        await asyncio.sleep(100)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="CS:GO Ranking | Faceit"))
    await bot.wait_until_ready()
    await tree.sync()
    await check_users()
    print("Established connection to Discord API Servers!")


class AuthButton(View):
    def __init__(self, userid):
        super().__init__(timeout=None)
        self.userid = userid
        self.add_item(discord.ui.Button(label="Auth with Faceit", style=ButtonStyle.link, url=self.get_auth_url(self.userid), emoji="🛡️"))

    def get_auth_url(self, userid):
        params = {
            "client_id": faceit_client_id,
            "response_type": "code",
            "scope": "openid",
            "redirect_url": faceit_redirect_url,
            "redirect_popup": "true",
            "state": userid,
        }
        query = urllib.parse.urlencode(params)
        return f"{os.getenv('APP_ENDPOINT_CONSENT')}?{query}"


@app_commands.command(name="setup", description="Create message with a button for users to add there Faceit account")
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(title="Authorize your Faceit account here", description="You need to OAuth with Faceit in order to get a rank on this Discord Server based on your CS:GO skill level.\n"
                                                                                  "We update the level in a specific time periode!")
    await interaction.guild.get_channel(interaction.channel_id).send(embed=embed, view=AuthButton(interaction.user.id))
    await interaction.response.send_message("Message created. The message should be persistent over bot restarts.", ephemeral=True)

