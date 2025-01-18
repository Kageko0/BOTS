import discord
from discord.ext import commands
from discord import app_commands

class Mover(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mover", description="Move um usuário de um canal de voz para outro.")
    async def mover(self, interaction: discord.Interaction, de: str, para: str, usuario: discord.Member):
        """Comando de barra para mover usuários entre canais de voz."""
        guild = interaction.guild

        canal_de = discord.utils.get(guild.voice_channels, name=de)
        canal_para = discord.utils.get(guild.voice_channels, name=para)

        if not canal_de or not canal_para:
            await interaction.response.send_message("Um dos canais especificados não foi encontrado.", ephemeral=True)
            return

        if usuario not in canal_de.members:
            await interaction.response.send_message("O usuário especificado não está no canal de origem.", ephemeral=True)
            return

        # Move o usuário para o canal de destino
        await usuario.move_to(canal_para)
        await interaction.response.send_message(f"{usuario.mention} foi movido de {canal_de.name} para {canal_para.name}.")

async def setup(bot):
    await bot.add_cog(Mover(bot))
