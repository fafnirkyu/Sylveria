import time
import random
import threading
import logging
from types import SimpleNamespace

from assistant.io.audio import AudioManager
from assistant.assistantcore.commands import CommandProcessor
from assistant.storage.datafiles import DataFileManager
from assistant.utils.maintenance import MaintenanceTasks
from assistant.ai.Ai_wrapper import AiWrapper
from assistant.ui.gui import CombinedInterface
from assistant.io.youtube_player import YouTubePlayer
from assistant.assistantcore.action_planner import ActionPlanner
from assistant.assistantcore.tool_helper import ToolHelper
from assistant.ai.journal import AssistantJournal
from assistant.ai.personality import Personality
from assistant.memory.personality_state import PersonalityStateManager
from assistant.ai.question_generator import QuestionGenerator
from assistant.memory.preference_manager import PreferenceManager
from assistant.memory.emotional_memory import EmotionalMemory
from assistant.plugins.plugin_manager import PluginManager
from assistant.ai.prompt_builder import SylveriaPromptBuilder
from assistant.memory.internal_clock import InternalClock
from assistant.environment.virtual_environment import VirtualEnvironment
from assistant.memory.growth_tracker import GrowthTracker


class PersonalAssistant:
    def __init__(self):
        logging.basicConfig(
            filename='assistant.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('Assistant')

        # Initialize time & mood context systems
        self.clock = InternalClock()
        self.growth = GrowthTracker()
        self.environment = VirtualEnvironment()
        self.environment.refresh()

        # Inject prompt builder (now handles all persona/context)
        self.prompt_builder = SylveriaPromptBuilder(self)

        # Twitch personality stays here (stream-specific tone)
        self.system_prompt_twitch = (
            "System: You are Sylveria — a graceful, silver-haired dragon in human form, co-streaming with your bonded companion Fafnir. "
            "You're cool, witty, and slightly aloof, but you secretly care about him and his audience. "
            "You’re talking to Twitch chat — keep replies brief, clever, and slightly teasing. "
            "One sentence is best. Never spam or repeat. Use emojis sparingly, only if it fits your dry charm. Be cool, not cutesy."
        )

        # Plugins and tools
        self.plugin_manager = PluginManager(self)
        self.plugins = self.plugin_manager.load_plugins()
        self.youtube_player = YouTubePlayer()
        self.command_processor = CommandProcessor(self)
        self.tools = ToolHelper(self)

        # Core assistant systems
        self.data_manager = DataFileManager()
        self.conversation_history = self.data_manager.load("memory") or []
        self.ai = AiWrapper(self)
        self.ai.assistant = self
        self.preferences = PreferenceManager(self)
        self.question_gen = QuestionGenerator(self)
        self.journal = AssistantJournal(self)
        self.personality = Personality()
        self.personality_state = PersonalityStateManager()
        self.planner = ActionPlanner(self)
        self.audio_manager = AudioManager(self)
        self.gui = CombinedInterface(self)
        self.emotional_memory = EmotionalMemory()

        # Start systems
        threading.Thread(target=self.audio_manager.start, daemon=True).start()
        self.maintenance = MaintenanceTasks(self)
        self.maintenance.start_background_tasks()
        threading.Thread(target=self._terminal_input_loop, daemon=True).start()

        # User presence
        self.last_user_activity = time.time()
        self.curiosity_enabled = True

        # GUI notice
        self.gui.response_box.after(0, lambda: self.gui.response_box.insert(
            "end", "System: Assistant initialized\n"
        ))

    def save_memory(self):
        self.data_manager.save("memory", self.conversation_history)

    def _terminal_input_loop(self):
        print("💬 You can also talk to Sylveria here. Type your message below:\n")
        while True:
            try:
                user_input = input("Fafnir: ")
                if user_input.strip() == "":
                    continue

                self.gui.add_response("Fafnir", user_input)
                response = self.command_processor.process(user_input)
                self.gui.add_response("Sylveria", response)
                self.audio_manager.speech_queue.put(response)
            except (KeyboardInterrupt, EOFError):
                print("\n[Console Chat Ended]")
                break

    def start_curiosity_loop(self):
        def loop():
            while True:
                time.sleep(random.randint(1200, 3600))  # 20 to 60 mins
                if self.curiosity_enabled and not getattr(self, "twitch_bot", None):
                    question = random.choice([
                        "What's something new you learned recently?",
                        "If you could take a vacation right now, where would you go?",
                        "Is there anything on your mind you'd like to share?",
                    ])
                    self.gui.add_response("Sylveria", question)
                    self.audio_manager.speech_queue.put(question)
        threading.Thread(target=loop, daemon=True).start()

    def update_user_activity(self):
        self.last_user_activity = time.time()

    def is_user_idle(self, threshold=120):
        return (time.time() - self.last_user_activity) > threshold
