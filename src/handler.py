import logging
import os
import datetime
import time
import re

import discord
from dotenv import load_dotenv

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

load_dotenv()
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD")
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_BOT_ID = os.getenv('DISCORD_BOT_ID')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


def extract_emojis(message: discord.Message) -> list:
    """Extract custom emojis from message text and reactions to a list. Elements may repeat multiple times."""
    # Extract emojis from the message
    found_emojis = re.findall(r"<:[a-zA-Z0-9\-_]+:[0-9]+>", message.content)

    # Extract emojis from reactions
    if len(message.reactions) > 0:
        for reaction in message.reactions:
            emoji_text = str(reaction.emoji)
            emoji_match = re.search(r"<.+>", emoji_text)
            if emoji_match is None:
                continue

            for i in range(reaction.count):
                found_emojis.append(emoji_text)

    return found_emojis


def count_emojis(emoji_list: list) -> list:
    """Return a sorted list of emoji usage tuples: [emoji_name, count]"""
    emoji_usage = dict()
    for emoji in emoji_list:
        if emoji in emoji_usage:
            emoji_usage[emoji] += 1
        else:
            emoji_usage[emoji] = 1

    return sorted(emoji_usage.items(), key=lambda x: x[1], reverse=True)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=DISCORD_GUILD_ID))
    _logger.info("Ready!")


@tree.command(name="emoji_count", description="Test Command", guild=discord.Object(id=DISCORD_GUILD_ID))
async def generate_emoji_count_report(interaction, days: int):
    print(f"Received request from channel: {interaction.channel.name}. Day count: {days}")
    all_emojis = list()
    before_30_days = datetime.datetime.fromtimestamp(time.time() - days * 86400)
    async for response in interaction.channel.history(limit=10000, after=before_30_days):
        if str(response.author.id) == DISCORD_BOT_ID:
            continue
        all_emojis.extend(extract_emojis(response))

    emoji_usage = count_emojis(all_emojis)
    message = f"Emoji usage statistics for the last {days} days:\n"
    for item in emoji_usage:
        message += f"{item[0]} x {item[1]}\n"

    await interaction.response.send_message(message)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


if __name__ == "__main__":
    client.run(DISCORD_BOT_TOKEN)
