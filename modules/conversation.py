import discord, json
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from functions import ConfigManager, OllamaHandler, BOT_DESCRIPTION_FILE

config = ConfigManager('config.yml')

ollama_handler = OllamaHandler()


class Conversation(commands.Cog, name="conversation"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="description",
        description="Set up the bot's description.",
    )
    @app_commands.describe(desc="The character description of the bot.")
    async def setDescription(self, context: Context, *, desc: str) -> None:
        """
        Set up the bot's description.

        :param context: The hybrid command context.
        :param desc: The character description of the bot.
        """
        ollama_handler.bot_description = desc
        with open(BOT_DESCRIPTION_FILE, "w") as file:
            file.write(json.dumps({"description": desc}, indent=4))

        await context.send(
            embed=discord.Embed(
                title="Description Updated",
                description=f"The bot's description has been updated!",
                color=discord.Color.green(),
            )
        )

    @commands.hybrid_command(
        name="reset",
        description="Reset the bot's conversation history and clear the channel.",
    )
    async def reset(self, context: Context) -> None:
        """
        Reset the bot's conversation history and clear the channel.

        :param context: The hybrid command context.
        """
        ollama_handler.reset()

        channel_id = config.fetch("channel_id")
        channel = self.bot.get_channel(channel_id)

        if channel:
            async for message in channel.history(limit=100):
                await message.delete()

            await context.send(
                embed=discord.Embed(
                    title="Conversation Reset",
                    description="The bot's conversation history has been reset, and the channel has been cleared.",
                    color=discord.Color.blue(),
                )
            )
        else:
            await context.send(
                embed=discord.Embed(
                    title="Error",
                    description="Failed to fetch the channel. Ensure the `channel_id` is configured correctly in `config.yml`.",
                    color=discord.Color.red(),
                )
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Conversation(bot))
