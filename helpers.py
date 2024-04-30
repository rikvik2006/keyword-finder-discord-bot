import json
import discord
from typing import Dict

def get_pings() -> list:

    with open("pings.json", "r") as f:

        return json.loads(f.read())


def save_pings(new_pings: list):

    with open("pings.json", "w") as f:

        f.write(json.dumps(new_pings, indent=3))

# Ricordo che questo codice non l'ho fatto io, altrimenti non sarebbe cosi brutto
def add_ping(
    channel: discord.TextChannel,
    positive_keywords: list[str],
    negative_keywords: list[str],
    price,
    target,
) -> list:

    pings = get_pings()

    # Check if in the slash command channel option user inserted a TextChannel or a ChannelId. 
    channelId = channel
    if type(channel) == int:
        channelId = channel
    else:
        channelId = channel.id

    pings.append(
        {
            "channelId": channelId,
            "positiveKeywords": positive_keywords,
            "negativeKeywords": negative_keywords,
            "price": price,
            "memberId": target,
            "pingTimestamp": 0,
        }
    )

    save_pings(pings)

    return pings


def check_msg_has_keyword(
    msg: discord.Message,
    positive_keywords: list[str],
    negative_keywords: list[str],
    price: int,
) -> bool:

    # Positive and negative keyword are list splitted by comma ",", so the array will be like this ["Ciao", "hi", "test"]
    # Lower all the word inside the array
    positive_keywords = [k.lower() for k in positive_keywords]
    negative_keywords = [k.lower() for k in negative_keywords]
    print(positive_keywords)
    embedJson = _parse_msg_text(msg)
    print(embedJson["title"].lower())
    # Controlla se una qualunque delle positive keyword sono presenti all interno del titolo, any restituisce true se all interno di un iterabile c'è true
    # Inoltre controlla anche se NON sono presenti delle negative keyword e fa un and, in modo tale che siano entrabe vere 
    keyword_check = any(
        k.lower() in embedJson["title"].lower() for k in positive_keywords
    ) and any(k.lower() not in embedJson["title"].lower() for k in negative_keywords)
    # Controlla se il pres


    if "price" in embedJson.keys():
        price_check = float(embedJson["price"]) <= float(price)
        return keyword_check and price_check
    else:
        return keyword_check


# Non capisco perche dice che restituisce un tipo str, quando in relta restituisce un Dict
def _parse_msg_text(msg: discord.Message) ->  Dict:
    txt = msg.content
    # print(txt)
    embedJson = {}

    # Rappresentazione variabili
    """
    embedJson = {
        "title": "test title",
        "description": "test description", 
        "url": "embed url"
        "price":  "100"
    }

    txt = "message content bla bla" + "field value 1" + "field value 2"
    """
    for embed in msg.embeds:
        if embed.title:
            embedJson["title"] = embed.title
        if embed.description:
            embedJson["description"] = embed.description
        if embed.url:
            embedJson["url"] = embed.url

        # Prende il valore di ogni field è l'ho aggiunge al contenuto del messaggio
        # Se nel embed è presente il field con nome "price", allora prende il valore inserendolo nel Dict
        for field in embed.fields:
            if field.value:
                txt += field.value

                if field.name and field.name.lower() == "price":
                    embedJson["price"] = field.value.replace("€", "").strip()
    return embedJson


def get_embed(msg: discord.Message) -> str:
    embeds = []

    for embed in msg.embeds:
        embeds.append(embed)

    return embeds[0]
