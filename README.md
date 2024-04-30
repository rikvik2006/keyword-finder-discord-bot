# Keyword Finder discord bot

This bot is able to find keywords within posts and embeds them on Discord. If the keyword is found, the bot sends a DM to the recipient containing the message with the keyword.

## ⚠️ Warning

This code is not mine, I have only edited it and made fixes, so do not judge me on the quality of the code in this project.

## 📝 Setup

1. Install the required packages using `pip install -r requirements.txt`
2. Copy the `ping.json.template` file and rename it to `ping.json`
3. Copy the `settings.json.template` file and rename it to `settings.json`
4. Fill the `settings.json` file with this information:
    1. `bot_token`: Your bot token
    2. `roleId`: Only users with this role will be able to use the bot
    3. `add_log_webhook`: The webhook to log the bot's actions
    4. `ping_log_webhook`: The webhook to log all messages containing keywords set by server users
