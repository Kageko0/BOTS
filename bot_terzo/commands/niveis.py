from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color, Member
from discord.utils import get

class Nivel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users_collection = bot.users_collection

    async def _atualizar_usuario(self, user_id):
        user_data = await self.users_collection.find_one({"_id": user_id})
        if not user_data:
            user_data = {"_id": user_id, "level": 1, "messages": 0}
            await self.users_collection.insert_one(user_data)
        return user_data

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        user_id = message.author.id
        user_data = await self._atualizar_usuario(user_id)

        # Incrementa mensagens e XP
        user_data["messages"] += 1
        xp_needed = user_data["level"] * 10
        if user_data["messages"] >= xp_needed:
            user_data["level"] += 1
            user_data["messages"] -= xp_needed
            await message.channel.send(f"Parabéns {message.author.mention}, você subiu para o nível {user_data['level']}!")
        await self.users_collection.replace_one({"_id": user_id}, user_data)

    @app_commands.command(name="lvl", description="Mostra o nível de um membro")
    @app_commands.describe(member="O membro que você quer ver o nível")
    async def lvl(self, interaction: Interaction, member: Member = None):
        if member is None:
            # Se não for passado um membro, mostra o top 10
            top_users = await self.users_collection.find().sort("level", -1).limit(10).to_list(length=10)
            
            embed = Embed(
                title="Top 10 Membros com Maior Nível",
                description="Veja os top 10 membros com maior nível!",
                color=Color.red()
            )

            for idx, user_data in enumerate(top_users, start=1):
                member = await self.bot.fetch_user(user_data["_id"])
                embed.add_field(
                    name=f"{idx}. {member.name}",
                    value=f"Nível: {user_data['level']} | Mensagens: {user_data['messages']}",
                    inline=False
                )
            await interaction.response.send_message(embed=embed)

        else:
            # Se o membro for passado, mostra os dados dele
            user_data = await self.users_collection.find_one({"_id": member.id})
            if not user_data:
                await interaction.response.send_message(f"{member.mention} ainda não tem nível registrado.")
                return

            embed = Embed(
                title=f"Nível de {member.name}",
                description=f"**Nível:** {user_data['level']}\n**Mensagens:** {user_data['messages']}",
                color=Color.red()
            )
            embed.set_thumbnail(url=member.avatar.url)

            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Nivel(bot))
