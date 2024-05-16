import json
import discord
import re
from typing import Dict, List


def get_pings() -> list:

    with open("pings.json", "r") as f:

        return json.loads(f.read())


def save_pings(new_pings: list):

    with open("pings.json", "w") as f:

        f.write(json.dumps(new_pings, indent=3))


# Ricordo che questo codice non l'ho fatto io, altrimenti non sarebbe cosi brutto
def add_ping(
    uuid: str,
    channel: discord.TextChannel | str,
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
    if channel == "server":
        channelId = "server"
    else:
        channelId = channel.id

    pings.append(
        {
            "keywordId": uuid, # TODO: Generate a UUID
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
    price: int | None,
) -> bool:

    # Positive and negative keyword are list splitted by comma ",", so the array will be like this ["Ciao", "hi", "test"]
    # Lower all the word inside the array
    positive_keywords = [k.lower() for k in positive_keywords]
    negative_keywords = [k.lower() for k in negative_keywords]

    print("🟢 Positive keywords", positive_keywords)
    print("🔴 Negative  keywords", negative_keywords)
    embedJson = _parse_msg_text(msg)

    # Controlla se una qualunque delle positive keyword sono presenti all interno del titolo, any restituisce true se all interno di un iterabile c'è true
    # Inoltre controlla anche se NON sono presenti delle negative keyword e fa un and, in modo tale che siano entrabe vere
    # if len(negative_keywords) > 0:
    #     title_check = any(
    #         k.lower() in embedJson["title"].lower() for k in positive_keywords
    #     ) and any(k.lower() not in embedJson["title"].lower() for k in negative_keywords)
    #     print("🚀 ~ title_check:", title_check)
    #     # Controlla se il pres

    #     description_check = any(
    #         k.lower() in embedJson["description"].lower() for k in positive_keywords
    #     ) and any(k.lower() not in embedJson["description"].lower() for k in negative_keywords)
    #     print("🚀 ~ description_check:", description_check)

    #     txt_pos_check = [k.lower() in embedJson["txt"].lower() for k in positive_keywords]
    #     txt_neg_check = [k.lower() not in embedJson["txt"].lower() for k in negative_keywords]
    #     txt_check = any(txt_pos_check) and any(txt_neg_check)
    #     print("🚀 ~ txt_check:", txt_check)

    #     url_check = any(
    #         k.lower() in embedJson["url"].lower() for k in positive_keywords
    #     ) and any(k.lower() not in embedJson["url"].lower() for k in negative_keywords)
    #     print("🚀 ~ url_check:", url_check)
    # else:
    #     title_check = any(k.lower() in embedJson["title"].lower() for k in positive_keywords)
    #     description_check = any(k.lower() in embedJson["description"].lower() for k  in positive_keywords)
    #     txt_check = any(k.lower() in embedJson["txt"].lower() for k in positive_keywords)
    #     url_check = any(k.lower() in embedJson["url"].lower() for k in positive_keywords)


    # if price and len(embedJson["price"]) > 0:
    #     # price_check = float(embedJson["price"].split()) <= float(price)
    #     price_check = any(list(map(lambda x: float(x) <= float(price), embedJson["price"].split("|"))))
    #     print("🚀 ~ price_check:", price_check)
    #     return (title_check or description_check or txt_check or url_check) and price_check
   
    # return title_check or description_check or txt_check or url_check

    ping_condition = check_msg_text_keyword_regex(embedJson, positive_keywords, negative_keywords, price)
    return ping_condition


# Non capisco perche dice che restituisce un tipo str, quando in relta restituisce un Dict
def _parse_msg_text(msg: discord.Message) -> Dict[str, str]:
    txt = msg.content.lower()
    # print(txt)
    embedJson = {
        "title": "",
        "description": "",
        "url": "",
        "txt": txt,
        "price": "",
    }

    # Rappresentazione variabili
    """
    embedJson = {
        "title": "test title",
        "description": "test description", 
        "url": "embed url"
        "txt": "message content bla bla" + "field value 1" + "field value 2",
        "price":  "100"
    }
    """
    for embed in msg.embeds:
        if embed.title:
            embedJson["title"] += embed.title
        if embed.description:
            embedJson["description"] += embed.description
        if embed.url:
            embedJson["url"] += embed.url

        # Prende il valore di ogni field è l'ho aggiunge al contenuto del messaggio
        # Se nel embed è presente il field con nome "price", allora prende il valore inserendolo nel Dict
        for field in embed.fields:
            if field.value:
                embedJson["txt"] += f" {field.value}"

                if field.name and field.name.lower() == "price":
                    embedJson["price"] += f"{field.value.replace('€', '').replace('$', '').strip()}|"

    embedJson["txt"] = embedJson["txt"].strip()
    return embedJson

# TODO: Use regex to check if the keyword is present in the message
def check_msg_text_keyword_regex(
    msg_text: Dict[str, str], 
    positive_keywords: list[str], 
    negative_keywords: list[str], 
    price: float | None
) -> bool:
    parsed_embed_keys = msg_text.keys()
    positive_keywords = [k.lower() for k in positive_keywords]
    negative_keywords = [k.lower() for k in negative_keywords]

    pings_condition: List[bool] = []
    price_condition: bool = None
    for key in parsed_embed_keys:
        if key == "price" and len(msg_text["price"]) > 0 and price:
            # Split the price string by "|" and remove empty strings
            filtered_price_list = list(filter(lambda x: x != "", msg_text["price"].split("|")))
            # Check if  any of the price is less than the price set by the user
            ping_condition = any(list(map(lambda x: float(x) <= float(price), filtered_price_list)))
            if ping_condition:
                price_condition = True

        else:
            if len(negative_keywords) > 0:
                # Check if all positive keywords are present in the message and none of the negative keywords are present
                # ping_condition = all(k.lower() in msg_text[key].lower() for k in positive_keywords) and any(k.lower() not in msg_text[key].lower() for k in negative_keywords)
                # if ping_condition:
                #     pings_condition.append(True)

                ping_condition = True
                for keyword in positive_keywords:
                    regex = fr"\b{keyword}\b"
                    if not re.search(regex, msg_text[key], re.IGNORECASE):
                        ping_condition = False
                        break
                    
                found_negative_keyword: List[bool] = []
                for keyword in negative_keywords:
                    regex = fr"\b{keyword}\b"
                    if re.search(regex, msg_text[key], re.IGNORECASE):
                        found_negative_keyword.append(True)
                    else:
                        found_negative_keyword.append(False)
                contain_all_negative_keywords = all(found_negative_keyword)

                ping_condition = ping_condition and not contain_all_negative_keywords 
                pings_condition.append(ping_condition)        
            else:
                ping_condition = True
                for keyword in positive_keywords:
                    regex = fr"\b{keyword}\b"
                    if not re.search(regex, msg_text[key], re.IGNORECASE):
                        ping_condition = False
                        break
                    
                pings_condition.append(ping_condition) 
                
    if price_condition:
        return any(pings_condition) and price_condition
    else:
        return any(pings_condition)


def get_embed(msg: discord.Message) -> str:
    embeds = []

    for embed in msg.embeds:
        embeds.append(embed)

    return embeds

def remove_space(keyword: str) -> str:
    return keyword.strip()

def format_keywords(keywords_str: str) -> List[str]:
    keywords = list(map(remove_space, keywords_str.strip().split(",")))
    keywords = list(filter(lambda x: x != "", keywords))
    keywords = list(filter(lambda x: len(x) > 0, keywords))
    keywords = list(map(lambda x: x.lower(), keywords))

    return keywords
