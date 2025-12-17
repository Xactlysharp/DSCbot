#imports
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

from keep_alive import keep_alive

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

keep_alive()

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
#declare intents (permissions) for the bots to run
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix='<',intents=intents)

AdminRole = "goob"
ticket_category_name = "Info"
VerifyName = "Member"
WelcomeChannel = 1450708052369211392
LogsChannel = 1450772719279935518
RulesChannel = 1450710176922337340
VerifyChannel = 1450766129831219232



#commands start
#--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
#define an event on bot ready
@bot.event
async def on_ready():
    print(f"Bot is up and running!\nBot Name: {bot.user.name}")


#testing commands
#--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
# <hello
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}")

# <ping
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

#embeds
@bot.command()
@commands.has_role(AdminRole)
async def embed(ctx, *, text):
    embed = discord.Embed(title="Title", description=text)
    embed_message = await ctx.send(embed=embed)
    await embed_message.add_reaction("😘")
    await embed_message.add_reaction("👺")
@embed.error
async def embed_error(ctx):
    await ctx.send("Error! Make sure you have the right role to use this command")

#Rules
@bot.command()
@commands.has_role(AdminRole)
async def sendtorules(ctx, *, text):
    embed = discord.Embed(title="Discord Server Rules", description=text, color=discord.Color.blue())
    channel = bot.get_channel(RulesChannel)
    embed_message = await channel.send(embed=embed)
@sendtorules.error
async def sendtorules_error(ctx):
    await ctx.send("Error! Make sure you have the right role to use this command")


#--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

#logging cmds
#Welcome
#sends welcome message on member join
#Log user join
#sends message in logs on user join
@bot.event
async def on_member_join(member):
    Logchannel = bot.get_channel(LogsChannel)
    Joinchannel = bot.get_channel(WelcomeChannel)
    embed = discord.Embed(title="User Joined", description=f"{member.name} has joined the server\n{member.id}", color=discord.Color.green())
    await Logchannel.send(embed=embed)
    welcome_message = await Joinchannel.send(f"Welcome {member.mention} to {member.guild.name}!")
    await welcome_message.add_reaction("👋")

#Log user leave
#sends message in logs on user leave
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LogsChannel)
    embed = discord.Embed(title="User Left", description=f"{member.name} has left the server\n{member.id}", color=discord.Color.red())
    await channel.send(embed=embed)

#message deleted logs
@bot.event
async def on_message_delete(message):
    logchannel = bot.get_channel(LogsChannel)
    embed = discord.Embed(title="Message deleted", description=f"```{message.content}```\nWas sent by {message.author}", color=discord.Color.red())
    await logchannel.send(embed=embed)

#--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
class menu2(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket_button")
    async def close_ticket(self, interaction: discord.Interaction, button:discord.ui.Button):
        await interaction.response.send_message(f"Closing Ticket", ephemeral=True)
        await interaction.channel.delete()

#button creation
class Menu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=" Tickets", style=discord.ButtonStyle.blurple, emoji="📩", custom_id="open_ticket_button")
    #button command
    async def create_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defines
        guild = interaction.guild
        user = interaction.user
        channel_name = f"{user.name}-channel"
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False),user: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        category = discord.utils.get(guild.categories, name=ticket_category_name)
        existing = discord.utils.get(category.text_channels, name=channel_name)
        if existing:
            await interaction.response.send_message("You already have a ticket open.", ephemeral=True)
            return
        await interaction.response.send_message(f"Creating Ticket", ephemeral=True)

        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        embed = discord.Embed(title=f"{user.name}'s ticket", description="Click the red button to close this ticket.\n\nAdmins can use ```<verify @user``` to add access to users")
        await channel.send(embed=embed, view=menu2())
        await channel.send(f"{user.mention} This is your ticket. Please wait for an admin to verify you.")

    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---



#resend ticket message to one channel and keep channel clean
@bot.event
async def on_ready():
    bot.add_view(Menu())
    bot.add_view(menu2())
    channel = bot.get_channel(VerifyChannel)
    view = Menu()
    await channel.purge(limit=1)
    embed = discord.Embed(title="Verification",description="Click the button below to open a ticket\n\nYou will get verified shortly after you open a ticket")
    await channel.send(embed=embed, view=view)

#cleanup test
@bot.command()
@commands.has_permissions(manage_messages=True)
async def cleanup(ctx, amount: int):
    amount = amount + 2
    await ctx.send("Cleaning up")
    if amount >= 100:
        await ctx.send("Tooooooo many messages, dont delete more than 100 please!")
        return
    else:
        await ctx.channel.purge(limit=amount)

#<cleanup error handling
@cleanup.error
async def cleanup_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("Error! ): (no perms xd)")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def verify(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=VerifyName)
    if role is None:
        await ctx.send("Error! role not found, dm sharp")
        return
    if role in member.roles:
        await ctx.send(f"{member.mention} already has that role!")
        return
    await member.add_roles(role)
    await ctx.send(f"{member.mention} has been given the {role.name} role")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unverify(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=VerifyName)
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} has had the {role.name} role removed")
        return
    else:
        await ctx.send(f"{member.mention} does not have the {role.name} role")

#run bot
bot.run(token, log_handler=handler, log_level=logging.DEBUG)

#locked out from server until command
#only access to rules till roled
#have to make a ticket to join