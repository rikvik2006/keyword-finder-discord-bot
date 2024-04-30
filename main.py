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

client = commands.Bot(command_prefix="!", intents=Intents(65059))

with open("settings.json", "r") as file:
    settings = json.load(file)

pings = get_pings()


async def send_embed_log(webhook: str, log: int, target: int, kws: str, price):
    if log == 1:
        title = "Kw Aggiunta"
    elif log == 2:
        title = "Kw Editata"
    else:
        title = "Kw Rimossa"
    try:
        webhook = DiscordWebhook(
            url=webhook,
            username="HUNTERS",
            avatar_url="https://imgur.com/eI3OKkX",
        )
        embed = DiscordEmbed(title=title, color=16777215)
        embed.set_footer(
            url="https://imgur.com/eI3OKkX",
            icon_url="https://imgur.com/eI3OKkX",
            text="HUNTERS",
        )
        embed.set_timestamp()
        embed.set_author(
            name="Logger",
            icon_url="https://imgur.com/eI3OKkX",
        )
        embed.add_embed_field(name="MemberId", value=str(target), inline=False)
        embed.add_embed_field(name="Kw", value=str(kws), inline=True)
        embed.add_embed_field(name="Price", value=str(price), inline=True)
        webhook.add_embed(embed)
        webhook.execute()
    except Exception as e:
        print(f"Failed to Sent Notification to Discord: {e}")


async def send_embed_ping(webhook: str, embed, target: int, kws: str, price):
    try:
        webhook = DiscordWebhook(
            url=webhook,
            username="HUNTERS",
            avatar_url="https://imgur.com/eI3OKkX",
        )
        embed = DiscordEmbed(title="Kw Ping", color=16777215)
        embed.set_footer(
            url="https://imgur.com/eI3OKkX",
            icon_url="https://imgur.com/eI3OKkX",
            text="HUNTERS",
        )
        embed.set_timestamp()
        embed.set_author(
            name="Logger",
            icon_url="https://imgur.com/eI3OKkX",
        )
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

    await client.tree.sync()


@client.event
async def on_message(message: discord.Message):

    if message.author.name != client.user.name:

        msg_channel = message.channel.id
        pings_updated = False

        mentions = []

        for ping in pings:

            pkws: str = ping["positiveKeywords"]
            nkws: str = ping["negativeKeywords"]
            price: int = ping["price"]
            timestamp: int = ping["pingTimestamp"]
            target = get(message.guild.members, id=ping["memberId"])
            channel: int = ping["channelId"]

            if msg_channel == channel:

                now = int(time.time())

                if check_msg_has_keyword(message, pkws, nkws, price):
                    pings_updated = True
                    print("ping")
                    ping["pingTimestamp"] = now

                    await DMChannel.send(target, embed=get_embed(message))
                    await send_embed_ping(
                        settings["ping_log_webhook"],
                        get_embed(message),
                        target,
                        pkws,
                        price,
                    )
                else:
                    print("No ping")

        if pings_updated:
            save_pings(pings)

    await client.process_commands(message)


@client.tree.command(name="add_kw", description="Aggiungi una nuova kw.")
@app_commands.checks.has_role(str(settings["roleId"]))
async def add_new_ping(
    itr: discord.Interaction,
    target_channel: discord.TextChannel,
    positive_keywords: str,
    price: int,
    negative_keywords: str = None,
):

    global pings
    if not negative_keywords:

        negative_keywords = []

    else:

        negative_keywords = negative_keywords.split(",")

    positive_keywords = positive_keywords.split(",")

    updated_pings = add_ping(
        target_channel, positive_keywords, negative_keywords, price, itr.user.id
    )
    await send_embed_log(
        settings["ping_log_webhook"], 1, itr.user.id, positive_keywords, price
    )
    pings = updated_pings

    await itr.response.send_message(
        "✅ Keyword aggiunta correttamente!", ephemeral=True
    )


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


@client.tree.command(name="delete_kw", description="Rimuovi una kw salvata.")
@app_commands.autocomplete(ping=delete_ping_autocomplete)
@app_commands.checks.has_role(str(settings["roleId"]))
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


@client.tree.command(name="edit_kw", description="Edita una kw salvata.")
@app_commands.autocomplete(ping=delete_ping_autocomplete)
@app_commands.checks.has_role(str(settings["roleId"]))
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
                settings["ping_log_webhook"], 2, itr.user.id, positive_keywords, price
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
        await itr.response.send_message("Permessi mancanti", ephemeral=True)


client.run(settings["bot_token"])
