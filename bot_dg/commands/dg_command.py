import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import pytz
from pymongo import MongoClient
import os

# Conexão com MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["dg_main"]
embeds_collection = db["embeds"]

# IDs dos emojis personalizados do servidor
EMOJIS = {
    "TANK": "<:TANKS:1291553864385822760>",  # Substitua pelo ID do emoji do servidor
    "HEALER": "<:HEALERS:1291554307858235463>",
    "DPS": "<:DPS:1291554083416703078>",
}

# Função para converter data e hora em timestamps do Discord
def convert_to_timestamp(data_horario: str, formato: str = 'f', timezone: str = 'America/Sao_Paulo') -> str:
    try:
        # Cria um datetime "offset-naive"
        naive_datetime = datetime.strptime(data_horario, '%d/%m/%Y %H:%M')

        # Converte para um datetime "offset-aware" usando pytz
        tz = pytz.timezone(timezone)
        aware_datetime = tz.localize(naive_datetime)

        # Retorna o timestamp formatado
        return discord.utils.format_dt(aware_datetime, formato)
    except Exception as e:
        raise ValueError(f"Erro ao converter para timestamp: {e}")

class DGCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dg", description="Cria um ping de DG de grupo")
    async def dg(
        self,
        interaction: discord.Interaction,
        tier: str,
        ip: str,
        horario: str,
        saida: str,
        descricao: str,
        pessoas: int = 5,
    ):
        # Verificar se o servidor está autorizado
        server_verification_cog = self.bot.get_cog("ServerVerification")
        if not await server_verification_cog.check_server_authorized(interaction.guild.id):
            await interaction.response.send_message(
                "Este servidor não está autorizado a usar comandos deste bot. "
                "Por favor, entre em contato com o administrador <@325765332038057987>.",
                ephemeral=True,
            )
            return

        try:
            if pessoas > 10:
                await interaction.response.send_message("O número máximo de pessoas é 10.", ephemeral=True)
                return

            # Validar e converter horários
            try:
                horario_datetime = datetime.strptime(horario, "%H:%M")
                saida_datetime = datetime.strptime(saida, "%H:%M")
            except ValueError:
                await interaction.response.send_message(
                    "Por favor, insira os horários no formato HH:MM (ex: 14:30).",
                    ephemeral=True,
                )
                return

            now_date = datetime.now().strftime("%d/%m/%Y")

            # Usar a função convert_to_timestamp para os horários
            horario_ts = convert_to_timestamp(f"{now_date} {horario}", 'f')
            saida_ts = convert_to_timestamp(f"{now_date} {saida}", 'R')

            await interaction.response.defer()

            embed = discord.Embed(
                title=f"DG DE GRUPO T{tier}",
                description=descricao,
                color=discord.Color.red(),
            )
            embed.add_field(name="🔢 IP", value=ip, inline=True)
            embed.add_field(name="🕒 Horário", value=horario_ts, inline=True)
            embed.add_field(name="🕗 Saída", value=saida_ts, inline=True)

            # Criar campos para cargos
            embed.add_field(name=f"{EMOJIS['TANK']} TANK", value="livre", inline=False)
            embed.add_field(name=f"{EMOJIS['HEALER']} HEALER", value="livre", inline=False)
            for i in range(pessoas - 2):  # Criar campos DPS
                embed.add_field(name=f"{EMOJIS['DPS']} DPS", value="livre", inline=False)

            embed.set_footer(
                text="Criado em",
                icon_url="https://images-ext-1.discordapp.net/external/kMF_YgHp7SICduKo1zFYdz54dHfrD2e5_E18qqtPtrw/%3Fsize%3D2048/https/cdn.discordapp.com/icons/797227962171916319/a_426de0ad01c7ac138ff336468a00d43b.gif?width=559&height=559",
            )
            embed.timestamp = datetime.now()

            embed_data = {
                "_id": interaction.id,
                "userid": interaction.user.id,
                "date": datetime.now(),
                "saida": datetime.strptime(f"{now_date} {saida}", "%d/%m/%Y %H:%M"),
                "persons": {role: [] for role in ["TANK", "HEALER", "DPS"]},
            }
            embeds_collection.insert_one(embed_data)

            # Obter o canal onde a mensagem será enviada
            channel = interaction.channel

            # Enviar a menção @everyone e a role antes do embed
            mention_message_role = f"@everyone DG de grupo T{tier} marcado para às {horario}"

            view = RoleSelector(embed, embed_data, embed_data["saida"])

            # Enviar a menção @everyone e a role para o canal
            await channel.send(content=mention_message_role)

            # Enviar o embed com a view associada
            await interaction.followup.send(embed=embed, view=view)

            # Enviar mensagens de aviso 5 minutos antes e no horário de início
            self.send_timer_messages(interaction.user.id, horario_datetime)

        except Exception as e:
            await interaction.followup.send(f"Erro ao criar o embed: {e}", ephemeral=True)

    async def send_timer_messages(self, user_id, horario_datetime):
        # Calcular os tempos para as mensagens
        now = datetime.now()
        time_to_start = horario_datetime - now  # Tempo até o horário de início
        time_to_alert = time_to_start - timedelta(minutes=5)  # 5 minutos antes

        # Enviar mensagem 5 minutos antes
        if time_to_alert > timedelta(seconds=0):
            await self.bot.wait_for('message', timeout=time_to_alert.total_seconds())
            user = await self.bot.fetch_user(user_id)
            await user.send(f"5 minutos para o horário de início do DG!")

        # Enviar mensagem no horário de início
        await self.bot.wait_for('message', timeout=time_to_start.total_seconds())
        user = await self.bot.fetch_user(user_id)
        await user.send(f"É hora de iniciar o DG!")

class RoleSelector(discord.ui.View):
    def __init__(self, embed, embed_data, saida_datetime):
        # Define o timeout como a diferença entre agora e o horário de saída
        timeout_duration = max((saida_datetime - datetime.now()).total_seconds(), 0)
        super().__init__(timeout=timeout_duration)
        self.embed = embed
        self.embed_data = embed_data

    @discord.ui.select(
        placeholder="Escolha seu cargo...",
        options=[ 
            discord.SelectOption(label="TANK", value="TANK", emoji=EMOJIS["TANK"]),
            discord.SelectOption(label="HEALER", value="HEALER", emoji=EMOJIS["HEALER"]),
            discord.SelectOption(label="DPS", value="DPS", emoji=EMOJIS["DPS"]),
        ],
        custom_id="role_selector",
    )
    async def select_callback(self, interaction: discord.Interaction, item: discord.ui.Select):
        try:
            await interaction.response.defer(ephemeral=True)

            role = item.values[0]
            user_mention = interaction.user.mention

            # Verificar se o usuário já está registrado em algum cargo
            for current_role, members in self.embed_data["persons"].items():
                if user_mention in members and current_role != role:
                    # Remover o usuário do cargo anterior
                    self.embed_data["persons"][current_role].remove(user_mention)

                    # Atualizar embed para remover o usuário do cargo anterior
                    for i, field in enumerate(self.embed.fields):
                        if f"{EMOJIS[current_role]} {current_role}" in field.name and field.value == user_mention:
                            self.embed.set_field_at(i, name=field.name, value="livre", inline=False)
                            break

            # Verificar se o cargo escolhido já está preenchido
            if len(self.embed_data["persons"][role]) >= 1 and role != "DPS":
                await interaction.followup.send(f"O cargo **{role}** já está preenchido.", ephemeral=True)
                return

            # Verificar limite de DPS
            if role == "DPS":
                max_dps = len([field for field in self.embed.fields if f"{EMOJIS['DPS']} DPS" in field.name])

                if len(self.embed_data["persons"][role]) >= max_dps:
                    await interaction.followup.send(
                        "O cargo **DPS** já atingiu o limite de jogadores.", ephemeral=True
                    )
                    return

            # Atualizar embed com o novo cargo
            for i, field in enumerate(self.embed.fields):
                if f"{EMOJIS[role]} {role}" in field.name and field.value == "livre":
                    self.embed.set_field_at(i, name=field.name, value=user_mention, inline=False)
                    break

            # Atualizar dados no MongoDB
            self.embed_data["persons"][role].append(user_mention)
            embeds_collection.update_one(
                {"_id": self.embed_data["_id"]}, {"$set": {"persons": self.embed_data["persons"]}}
            )

            await interaction.message.edit(embed=self.embed)
            await interaction.followup.send(f"Você escolheu o cargo **{role}**!", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"Erro ao processar sua escolha: {e}", ephemeral=True)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True  # Desativar o menu de seleção
        await self.message.edit(content="O tempo de seleção acabou.", view=self)

async def setup(bot: commands.Bot):
    await bot.add_cog(DGCommand(bot))
