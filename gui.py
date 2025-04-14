import sys
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from git_cloner import GitCloner

logging.basicConfig(
    filename='cloner.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
        self.setWindowTitle("GitHub Repository Cloner")
        self.setGeometry(100, 100, 800, 600)
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        
        # URL Input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Repository URL:"))
        self.url_input = QLineEdit()
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Exclude Branches
        exclude_layout = QHBoxLayout()
        exclude_layout.addWidget(QLabel("Exclude Branches (comma-separated):"))
        self.exclude_input = QLineEdit()
        exclude_layout.addWidget(self.exclude_input)
        layout.addLayout(exclude_layout)

        # Progress
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Log
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        # Buttons
        self.start_btn = QPushButton("Start Cloning")
        self.start_btn.clicked.connect(self.start_cloning)
        layout.addWidget(self.start_btn)

        central_widget.setLayout(layout)

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
        self.log_output.append(f"✓ {message}")
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def _on_complete(self, success, message):
        self.start_btn.setEnabled(True)
        status = "SUCCESS" if success else "ERROR"
        self._log(f"\nProcess complete: {status} - {message}")
        if not success:
            self._log(message, "error")

    def _log(self, message, level="info"):
        css = {
            "error": "color: red;",
            "warning": "color: orange;",
            "info": "color: black;"
        }
        self.log_output.append(f'<span style="{css.get(level, "")}">{message}</span>')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())