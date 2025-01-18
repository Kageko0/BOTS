import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

class Tocar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tocar", description="Toca uma música a partir de um link do YouTube ou Spotify.")
    async def tocar(self, interaction: discord.Interaction, link: str):
        """Comando de barra para tocar músicas."""
        # Verifica se o usuário está em um canal de voz
        if not interaction.user.voice:
            await interaction.response.send_message("Você precisa estar em um canal de voz para usar este comando!", ephemeral=True)
            return

        await interaction.response.defer()  # Evita timeout enquanto processa o comando

        try:
            # Conecta ao canal de voz do usuário
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
                'noplaylist': True,  # Toca apenas o vídeo fornecido, sem playlists
            }

            # Obtém o link de áudio usando yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                audio_url = info['url']
                title = info.get('title', 'uma música')  # Nome do vídeo/música

            # Reproduz a música no canal de voz
            voice_client = interaction.guild.voice_client
            if voice_client.is_playing():
                voice_client.stop()

            # Caminho absoluto do FFmpeg (alterar para o caminho correto no seu sistema)
            FFMPEG_PATH = "C:/ffmpeg/bin/ffmpeg.exe"  # Para Windows
            # FFMPEG_PATH = "/usr/bin/ffmpeg"    # Para Linux/Mac

            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn',
                'executable': FFMPEG_PATH,  # Define o caminho do executável
            }
            voice_client.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))

            # Envia uma resposta ao usuário informando que a música está tocando
            await interaction.followup.send(f"Tocando agora: **{title}**")

        except yt_dlp.utils.DownloadError:
            await interaction.followup.send("Erro ao processar o link. Certifique-se de que ele seja válido e tente novamente.")
        except Exception as e:
            await interaction.followup.send(f"Ocorreu um erro: {str(e)}")

async def setup(bot):
    await bot.add_cog(Tocar(bot))
