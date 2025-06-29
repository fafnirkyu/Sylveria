import yt_dlp
import vlc
import threading
import time

class YouTubePlayer:
    def __init__(self, assistant=None):
        self.assistant = assistant
        self.player = None
        self.current_video = None

    def _play_audio(self, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{url}", download=False)['entries'][0]
            stream_url = info['url']
            self.current_video = info
            self.player = vlc.MediaPlayer(stream_url)
            self.player.play()

            # Let the video buffer a bit before reacting
            time.sleep(2)
            self._react_to_video(info)

    def play(self, query):
        threading.Thread(target=self._play_audio, args=(query,), daemon=True).start()

    def stop(self):
        if self.player:
            self.player.stop()
            self.current_video = None

    def search(self, query):
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                results = ydl.extract_info(f"ytsearch3:{query}", download=False)['entries']
                return [(entry['title'], entry['webpage_url']) for entry in results]
        except Exception as e:
            print(f"[YouTube Search Error] {e}")
            return []

    def _react_to_video(self, video_info):
        if not self.assistant or not video_info:
            return

        title = video_info.get("title", "a video")
        description = video_info.get("description", "")
        uploader = video_info.get("uploader", "someone")

        prompt = (
            f"You are Sylveria, a clever and kind assistant watching YouTube with your friend. "
            f"The current video is titled '{title}' uploaded by {uploader}. "
            f"Here's a description:\n{description[:300]}\n"
            f"React naturally as if you're watching this video with them."
        )

        try:
            response = self.assistant.ai.generate(prompt)
            if response:
                self.assistant.gui.add_response("Sylveria", response)
        except Exception as e:
            print(f"[YouTube Reaction Error] {e}")
