import discord
from discord.ext import commands
from pymongo import MongoClient
import os

# Conexão com o MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["dg_main"]
servers_collection = db["authorized_servers"]

class ServerVerification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_server_authorized(self, guild_id: int) -> bool:
        """Método para verificar se o servidor (guild) está autorizado."""
        # Converte para string para garantir que a comparação com o banco seja correta
        server_id = str(guild_id)

        # Verifica se o servidor está na lista de autorizados
        authorized = servers_collection.find_one({"server_id": server_id})
        return authorized is not None

async def setup(bot):
    await bot.add_cog(ServerVerification(bot))
