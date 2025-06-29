import os
import importlib
import json
import sys

PLUGINS_DIR = os.path.dirname(__file__)
ENABLED_PLUGINS_FILE = os.path.join(PLUGINS_DIR, "enabled_plugins.json")


class PluginManager:
    def __init__(self, assistant):
        self.assistant = assistant
        self.plugins_dir = PLUGINS_DIR
        self.enabled_plugins_file = ENABLED_PLUGINS_FILE
        self.loaded_plugins = {}

    def list_all_plugins(self):
        return [
            f[:-3]
            for f in os.listdir(self.plugins_dir)
            if f.endswith(".py") and f not in ("__init__.py", "plugin_manager.py")
        ]

    def load_plugins(self):
        """Loads plugins from enabled_plugins.json and calls their `start()`."""
        if not os.path.exists(self.enabled_plugins_file):
            with open(self.enabled_plugins_file, "w", encoding="utf-8") as f:
                json.dump([], f)

        try:
            with open(self.enabled_plugins_file, "r", encoding="utf-8") as f:
                enabled = json.load(f)
        except Exception as e:
            print(f"[Plugin Manager Error] Failed to read enabled plugins: {e}")
            enabled = []

        self.loaded_plugins = {}

        for plugin_name in enabled:
            try:
                module_name = f"assistant.plugins.{plugin_name}"
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    module = sys.modules[module_name]
                else:
                    module = importlib.import_module(module_name)

                if hasattr(module, "start"):
                    result = module.start(self.assistant)
                    self.loaded_plugins[plugin_name] = result
                    print(f"[Plugin Loaded] {plugin_name}")
                else:
                    print(f"[Plugin Skipped] {plugin_name} has no start() method")

            except Exception as e:
                print(f"[Plugin Error] {plugin_name}: {e}")

        self.assistant.plugins = self.loaded_plugins
        return self.loaded_plugins

    def reload_plugins(self):
        print("[Plugin Manager] Reloading plugins...")
        return self.load_plugins()
