import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio

class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="playlist", description="Toca uma playlist do YouTube ou Spotify.")
    async def playlist(self, interaction: discord.Interaction, link: str):
        """Comando de barra para tocar playlists."""
        if not interaction.user.voice:
            await interaction.response.send_message("Você precisa estar em um canal de voz para usar este comando!", ephemeral=True)
            return

        await interaction.response.defer()  # Evita timeout enquanto processa o comando

        try:
            # Conecta ao canal de voz
            channel = interaction.user.voice.channel
            if interaction.guild.voice_client is None:
                await channel.connect()
            elif interaction.guild.voice_client.channel != channel:
                await interaction.guild.voice_client.move_to(channel)

            # Configurações do yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'noplaylist': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                playlist_title = info.get('title', 'uma playlist')

                await interaction.followup.send(f"Tocando a playlist: **{playlist_title}**")

                # Obtém as entradas da playlist
                entries = info.get('entries', [])
                for entry in entries:
                    url = entry['url']
                    title = entry.get('title', 'uma música')

                    # Toca cada música da playlist
                    voice_client = interaction.guild.voice_client
                    if voice_client.is_playing():
                        voice_client.stop()

                    # Configurações do FFmpeg
                    FFMPEG_PATH = "C:/ffmpeg/bin/ffmpeg.exe"
                    # FFMPEG_PATH = "/usr/bin/ffmpeg"
                    FFMPEG_OPTIONS = {
                        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        'options': '-vn',
                        'executable': FFMPEG_PATH,
                    }

                    voice_client.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
                    await interaction.channel.send(f"Tocando agora: **{title}**")

                    # Aguarda a música terminar antes de passar para a próxima
                    while voice_client.is_playing():
                        await asyncio.sleep(1)

        except yt_dlp.utils.DownloadError:
            await interaction.followup.send("Erro ao processar o link. Certifique-se de que ele seja válido e tente novamente.")
        except Exception as e:
            await interaction.followup.send(f"Ocorreu um erro: {str(e)}")

async def setup(bot):
    await bot.add_cog(Playlist(bot))
