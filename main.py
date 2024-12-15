import os
import discord
import logging
import re
import aiohttp
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View

# Load token from environment variable
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Setting up logging
logging.basicConfig(level=logging.INFO)

# Define the bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Regular expression for URL detection
url_pattern = re.compile(r"https?://\S+")
paywall_keywords = [
    "paywall",
    "subscription",
    "register to view",
    "premium",
    "subscribe",
    "paid content",
    "member access",
]


async def is_paywalled(url):
    # Checks if a URL contains a paywall based on specific keywords.
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    if any(keyword in html.lower() for keyword in paywall_keywords):
                        return True
                return False
    except aiohttp.ClientError as e:
        logging.error(f"Error during HTTP request to {url}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error checking URL {url}: {e}")
    return False


# Context menu command for bypassing paywall
@bot.tree.context_menu(name="Bypass Paywall")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def bypass_paywall(interaction: discord.Interaction, message: discord.Message):
    """Context menu command to find and bypass paywalled links in a message."""
    # Find URLs in the message content
    urls = url_pattern.findall(message.content)
    paywalled_links = []

    # Check each URL for paywall
    for url in urls:
        url = url.rstrip(".,!?)")  # Clean up common punctuation from the URL
        is_paywall = await is_paywalled(url)
        if is_paywall:
            bypass_url = f"https://12ft.io/proxy?q={url}"
            paywalled_links.append(bypass_url)

    if paywalled_links:
        view = View()
        for link in paywalled_links:
            button = Button(label="Open Unpaywalled Link", url=link)
            view.add_item(button)
        await interaction.response.send_message(
            "Here are unpaywalled versions of the links:",
            view=view,
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            "No paywalled links found in this message.", ephemeral=True
        )


@bot.event
async def on_ready():
    # Triggered when the bot is logged in and ready.
    await bot.tree.sync()
    print(f"Bot is ready and logged in as {bot.user}")
    print("Context menu 'Bypass Paywall' is now available")


@bot.event
async def on_message(message):
    # Triggered when a message is received.
    if message.author.bot:
        return

    # Find URLs in the message content
    urls = url_pattern.findall(message.content)
    paywalled_links = []

    for url in urls:
        url = url.rstrip(".,!?)")  # Clean up common punctuation from the URL
        is_paywall = await is_paywalled(url)
        if is_paywall:
            bypass_url = f"https://12ft.io/proxy?q={url}"
            paywalled_links.append(bypass_url)

    if paywalled_links:
        view = View()
        for link in paywalled_links:
            button = Button(label="Open Unpaywalled Link", url=link)
            view.add_item(button)
        await message.reply(
            "Here are unpaywalled versions of the links:",
            mention_author=False,
            view=view,
        )

    await bot.process_commands(message)


if __name__ == "__main__":
    bot.run(TOKEN)
