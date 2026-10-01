import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QFileDialog, QSlider
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class AudioPlayer(QWidget):
    def __init__(self):
        super().__init__()

        # --- Инициализация Аудио-движка ---
        self.mediaPlayer = QMediaPlayer()
        self.audioOutput = QAudioOutput()
        self.mediaPlayer.setAudioOutput(self.audioOutput)

        # Подключаем сигнал ошибки, чтобы знать, если GStreamer/PipeWire сбоит
        self.mediaPlayer.errorOccurred.connect(self.handle_errors)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Cross-Platform Audio Player")
        self.resize(400, 250)

        # Виджеты
        self.label_name = QLabel("Файл не выбран")
        self.label_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Добавляем статус-бар для отладки (поможет понять, работает ли звук)
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("font-size: 11px; color: #888;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_open = QPushButton("Открыть файл")
        self.btn_open.setObjectName("openBtn")

        self.btn_play = QPushButton("▶ Play")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_stop = QPushButton("⏹ Stop")

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.audioOutput.setVolume(0.7)

        # Компоновка
        main_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_pause)
        controls_layout.addWidget(self.btn_stop)

        main_layout.addWidget(self.label_name)
        main_layout.addWidget(self.btn_open)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(QLabel("Громкость:"))
        main_layout.addWidget(self.volume_slider)
        main_layout.addWidget(self.status_label) # Добавляем статус в низ

        self.setLayout(main_layout)

        # Сигналы
        self.btn_open.clicked.connect(self.open_file)
        self.btn_play.clicked.connect(self.mediaPlayer.play)
        self.btn_pause.clicked.connect(self.mediaPlayer.pause)
        self.btn_stop.clicked.connect(self.stop_audio)
        self.volume_slider.valueChanged.connect(self.change_volume)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите аудио файл", "", "Audio Files (*.mp3 *.wav *.ogg *.flac)"
        )

        if file_path:
            url = QUrl.fromLocalFile(file_path)
            self.mediaPlayer.setSource(url)
            self.label_name.setText(Path(file_path).name)
            self.status_label.setText("Загрузка файла...")
            self.mediaPlayer.play()

    def stop_audio(self):
        self.mediaPlayer.stop()
        self.status_label.setText("Остановлено")

    def change_volume(self, value):
        self.audioOutput.setVolume(value / 100)

    def handle_errors(self, error, error_string):
        # Эта функция сработает, если GStreamer не может проиграть файл
        # или если звук в системе (PipeWire/Pulse) недоступен
        print(f"Ошибка плеера: {error_string}")
        self.status_label.setText(f"Ошибка: {error_string}")
        self.status_label.setStyleSheet("color: #ff5555;")

# --- Стандартный запуск ---
def load_stylesheet(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

app = QApplication(sys.argv)
BASE_DIR = Path(__file__).resolve().parent
app.setStyleSheet(load_stylesheet(BASE_DIR / "style.qss"))

player = AudioPlayer()
player.show()
sys.exit(app.exec())
