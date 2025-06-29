import threading

class MyPlugin:
    def __init__(self, assistant, config=None):
        self.assistant = assistant
        self.config = config or {}
        print("[MyPlugin] Plugin initialized.")

    def start(self):
        # Optional threaded background task
        print("[MyPlugin] Background task started.")
        threading.Thread(target=self.run_loop, daemon=True).start()

    def run_loop(self):
        while True:
            # Replace with real logic
            print("[MyPlugin] Running background task...")
            break

    def do_something(self):
        return "Hello from MyPlugin!"

#Required plugin loader
def load_plugin(assistant, config=None):
    plugin = MyPlugin(assistant, config)
    plugin.start()
    return plugin
