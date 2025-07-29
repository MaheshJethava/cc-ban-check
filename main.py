import discord
from discord.ext import commands
from flask import Flask
import threading
import os
import aiohttp
from dotenv import load_dotenv


# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Constants – replace with your own IDs
ALLOWED_CHANNEL_ID = 1397887223344398446 #1397887223344398446  #1399639011915726879
LOG_CHANNEL_ID = 1381004112170061864

# Flask server to keep bot alive
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Game("Clutch BanCheck"), status=discord.Status.dnd
    )
    print(f"✅ Logged in as {bot.user.name}")

# Ban check function
async def check_ban(uid: str) -> dict | None:
    url = f"https://api-check-ban2.vercel.app/check_ban/{uid}" # https://api-check-ban.vercel.app/check_ban/{uid} OLD API
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
            embed.title = "**▌ Banned Account 🛑 **"
            embed.description = (
                f"**• Reason :** This account was confirmed for using cheats.\n"
                f"**• Suspension duration :** `{period} days`\n"
                f"**• Nickname :** `{nickname}`\n"
                f"**• Player ID :** `{uid}`\n"
                f"**• Region :** `{region}`"
            )
            file = discord.File("assets/banned.gif", filename="banned.gif")
            embed.set_image(url="attachment://banned.gif")
        else:
            embed.title = "**▌ Clean Account ✅ **"
            embed.description = (
                f"**• Status :** No sufficient evidence of cheat usage on this account.\n"
                f"**• Nickname :** `{nickname}`\n"
                f"**• Player ID :** `{uid}`\n"
                f"**• Region :** `{region}`"
            )
            file = discord.File("assets/notbanned.gif", filename="notbanned.gif")
            embed.set_image(url="attachment://notbanned.gif")

        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text="CLUTCH CORPORATION ID CHECKER")

        await ctx.send(content=f"{ctx.author.mention}", embed=embed, file=file)

        # Optional logging
        if LOG_CHANNEL_ID:
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(
                    f"🔍 `{ctx.author}` checked UID `{uid}` — Result: {'Banned' if is_banned else 'Clean'}"
                )

# Start Flask and Bot
threading.Thread(target=run_flask).start()
bot.run(TOKEN)
