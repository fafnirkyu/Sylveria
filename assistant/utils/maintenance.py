import threading
import time

class MaintenanceTasks:
    def __init__(self, assistant):
        self.assistant = assistant

    def start_background_tasks(self):
        threading.Thread(target=self._self_talk_loop, daemon=True).start()

    def _self_talk_loop(self):
        while True:
            time.sleep(600)
            message = ""
            self.assistant.gui.add_response("Sylveria", message)
            self.assistant.audio_manager.speech_queue.put(message)