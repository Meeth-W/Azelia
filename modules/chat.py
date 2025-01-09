import discord
from discord.ext import commands
from discord.ext.commands import Context

from functions.config import ConfigManager
from chat import ChatHandler, get_about, save_about, get_history, save_history

config = ConfigManager('config.yml')

class Chat(commands.Cog, name="Chat"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.content.startswith(config.fetch('prefix')):
            return
        if message.channel.id != config.fetch('channel_id'):
            return

        chat_handler = ChatHandler()
        await chat_handler.chat(message)

    @commands.hybrid_command(
        name="description",
        description="Set up the bot's description.",
    )
    async def setDescription(self, context: Context, *, desc: str) -> None:
        about = get_about()
        about['description'] = desc
        save_about(about)
        await context.send(f"Description updated to: {desc}")

    @commands.hybrid_command(
        name="reset",
        description="Reset the bot's conversation history",
    )
    async def reset(self, context: Context) -> None:
        history = get_history()

        history['archived'].append(history['current'])
        history['current'] = {}
        save_history(history)

        await context.send("Conversation history has been reset.")
    


async def setup(bot) -> None:
    await bot.add_cog(Chat(bot))
