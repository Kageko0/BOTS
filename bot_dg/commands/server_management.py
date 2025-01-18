# server_management.py
import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
import os

# Conexão com o MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["dg_main"]
servers_collection = db["authorized_servers"]

class ServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Verifica se o usuário que usa o comando é o dono do bot
    async def is_owner(interaction: discord.Interaction):
        return interaction.user.id == int(os.getenv("BOT_OWNER_ID"))  # Substitua pelo seu ID

    @app_commands.command(name="listar_servidores", description="Lista os servidores aos quais o bot está conectado (somente o dono do bot pode usar).")
    @app_commands.check(is_owner)
    async def list_servers(self, interaction: discord.Interaction):
        guilds = self.bot.guilds
        server_list = "\n".join([f"{guild.name} (ID: {guild.id})" for guild in guilds])
        await interaction.response.send_message(
            f"Servidores conectados:\n{server_list}", ephemeral=True
        )

    @app_commands.command(name="autorizar_servidor", description="Autoriza um servidor para usar comandos (somente o dono do bot pode usar).")
    @app_commands.check(is_owner)
    async def authorize_server(self, interaction: discord.Interaction, server_id: str):
        if servers_collection.find_one({"server_id": server_id}):
            await interaction.response.send_message(f"O servidor {server_id} já está autorizado.", ephemeral=True)
        else:
            servers_collection.insert_one({"server_id": server_id})
            await interaction.response.send_message(f"Servidor {server_id} autorizado com sucesso!", ephemeral=True)

    @app_commands.command(name="remover_servidor", description="Remove um servidor da lista de autorizados (somente o dono do bot pode usar).")
    @app_commands.check(is_owner)
    async def remove_server(self, interaction: discord.Interaction, server_id: str):
        result = servers_collection.delete_one({"server_id": server_id})
        if result.deleted_count > 0:
            await interaction.response.send_message(f"Servidor {server_id} removido da lista de autorizados.", ephemeral=True)
        else:
            await interaction.response.send_message(f"O servidor {server_id} não está na lista de autorizados.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerManagement(bot))
