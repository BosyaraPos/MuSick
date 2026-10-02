import logging
import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal


logger = logging.getLogger(__name__)


class SoundCloudSearchWorker(QThread):
    """
    Фоновый поток для поиска треков на SoundCloud через yt-dlp.
    Выполняется отдельно от основного потока интерфейса (GUI).
    """

    
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

  
    YDL_OPTIONS = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,  
        "nocheckcertificate": True,
    }

    def __init__(self, query: str, limit: int = 10, parent=None):
        super().__init__(parent)
        self.query = query.strip()
        self.limit = limit

    def run(self):
        """Запускается автоматически в отдельном потоке при вызове .start()"""
        if not self.query:
            self.results_ready.emit([])
            return

        
        search_target = f"scsearch{self.limit}:{self.query}"

        try:
            with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
               
                info = ydl.extract_info(search_target, download=False)

                
                raw_entries = info.get("entries", []) if info else []
                entries = list(raw_entries or [])

                parsed_results = []
                for entry in entries:
                    if not entry:
                        continue

                   
                    web_url = entry.get("url", "")
                    if web_url and not web_url.startswith("http"):
                        web_url = f"https://soundcloud.com/{web_url}"

                 
                    duration_sec = entry.get("duration") or 0
                    duration_ms = int(duration_sec * 1000)

                    parsed_results.append({
                        "title": entry.get("title", "Без названия"),
                        "artist": entry.get("uploader", "Неизвестный исполнитель"),
                        "web_url": web_url,  
                        "duration": duration_ms,
                    })

               
                self.results_ready.emit(parsed_results)

        except Exception as e:
            logger.error(f"Ошибка при поиске на SoundCloud: {e}")
            self.error_occurred.emit(str(e))