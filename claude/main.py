"""
Main module for Claude QML Generator
"""
import os
import sys
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFileDialog, QApplication

from .project_generator import get_valid_project_name, create_project_structure
from .qml_reloader import QmlReloader
from .ui import create_main_window_qml


def get_reference_image():
    """
    Prompt for a reference image path and use a file dialog when selected
    """
    use_reference = input("Do you want to use a reference image? (y/n): ").lower().strip()
    
    if use_reference != 'y':
        return None
    
    # Create a temporary QApplication for the file dialog
    # If we're already in a QApplication context (main GUI), this won't be used
    app = QApplication.instance() or QApplication(sys.argv)
    
    print("Opening file dialog to select an image...")
    print("The QML will be automatically generated based on this image.")
    file_dialog = QFileDialog()
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
                return image_path
            else:
                print(f"Selected file is not a supported image type. Please use: {', '.join(valid_extensions)}")
    
    # Ask for manual path if dialog was canceled or invalid
    manual_entry = input("Would you like to enter the image path manually instead? (y/n): ").lower().strip()
    if manual_entry == 'y':
        while True:
            image_path = input("Enter the absolute path to your reference image (or leave empty to skip): ").strip()
            
            if not image_path:
                return None
                
            if not os.path.isabs(image_path):
                print("Please provide an absolute path (starting with / or C:\\)")
                continue
                
            if not os.path.exists(image_path):
                print(f"File not found: {image_path}")
                continue
                
            # Basic file type validation
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
                print(f"File must be one of these types: {', '.join(valid_extensions)}")
                continue
                
            return image_path
    
    return None


def main():
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("\n===== API Key Required =====")
        print("The ANTHROPIC_API_KEY environment variable is not set.")
        api_key = input("Please enter your Anthropic API key: ").strip()
        if not api_key:
            print("No API key provided. Exiting.")
            return 1
        os.environ["ANTHROPIC_API_KEY"] = api_key
        print("API key set for this session.")
    
    # Get project name first
    print("\n===== Qt 6.8 Project Generator =====")
    project_name = get_valid_project_name()
    
    # Get reference image if needed
    print("\n===== Reference Image =====")
    reference_image_path = get_reference_image()
    
    # Start a separate thread for image processing
    image_thread = None
    
    if reference_image_path:
        import threading
        import base64
        import requests
        
        print(f"Using reference image: {reference_image_path}")
        print("Claude will automatically generate QML to match this image.")
        
        # Send initial request to Claude asynchronously
        print("\n===== Contacting Claude AI =====")
        print("Sending initial request to Claude in background...")
        
        # Variable to track completion status and result
        class ImageProcessingResult:
            def __init__(self):
                self.is_complete = False
                self.qml_content = None
                self.error = None
                
        result = ImageProcessingResult()
        
        # Define image processing thread function
        def process_image_thread():
            try:
                # Read and encode the image
                with open(reference_image_path, "rb") as image_file:
                    image_data = image_file.read()
                    base64_image = base64.b64encode(image_data).decode("utf-8")
                    
                # Determine media type based on file extension
                media_type = "image/jpeg"  # default
                if reference_image_path.lower().endswith(".png"):
                    media_type = "image/png"
                elif reference_image_path.lower().endswith(".gif"):
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
                with open("debug_qml_output.txt", "w") as debug_file:
                    debug_file.write(generated_qml)
                
                # Set the result
                result.qml_content = generated_qml
                result.is_complete = True
                print("\nImage analysis complete. QML code generated and saved to debug_qml_output.txt")
                
            except Exception as e:
                result.error = str(e)
                result.is_complete = True
                print(f"\nError processing reference image: {e}")
        
        # Start the thread
        image_thread = threading.Thread(target=process_image_thread)
        image_thread.daemon = True
        image_thread.start()
        
        print("Image processing started in background. Continuing with project creation...")
    else:
        print("No reference image will be used.")
    
    # Create project structure while image is being processed
    content_qml_file = create_project_structure(project_name)
    if not content_qml_file:
        print("Project creation cancelled.")
        return 1
    
    # Initialize QML application
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    app.setApplicationName(f"{project_name} QML Generator")
    engine = QQmlApplicationEngine()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    window_qml_file = os.path.join(base_dir, "mainWindow.qml")
    
    # Create/update main window QML with loading indicator
    create_main_window_qml(window_qml_file)
    
    # Set up QML reloader
    if reference_image_path:
        # Pass the background image processing result to the reloader
        reloader = QmlReloader(engine, window_qml_file, content_qml_file, reference_image_path, result)
    else:
        reloader = QmlReloader(engine, window_qml_file, content_qml_file)
    
    # Load the main window
    engine.load(QUrl.fromLocalFile(window_qml_file))
    
    if not engine.rootObjects():
        print("Error loading QML file!")
        return -1
    
    if reference_image_path:
        print("\n===== Generating QML from reference image =====")
        print("Claude is analyzing your image and generating QML...")
        print("This may take a few moments. Please wait...")
    
    # Command line interface in main thread
    print(f"\n===== QML Generator for {project_name} =====")
    print(f"- Working on file: {os.path.relpath(content_qml_file)}")
    print("- Style guidelines: no version numbers in imports, lowercase IDs")
    if reference_image_path:
        print(f"- Using reference image: {os.path.basename(reference_image_path)}")
    print("- Type any instructions to update the QML")
    print("- Empty inputs will be ignored")
    print("- Type 'exit' to quit")
    print("===========================================\n")
    
    while True:
        user_input = input("\nQML> ")
        
        # Check for exit commands
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Shutting down...")
            reloader.shutdown()
            break
        
        # Ignore empty inputs
        if not user_input.strip():
            continue
        
        # Treat all non-empty input as QML instructions
        reloader.submitPrompt(user_input)
    
    return 0