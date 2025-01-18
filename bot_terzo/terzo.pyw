import discord
from discord.ext import commands
import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Conexão com o MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client['bot_dbmain']

bot.users_collection = db['users']
bot.obras_collection = db['obras']
bot.tickets_collection = db['tickets']

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        await db.command("ping")
        print("Conectado ao MongoDB")
    except Exception as e:
        print("Erro ao conectar ao MongoDB:", e)
        await bot.close()

    # Sincronizar os comandos no servidor
    try:
        await bot.tree.sync()
        print("Comandos slash sincronizados!")
    except Exception as e:
        print("Erro ao sincronizar os comandos:", e)


async def load_cogs():
    for extension in list(bot.extensions):
        await bot.unload_extension(extension)  # Descarrega cogs antigos
    await bot.load_extension("commands.niveis")
    await bot.load_extension("commands.obras")
    await bot.load_extension("commands.tickets")


@bot.command()
@commands.is_owner()
async def reload(ctx):
    await load_cogs()
    await ctx.send("Cogs recarregados com sucesso!")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
