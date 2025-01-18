import discord
from discord import app_commands, Embed
from discord.ext import commands
from collections import defaultdict
from datetime import datetime
import pytz
import os

# Dicionário de emojis associados aos cargos
ROLE_EMOJIS = {
    "MainHealer": "<:MainHealer:1291565689290887220>",
    "MainTank": "<:MainTank:1291565285110714379>",
    "OffTank": "<:OffTank:1291565385275146341>",
    "Silence": "<:Silence:1291565569216352328>",
    "Elevado": "<:Elevado:1291565497305006202>",
    "Raiz-Férrea": "<:RaizFerrea:1291565815392505887>",
    "Raiz-Corrompido": "<:RaizCorrompido:1291565914348847175>",
    "Bruxo": "<:Bruxo:1291566112324063372>",
    "Quebra-Reinos": "<:QuebraReinos:1291566227210375199>",
    "Frost": "<:Frost:1291566356772294706>",
    "Xbow": "<:Xbow:1291566477341757513>",
    "Fulgurante": "<:Fulgurante:1291566731969429505>",
    "Águia": "<:Aguia:1291570026200961135>",
    "Caça-Espírito": "<:CacaEspirito:1291570194455728220>",
    "Maça-Pétrea": "<:MacaPetrea:1291572087881863210>",
}

# Função para converter data e hora em timestamps do Discord considerando o fuso horário de SP
def convert_to_timestamp(data_horario: str, formato: str = 'f') -> str:
    # Define o fuso horário de São Paulo (GMT-3)
    sp_tz = pytz.timezone('America/Sao_Paulo')
    
    # Converte a string para datetime
    dt = datetime.strptime(data_horario, '%d/%m/%Y %H:%M')
    
    # Ajusta para o fuso horário de São Paulo
    dt_sp = sp_tz.localize(dt)
    
    # Retorna o timestamp formatado conforme o formato do Discord
    return discord.utils.format_dt(dt_sp, formato)

class AvalonCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_embeds = {}  # Armazena os embeds associados às mensagens
        self.reactions_by_message = {}  # Reações separadas para cada mensagem

    @app_commands.command(name="avalon", description="Cria um evento de DG Avaloniana")
    async def create(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        tier: str,
        caller: str,
        dia: str,
        horario_inicio: str,
        horario_saida: str,
        ip_minimo: str,
        mensagem_personalizada: str,
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

        # Converte a data e horários para timestamps
        dia_ts = convert_to_timestamp(f"{dia} 00:00", 'D')
        horario_inicio_ts = convert_to_timestamp(f"{dia} {horario_inicio}", 't')
        horario_saida_ts = convert_to_timestamp(f"{dia} {horario_saida}", 't')

        # Criação do embed inicial com informações fixas
        embed = Embed(
            title=f'DG AVALONIANA T[{tier}]',
            description=mensagem_personalizada,
            color=discord.Color.red(),
        )
        embed.add_field(name='📢 Caller', value=caller, inline=True)
        embed.add_field(name='📅 Dia', value=dia_ts, inline=True)
        embed.add_field(name='🕒 Horário de Início', value=horario_inicio_ts, inline=True)
        embed.add_field(name='🕙 Horário de Saída', value=horario_saida_ts, inline=True)
        embed.add_field(name='🔢 IP Mínimo', value=ip_minimo, inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=False)  # Separação visual

        # Adicionando campos para cada cargo
        for role, emoji in ROLE_EMOJIS.items():
            embed.add_field(name=f'{emoji} {role}', value=f'(0)\n', inline=True)

        # Envia o embed no canal especificado
        message = await channel.send(f"@everyone DG Avalon T{tier} marcado para às {horario_inicio}", embed=embed)  # Marca @everyone fora do embed

        # Armazena o embed e inicializa as reações por mensagem
        self.message_embeds[message.id] = embed
        self.reactions_by_message[message.id] = defaultdict(list)

        # Adiciona reações ao embed
        for emoji in ROLE_EMOJIS.values():
            await message.add_reaction(emoji)

        await interaction.response.send_message(f"Evento Avalon criado em {channel.mention}!", ephemeral=True)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Atualiza o embed quando uma reação é adicionada."""
        if user.bot:
            return

        message = reaction.message
        if message.id in self.message_embeds:
            embed = self.message_embeds[message.id]
            reactions = self.reactions_by_message[message.id]
            role_updated = False

            for role, emoji in ROLE_EMOJIS.items():
                if str(reaction.emoji) == emoji:
                    if user not in reactions[role]:
                        reactions[role].append(user)
                        role_updated = True

            if role_updated:
                for role, emoji in ROLE_EMOJIS.items():
                    embed.set_field_at(
                        list(ROLE_EMOJIS.keys()).index(role) + 6,
                        name=f'{emoji} {role}',
                        value=f'({len(reactions[role])})\n{", ".join(user.mention for user in reactions[role])}',
                        inline=True,
                    )
                await message.edit(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Atualiza o embed quando uma reação é removida."""
        if user.bot:
            return

        message = reaction.message
        if message.id in self.message_embeds:
            embed = self.message_embeds[message.id]
            reactions = self.reactions_by_message[message.id]
            role_updated = False

            for role, emoji in ROLE_EMOJIS.items():
                if str(reaction.emoji) == emoji:
                    if user in reactions[role]:
                        reactions[role].remove(user)
                        role_updated = True

            if role_updated:
                for role, emoji in ROLE_EMOJIS.items():
                    embed.set_field_at(
                        list(ROLE_EMOJIS.keys()).index(role) + 6,
                        name=f'{emoji} {role}',
                        value=f'({len(reactions[role])})\n{", ".join(user.mention for user in reactions[role])}',
                        inline=True,
                    )
                await message.edit(embed=embed)


async def setup(bot):
    """Função para adicionar o cog ao bot."""
    await bot.add_cog(AvalonCommand(bot))
