import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.voice_states = True
client = commands.Bot(command_prefix="!", intents=intents)

# Dicionário para armazenar dados por servidor
server_data = {}

# Tempo mínimo para qualificar um usuário (em segundos para teste)
MINIMUM_TIME = timedelta(seconds=5)

@client.event
async def on_ready():
    print(f'{client.user} está conectado ao Discord!')
    try:
        synced = await client.tree.sync()
        print(f"Comandos Slash sincronizados: {len(synced)} comandos.")
    except Exception as e:
        print(e)

@client.event
async def on_voice_state_update(member, before, after):
    guild_id = member.guild.id
    if guild_id not in server_data:
        server_data[guild_id] = {"voice_times": {}, "total_times": {}}
    
    voice_times = server_data[guild_id]["voice_times"]
    total_times = server_data[guild_id]["total_times"]

    # Usuário entra no canal de voz
    if before.channel is None and after.channel is not None:
        voice_times[member.id] = datetime.now()

    # Usuário sai do canal de voz
    elif before.channel is not None and after.channel is None:
        join_time = voice_times.pop(member.id, None)
        if join_time:
            time_spent = datetime.now() - join_time
            if time_spent >= MINIMUM_TIME:
                if member.id in total_times:
                    total_times[member.id] += time_spent
                else:
                    total_times[member.id] = time_spent

class TimeView(View):
    def __init__(self, member_times, user=None):
        super().__init__()
        self.member_times = member_times
        self.page = 0
        self.user = user

    async def format_all_users_embed(self):
        """Gera embed com paginação para todos os usuários"""
        embed = discord.Embed(title="Ranking de Tempo em Call", color=discord.Color.green())
        sorted_times = sorted(self.member_times.items(), key=lambda x: x[1], reverse=True)
        start = self.page * 10
        end = start + 10
        users = sorted_times[start:end]

        for i, (user_id, time) in enumerate(users, start=1):
            user = await client.fetch_user(user_id)
            if user:
                embed.add_field(name=f"{i + start}. {user.name}", value=f"Tempo: {time}", inline=False)

        total_pages = (len(self.member_times) - 1) // 10 + 1
        embed.set_footer(text=f"Página {self.page + 1}/{total_pages}")
        return embed

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        embed = await self.format_all_users_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Página Principal", style=discord.ButtonStyle.secondary)
    async def main_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 0
        embed = await self.format_all_users_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Próximo", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < len(self.member_times) // 10:
            self.page += 1
        embed = await self.format_all_users_embed()
        await interaction.response.edit_message(embed=embed, view=self)

@client.tree.command(name="tempo_em_call", description="Mostra o tempo em call de um usuário ou de todos")
@app_commands.describe(member="Opcional: usuário específico para mostrar o tempo")
async def show_call_time(interaction: discord.Interaction, member: discord.Member = None):
    guild_id = interaction.guild.id
    if guild_id not in server_data:
        server_data[guild_id] = {"voice_times": {}, "total_times": {}}

    total_times = server_data[guild_id]["total_times"]
    member_times = {k: v for k, v in total_times.items() if v >= MINIMUM_TIME}

    if member:
        if member.id in member_times:
            embed = discord.Embed(title=f"Tempo em Call de {member.name}", color=discord.Color.blue())
            embed.add_field(name="Tempo Total", value=str(member_times[member.id]))
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"{member.name} não possui tempo suficiente em call.", ephemeral=True)
    else:
        if member_times:
            view = TimeView(member_times)
            embed = await view.format_all_users_embed()
            await interaction.response.send_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("Nenhum usuário atingiu o tempo mínimo em call.", ephemeral=True)

client.run(TOKEN)
