#imports
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import yt_dlp
import asyncio

from keep_alive import keep_alive

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

#music bot commands
async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

keep_alive()

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
#declare intents (permissions) for the bots to run
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix='<',intents=intents)

AdminRole = "goob"
TicketCategory = 1451100798531539005
VerifyName = "Member"
WelcomeChannel = 1450708052369211392
LogsChannel = 1450772719279935518
RulesChannel = 1450710176922337340
VerifyChannel = 1450766129831219232
music_queues = {}
current_song = {}



#commands start
#--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
#define an event on bot ready
@bot.event
async def on_ready():
    print(f"Bot is up and running!\nBot Name: {bot.user.name}")

    #send verify message to fix
    bot.add_view(Menu())
    bot.add_view(menu2())
    channel = bot.get_channel(VerifyChannel)
    view = Menu()
    async for msg in channel.history(limit=1):
        await msg.delete()
    embed = discord.Embed(title="Verification",description="Click the button below to open a ticket\n\nYou will get verified shortly after you open a ticket")
    await channel.send(embed=embed, view=view)


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
#music bot commands
#--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
@bot.command()
async def play(ctx, *, song_query: str):

    # join a vc
    if ctx.author.voice is None:
        await ctx.send("You must be in a voice channel!")
        return

    voice_channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    await ctx.send(f"Searching for *{song_query}*\nThis may take a few seconds...")


    ydl_options = {
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }

    #search for the audio

    query = "ytsearch1: " + song_query
    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get("entries", [])

    if not tracks:
        await ctx.send("No results found")
        return

    first_track = tracks[0]
    audio_url = first_track["url"]
    title = first_track.get("title", "Untitled")

    queue = music_queues.setdefault(ctx.guild.id, [])
    was_empty = len(queue) == 0
    queue.append((audio_url, title))

    if was_empty:
        await ctx.send(f"Now playing **{title}**")
        play_next(ctx)
    else:
        await ctx.send(f"Queued: **{title}**")

    if not voice_client.is_playing() and not voice_client.is_paused():
        await ctx.send(f"Now playing **{title}**")
        play_next(ctx)

#--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
#play next
def play_next(ctx):
    queue = music_queues.get(ctx.guild.id)

    if not queue or len(queue) == 0:
        current_song[ctx.guild.id] = None
        return

    voice_client = ctx.voice_client
    audio_url, title = queue.pop(0)

    current_song[ctx.guild.id] = title

    ffmpeg_options = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn -c:a libopus -b:a 96k"
    }

    source = discord.FFmpegOpusAudio(
        audio_url,
        **ffmpeg_options,
        executable="bin\\ffmpeg\\ffmpeg.exe"
    )

    voice_client.play(
        source,
        after=lambda e: bot.loop.call_soon_threadsafe(play_next, ctx)
    )
#--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused")


@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed")


@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped")


@bot.command()
async def stop(ctx):
    if ctx.guild.id in music_queues:
        music_queues[ctx.guild.id].clear()

    if ctx.voice_client:
        await ctx.voice_client.disconnect()

    await ctx.send("Stopped and emptied the queue")


@bot.command()
async def queue(ctx):
    queue_list = music_queues.get(ctx.guild.id, [])
    now_playing = current_song.get(ctx.guild.id)
    voice_client = ctx.voice_client

    message = "**Current Queue:**\n"

    #add currently playing song
    if now_playing:
        message += f"Now Playing: {now_playing}\n"

    if not queue_list:
        message += "Queue is empty"
    else:
        for i, (_, title) in enumerate(queue_list, start=1):
            message += f"{i}. {title}\n"

    await ctx.send(message)


#--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
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
        category = guild.get_channel(TicketCategory)
        if category is None:
            await interaction.response.send_message("Ticket category not found", ephemeral=True)
            return
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