"""
QML Reloader module
"""
import os
from PySide6.QtCore import QObject, Signal, Slot, QFileSystemWatcher, QUrl, QTimer
from .controller import QmlReloaderController
from .worker import ClaudeApiWorker


class QmlReloader(QObject):
    def __init__(self, engine, window_qml_file, content_qml_file, reference_image_path=None, image_processing_result=None):
        super().__init__()
        self.engine = engine
        self.window_qml_file = window_qml_file
        self.content_qml_file = content_qml_file
        self.image_processing_result = image_processing_result
        
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
        
        # Set the content source initially with proper URL format
        from PySide6.QtCore import QUrl
        content_url = QUrl.fromLocalFile(content_qml_file).toString()
        self.controller.set_content_source(content_url)
        
        # Start a timer to check if the background image processing is complete
        if self.image_processing_result is not None:
            # Set the image processing flag to show loading indicator
            self.controller.set_is_image_processing(True)
            
            # Start timer to check completion
            self.check_image_processing_timer = QTimer(self)
            self.check_image_processing_timer.setInterval(1000)  # Check every 1 second
            self.check_image_processing_timer.timeout.connect(self.check_image_processing)
            self.check_image_processing_timer.start()
        
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
            
            # Convert file path to proper URL format for Windows compatibility
            file_url = QUrl.fromLocalFile(self.content_qml_file).toString()
            self.controller.set_content_source(file_url)
            
            print("Content reload triggered")
        else:
            print("Content file not found, waiting...")
            self.timer.start(500)
    
    def check_image_processing(self):
        # Check if the async image processing has completed
        if self.image_processing_result and self.image_processing_result.is_complete:
            # Stop the timer
            self.check_image_processing_timer.stop()
            
            # Turn off the image processing indicator
            self.controller.set_is_image_processing(False)
            
            if self.image_processing_result.qml_content:
                print("Applying QML generated from reference image...")
                try:
                    # Write the QML content to the file with explicit UTF-8 encoding
                    with open(self.content_qml_file, "w", encoding="utf-8") as f:
                        f.write(self.image_processing_result.qml_content)
                    
                    # Trigger a reload using the correct file URL format
                    self.check_file()
                    
                    # Update status message
                    self.controller.updatePromptStatus("Reference image QML applied successfully!")
                except Exception as e:
                    print(f"Error applying generated QML: {e}")
                    self.controller.updatePromptStatus(f"Error applying QML: {e}")
            elif self.image_processing_result.error:
                # Show error in status
                error_msg = f"Image processing error: {self.image_processing_result.error}"
                print(error_msg)
                self.controller.updatePromptStatus(error_msg)
    
    def shutdown(self):
        self.claude_worker.stop()
        if hasattr(self, 'check_image_processing_timer') and self.check_image_processing_timer.isActive():
            self.check_image_processing_timer.stop()