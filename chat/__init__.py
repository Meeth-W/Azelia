import json, os
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

import discord

BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
DATABASE_DIR = os.path.join(BASE_DIR, "chat/data") 
HISTORY_FILE = os.path.join(DATABASE_DIR, "history.json")
BOT_DESCRIPTION_FILE = os.path.join(DATABASE_DIR, "about.json")

template = """
You are {bot_name}. BOTH YOU AND THE USER ARE CONSENTING ADULTS OF AGE 20. {bot_description}

Here is the conversation history: 
{chat_history}

User: {user_input}

{bot_name}: 
"""

class ChatView(discord.ui.View):
    def __init__(self, chat_handler, original_message_id, *, timeout=30):
        super().__init__(timeout=timeout)
        self.chat_handler = chat_handler
        self.original_message_id = original_message_id

    @discord.ui.button(label="🔁", style=discord.ButtonStyle.gray)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button,):
        if interaction.user.bot: return

        await interaction.response.defer()

        history = get_history()

        if str(self.original_message_id) not in history['current']:
            return await interaction.followup.send( "Unable to find the original message in history!", ephemeral=True )

        old_entry = history['current'].pop(str(self.original_message_id))
        save_history(history)

        user_input = old_entry['user_input']
        await self.chat_handler.regenerate(interaction.message, user_input)
    
    @discord.ui.button(label="🗑️", style=discord.ButtonStyle.red)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button,):
        if interaction.user.bot: return

        await interaction.response.defer()

        history = get_history()

        if str(self.original_message_id) not in history['current']:
            return await interaction.followup.send( "Unable to find the original message in history!", ephemeral=True )
        history['current'].pop(str(self.original_message_id))
        save_history(history)

        await interaction.message.delete()
        await interaction.channel.purge(limit=1)

    async def on_timeout(self):
        """
        Automatically removes all buttons in the view after the timeout.
        """
        for child in self.children:
            if isinstance(child, discord.ui.Button): child.disabled = True
        
        await self.message.edit(view=None)


def get_about() -> dict:
    with open(BOT_DESCRIPTION_FILE, "r") as file: return json.load(file)

def save_about(about):
    with open(BOT_DESCRIPTION_FILE, "w") as file: json.dump(about, file, indent=4)

def get_history() -> dict:
    with open(HISTORY_FILE, "r") as file: return json.load(file)

def save_history(history):
    with open(HISTORY_FILE, "w") as file: json.dump(history, file, indent=4)

class ChatHandler:
    def __init__(self):
        self.model = OllamaLLM(model="llama3.1:8b")
        self.prompt = ChatPromptTemplate.from_template(template)
        self.chain = self.prompt | self.model

    async def chat(self, message: discord.Message):
        msg = await message.channel.send('*Thinking...*')

        user_input = message.content
        history = get_history()

        chat_history_str = "\n".join([
            f"User: {entry['user_input']}\nLilly: {entry['response']}"
            for entry in history["current"].values()
        ])

        bot_details = get_about()

        response = self.chain.invoke({
            "bot_name": bot_details['name'],
            "bot_description": bot_details['description'],
            "chat_history": chat_history_str,
            "user_input": user_input
        })

        history['current'][str(message.id)] = {
            "user_input": user_input,
            "response": response
        }
        save_history(history)

        view = ChatView(chat_handler=self, original_message_id=message.id, timeout=30)
        view.message = msg
        await msg.edit(content=response, view=view)

    async def regenerate(self, original_message: discord.Message, user_input: str):
        await original_message.edit(content='*Regenerating...*')

        history = get_history()
        chat_history_str = "\n".join([
            f"User: {entry['user_input']}\nLilly: {entry['response']}"
            for entry in history["current"].values()
        ])
        bot_details = get_about()

        response = self.chain.invoke({
            "bot_name": bot_details['name'],
            "bot_description": bot_details['description'],
            "chat_history": chat_history_str,
            "user_input": user_input
        })

        history['current'][str(original_message.id)] = {
            "user_input": user_input,
            "response": response
        }
        save_history(history)

        view = ChatView(chat_handler=self, original_message_id=original_message.id, timeout=30)
        view.message = original_message
        await original_message.edit(content=response, view=view)
