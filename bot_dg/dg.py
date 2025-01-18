import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from pymongo import MongoClient
import logging
logging.basicConfig(level=logging.DEBUG)


# Carregar variáveis de ambiente
load_dotenv()

# Configurações do bot
intents = discord.Intents.all()
intents.members = True
intents.messages = True
allowed_mentions=discord.AllowedMentions(everyone=True, roles=True)
bot = commands.Bot(command_prefix="/", intents=intents)

# Conexão com o MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["dg_main"]
embeds_collection = db["embeds"]

# Evento on_ready
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        # Sincroniza comandos globalmente (ou use guild-specific para testes mais rápidos)
        synced = await bot.tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

# Função principal para carregar extensões e rodar o bot
async def main():
    async with bot:
        # Carregando comandos (extensões)
        await bot.load_extension("commands.server_verification")
        await bot.load_extension("commands.dg_command")
        await bot.load_extension("commands.cacada_command")
        await bot.load_extension("commands.avalon_command")
        await bot.load_extension("commands.roaming_command")
        await bot.load_extension("commands.small_command")
        await bot.load_extension("commands.server_management")

        # Inicia o bot
        await bot.start(os.getenv("DISCORD_TOKEN"))

# Executa a função principal
if __name__ == "__main__":
    asyncio.run(main())
