import sys
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTextEdit, QProgressBar, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QPalette
from cloner import GitCloner

# Configure logging
logging.basicConfig(
    filename='cloner.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Color constants
DARK_BG = "#1a1a1a"
DARKER_BG = "#0d0d0d"
RED_PRIMARY = "#ff4444"
RED_SECONDARY = "#cc0000"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#cccccc"

class Worker(QThread):
    update_progress = pyqtSignal(str)
    complete = pyqtSignal(bool, str)

    def __init__(self, url, exclude_branches):
        super().__init__()
        self.url = url
        self.exclude_branches = exclude_branches
        self.cloner = GitCloner()

    def run(self):
        try:
            success, message = self.cloner.clone_branches(
                self.url,
                self.exclude_branches,
                progress_callback=self.update_progress.emit
            )
            self.complete.emit(success, message)
        except Exception as e:
            self.complete.emit(False, str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Red Cloner")
        self.setFixedSize(600, 500)  # Fixed window size
        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header = QLabel("GitHub Repository Cloner")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet(f"color: {RED_PRIMARY};")
        main_layout.addWidget(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {RED_PRIMARY};")
        main_layout.addWidget(sep)

        # URL Input
        url_layout = QVBoxLayout()
        url_layout.addWidget(self._create_label("Repository URL:"))
        self.url_input = self._create_input()
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)

        # Exclude Branches
        exclude_layout = QVBoxLayout()
        exclude_layout.addWidget(self._create_label("Exclude Branches (comma-separated):"))
        self.exclude_input = self._create_input()
        exclude_layout.addWidget(self.exclude_input)
        main_layout.addLayout(exclude_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(150)
        main_layout.addWidget(self.log_output)

        # Start Button
        self.start_btn = QPushButton("Start Cloning")
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self.start_cloning)
        main_layout.addWidget(self.start_btn)

        central_widget.setLayout(main_layout)

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        return label

    def _create_input(self):
        input_field = QLineEdit()
        input_field.setStyleSheet(
            f"background-color: {DARKER_BG};"
            f"border: 1px solid {RED_PRIMARY};"
            "border-radius: 4px;"
            f"color: {TEXT_PRIMARY};"
            "padding: 8px;"
        )
        return input_field

    def _apply_styles(self):
        self.setStyleSheet(
            f"QMainWindow, QWidget {{ background-color: {DARK_BG}; }}"
            f"QProgressBar {{"
            f"  border: 1px solid {RED_PRIMARY};"
            f"  border-radius: 4px;"
            f"  background-color: {DARKER_BG};"
            f"  height: 12px;"
            f"}}"
            f"QProgressBar::chunk {{"
            f"  background-color: {RED_PRIMARY};"
            f"  border-radius: 3px;"
            f"}}"
            f"QPushButton {{"
            f"  background-color: {RED_PRIMARY};"
            f"  color: {TEXT_PRIMARY};"
            "  border: none;"
            "  border-radius: 4px;"
            "  padding: 10px 20px;"
            "  font-weight: bold;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {RED_SECONDARY};"
            f"}}"
            f"QPushButton:disabled {{"
            "  background-color: #444444;"
            "  color: #888888;"
            f"}}"
        )

        # Set text color palette
        palette = self.palette()
        palette.setColor(QPalette.Text, QColor(TEXT_PRIMARY))
        palette.setColor(QPalette.PlaceholderText, QColor(TEXT_SECONDARY))
        self.setPalette(palette)

    def start_cloning(self):
        url = self.url_input.text().strip()
        exclude = [b.strip() for b in self.exclude_input.text().split(',') if b.strip()]

        if not url:
            self._log("Please enter a repository URL", "error")
            return

        self.worker = Worker(url, exclude)
        self.worker.update_progress.connect(self._update_log)
        self.worker.complete.connect(self._on_complete)
        self.worker.start()

        self.start_btn.setEnabled(False)
        self._log("Starting cloning process...")

    def _update_log(self, message):
        self.log_output.append(f'<span style="color:{TEXT_PRIMARY}">✓ {message}</span>')
        self.log_output.ensureCursorVisible()

    def _on_complete(self, success, message):
        self.start_btn.setEnabled(True)
        status_color = RED_PRIMARY if success else RED_SECONDARY
        status_text = "SUCCESS" if success else "ERROR"
        self.log_output.append(
            f'<span style="color:{status_color}">\nProcess complete: {status_text} - {message}</span>'
        )

    def _log(self, message, level="info"):
        color = RED_SECONDARY if level == "error" else TEXT_PRIMARY
        self.log_output.append(f'<span style="color:{color}">{message}</span>')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for better look
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())