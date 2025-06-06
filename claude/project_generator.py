"""
Project generation module
"""
import os
from PySide6.QtCore import Qt
from .api import ask_claude


def create_project_structure(project_name, image_generated_qml=None, gui_mode=True, log_callback=None):
    """Create a complete Qt project structure using Claude API
    
    Args:
        project_name: Name of the project
        image_generated_qml: Pre-generated QML from image analysis
        gui_mode: Whether to use GUI dialogs instead of CLI prompts
        log_callback: Function to call for logging messages in GUI mode
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_dir = os.path.join(base_dir, project_name)
    
    # Helper function for logging
    def log(message):
        if gui_mode and log_callback:
            log_callback(message)
        print(message)
    
    # Initialize conversation history
    conversation_history = []
    
    # Create project directory
    if os.path.exists(project_dir):
        if gui_mode:
            from PySide6.QtWidgets import QMessageBox
            result = QMessageBox.question(None, "Project Exists", 
                                       f"Project directory {project_name} already exists. Overwrite?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if result != QMessageBox.Yes:
                return None
        else:
            overwrite = input(f"Project directory {project_name} already exists. Overwrite? (y/n): ").lower()
            if overwrite != 'y':
                return None
    
    os.makedirs(project_dir, exist_ok=True)
    
    # Define file paths
    cmakelists_path = os.path.join(project_dir, "CMakeLists.txt")
    main_cpp_path = os.path.join(project_dir, "main.cpp")
    main_qml_path = os.path.join(project_dir, "Main.qml")
    content_qml_path = os.path.join(project_dir, "Content.qml")
    
    # Generate CMakeLists.txt
    if gui_mode:
        from PySide6.QtWidgets import QApplication
        QApplication.setOverrideCursor(Qt.WaitCursor)
    
    log("Generating CMakeLists.txt...")
    cmakelists_prompt = f"""Create a CMakeLists.txt file for a Qt 6.8 Quick application with the following details:
- Project name: {project_name}
- Minimum CMake version: 3.20
- Minimum Qt version: 6.8
- Required packages: Qt6 Core, Quick, QuickControls2
- Set QT_DISABLE_DEPRECATED_BEFORE to enforce using modern APIs
- Use qt_standard_project_setup(REQUIRES 6.8) to enforce Qt 6.8
- Use qt_add_executable to configure the executable
- Use qt_add_qml_module to register the QML files like this:
  qt_add_qml_module({project_name}
    URI {project_name}
    VERSION 1.0
    QML_FILES
      Main.qml
      Content.qml
  )
- Create an executable from main.cpp and link it to the QML module
- Set up proper linking to the Qt libraries
- Include any modern best practices for Qt 6.8 CMake projects

Please provide only the complete CMakeLists.txt content without any explanation or markdown formatting."""

    try:
        cmakelists_content, conversation_history = ask_claude(cmakelists_prompt, conversation_history)
        if not cmakelists_content:
            raise Exception("Failed to generate CMakeLists.txt")
            
        with open(cmakelists_path, "w") as f:
            f.write(cmakelists_content)
    except Exception as e:
        log(f"Error generating CMakeLists.txt: {e}")
        if gui_mode:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Generation Error", f"Failed to generate CMakeLists.txt: {e}")
            QApplication.restoreOverrideCursor()
        return None
    
    # Generate main.cpp
    log("Generating main.cpp...")
    main_cpp_content = """#include <QGuiApplication>
#include <QQmlApplicationEngine>
int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    app.setOrganizationName("PROJECTNAME");
    app.setApplicationName("PROJECTNAMEApp");
    
    QQmlApplicationEngine engine;
    QObject::connect(
        &engine,
        &QQmlApplicationEngine::objectCreationFailed,
        &app,
        []() { QCoreApplication::exit(-1); },
        Qt::QueuedConnection);
    engine.loadFromModule("PROJECTNAME", "Main");
    return app.exec();
}"""
    
    # Replace the project name placeholder
    main_cpp_content = main_cpp_content.replace("PROJECTNAME", project_name)
    
    with open(main_cpp_path, "w") as f:
        f.write(main_cpp_content)
    
    # Generate Main.qml
    log("Generating Main.qml...")
    main_qml_prompt = f"""Create a Main.qml file for a Qt 6.8 application with the following details:
- The file will be the entry point for a {project_name} QML module
- Create a main ApplicationWindow (not just Window) element with a title, width, and height
- Add proper import statements with no version numbers (QtQuick, QtQuick.Controls, QtQuick.Layouts)
- Inside the window, have a Loader that loads Content.qml
- Follow these style guidelines:
  1. Don't use version numbers in imports (use "import QtQuick" not "import QtQuick 2.15")
  2. Don't start IDs with capital letters (use "id: window" not "id: Window")
  3. Make the Loader fill the entire window area using anchors
  4. Set visible: true for the main window

Please provide only the complete Main.qml content without any explanation or markdown formatting."""

    main_qml_content, conversation_history = ask_claude(main_qml_prompt, conversation_history)
    with open(main_qml_path, "w") as f:
        f.write(main_qml_content)
    
    # Generate Content.qml
    log("Generating Content.qml...")
    
    # If we have pre-generated QML from image analysis, use that instead of generating new content
    if image_generated_qml:
        log("Using pre-generated QML from image analysis...")
        content_qml_content = image_generated_qml
    else:
        # Generate default Content.qml if no image-based QML is available
        content_qml_prompt = f"""Create a Content.qml file for a Qt 6.8 application with the following details:
- This file will be loaded by the Main.qml Loader
- Create a Rectangle as the root element that fills its parent
- Add a Text element centered in the rectangle with a welcome message for {project_name}
- Follow these style guidelines:
  1. Don't use version numbers in imports (use "import QtQuick" not "import QtQuick 2.15")
  2. Don't start IDs with capital letters (use "id: root" not "id: Root")
  3. Make sure the root element has anchors.fill: parent

Please provide only the complete Content.qml content without any explanation or markdown formatting."""

        content_qml_content, conversation_history = ask_claude(content_qml_prompt, conversation_history)
    
    # Write Content.qml
    with open(content_qml_path, "w") as f:
        f.write(content_qml_content)
    
    log(f"\nProject {project_name} created successfully in {project_dir}")
    log("Directory structure:")
    log(f"{project_name}/")
    log(f"├── CMakeLists.txt")
    log(f"├── main.cpp")
    log(f"├── Main.qml")
    log(f"└── Content.qml")
    log("\nTo build the project:")
    log(f"cd {project_name}")
    log("mkdir build && cd build")
    log("cmake ..")
    log("make")
    
    return content_qml_path  # Return the path to the Content.qml file for QML reloading


def get_valid_project_name():
    """
    Prompt the user for a project name and validate it.
    Returns the project name.
    """
    while True:
        project_name = input("Enter a name for your Qt project: ").strip()
        
        # Skip empty input
        if not project_name:
            print("Project name cannot be empty. Please try again.")
            continue
        
        # Basic validation (simple project name validation)
        if not all(c.isalnum() or c == '_' or c == '-' for c in project_name):
            print("Project name can only contain alphanumeric characters, hyphens, and underscores.")
            continue
        
        return project_name