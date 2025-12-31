import discord

intents = discord.Intents.none()
bot = discord.Client(intents=intents)

bot.run("YOUR_TOKEN")