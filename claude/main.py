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
    
    # Get reference image if needed
    print("\n===== Reference Image =====")
    reference_image_path = get_reference_image()
    if reference_image_path:
        print(f"Using reference image: {reference_image_path}")
        print("Claude will automatically generate QML to match this image.")
    else:
        print("No reference image will be used.")
        
    # Get project name
    print("\n===== Qt 6.8 Project Generator =====")
    project_name = get_valid_project_name()
    
    # Create project structure
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
    reloader = QmlReloader(engine, window_qml_file, content_qml_file, reference_image_path)
    
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