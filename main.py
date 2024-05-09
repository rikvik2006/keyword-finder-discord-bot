import discord
from discord.ext import commands
from discord.utils import get
from discord import app_commands
from discord import DMChannel, Embed
import time
import json
from discord_webhook import DiscordWebhook, DiscordEmbed
from helpers import add_ping, check_msg_has_keyword, get_pings, save_pings, remove_space, format_keywords
import traceback
from typing import Union, List
import uuid

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

with open("settings.json", "r") as file:
    settings = json.load(file)

pings = get_pings()


async def send_embed_log(webhook: str, log: int, target: int, kws: str, price):
    try:
        webhook = DiscordWebhook(
            url=webhook,
            username="[LOG] Keyword Logger",
            avatar_url=settings["avatar_url"],
        )

        embed = DiscordEmbed()

        if log == 1:
            embed.title = "Added Keyword"
            embed.color = 5763719
        elif log == 2:
            embed.title = "Edited Keyword"
            embed.color = 16776960
        else:
            embed.title = "Removed Keyword"
            embed.color = 15548997
    
        embed.set_footer(
            icon_url=settings["avatar_url"],
            text="[LOG] Keyword Logger",
        )
        embed.set_timestamp()
        embed.set_thumbnail(url=settings["avatar_url"])
        embed.add_embed_field(name="Member Id", value=str(target), inline=True)
        embed.add_embed_field(name="Member Username", value=str(get(client.get_all_members(), id=target).name), inline=True)
        embed.add_embed_field(name="", value="", inline=False)
        embed.add_embed_field(name="Kewords", value=str(kws), inline=True)
        embed.add_embed_field(name="Price", value=str(price), inline=True)
        webhook.add_embed(embed)
        webhook.execute()
    except Exception as e:
        print(f"Failed to Sent Notification to Discord: {e}")


async def send_embed_ping(webhook: str, target: int, message: discord.Message, kws: str, price: int = None):
    try:
        webhook = DiscordWebhook(
            url=webhook,
            username="[PING] Keyword Logger",
            avatar_url=settings["avatar_url"],
        )
        embed = DiscordEmbed(title="Keyword PING", color=5793266)
        embed.set_footer(
            icon_url=settings["avatar_url"],
            text="Keyword Logger",
        )
        embed.set_timestamp()
        embed.set_thumbnail(url=settings["avatar_url"])
        embed.add_embed_field(name="Ping Target", value=str(target), inline=False)
        embed.add_embed_field(
            name="Product", value=f"[Jump to Message](<{message.jump_url}>)", inline=False
        )
        embed.add_embed_field(name="Positive Keyword", value=str(kws), inline=True)
        embed.add_embed_field(name="Price", value=str(price), inline=True)
        webhook.add_embed(embed)
        webhook.execute()
    except Exception as e:
        print(f"Failed to Sent Notification to Discord: {e}")


@client.event
async def on_ready():

    client.tree.copy_global_to(guild=client.get_guild(980586843072503808))
    await client.tree.sync(guild=client.get_guild(980586843072503808))


@client.event
async def on_message(message: discord.Message):
    
    if not message.guild:
        return
    
    if message.author.id == client.user.id:
        return
    
    channel_webhooks = await message.channel.webhooks()
    for webhook in channel_webhooks:
        if webhook.url == settings["add_log_webhook"] or webhook.url == settings["ping_log_webhook"]:
            return

    msg_channel = message.channel.id
    pings_updated = False

    for ping in pings:

        pkws: str = ping["positiveKeywords"]
        nkws: str = ping["negativeKeywords"]
        price: int = ping["price"]
        timestamp: int = ping["pingTimestamp"]
        target = get(message.guild.members, id=ping["memberId"])
        channel: int = ping["channelId"]

        print(f"🌸 Keyword: {pkws} On Channel: {channel}, Original message on channel: {msg_channel}")
        if msg_channel == channel or channel == "server":

            now = int(time.time())

            if check_msg_has_keyword(message, pkws, nkws, price):
                pings_updated = True
                print("🌟 PING!")
                ping["pingTimestamp"] = now

                await DMChannel.send(target, content="# `🎯 Found a new keyword`")
                await DMChannel.send(target, embeds=message.embeds, content=message.content, files=message.attachments)
                await DMChannel.send(target, content=f"Easy actions: [[Jump to message](<{message.jump_url}>)]")
                await send_embed_ping(
                    settings["ping_log_webhook"],
                    target,
                    message,
                    pkws,
                    price,
                )
            else:
                print("🧙 No ping")

    if pings_updated:
        save_pings(pings)

    await client.process_commands(message)


async def add_new_keyword(
    server_keyword: bool,
    itr: discord.Interaction, 
    target_channel: discord.TextChannel,
    positive_keywords: str,
    price: int = None,
    negative_keywords: str = None,
):
    global pings
    
    if not negative_keywords:
        negative_keywords = []
    else:
        negative_keywords = format_keywords(negative_keywords)

    positive_keywords = format_keywords(positive_keywords)


    if server_keyword:
        target_channel = "server"

    # Generate a new UUID for the keyword
    keyword_uuid: str = str(uuid.uuid4())

    updated_pings = add_ping(
        keyword_uuid, target_channel, positive_keywords, negative_keywords, price, itr.user.id
    )

    # Send a log that say that a new keyword has been added with the keyword info
    await send_embed_log(
        settings["add_log_webhook"], 1, itr.user.id, positive_keywords, price
    )
    pings = updated_pings

    await itr.response.send_message(
        "✅ Keyword aggiunta correttamente!", ephemeral=True
    )

@client.tree.command(name="add_keyword", description="Add a new kw.")
# @app_commands.checks.has_role(str(settings["roleId"]))
async def add_new_keyword_command(
    itr: discord.Interaction,
    target_channel: discord.TextChannel,
    positive_keywords: str,
    price: int = None,
    negative_keywords: str = None,
):
    await add_new_keyword(False, itr, target_channel, positive_keywords, price, negative_keywords)
    

@client.tree.command(name="add_keyword_server", description="Add a new keyword. For the entire server (not just one channel)")
# @app_commands.checks.has_role(str(settings["roleId"]))
async def add_new_keyword_server_command(
    itr: discord.Interaction,
    positive_keywords: str,
    price: int = None,
    negative_keywords: str = None,
):
    await add_new_keyword(True, itr, None, positive_keywords, price, negative_keywords)

# Autocomplete for the delete_keyword an edit_keyword commands (is the data that appear in the selection menu to select the keyword to delete/edit)
async def delete_keyword_autocomplete(
    itr: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    if not itr.guild:  
        return [] 
    
    data = []

    for ping in pings:

        if ping["memberId"] == itr.user.id:
            keyword_id: str = ping["keywordId"]
            if current in "".join(keyword_id.split("-")) or current in keyword_id:
                data.append(
                    app_commands.Choice(
                        name=f"Keyword ID: {keyword_id}",
                        value=keyword_id,
                    )
                )

    return data


@client.tree.command(name="delete_keyword", description="Remove a saved keyword.")
@app_commands.autocomplete(keyword_id=delete_keyword_autocomplete)
async def delete_ping(itr: discord.Interaction, keyword_id: str):
    global pings

    for ping in pings:
        if ping["keywordId"] == keyword_id:
            target_ping = ping
            break

    if not target_ping:
        await itr.response.send_message("❌ Keyword not found", ephemeral=True)
        return
        
    if target_ping["memberId"] and (target_ping["memberId"] != itr.user.id):
        await itr.response.send_message("❌ You do not have permissions to modify this keyword", ephemeral=True)
        return
    
    pings.remove(target_ping)
    save_pings(pings)
    # updated_pings = get_pings()
    # # Update the pings variable with the new pings list (with the deleted keyword)
    # pings = updated_pings
    

    await itr.response.send_message(
        "✅ Keyword rimossa correttamente!", ephemeral=True
    )


@client.tree.command(name="edit_keyword", description="Edit a saved keyword.")
@app_commands.autocomplete(keyword_id=delete_keyword_autocomplete)
# @app_commands.checks.has_role(str(settings["roleId"]))
async def edit_ping(
    itr: discord.Interaction,
    keyword_id: str,
    new_target_channel: discord.TextChannel = None,
    new_positive_keywords: str = None,
    new_price: int = None,
    new_negative_keywords: str = None,
):
    # TODO: Controlla che pings si aggiorni correttamente, non so ancora se lo fa, altrimenti ogni volta fetcha il file pings.json
    global pings

    for ping in pings:
        if ping["keywordId"] == keyword_id:
            target_ping = ping
            break

    if not target_ping:
        await itr.response.send_message("❌ Keyword not found (check the uuid)", ephemeral=True)
        return
    
    if target_ping["memberId"] and (target_ping["memberId"] != itr.user.id):
        await itr.response.send_message("❌ You do not have permissions to modify this keyword", ephemeral=True)
        return
    
    try:
        if not new_target_channel:
            new_target_channel = target_ping["channelId"]

        if not new_positive_keywords:
            new_positive_keywords = target_ping["positiveKeywords"]
        else:
            new_positive_keywords = format_keywords(new_positive_keywords)

        if not new_price:
            new_price = target_ping["price"]

        if not new_negative_keywords:
            new_negative_keywords = target_ping["negativeKeywords"]
        else:
            new_negative_keywords = format_keywords(new_negative_keywords)


        # TODO: Prima rimuove il ping dal file JSON, e poi lo aggiunge con i nuovi dati
        pings.remove(target_ping)
        save_pings(pings)
        # positive_keywords = positive_keywords.split(",")

        updated_pings = add_ping(
            keyword_id, new_target_channel, new_positive_keywords, new_negative_keywords, new_price, itr.user.id
        )
        await send_embed_log(
            settings["add_log_webhook"], 2, itr.user.id, new_positive_keywords, new_price
        )
        pings = updated_pings

        await itr.response.send_message(
            "✅ Keyword Editata correttamente!", ephemeral=True
        )
    except Exception as e:
        print(e)
        traceback.print_exc()


@client.tree.command(name="list_keywords", description="List all saved keywords.")
async def list_keywords(itr: discord.Interaction):

    pings = get_pings()

    username = itr.user.name
    embed_description = ""
    for i, ping in enumerate(pings):

        if ping["memberId"] == itr.user.id:
            keyword_id = ping["keywordId"]            
            channel: Union[discord.TextChannel, None] = None
            if  ping["channelId"] == "server":
                channel = None
            else:
                channel = get(itr.guild.channels, id=ping["channelId"])
            pkws: list[str] = ", ".join(ping["positiveKeywords"])
            nkws: list[str] = ", ".join(ping["negativeKeywords"])
            price: int | None = ping["price"]


            embed_description += f"**Keyword ID:** {keyword_id}\n"
            if channel:
                embed_description += f"**Channel:** <#{channel.id}>\n"
            else:
                embed_description += f"**Channel:** Server\n"

            embed_description += f"**Positive Keywords:** {pkws}\n"
            if len(nkws) > 0:
                embed_description += f"**Negative Keywords:** {nkws}\n"
            else:
                embed_description += f"**Negative Keywords:** Not set\n"

            if price: 
                embed_description += f"**Price:** {price} €\n"
            else:
                embed_description += f"**Price:** Not set\n\n"
    
    if embed_description == "":
        embed_description = "No keywords found"

    embed = Embed()
    embed.set_author(name=f"{username}'s Keywords", icon_url=itr.user.avatar)
    embed.description = embed_description
    embed.color = 0x2D2D2D
    embed.set_footer(text="Keyword Logger", icon_url=settings["avatar_url"])
    
    try:
        await itr.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"Errore nell'invio del messaggio: {e}")

@client.tree.error
async def on_app_command_error(itr: discord.Interaction, error):

    if isinstance(error, app_commands.errors.MissingRole):
        await itr.response.send_message("Error: Permessi mancanti", ephemeral=True)


client.run(settings["bot_token"])