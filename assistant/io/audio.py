import threading
import queue
import time
import numpy as np
import pyaudio
import re
import os
import tempfile
import asyncio
import edge_tts
import whisper
import soundfile as sf
from pydub import AudioSegment
from pydub.playback import play

class AudioManager:
    def __init__(self, assistant):
        self.assistant = assistant
        self.speech_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.whisper_model = whisper.load_model("base.en")

        self.sample_rate = 16000
        self.frame_length = 512
        self.command_mode = False
        self._command_timeout = 10.0
        self.last_active = time.time()
        self.wake_word = "hey sylveria"
        self._conversation_followups = ("and", "also", "then", "next", "too", "what about")

    def start(self):
        threading.Thread(target=self._speech_loop, daemon=True).start()
        threading.Thread(target=self._process_audio_loop, daemon=True).start()
        self._start_audio_capture()

    def _start_audio_capture(self):
        pa = pyaudio.PyAudio()
        self.stream = pa.open(
            rate=self.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.frame_length,
            stream_callback=self._audio_callback
        )
        self.stream.start_stream()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def _process_audio_loop(self):
        while True:
            if not self.audio_queue.empty():
                raw_data = self.audio_queue.get()
                pcm = np.frombuffer(raw_data, dtype=np.int16)

                if not self.command_mode:
                    text = self._try_quick_transcribe(pcm)
                    if self.wake_word in text.lower():
                        print(f"[Wake Word Detected]: {text}")
                        self._handle_wake_word()
                else:
                    self.last_active = time.time()
                    self._handle_command_mode()
            else:
                time.sleep(0.01)

    def _handle_wake_word(self):
        self.command_mode = True
        self.speech_queue.put("Yes?")
        self._clear_audio_queue()
        time.sleep(1.0)

    def _handle_command_mode(self):
        start_time = time.time()
        audio_data = []

        while time.time() - start_time < self._command_timeout:
            if not self.audio_queue.empty():
                pcm = np.frombuffer(self.audio_queue.get(), dtype=np.int16)
                audio_data.append(pcm)
            else:
                time.sleep(0.05)

        if not audio_data:
            self.command_mode = False
            self.speech_queue.put("I didn't catch that.")
            return

        audio_array = np.concatenate(audio_data)
        if np.abs(audio_array).mean() < 30:
            self.command_mode = False
            self.speech_queue.put("It was too quiet, I couldn't hear you.")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            sf.write(temp_audio.name, audio_array, self.sample_rate)
            result = self.whisper_model.transcribe(temp_audio.name)
            text = result["text"].strip()

        if not text or len(text.split()) < 2:
            self.command_mode = False
            self.speech_queue.put("Sorry, I didn't understand that clearly.")
            return

        lower_text = text.lower().strip()
        if any(lower_text.endswith(phrase) for phrase in self._conversation_followups):
            self._process_command(text)
            self._handle_command_mode()
            return
        elif "thank you" in lower_text or "that's all" in lower_text:
            self._process_command(text)
            self.command_mode = False
            self.speech_queue.put("Alright, I'm here when you need me.")
            return

        self._process_command(text)
        self.command_mode = False

    def _clear_audio_queue(self):
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def _process_command(self, text):
        self.assistant.gui.add_response("You", text)
        response = self.assistant.command_processor.process(text)
        if response and response.strip():
            self.assistant.gui.add_response(self.assistant.personality.get_name(), response)
            self.speech_queue.put(response)

    def _try_quick_transcribe(self, pcm):
        audio_array = np.array(pcm).astype(np.float32) / 32768.0
        if np.abs(audio_array).mean() < 0.01:
            return ""

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            sf.write(temp_audio.name, pcm, self.sample_rate)
            result = self.whisper_model.transcribe(temp_audio.name)
            return result.get("text", "")

    def _speech_loop(self):
        while True:
            try:
                text = self.speech_queue.get(timeout=0.1)
                if not text.strip():
                    continue
                if hasattr(self.assistant, "gui") and hasattr(self.assistant.gui, "is_talking"):
                    if self.assistant.gui.is_talking():
                        continue
                self._speak(text)
            except queue.Empty:
                time.sleep(0.05)

    def _speak(self, text):
        if not text or not text.strip():
            text = "Sorry, I was going to say something, but it slipped my tongue."

        print("[TTS] Using Edge TTS.")
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'[\\*\\_\$\$\$\$]', '', text)
        if len(text) > 500:
            text = text[:500] + '...'

        if hasattr(self.assistant, "gui"):
            self.assistant.gui.set_talking(True)

        filename = "temp_voice.mp3"
        try:
            if os.path.exists(filename):
                os.remove(filename)

            try:
                asyncio.run(self._speak_edge(text, filename))
            except RuntimeError:
                loop = asyncio.get_event_loop()
                loop.create_task(self._speak_edge(text, filename))
                return

            if not os.path.exists(filename):
                raise RuntimeError("TTS output file not created.")

            sound = AudioSegment.from_file(filename, format="mp3")
            play(sound - 6)
            time.sleep(0.75)
        except Exception as e:
            print(f"[Edge TTS error]: {e}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)
            if hasattr(self.assistant, "gui"):
                self.assistant.gui.set_talking(False)

    async def _speak_edge(self, text, filename):
        try:
            if not text or not text.strip():
                raise ValueError("Empty text passed to TTS.")

            voice = "en-US-JennyNeural"
            current_mood = getattr(self.assistant, "current_mood", "soft").lower()
            mood_parameters = {
                "soft": {"rate": "-10%", "pitch": "-2Hz"},
                "playful": {"rate": "+15%", "pitch": "+5Hz"},
                "affectionate": {"rate": "+5%", "pitch": "+2Hz"},
                "serious": {"rate": "-5%", "pitch": "-1Hz"},
            }
            params = mood_parameters.get(current_mood, {"rate": "0%", "pitch": "0Hz"})

            print(f"[TTS] Mood: {current_mood}, Rate: {params['rate']}, Pitch: {params['pitch']}")

            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=params["rate"],
                pitch=params["pitch"]
            )
            await communicate.save(filename)
            print(f"[TTS] Saved voice output to: {filename}")

        except Exception as e:
            print(f"[Edge TTS Internal Error] {e}")
            raise
