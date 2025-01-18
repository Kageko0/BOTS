import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, ButtonStyle, TextChannel
from discord.ui import Button, View
from datetime import datetime
import motor.motor_asyncio


class TicketView(View):
    def __init__(self, bot, admin_roles, ticket_category, ticket_data=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.admin_roles = admin_roles
        self.ticket_category = ticket_category
        self.ticket_data = ticket_data  # Dados do ticket recuperados, se disponíveis

    @discord.ui.button(label="Abrir Ticket", style=ButtonStyle.green)
    async def abrir_ticket(self, interaction: Interaction, button: Button):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
        }
        for role in guild.roles:
            if role.name in self.admin_roles:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True)

        # Obtém a categoria do painel principal
        category = discord.utils.get(guild.categories, id=self.ticket_category.id)

        # Cria o canal do ticket na mesma categoria
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites,
            category=category
        )
        embed = Embed(
            title="Recrutamento",
            description="Acesse os arquivos dos testes aqui:  \n https://drive.google.com/drive/folders/1EJs48Khqe26kmXd58QBDBIourWAVNnX_?usp=sharing",
            color=discord.Color.red()
        )
        embed.add_field(name="**Tradutor**", value="<@&1243974538526589089>  \n Cargo dedicado a pessoa que __**Traduz**__ a obra do idioma nativo ou alternativo.  \n __**Requisitamos que saiba uma das seguintes línguas - Inglês, Japonês, Chinês, Coreano**__", inline=False)
        embed.add_field(name="**Redraw/Cleaner**", value="<@&1243974533430509589>  \n Cargo Dedicado a pessoa que __**Limpa**__ as falas, dentro e fora dos balões  \n __**Requisitamos que tenha Photoshop instalado ou que tenha um PC/Laptop**__", inline=False)
        embed.add_field(name="**TypeSetter**", value="<@&1243974475901304912>  \n Cargo Dedicado a pessoa que __**Coloca**__ as falas dentro e fora dos balões  \n __**Requisitamos que tenha Photoshop instalado ou que tenha um PC/Laptop**__", inline=False)
        embed.add_field(name="**QC/Revisor**", value="<@&1243974583606841516>  \n Cargo Dedicado a pessoa que __**Corrige**__ as falas, diagramação e desenho, revisando o capítulo ao final dos outros processos  \n __**Requisitamos que tenha Photoshop instalado ou que tenha um PC/Laptop**__", inline=False)
        embed.set_thumbnail(url=interaction.user.avatar.url)
        embed.set_footer(text=f"Ticket criado por {interaction.user.name} | ID do usuário: {interaction.user.id}")

        close_view = TicketCloseView(self.bot)
        await ticket_channel.send(
            content=f"{interaction.user.mention}, {', '.join([role.mention for role in guild.roles if role.name in self.admin_roles])}",
            embed=embed,
            view=close_view
        )

        # Registrar o ticket no MongoDB
        ticket_data = {
            "ticket_id": ticket_channel.id,
            "personid": interaction.user.id,
            "person": interaction.user.name,
            "date": datetime.utcnow()  # Armazenando a data de criação
        }
        await self.bot.tickets_collection.insert_one(ticket_data)

        await interaction.response.send_message("Seu ticket foi criado!", ephemeral=True)

    async def sync_ticket(self, ticket_channel):
        """Sincroniza um ticket com o banco de dados e envia o embed correspondente."""
        ticket_data = await self.bot.tickets_collection.find_one({"ticket_id": ticket_channel.id})
        if ticket_data:
            embed = Embed(
                title="Recrutamento",
                description="Acesse os arquivos dos testes aqui:  \n https://drive.google.com/drive/folders/1EJs48Khqe26kmXd58QBDBIourWAVNnX_?usp=sharing",
                color=discord.Color.red()
            )
            embed.add_field(name="**Tradutor**", value="<@&1243974538526589089>  \n Cargo dedicado a pessoa que __**Traduz**__ a obra do idioma nativo ou alternativo.", inline=False)
            embed.set_footer(text=f"Ticket criado por {ticket_data['person']} | ID do usuário: {ticket_data['personid']}")
            close_view = TicketCloseView(self.bot)
            await ticket_channel.send(
                content=f"{ticket_data['person']}, {', '.join([role.mention for role in ticket_channel.guild.roles if role.name in self.admin_roles])}",
                embed=embed,
                view=close_view
            )

class TicketCloseView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Fechar Ticket", style=ButtonStyle.red)
    async def fechar_ticket(self, interaction: Interaction, button: Button):
        await interaction.channel.delete()

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_roles = ["Adm", "Moderação"]  # Defina os cargos permitidos aqui

    @app_commands.command(name="postticket", description="Cria um embed para abrir tickets")
    @app_commands.describe(channel="O canal onde o painel de tickets será postado")
    async def postticket(self, interaction: Interaction, channel: TextChannel):
        # Verifica se o usuário tem um dos cargos permitidos
        if not any(role.name in self.admin_roles for role in interaction.user.roles):
            await interaction.response.send_message(
                "Você não tem permissão para usar este comando.", ephemeral=True
            )
            return

        embed = Embed(
            title="Recrutamento",
            description="Clique no botão 📩 abaixo para abrir um ticket de recrutamento.",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"TerzoScan")

        category = channel.category  # Obtém a categoria do canal
        view = TicketView(self.bot, self.admin_roles, category)
        await channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            f"O painel de tickets foi postado em {channel.mention}.", ephemeral=True
        )

    async def on_ready(self):
        """Sincroniza todos os tickets quando o bot for iniciado."""
        tickets = await self.bot.tickets_collection.find().to_list(length=None)
        for ticket_data in tickets:
            guild = self.bot.get_guild(ticket_data["guild_id"])  # Supondo que o guild_id esteja armazenado no MongoDB
            if guild:
                # Verifica se o canal de ticket ainda existe
                ticket_channel = guild.get_channel(ticket_data["ticket_id"])
                if ticket_channel:
                    ticket_view = TicketView(self.bot, self.admin_roles, ticket_channel.category, ticket_data)
                    await ticket_view.sync_ticket(ticket_channel)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
