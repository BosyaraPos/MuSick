import logging
import yt_dlp
from PyQt6.QtCore import QObject, QThread, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

logger = logging.getLogger(__name__)


class SoundCloudWorker(QThread):
    """
    Фоновый поток для получения прямого аудиопотока и метаданных конкретного трека.
    Используется, когда пользователь нажимает на трек из списка результатов.
    """

    
    track_loaded = pyqtSignal(dict)
   
    error_occurred = pyqtSignal(str)

    YDL_OPTIONS = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
    }

    def __init__(self, web_url: str, parent=None):
        super().__init__(parent)
        self.web_url = web_url

    def run(self):
        if not self.web_url:
            self.error_occurred.emit("Передана пустая ссылка на трек.")
            return

        try:
            with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
               
                info = ydl.extract_info(self.web_url, download=False)

                if not info:
                    self.error_occurred.emit("Не удалось получить информацию о треке.")
                    return

                
                stream_url = info.get("url")
                if not stream_url:
                    self.error_occurred.emit("Аудиопоток не найден.")
                    return

                duration_sec = info.get("duration") or 0

                track_data = {
                    "stream_url": stream_url,
                    "title": info.get("title", "Без названия"),
                    "artist": info.get("uploader", "Неизвестный исполнитель"),
                    "thumbnail": info.get("thumbnail"),  
                    "duration": int(duration_sec * 1000),  
                    "web_url": self.web_url,
                }

                self.track_loaded.emit(track_data)

        except Exception as e:
            logger.error(f"Ошибка при загрузке аудиопотока: {e}")
            self.error_occurred.emit(str(e))


class AudioPlayer(QObject):
    """
    Основной класс-контроллер плеера.
    Управляет воспроизведением звука и связывает worker с QMediaPlayer.
    """

    
    track_ready = pyqtSignal(dict)
    load_failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        
        
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)  

        self.worker = None

    def load_track(self, web_url: str):
        """Запускает фоновый поток для получения аудиопотока по веб-ссылке"""
        
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        self.worker = SoundCloudWorker(web_url)
        self.worker.track_loaded.connect(self._on_track_loaded)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _on_track_loaded(self, track_data: dict):
        """Вызывается, когда worker успешно извлек прямой stream_url"""
        stream_url = track_data.get("stream_url")
        if stream_url:
           
            self.player.setSource(QUrl(stream_url))
            self.play()
            
            self.track_ready.emit(track_data)

    def _on_error(self, error_message: str):
        self.load_failed.emit(error_message)

   

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def set_volume(self, value: int):
       
        self.audio_output.setVolume(value / 100.0)

    def set_position(self, position_ms: int):

        self.player.setPosition(position_ms)