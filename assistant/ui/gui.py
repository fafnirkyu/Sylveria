import tkinter as tk
from tkinter import ttk, Toplevel, BooleanVar, Checkbutton, Button
from PIL import Image, ImageTk
import threading
import time
import os
import json
from assistant.plugins.plugin_manager import ENABLED_PLUGINS_FILE



class CombinedInterface:
    def __init__(self, assistant):
        self.assistant = assistant
        self.root = tk.Tk()
        self.root.title("Sylveria - Assistant")
        self.root.geometry("400x800")
        self.root.configure(bg="#1a1a1a")
        self.root.resizable(False, False)

        self.last_activity = time.time()
        self.sleepy = False

        self._load_images()
        self._setup_gui()
        threading.Thread(target=self._idle_check_loop, daemon=True).start()

    def _load_images(self):
        try:
            self.gui_photo_idle = ImageTk.PhotoImage(Image.open("assets/avatar_idle.png").resize((360, 480)))
            self.gui_photo_talking = ImageTk.PhotoImage(Image.open("assets/avatar_talking.png").resize((360, 480)))
            self.gui_photo_sleepy = ImageTk.PhotoImage(Image.open("assets/avatar_sleepy.png").resize((360, 480)))
        except Exception as e:
            print(f"[Avatar Error] Could not load one or more images: {e}")
            self.gui_photo_idle = self.gui_photo_talking = self.gui_photo_sleepy = None

    def _setup_gui(self):
        self.gui_label = tk.Label(self.root, image=self.gui_photo_idle, bg="#1a1a1a")
        self.gui_label.pack(pady=(10, 0))

        timer_frame = tk.Frame(self.root, bg="#1a1a1a")
        timer_frame.pack(pady=(5, 5))

        self.timer_entry = tk.Entry(timer_frame, width=25, font=("Segoe UI", 10))
        self.timer_entry.insert(0, "set a timer for 10 minutes")
        self.timer_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(timer_frame, text="Set Timer", command=self.set_timer, bg="#5c5c5c", fg="white").pack(side=tk.LEFT)

        self.response_log = tk.Text(self.root, height=6, width=48, wrap="word", bg="#101010", fg="white", font=("Segoe UI", 10))
        self.response_log.pack(pady=(10, 5))
        self.response_log.insert(tk.END, "🔸 Sylveria is online.\n")
        self.response_log.config(state=tk.DISABLED)

        input_frame = tk.Frame(self.root, bg="#1a1a1a")
        input_frame.pack(pady=(5, 10))

        self.entry = tk.Entry(input_frame, width=30, font=("Segoe UI", 11), bg="#2a2a2a", fg="white", insertbackground="white")
        self.entry.pack(side=tk.LEFT, padx=(5, 5))

        self.send_button = tk.Button(input_frame, text="Send", command=self.send_command, bg="#444", fg="white", relief="flat")
        self.send_button.pack(side=tk.LEFT)

        script_frame = tk.Frame(self.root, bg="#1a1a1a")
        script_frame.pack(pady=(0, 5))

        self.script_var = tk.StringVar(self.root)
        self.script_dropdown = ttk.Combobox(script_frame, textvariable=self.script_var, values=self._get_scripts(), state="readonly", width=30)
        self.script_dropdown.pack(side=tk.LEFT, padx=(5, 5))

        tk.Button(script_frame, text="Run", command=self.run_script, bg="#2e8b57", fg="white", relief="flat").pack(side=tk.LEFT)
        tk.Button(self.root, text="Stop Script", command=self.stop_script, bg="#a52a2a", fg="white", relief="flat").pack(pady=(0, 10))

        quick_frame = tk.Frame(self.root, bg="#1a1a1a")
        quick_frame.pack(pady=(5, 10))
        tk.Button(quick_frame, text="Plugins", command=self.open_plugin_window, bg="#5a5a88", fg="white", relief="flat").pack(side=tk.LEFT, padx=5)
        self.response_box = tk.Text(self.root, height=8, bg="#1e1e1e", fg="white")
        self.response_box.pack(fill="x", padx=10, pady=5)

        # Plugin Manager at bottom left
        plugin_frame = tk.Frame(self.root, bg="#1a1a1a")
        plugin_frame.pack(side=tk.LEFT, anchor="sw", padx=10, pady=5)

        tk.Button(self.root, text="Plugins", command=self.open_plugin_window, bg="#5a5a88", fg="white", relief="flat").pack(pady=(0, 10), anchor="w", padx=10)


    def _get_scripts(self):
        scripts_path = os.path.join("scripts")
        if not os.path.exists(scripts_path):
            return []
        return [f for f in os.listdir(scripts_path) if f.endswith(".py")]

    def send_command(self):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.entry.delete(0, tk.END)
        self.add_response("You", user_input)
        self.show_thinking()

        def worker():
            response = self.assistant.command_processor.process(user_input)

            def update_gui():
                self.hide_thinking()
                if response and response.strip():
                    self.add_response("Sylveria", response)
                else:
                    self.add_response("Sylveria", "I'm still thinking about that... 🤔")

            self.root.after(0, update_gui)

        threading.Thread(target=worker, daemon=True).start()

    def run_script(self):
        filename = self.script_var.get()
        if not filename:
            self.add_response("System", "No script selected.")
            return
        self.add_response("System", f"Running script: {filename}")
        self.assistant.command_processor.run_script(f"run script {filename}")

    def stop_script(self):
        self.assistant.command_processor.stop_script("stop script")
        self.add_response("System", "Stopped running script.")

    def check_weather(self):
        response = self.assistant.command_processor.process("what's the weather today?")
        if response.strip():
            self.add_response("Sylveria", response)

    def set_timer(self):
        timer_text = self.timer_entry.get().strip()
        if not timer_text:
            timer_text = "set a timer for 5 minutes"
        self.add_response("You", timer_text)
        response = self.assistant.command_processor.process(timer_text)
        if response.strip():
            self.add_response("Sylveria", response)

    def add_response(self, speaker, text):
        clean_text = text.strip()
        if not clean_text:
            print(f"[GUI] Skipped empty response from {speaker}.")
            return

        self.last_activity = time.time()
        self.sleepy = False
        self.set_idle()

        self.response_log.config(state=tk.NORMAL)
        self.response_log.insert(tk.END, f"{speaker}: {clean_text}\n\n")
        self.response_log.config(state=tk.DISABLED)
        self.response_log.see(tk.END)

        if "Sylveria" in speaker and hasattr(self.assistant, "audio_manager"):
            self.assistant.audio_manager.speech_queue.put(clean_text)

    def set_talking(self, is_talking):
        self.last_activity = time.time()
        self.sleepy = False
        if is_talking and self.gui_photo_talking:
            self.gui_label.config(image=self.gui_photo_talking)
        elif self.gui_photo_idle:
            self.gui_label.config(image=self.gui_photo_idle)

    def set_idle(self):
        if self.gui_photo_idle:
            self.gui_label.config(image=self.gui_photo_idle)

    def _idle_check_loop(self):
        while True:
            if not self.sleepy and time.time() - self.last_activity > 360:
                if self.gui_photo_sleepy:
                    self.gui_label.after(0, lambda: self.gui_label.config(image=self.gui_photo_sleepy))
                    self.sleepy = True
            time.sleep(5)

    def run(self):
        self.root.mainloop()

    def is_talking(self):
        return self.gui_label.cget("image") == str(self.gui_photo_talking)

    def show_thinking(self):
        self.response_log.config(state=tk.NORMAL)
        self.response_log.insert(tk.END, "Sylveria is thinking...\n")
        self.response_log.config(state=tk.DISABLED)
        self.response_log.see(tk.END)

    def hide_thinking(self):
        self.response_log.config(state=tk.NORMAL)
        lines = self.response_log.get("1.0", tk.END).strip().split("\n")
        if lines and lines[-1] == "Sylveria is thinking...":
            self.response_log.delete(f"{len(lines)}.0", tk.END)
        self.response_log.config(state=tk.DISABLED)

    def open_plugin_window(self):
        window = Toplevel(self.root)
        window.title("Plugin Manager")
        window.geometry("300x400")
        window.configure(bg="#1a1a1a")

        try:
            with open(ENABLED_PLUGINS_FILE, "r", encoding="utf-8") as f:
                current_enabled = json.load(f)
        except:
            current_enabled = []

        plugin_vars = {}
        for plugin in self.assistant.plugin_manager.list_all_plugins():
            var = BooleanVar(value=(plugin in current_enabled))
            plugin_vars[plugin] = var
            Checkbutton(window, text=plugin, variable=var, bg="#1a1a1a", fg="white", selectcolor="#333").pack(anchor="w", padx=10, pady=2)

        def save_plugins():
            enabled = [p for p, v in plugin_vars.items() if v.get()]
            with open(ENABLED_PLUGINS_FILE, "w", encoding="utf-8") as f:
                json.dump(enabled, f, indent=2)
            print("[Plugin Manager] Plugins saved.")
            self.assistant.plugin_manager.reload_plugins()
            window.destroy()

        Button(window, text="Save", command=save_plugins, bg="#2e8b57", fg="white").pack(pady=10)
