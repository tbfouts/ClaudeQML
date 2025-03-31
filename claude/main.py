"""
Main module for Claude QML Generator
"""
import os
import sys
import threading
import base64
import requests
from pathlib import Path
from PySide6.QtCore import QUrl, Qt, Slot, Signal, QObject, QFile, QIODevice
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtGui import QGuiApplication, QImageReader
from PySide6.QtWidgets import (
    QFileDialog, QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QLineEdit, QWidget, QSplitter, 
    QScrollArea, QDialog, QMessageBox, QSizePolicy
)

from .project_generator import get_valid_project_name, create_project_structure
from .qml_reloader import QmlReloader
from .ui import create_main_window_qml
from .api import is_valid_api_key


class ImageProcessingResult:
    """Class to track completion status and result of image processing"""
    def __init__(self):
        self.is_complete = False
        self.qml_content = None
        self.error = None


class ClaudeWindow(QMainWindow):
    """Main application window for Claude QML Generator"""
    promptSubmitted = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        # Initialize variables
        self.reference_image_path = None
        self.project_name = "QMLProject"
        self.content_qml_file = None
        self.reloader = None
        self.result = ImageProcessingResult()
        
        # Set up the UI
        self.setWindowTitle("Claude QML Generator")
        self.setMinimumSize(1000, 800)
        
        # Check API key
        self.check_api_key()
        
        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)
        
        # Create splitter for image/QML preview and command area
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Top area for reference image and QML preview
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)  # Changed from HBox to VBox for vertical arrangement
        
        # Main container for toolbar and previews
        
        # Create a container for the two control areas
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 15)  # Add space below the controls
        
        # Left control area (for reference image button)
        left_control = QWidget()
        left_control_layout = QHBoxLayout(left_control)
        left_control_layout.setContentsMargins(0, 0, 0, 0)
        
        # Select Image button
        self.select_image_button = QPushButton("Select Reference Image")
        self.select_image_button.setMinimumHeight(40)  # Make button taller
        self.select_image_button.setMinimumWidth(200)  # Set fixed width
        self.select_image_button.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.select_image_button.clicked.connect(self.select_reference_image)
        left_control_layout.addWidget(self.select_image_button, alignment=Qt.AlignCenter)
        
        # Right control area (for Qt logo)
        right_control = QWidget()
        right_control_layout = QHBoxLayout(right_control)
        right_control_layout.setContentsMargins(0, 0, 0, 0)
        
        # Qt logo
        qt_logo_label = QLabel()
        qt_logo_label.setAlignment(Qt.AlignCenter)
        qt_logo_label.setMinimumHeight(70)
        qt_logo_label.setAttribute(Qt.WA_TranslucentBackground)
        qt_logo_label.setStyleSheet("background-color: transparent;")
        
        # Add the Qt logo image
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              "images", "Qt-Group-logo-white.png")
        if os.path.exists(logo_path):
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(logo_path)
            # Make the logo significantly bigger
            pixmap = pixmap.scaledToHeight(65, Qt.SmoothTransformation)
            qt_logo_label.setPixmap(pixmap)
        else:
            qt_logo_label.setText("Qt")
            qt_logo_label.setStyleSheet("color: white; font-weight: bold;")
            
        right_control_layout.addWidget(qt_logo_label, alignment=Qt.AlignCenter)
        
        # Add both control areas to the controls container with equal width
        controls_layout.addWidget(left_control)
        controls_layout.addWidget(right_control)
        
        # Add controls to main layout
        top_layout.addWidget(controls_widget)
        
        # Create preview panels container
        previews_widget = QWidget()
        previews_layout = QHBoxLayout(previews_widget)
        previews_layout.setContentsMargins(0, 0, 0, 0)
        previews_layout.setSpacing(10)  # Add space between previews
        
        # Left side: Reference image preview
        self.image_label = QLabel("No Reference Image\n\nUse the button above to select an image")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedHeight(450)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.image_label.setStyleSheet("background-color: #000000; border: 1px solid #444; color: #ffffff; font-size: 14px;")
        previews_layout.addWidget(self.image_label)
        
        # Right side: QML Preview
        self.qml_preview_widget = QWidget()
        self.qml_preview_layout = QVBoxLayout(self.qml_preview_widget)
        self.qml_preview_layout.setContentsMargins(0, 0, 0, 0)
        self.qml_preview_layout.setSpacing(0)
        
        # QML placeholder
        self.qml_placeholder = QLabel("QML Preview (Will show after generation)")
        self.qml_placeholder.setAlignment(Qt.AlignCenter)
        self.qml_placeholder.setFixedHeight(450)
        self.qml_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.qml_placeholder.setStyleSheet("background-color: #000000; border: 1px solid #444; color: #ffffff; font-size: 14px;")
        self.qml_preview_layout.addWidget(self.qml_placeholder)
        
        previews_layout.addWidget(self.qml_preview_widget)
        
        # Add previews to main layout
        top_layout.addWidget(previews_widget)
        
        # The horizontal_splitter is no longer needed as we've restructured the layout
        
        splitter.addWidget(top_widget)
        
        # Bottom area for command input and output log
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        
        # Output log
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setPlaceholderText("Output will appear here...")
        bottom_layout.addWidget(self.output_log)
        
        # Command input area
        command_layout = QHBoxLayout()
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter instructions for Claude...")
        self.command_input.returnPressed.connect(self.submit_command)
        command_layout.addWidget(self.command_input)
        
        self.submit_button = QPushButton("Send")
        self.submit_button.clicked.connect(self.submit_command)
        command_layout.addWidget(self.submit_button)
        
        bottom_layout.addLayout(command_layout)
        
        splitter.addWidget(bottom_widget)
        
        # Set initial splitter position
        splitter.setSizes([500, 300])
        
        # Add status bar
        self.statusBar().showMessage("Ready")
        
        # Initial log message
        self.log_message("Claude QML Generator started. Select a reference image to begin.")
    
    def check_api_key(self):
        """Check for valid API key and prompt if not found"""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key or not is_valid_api_key(api_key):
            api_key = self.prompt_for_api_key()
            if not api_key:
                QMessageBox.critical(self, "API Key Required", 
                                   "No valid API key provided. The application will exit.")
                sys.exit(1)
            os.environ["ANTHROPIC_API_KEY"] = api_key
    
    def prompt_for_api_key(self):
        """Prompt the user for API key"""
        dialog = QDialog(self)
        dialog.setWindowTitle("API Key Required")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("The ANTHROPIC_API_KEY environment variable is not set."))
        layout.addWidget(QLabel("Please enter your Anthropic API key:"))
        
        key_input = QLineEdit()
        key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(key_input)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            return key_input.text().strip()
        return ""
    
    def select_reference_image(self):
        """Open file dialog to select a reference image"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif)")
        file_dialog.setWindowTitle("Select Reference Image")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                image_path = selected_files[0]
                # Validate the selected image
                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
                if any(image_path.lower().endswith(ext) for ext in valid_extensions):
                    self.set_reference_image(image_path)
                else:
                    QMessageBox.warning(self, "Invalid Image", 
                                      f"Selected file is not a supported image type. Please use: {', '.join(valid_extensions)}")
    
    def set_reference_image(self, image_path):
        """Set the reference image and display it"""
        self.reference_image_path = image_path
        
        try:
            # Display the image in the UI
            from PySide6.QtGui import QPixmap, QImage
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                # Try alternative method
                image = QImage(image_path)
                if image.isNull():
                    raise Exception("Unable to load image")
                pixmap = QPixmap.fromImage(image)
                
            # Resize to fit within the label while maintaining aspect ratio
            label_size = self.image_label.size()
            if label_size.width() <= 1:  # If widget not yet sized, use default
                pixmap = pixmap.scaled(450, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                pixmap = pixmap.scaled(
                    label_size.width() - 10, 
                    label_size.height() - 10, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                
            # Set the image to the label
            self.image_label.setPixmap(pixmap)
            # Clear placeholder text and set proper alignment
            self.image_label.setText("")
            self.image_label.setAlignment(Qt.AlignCenter)
            self.log_message(f"Reference image set: {os.path.basename(image_path)}")
            
            # Keep the button visible so users can change the image if needed
            self.select_image_button.setText("Change Reference Image")
            
            # Initialize project and start QML generation
            self.initialize_project()
        except Exception as e:
            self.log_message(f"Error loading image: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load image: {image_path}\n{str(e)}")
    
    def initialize_project(self):
        """Initialize the project and set up the QML environment"""
        # Use predefined project name or prompt for one via GUI dialog
        if not self.project_name or self.project_name == "QMLProject":
            self.project_name = self.prompt_for_project_name()
            if not self.project_name:
                self.log_message("Project creation cancelled.")
                return
                
        self.log_message(f"Creating project: {self.project_name}")
        
        # Create project structure
        image_content = None
        if hasattr(self, 'result') and self.result.qml_content:
            image_content = self.result.qml_content
            
        # Pass the log_message method as callback for project creation output
        self.content_qml_file = create_project_structure(
            self.project_name, 
            image_content, 
            gui_mode=True,
            log_callback=self.log_message
        )
        
        if not self.content_qml_file:
            self.log_message("Project creation cancelled.")
            return
            
        self.log_message(f"Project created. Working on file: {os.path.relpath(self.content_qml_file)}")
        
        # Initialize QML engine
        app = QGuiApplication.instance() or QGuiApplication(sys.argv)
        app.setApplicationName(f"{self.project_name} QML Generator")
        engine = QQmlApplicationEngine()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        window_qml_file = os.path.join(base_dir, "mainWindow.qml")
        
        # Create main window QML with loading indicator
        create_main_window_qml(window_qml_file)
        
        # Start image processing thread
        if self.reference_image_path:
            self.statusBar().showMessage("Processing reference image...")
            self.log_message("Claude is analyzing your image and generating QML...")
            self.start_image_processing_thread()
            
            # Set up QML reloader with reference image
            self.reloader = QmlReloader(engine, window_qml_file, self.content_qml_file, 
                                      self.reference_image_path, self.result)
        else:
            # Set up QML reloader without reference image
            self.reloader = QmlReloader(engine, window_qml_file, self.content_qml_file)
        
        # Connect the prompt signal to the reloader
        self.promptSubmitted.connect(self.reloader.submitPrompt)
        
        # Embed the QML window in our widget
        engine.load(QUrl.fromLocalFile(window_qml_file))
        
        if not engine.rootObjects():
            self.log_message("Error loading QML file!")
            return
        
        # Get the root QML object and set it as our central widget
        qml_root = engine.rootObjects()[0]
        
        # Add QML view to the preview area
        if hasattr(qml_root, "winId"):
            # Create a container widget for the QML window
            container = QWidget.createWindowContainer(qml_root)
            container.setFixedHeight(450)
            container.setMinimumWidth(450)
            container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # Clear any existing widgets in the QML preview area
            while self.qml_preview_layout.count():
                item = self.qml_preview_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            
            # Add the QML container to the preview area
            self.qml_preview_layout.addWidget(container)
            
    def prompt_for_project_name(self):
        """Prompt for project name via GUI dialog"""
        from PySide6.QtWidgets import QInputDialog
        
        project_name, ok = QInputDialog.getText(
            self, "Project Name", "Enter a name for your Qt project:")
        
        if not ok or not project_name:
            return None
            
        # Basic validation (simple project name validation)
        if not all(c.isalnum() or c == '_' or c == '-' for c in project_name):
            QMessageBox.warning(self, "Invalid Project Name", 
                              "Project name can only contain alphanumeric characters, hyphens, and underscores.")
            return self.prompt_for_project_name()  # Recursively prompt again
            
        return project_name.strip()
    
    def start_image_processing_thread(self):
        """Start a thread to process the reference image with Claude"""
        # Clear result from any previous runs
        self.result = ImageProcessingResult()
        
        # Define the thread function
        def process_image_thread():
            try:
                # Read and encode the image
                with open(self.reference_image_path, "rb") as image_file:
                    image_data = image_file.read()
                    base64_image = base64.b64encode(image_data).decode("utf-8")
                    
                # Determine media type based on file extension
                media_type = "image/jpeg"  # default
                if self.reference_image_path.lower().endswith(".png"):
                    media_type = "image/png"
                elif self.reference_image_path.lower().endswith(".gif"):
                    media_type = "image/gif"
                
                # System prompt for image-to-QML conversion
                system_prompt = """You are an expert QML developer assistant who specializes in recreating UI designs from images.

Follow these style guidelines:
1. Don't use version numbers in imports (use "import QtQuick" not "import QtQuick 2.15")
2. Don't start IDs with capital letters (use "id: button" not "id: Button") 
3. Make sure the code is suitable for a Loader component (no Window element)
4. Make sure the root element utilizes a similar width and height to the image.
5. Include all necessary QML imports for the components you use
6. Make generous use of QtQuick.Layouts for proper responsive layout
7. Use QtQuick.Controls 2 components for standard UI elements
8. Implement custom graphics with Canvas when appropriate
9. Be precise with colors, try to match the exact colors from the image
10. Always use real numbers for decimal values (use 0.5 instead of 0 when appropriate)
11. Always use PathAngleArc instead of PathArc for arcs in Path elements
12. Never use QtGraphicalEffects
13. If a gauge is created, 0 mph should always be at -210 degrees

Return ONLY the QML code without any explanation or markdown formatting."""
                
                # Create message with image
                prompt = """Please create QML code that recreates the UI shown in this reference image.

Your task is to:
1. Analyze the visual elements, layout, colors, and design of the image
2. Create QML code that implements this interface as closely as possible
3. Use standard Qt Quick components and custom elements as needed
4. Ensure all interactive elements are functional
5. Pay special attention to colors, gradients, and visual styling

Please provide ONLY the complete QML code, with no explanation or markdown formatting."""
                
                # Process the image
                api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                api_url = "https://api.anthropic.com/v1/messages"
                
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                
                # Create message content with the image
                message_content = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
                
                data = {
                    "model": "claude-3-7-sonnet-20250219",
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": message_content}]
                }
                
                # Make the API call to Anthropic directly
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=data
                )
                
                # Check for errors
                if response.status_code != 200:
                    raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
                
                # Parse the response
                response_data = response.json()
                generated_qml = response_data['content'][0]['text'].strip()
                
                # Clean up the response to extract just the QML code
                if generated_qml.startswith("```qml"):
                    generated_qml = generated_qml[6:]
                elif generated_qml.startswith("```"):
                    generated_qml = generated_qml[3:]
                
                if generated_qml.endswith("```"):
                    generated_qml = generated_qml[:-3]
                
                generated_qml = generated_qml.strip()
                
                # Save generated QML to a debug file for inspection
                # Use absolute path to avoid Windows path issues
                debug_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                            "debug_qml_output.txt")
                with open(debug_file_path, "w", encoding="utf-8") as debug_file:
                    debug_file.write(generated_qml)
                
                # Set the result
                self.result.qml_content = generated_qml
                self.result.is_complete = True
                
                # Log via QMetaObject.invokeMethod to safely call from thread
                QApplication.instance().postEvent(self, StatusUpdateEvent("Image analysis complete. QML code generated."))
                
            except Exception as e:
                self.result.error = str(e)
                self.result.is_complete = True
                QApplication.instance().postEvent(self, StatusUpdateEvent(f"Error processing reference image: {e}"))
        
        # Start the thread
        image_thread = threading.Thread(target=process_image_thread)
        image_thread.daemon = True
        image_thread.start()
    
    def submit_command(self):
        """Handle command input submission"""
        command = self.command_input.text().strip()
        if not command:
            return
            
        # Check for exit command
        if command.lower() in ['exit', 'quit', 'bye']:
            self.log_message("Shutting down...")
            if self.reloader:
                self.reloader.shutdown()
            QApplication.quit()
            return
            
        # Log the command
        self.log_message(f"> {command}")
        
        # Clear the input field
        self.command_input.clear()
        
        # Submit the prompt to Claude
        if self.reloader:
            self.promptSubmitted.emit(command)
            self.statusBar().showMessage("Processing request...")
        else:
            self.log_message("Error: Project not initialized. Please select a reference image first.")
    
    def log_message(self, message):
        """Add a message to the output log"""
        self.output_log.append(message)
        
    def event(self, event):
        """Handle custom events"""
        if isinstance(event, StatusUpdateEvent):
            self.log_message(event.message)
            self.statusBar().showMessage(event.message)
            return True
        return super().event(event)


class StatusUpdateEvent(QObject):
    """Custom event for updating status from background threads"""
    def __init__(self, message):
        super().__init__()
        self.message = message


def main():
    """Main entry point for the application"""
    # Initialize Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Claude QML Generator")
    
    # Create and show the main window
    window = ClaudeWindow()
    window.show()
    
    # Start the application
    return app.exec()