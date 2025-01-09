import yaml
import json

class ConfigManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.config_data = None
        self._load_config()

    def _load_config(self):
        """Load the YAML configuration file."""
        with open(self.file_path, 'r') as file:
            self.config_data = yaml.safe_load(file)

    def save_config(self):
        """Save the current configuration data to the YAML file."""
        with open(self.file_path, 'w') as file:
            yaml.safe_dump(self.config_data, file)

    def fetch(self, key, default=None):
        """Get a value from the configuration data."""
        return self.config_data.get(key, default)

    def push(self, key, value):
        """Set a value in the configuration data."""
        self.config_data[key] = value
        self.save_config()

    def purge(self, key):
        """Delete a key from the configuration data."""
        if key in self.config_data:
            del self.config_data[key]
            self.save_config()

    def get_json(self):
        """Convert the configuration data to a JSON string."""
        return json.dumps(self.config_data, indent=4)


import json
import os
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate


BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
DATABASE_DIR = os.path.join(BASE_DIR, "database") 
HISTORY_FILE = os.path.join(DATABASE_DIR, "chat_history.json")
BOT_DESCRIPTION_FILE = os.path.join(DATABASE_DIR, "bot_description.json")

template = """
You are Oliver. {bot_description}

Here is the conversation history: 
{chat_history}

User: {user_input}

Oliver: 
"""

class OllamaHandler:
    def __init__(self):
        self.chat_history = []  
        self.bot_description = "A helpful and friendly AI assistant."  

        os.makedirs(DATABASE_DIR, exist_ok=True)

        model = OllamaLLM(model="llama3.1:8b")
        prompt = ChatPromptTemplate.from_template(template)
        self.chain = prompt | model

        self._load_history()
        self._load_bot_description()

    def _load_history(self):
        """Loads chat history from a local JSON file."""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as file:
                self.chat_history = json.load(file)
        else:
            self.chat_history = []

    def _load_bot_description(self):
        """Loads the bot description from a local JSON file."""
        if os.path.exists(BOT_DESCRIPTION_FILE):
            with open(BOT_DESCRIPTION_FILE, "r") as file:
                self.bot_description = json.load(file).get("description", self.bot_description)

    def _save_history(self):
        """Saves chat history to a local JSON file."""
        with open(HISTORY_FILE, "w") as file:
            json.dump(self.chat_history, file, indent=4)

    def chat(self, user_input):
        """Chat with the bot."""
        self.chat_history.append({"user": user_input})

        history_str = "\n".join(
            f"User: {entry['user']}\nLilly: {entry['bot']}" if "bot" in entry else f"User: {entry['user']}"
            for entry in self.chat_history
        )

        try:
            response = self.chain.invoke({
                "bot_description": self.bot_description,
                "chat_history": history_str,
                "user_input": user_input,
            })

            self.chat_history[-1]["bot"] = response
            self._save_history()
            return response
        except Exception as e:
            return f"Error: {str(e)}"

    def regenerate(self):
        """Remove the last bot input from the chat history and regenerate the bot response."""
        if self.chat_history and "bot" in self.chat_history[-1]:
            self.chat_history[-1].pop("bot", None)

            try:
                history_str = "\n".join(
                    f"User: {entry['user']}\nLilly: {entry['bot']}" if "bot" in entry else f"User: {entry['user']}"
                    for entry in self.chat_history
                )
                user_input = self.chat_history[-1]["user"]
                response = self.chain.invoke({
                    "bot_description": self.bot_description,
                    "chat_history": history_str,
                    "user_input": user_input,
                })

                self.chat_history[-1]["bot"] = response
                self._save_history()
                return response
            except Exception as e:
                return f"Error: {str(e)}"
        else:
            return "No message to regenerate."

    def reset(self):
        """Reset the chat history."""
        self.chat_history = []
        self._save_history()
        self._load_bot_description()
        return "Chat history has been reset."

