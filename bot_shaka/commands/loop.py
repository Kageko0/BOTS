import discord
from discord.ext import commands
from discord import app_commands

class Loop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loop", description="Repete uma música várias vezes.")
    async def loop(self, interaction: discord.Interaction, link: str):
        """Comando de barra para repetir uma música."""
        if not interaction.user.voice:
            await interaction.response.send_message("Você precisa estar em um canal de voz para usar este comando!", ephemeral=True)
            return

        # Conecta ao canal de voz
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            await channel.connect()
        elif interaction.guild.voice_client.channel != channel:
            await interaction.guild.voice_client.move_to(channel)

        voice_client = interaction.guild.voice_client

        # Reproduz a música em loop
        if voice_client.is_playing():
            voice_client.stop()

        def repeat_playback(error):
            voice_client.play(discord.FFmpegPCMAudio(link), after=repeat_playback)

        voice_client.play(discord.FFmpegPCMAudio(link), after=repeat_playback)
        await interaction.response.send_message(f"Tocando em loop: {link}")

async def setup(bot):
    await bot.add_cog(Loop(bot))
