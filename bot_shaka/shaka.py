import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True  # Para habilitar mensagens de texto (se necessário)

bot = commands.Bot(command_prefix="!", intents=intents)


# Evento para carregar os Cogs e sincronizar comandos
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Comandos sincronizados: {len(synced)} comandos")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


# Carrega os Cogs automaticamente
async def load_cogs():
    for filename in os.listdir("./commands"):
        if filename.endswith(".py") and not filename.startswith("__"):
            await bot.load_extension(f"commands.{filename[:-3]}")

# Executa a inicialização do bot
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
