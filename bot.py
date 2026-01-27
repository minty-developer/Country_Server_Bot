import discord
from discord import app_commands
import os

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

@client.tree.command(name="핑", description="봇이 살아있는지 확인")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("퐁! 나라 봇 정상 작동 중 🇰🇷")

client.run(os.environ["DISCORD_TOKEN"])
