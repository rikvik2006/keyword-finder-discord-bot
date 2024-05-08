import discord
from discord.ext import commands
from discord.utils import get
from discord import app_commands
from discord import DMChannel, Intents
import time
import json
from discord_webhook import DiscordWebhook, DiscordEmbed
from helpers import add_ping, check_msg_has_keyword, get_pings, save_pings, get_embed
import traceback

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
            embed.title = "Keyword Aggiunta"
            embed.color = 5763719
        elif log == 2:
            embed.title = "Keyword Editata"
            embed.color = 16776960
        else:
            embed.title = "Keyword Rimossa"
            embed.color = 15548997
    
        embed.set_footer(
            icon_url=settings["avatar_url"],
            text="[LOG] Keyword Logger",
        )
        embed.set_timestamp()
        embed.set_author(
            name="[LOG] Keyword Logger",
        )
        embed.set_thumbnail(url=settings["avatar_url"])
        embed.add_embed_field(name="Member Id", value=str(target), inline=False)
        embed.add_embed_field(name="Kewords", value=str(kws), inline=True)
        embed.add_embed_field(name="Price", value=str(price), inline=True)
        webhook.add_embed(embed)
        webhook.execute()
    except Exception as e:
        print(f"Failed to Sent Notification to Discord: {e}")


async def send_embed_ping(webhook: str, target: int, kws: str, price):
    try:
        webhook = DiscordWebhook(
            url=webhook,
            username="[PING] Keyword Logger",
            avatar_url=settings["avatar_url"],
        )
        embed = DiscordEmbed(title="Keyword PING", color=5793266)
        embed.set_footer(
            icon_url=settings["avatar_url"],
            text="HUNTERS",
        )
        embed.set_timestamp()
        embed.set_author(
            name="[PING] Keyword Logger"
        )
        embed.set_thumbnail(url=settings["avatar_url"])
        embed.add_embed_field(name="MemberId", value=str(target), inline=False)
        embed.add_embed_field(
            name="Product", value=f"{str(embed.title)}\n {embed.url}", inline=False
        )
        embed.add_embed_field(name="Kw", value=str(kws), inline=True)
        embed.add_embed_field(name="Price", value=str(price), inline=True)
        webhook.add_embed(embed)
        webhook.execute()
    except Exception as e:
        print(f"Failed to Sent Notification to Discord: {e}")


@client.event
async def on_ready():

    await client.tree.sync(guild=client.get_guild(980586843072503808))


@client.event
async def on_message(message: discord.Message):
    
    if not message.guild:
        return
    
    if message.author.id == client.user.id:
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

        print("🎯 Before message channel check")
        print(f"🌸 Keyword: {pkws} On Channel: {channel}, Original message on channel: {msg_channel}")
        if msg_channel == channel:

            now = int(time.time())

            if check_msg_has_keyword(message, pkws, nkws, price):
                pings_updated = True
                print("ping")
                ping["pingTimestamp"] = now

                await DMChannel.send(target, content="# `🎯 Found a new keyword`")
                await DMChannel.send(target, embeds=message.embeds, content=message.content, files=message.attachments)
                await DMChannel.send(target, content=f"Easy actions: [[Jump to message](<{message.jump_url}>)]")
                await send_embed_ping(
                    settings["ping_log_webhook"],
                    target,
                    pkws,
                    price,
                )
            else:
                print("No ping")

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

    def remove_space(keyword: str) -> str:
        return keyword.strip()
    
    if not negative_keywords:
        negative_keywords = []
    else:
        negative_keywords = list(map(remove_space, negative_keywords.strip().split(",")))

    positive_keywords = list(map(remove_space, positive_keywords.strip().split(",")))


    if server_keyword:
        target_channel = "server"

    updated_pings = add_ping(
        target_channel, positive_keywords, negative_keywords, price, itr.user.id
    )

    # Send a log that say that a new keyword has been added with the keyword info
    await send_embed_log(
        settings["add_log_webhook"], 1, itr.user.id, positive_keywords, price
    )
    pings = updated_pings

    await itr.response.send_message(
        "✅ Keyword aggiunta correttamente!", ephemeral=True
    )

@client.tree.command(name="add_keyword", description="Aggiungi una nuova kw.")
# @app_commands.checks.has_role(str(settings["roleId"]))
async def add_new_keyword_command(
    itr: discord.Interaction,
    target_channel: discord.TextChannel,
    positive_keywords: str,
    price: int = None,
    negative_keywords: str = None,
):
    await add_new_keyword(False, itr, target_channel, positive_keywords, price, negative_keywords)
    

@client.tree.command(name="add_keyword_server", description="Aggiungi una nuova kw. Per l'intero server (non solo un canale)")
# @app_commands.checks.has_role(str(settings["roleId"]))
async def add_new_keyword_server_command(
    itr: discord.Interaction,
    positive_keywords: str,
    price: int = None,
    negative_keywords: str = None,
):
    await add_new_keyword(True, itr, None, positive_keywords, price, negative_keywords)

async def delete_ping_autocomplete(itr: discord.Interaction, current: str):

    data = []

    for i, ping in enumerate(pings):

        if ping["memberId"] == itr.user.id:

            channel: discord.TextChannel = get(itr.guild.channels, id=ping["channelId"])
            target = get(itr.guild.members, id=ping["memberId"])
            pkws: list[str] = "/".join(ping["positiveKeywords"])
            nkws: list[str] = "/".join(ping["negativeKeywords"])
            price = ping["price"]
            if current in (channel.name + target.name + pkws + nkws):

                data.append(
                    app_commands.Choice(
                        name=f"#{channel.name} @{target.name} +({pkws}) -({nkws}) ({price} €)",
                        value=i,
                    )
                )

    return data


@client.tree.command(name="delete_keyword", description="Rimuovi una kw salvata.")
@app_commands.autocomplete(ping=delete_ping_autocomplete)
# @app_commands.checks.has_role(str(settings["roleId"]))
async def delete_ping(itr: discord.Interaction, ping: int):

    global pings

    target_ping = pings[ping]

    if target_ping["memberId"] and (target_ping["memberId"] != itr.user.id):

        await itr.response.send_message("Permessi mancanti", ephemeral=True)

    else:

        del pings[ping]

        save_pings(pings)

        await itr.response.send_message(
            "✅ Keyword rimossa correttamente!", ephemeral=True
        )


@client.tree.command(name="edit_keyword", description="Edita una kw salvata.")
@app_commands.autocomplete(ping=delete_ping_autocomplete)
# @app_commands.checks.has_role(str(settings["roleId"]))
async def edit_ping(
    itr: discord.Interaction,
    ping: int,
    target_channel: discord.TextChannel = None,
    positive_keywords: str = None,
    price: int = None,
    negative_keywords: str = None,
):

    global pings

    target_ping = pings[ping]

    if target_ping["memberId"] and (target_ping["memberId"] != itr.user.id):

        await itr.response.send_message("Permessi mancanti", ephemeral=True)

    else:
        try:
            # print(itr.user.id)

            if not target_channel:
                target_channel = pings[ping]["channelId"]

            if not positive_keywords:

                positive_keywords = pings[ping]["positiveKeywords"]
            else:

                positive_keywords = positive_keywords.split(",")

            if not price:

                price = pings[ping]["price"]

            if not negative_keywords:

                negative_keywords = pings[ping]["negativeKeywords"]

            else:

                negative_keywords = negative_keywords.split(",")

            del pings[ping]
            save_pings(pings)
            # positive_keywords = positive_keywords.split(",")

            updated_pings = add_ping(
                target_channel, positive_keywords, negative_keywords, price, itr.user.id
            )
            await send_embed_log(
                settings["add_log_webhook"], 2, itr.user.id, positive_keywords, price
            )
            pings = updated_pings

            await itr.response.send_message(
                "✅ Keyword Editata correttamente!", ephemeral=True
            )
        except Exception as e:
            print(e)
            traceback.print_exc()


@client.tree.error
async def on_app_command_error(itr: discord.Interaction, error):

    if isinstance(error, app_commands.errors.MissingRole):
        await itr.response.send_message("Error: Permessi mancanti", ephemeral=True)


client.run(settings["bot_token"])