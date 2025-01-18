import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from pymongo import MongoClient
import os
import pytz  # Importar a biblioteca pytz

# Conexão com MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["dg_main"]
embeds_collection = db["embeds"]

# IDs dos emojis personalizados do servidor
EMOJIS = {
    "TANK": "<:TANKS:1291553864385822760>",
    "HEALER": "<:HEALERS:1291554307858235463>",
    "DPS": "<:DPS:1291554083416703078>",
    "SUPORTE": "<:SUPORTES:1291554188458852455>"
}

# Fuso horário de São Paulo
sp_timezone = pytz.timezone("America/Sao_Paulo")

class SmallCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="small", description="Cria um ping de small fight")
    async def small(
        self,
        interaction: discord.Interaction,
        ip: str,
        horario: str,
        saida: str,
        descricao: str,
        pessoas: int = 5,
    ):
        try:
            # Verificação de autorização do servidor
            server_verification_cog = self.bot.get_cog("ServerVerification")
            if not await server_verification_cog.check_server_authorized(interaction.guild.id):
                await interaction.response.send_message(
                    "Este servidor não está autorizado a usar comandos deste bot. "
                    "Por favor, entre em contato com o administrador <@325765332038057987>.",
                    ephemeral=True,
                )
                return

            if pessoas > 10:
                await interaction.response.send_message("O número máximo de pessoas é 10.", ephemeral=True)
                return

            # Processar horários
            try:
                horario_time = datetime.strptime(horario, "%H:%M").time()
                saida_time = datetime.strptime(saida, "%H:%M").time()
            except ValueError:
                await interaction.response.send_message(
                    "Por favor, insira os horários no formato HH:MM (ex: 14:30).",
                    ephemeral=True,
                )
                return

            now_date = datetime.now().date()
            horario_datetime = datetime.combine(now_date, horario_time)
            saida_datetime = datetime.combine(now_date, saida_time)

            # Converter horários para o fuso horário de São Paulo
            horario_datetime = sp_timezone.localize(horario_datetime)
            saida_datetime = sp_timezone.localize(saida_datetime)

            await interaction.response.defer()

            embed = discord.Embed(
                title=f"SMALL FIGHT",
                description=descricao,
                color=discord.Color.red(),
            )
            embed.add_field(name="🔢 IP", value=ip, inline=True)
            embed.add_field(name="🕒 Horário", value=f"<t:{int(horario_datetime.timestamp())}:f>", inline=True)
            embed.add_field(name="🕗 Saída", value=f"<t:{int(saida_datetime.timestamp())}:R>", inline=True)

            # Determinar cargos
            cargos = self.calculate_roles(pessoas)
            for cargo, quantidade in cargos.items():
                for _ in range(quantidade):
                    embed.add_field(name=f"{EMOJIS[cargo]} {cargo}", value="livre", inline=False)

            embed.set_footer(
                text="Criado em",
                icon_url="https://images-ext-1.discordapp.net/external/kMF_YgHp7SICduKo1zFYdz54dHfrD2e5_E18qqtPtrw/%3Fsize%3D2048/https/cdn.discordapp.com/icons/797227962171916319/a_426de0ad01c7ac138ff336468a00d43b.gif?width=559&height=559",
            )
            embed.timestamp = datetime.now()

            embed_data = {
                "_id": interaction.id,
                "userid": interaction.user.id,
                "date": datetime.now(),
                "saida": saida_datetime,
                "persons": {role: [] for role in cargos.keys()},
            }
            embeds_collection.insert_one(embed_data)

            # Obter o canal onde a mensagem será enviada
            channel = interaction.channel

            # Enviar a menção @everyone e a role antes do embed
            mention_message_role = f"@everyone SMALL FIGHT marcado para às {horario}!"

            view = RoleSelector(embed, embed_data, saida_datetime)

            # Enviar a menção @everyone e a role para o canal
            await channel.send(content=mention_message_role)

            # Enviar o embed com a view associada
            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"Erro ao criar o embed: {e}", ephemeral=True)

    def calculate_roles(self, pessoas):
        """
        Calcula os cargos necessários dependendo do número de pessoas.
        """
        roles = {}

        if pessoas == 5:
            roles = {"TANK": 1, "HEALER": 1, "SUPORTE": 1, "DPS": 2}
        elif pessoas == 6:
            roles = {"TANK": 1, "HEALER": 1, "SUPORTE": 1, "DPS": 3}
        elif pessoas == 7:
            roles = {"TANK": 1, "HEALER": 1, "SUPORTE": 2, "DPS": 3}
        elif pessoas == 8:
            roles = {"TANK": 1, "HEALER": 2, "SUPORTE": 2, "DPS": 3}
        elif pessoas == 9:
            roles = {"TANK": 1, "HEALER": 2, "SUPORTE": 2, "DPS": 4}
        elif pessoas == 10:
            roles = {"TANK": 2, "HEALER": 2, "SUPORTE": 2, "DPS": 4}

        return roles

class RoleSelector(discord.ui.View):
    def __init__(self, embed, embed_data, saida_datetime):
        # Garantir que ambas as datas estão no mesmo fuso horário
        saida_datetime = sp_timezone.localize(saida_datetime) if saida_datetime.tzinfo is None else saida_datetime
        now_datetime = datetime.now(sp_timezone)  # Localiza o horário atual em São Paulo
        timeout_duration = max((saida_datetime - now_datetime).total_seconds(), 0)
        super().__init__(timeout=timeout_duration)
        self.embed = embed
        self.embed_data = embed_data

    @discord.ui.select(
        placeholder="Escolha seu cargo...",
        options=[ 
            discord.SelectOption(label="TANK", value="TANK", emoji=EMOJIS["TANK"]),
            discord.SelectOption(label="HEALER", value="HEALER", emoji=EMOJIS["HEALER"]),
            discord.SelectOption(label="DPS", value="DPS", emoji=EMOJIS["DPS"]),
            discord.SelectOption(label="SUPORTE", value="SUPORTE", emoji=EMOJIS["SUPORTE"]),
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

            # Verificar limite de jogadores no cargo
            max_slots = len([field for field in self.embed.fields if f"{EMOJIS[role]} {role}" in field.name])

            if len(self.embed_data["persons"][role]) >= max_slots:
                await interaction.followup.send(f"O cargo **{role}** já está preenchido.", ephemeral=True)
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
            child.disabled = True
        await self.message.edit(content="O tempo de seleção acabou.", view=self)

async def setup(bot: commands.Bot):
    await bot.add_cog(SmallCommand(bot))
