"""
QML Reloader module
"""
import os
from PySide6.QtCore import QObject, Signal, Slot, QFileSystemWatcher, QUrl, QTimer
from .controller import QmlReloaderController
from .worker import ClaudeApiWorker


class QmlReloader(QObject):
    def __init__(self, engine, window_qml_file, content_qml_file, reference_image_path=None):
        super().__init__()
        self.engine = engine
        self.window_qml_file = window_qml_file
        self.content_qml_file = content_qml_file
        
        self.controller = QmlReloaderController(engine)
        self.engine.rootContext().setContextProperty("reloaderController", self.controller)
        engine.rootContext().setContextProperty("qmlReloader", self)
        
        self.claude_worker = ClaudeApiWorker(content_qml_file, self.controller, reference_image_path)
        self.claude_worker.start()
        
        self.watcher = QFileSystemWatcher([content_qml_file])
        self.watcher.fileChanged.connect(self.handle_file_changed)
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.check_file)
        
        # Set the content source initially
        self.controller.set_content_source(content_qml_file)
        
        print(f"Watching {content_qml_file} for changes...")
    
    @Slot(str)
    def submitPrompt(self, prompt):
        print(f"Updating QML with: {prompt}")
        self.controller.updatePromptStatus("Processing your request...")
        self.claude_worker.submit_prompt(prompt)
        
    def handle_file_changed(self, path):
        print(f"Detected change in {path}")
        self.timer.start(100)

    def check_file(self):
        if os.path.exists(self.content_qml_file):
            if not self.watcher.files():
                self.watcher.addPath(self.content_qml_file)
            
            print("Reloading QML content...")
            self.engine.clearComponentCache()
            
            # Update the content source to trigger a reload
            self.controller.set_content_source("")
            self.controller.set_content_source(self.content_qml_file)
            
            print("Content reload triggered")
        else:
            print("Content file not found, waiting...")
            self.timer.start(500)
            
    def shutdown(self):
        self.claude_worker.stop()