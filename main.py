import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
import threading
from utils import check_ban

app = Flask(__name__)

load_dotenv()
APPLICATION_ID = os.getenv("APPLICATION_ID")
TOKEN = os.getenv("TOKEN")

# Constants – replace with your own IDs
ALLOWED_CHANNEL_ID = 1397887223344398446

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DEFAULT_LANG = "en"
user_languages = {}

nomBot = "None"

@app.route('/')
def home():
    global nomBot
    return f"Bot {nomBot} is working"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

threading.Thread(target=run_flask).start()

@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.dnd,  # Set to DND
        activity=discord.Game("Id Checker By Mahesh")  # Custom status
    )
    print(f"Logged in as {bot.user.name}")

@bot.command(name="guilds")
async def show_guilds(ctx):
    guild_names = [f"{i+1}. {guild.name}" for i, guild in enumerate(bot.guilds)]
    guild_list = "\n".join(guild_names)
    await ctx.send(f"Le bot est dans les guilds suivantes :\n{guild_list}")

@bot.command(name="lang")
async def change_language(ctx, lang_code: str):
    lang_code = lang_code.lower()
    if lang_code not in ["en", "fr"]:
        await ctx.send("❌ Invalid language. Available: `en`, `fr`")
        return

    user_languages[ctx.author.id] = lang_code
    message = "✅ Language set to English." if lang_code == 'en' else "✅ Langue définie sur le français."
    await ctx.send(f"{ctx.author.mention} {message}")

# Ban check function
async def check_ban(uid: str) -> dict | None:
    url = f"https://api-check-ban.vercel.app/check_ban/{uid}"
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                if data.get("status") == 200 and data.get("data"):
                    d = data["data"]
                    return {
                        "is_banned": d.get("is_banned", 0),
                        "nickname": d.get("nickname", "Unknown"),
                        "period": d.get("period", 0),
                        "region": d.get("region", "Unknown")
                    }
                return None
    except Exception as e:
        print(f"[❌] API error: {e}")
        return None


# !check command
@bot.command(name="check")
async def check_command(ctx, uid: str):
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        await ctx.send("❌ This command can only be used in the authorized channel.")
        return

    if ALLOWED_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("❌ You don't have permission to use this command.")
        return

    if not uid.isdigit() or len(uid) < 5:
        await ctx.send("❌ Invalid UID format.")
        return

    async with ctx.typing():
        result = await check_ban(uid)

        if not result:
            embed = discord.Embed(
                title="❌ UID Not Found",
                description="No data returned for the provided UID.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        # Extract data
        is_banned = result["is_banned"]
        nickname = result["nickname"]
        period = result["period"]
        region = result["region"]
        lang = "en"


        embed = discord.Embed(
            color=0xFF0000 if is_banned else 0x00FF00,
            timestamp=ctx.message.created_at
        )

        if is_banned:
            embed.title = "**▌ Banned Account 🛑 **" if lang == "en" else "**▌ Compte banni 🛑 **"
            embed.description = (
                f"**• {'Reason' if lang == 'en' else 'Raison'} :** "
                f"{'This account was confirmed for using cheats.' if lang == 'en' else 'Ce compte a été confirmé comme utilisant des hacks.'}\n"
                f"**• {'Suspension duration' if lang == 'en' else 'Durée de la suspension'} :** {period_str}\n"
                f"**• {'Nickname' if lang == 'en' else 'Pseudo'} :** `{nickname}`\n"
                f"**• {'Player ID' if lang == 'en' else 'ID du joueur'} :** `{id_str}`\n"
                f"**• {'Region' if lang == 'en' else 'Région'} :** `{region}`"
            )
            # embed.set_image(url="https://i.ibb.co/wFxTy8TZ/banned.gif")
            file = discord.File("assets/banned.gif", filename="banned.gif")
            embed.set_image(url="attachment://banned.gif")
        else:
            embed.title = "**▌ Clean Account ✅ **" if lang == "en" else "**▌ Compte non banni ✅ **"
            embed.description = (
                f"**• {'Status' if lang == 'en' else 'Statut'} :** "
                f"{'No sufficient evidence of cheat usage on this account.' if lang == 'en' else 'Aucune preuve suffisante pour confirmer l’utilisation de hacks sur ce compte.'}\n"
                f"**• {'Nickname' if lang == 'en' else 'Pseudo'} :** `{nickname}`\n"
                f"**• {'Player ID' if lang == 'en' else 'ID du joueur'} :** `{id_str}`\n"
                f"**• {'Region' if lang == 'en' else 'Région'} :** `{region}`"
            )
            # embed.set_image(url="https://i.ibb.co/Kx1RYVKZ/notbanned.gif")
            file = discord.File("assets/notbanned.gif", filename="notbanned.gif")
            embed.set_image(url="attachment://notbanned.gif")

        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text="FROM CLUTCH CORPORATION")
        await ctx.send(f"{ctx.author.mention}", embed=embed ,file=file)

bot.run(TOKEN)
