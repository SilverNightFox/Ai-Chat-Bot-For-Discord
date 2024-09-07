import discord
from discord.ext import commands
from collections import defaultdict, deque
import asyncio
import datetime
import re
import emoji
import aiohttp
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
import unicodedata
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration - Use environment variables for security
DISCORD_BOT_TOKEN = ('your-token-here')
GEMINI_API_KEY = ('your-key-here')

if not DISCORD_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("DISCORD_BOT_TOKEN or GEMINI_API_KEY not set in environment variables")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# Define intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Default response if Gemini API fails
DEFAULT_RESPONSE = "Sorry, I couldn't answer this question."

# File to store chat history
HISTORY_FILE = 'chat_history.json'

# Load chat history from file
def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as file:
                if os.stat(HISTORY_FILE).st_size == 0:
                    return {}
                return json.load(file)
        except json.JSONDecodeError:
            logging.error("JSON decode error: file might be corrupted")
            return {}
        except Exception as e:
            logging.error(f"Error loading chat history: {e}")
            return {}
    return {}

# Save chat history to file
def save_chat_history(chat_history):
    try:
        with open(HISTORY_FILE, 'w') as file:
            json.dump(chat_history, file, indent=4)
    except Exception as e:
        logging.error(f"Error saving chat history: {e}")

# Initialize chat history
chat_history = load_chat_history()

bot = commands.Bot(command_prefix='!', intents=intents)

status_list = [
    discord.Game(name="LolbitFurry's Chat Bot"),
    discord.Activity(type=discord.ActivityType.playing, name="I'm Ready To Chat With Fluffy Buddies ^w^"),
    discord.Activity(type=discord.ActivityType.listening, name="Foxy Land"),
    discord.Activity(type=discord.ActivityType.watching, name="OwO What's This?"),
]
@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    change_status.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = str(message.author.id)

    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append(message.content)
    save_chat_history(chat_history)

    if bot.user.mentioned_in(message):
        content = message.content
        mention = message.author.mention

        history_text = "\n".join(chat_history[user_id])
        prompt = (
            f"You Are a Furry Young Fox And You're Lovely And Kind, Patient, Cute, Understanding. "
            f"Remember all previous chats. Here is the chat history:\n{history_text}\n"
            f"Respond to the following message from {mention}: {content}"
        )

        if content.strip():
            try:
                response = await ask_gemini(prompt)
                await message.channel.send(f"{mention} {response}")
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                await message.channel.send(f"{mention} Bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

async def ask_gemini(prompt):
    try:
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: model.generate_content(prompt))
        if response and hasattr(response, 'text'):
            return response.text
        else:
            logging.info("API response: %s", response)
            return DEFAULT_RESPONSE
    except Exception as e:
        logging.error("API exception: %s", e)
        return DEFAULT_RESPONSE

@tasks.loop(seconds=60)
async def change_status():
    await bot.change_presence(activity=status_list[change_status.current_loop % len(status_list)])

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)