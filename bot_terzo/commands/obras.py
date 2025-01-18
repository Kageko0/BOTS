from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color, Permissions
import re

class Obras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.obras_collection = bot.obras_collection
        self.admin_roles = ["Adm", "Moderação"]  # Cargos permitidos para adicionar/remover obras

    @app_commands.command(name="obras", description="Lista todas as obras disponíveis")
    async def obras(self, interaction: Interaction):
        obras = self.obras_collection.find()
        description = ""
        async for obra in obras:
            description += f"[{obra['titulo']}]({obra['link']}) - {obra['status']}\n"

        embed = Embed(title="Obras", description=description, color=Color.red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="obra", description="Mostra detalhes de uma obra específica")
    async def obra(self, interaction: Interaction, nome: str):
        regex = re.compile(nome, re.IGNORECASE)  # Permite busca parcial e insensível a maiúsculas/minúsculas
        obra = await self.obras_collection.find_one({"titulo": regex})
        if not obra:
            await interaction.response.send_message("Obra não encontrada.")
            return

        embed = Embed(
            title=obra["titulo"],
            description=f"Status: {obra['status']}",
            url=obra["link"],
            color=Color.red()
        )
        embed.set_image(url=obra["image"])
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="addobra", description="Adiciona uma nova obra ao banco de dados")
    async def addobra(self, interaction: Interaction, nome: str, link: str, status: str, link_image: str):
        if not any(role.name in self.admin_roles for role in interaction.user.roles):
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        obra = {"titulo": nome, "link": link, "status": status, "image": link_image}
        await self.obras_collection.insert_one(obra)
        await interaction.response.send_message(f"Obra **{nome}** adicionada com sucesso!")

    @app_commands.command(name="remvobra", description="Remove uma obra do banco de dados")
    async def remvobra(self, interaction: Interaction, nome: str):
        if not any(role.name in self.admin_roles for role in interaction.user.roles):
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        result = await self.obras_collection.delete_one({"titulo": nome})
        if result.deleted_count:
            await interaction.response.send_message(f"Obra **{nome}** removida com sucesso!")
        else:
            await interaction.response.send_message(f"Obra **{nome}** não encontrada.")

async def setup(bot):
    await bot.add_cog(Obras(bot))
