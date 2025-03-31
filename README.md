# ClaudeQML

ClaudeQML combines the powerful capabilities of Claude AI with QML and PySide6 to generate and iterate on QML interfaces based on text prompts or reference images.

## Demo
Click the image below for a demonstration video:

[![Demo Video](https://vumbnail.com/1071065178.jpg)](https://vimeo.com/1071065178)

## Features

- Generate QML interfaces by describing what you want in plain text
- Optionally use a reference image as inspiration for your QML UI
- Modern GUI interface with side-by-side reference image and QML preview
- Interactive development environment with real-time QML updates
- Create complete Qt 6.8 projects with proper structure

## Prerequisites

- Python 3.8 or higher
- Qt 6.8 or higher
- Anthropic API key (Claude API access)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ClaudeQML.git
   cd ClaudeQML
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install PySide6 requests anthropic
   ```

4. Set up your Anthropic API key:
   ```bash
   # On Windows (Command Prompt)
   set ANTHROPIC_API_KEY=your_api_key_here
   # On Windows (PowerShell)
   $env:ANTHROPIC_API_KEY="your_api_key_here"
   # On macOS/Linux
   export ANTHROPIC_API_KEY="your_api_key_here"
   ```

## Usage

Run the application using:
```bash
python claude_generator.py
```

### Using the GUI Interface

1. The application will prompt for your Anthropic API key on first launch
2. Click the "Select Reference Image" button to choose an image
3. Name your project when prompted
4. The reference image will appear on the left, and the QML preview on the right
5. Enter QML generation or modification commands in the input box at the bottom
6. The QML preview updates in real-time as you submit prompts

### Example Prompts

- "Create a login form with username and password fields"
- "Add a gradient background from blue to purple"
- "Make the buttons rounded with a hover effect"
- "Increase the size of the gauge and add more tick marks"
- "Change the color scheme to dark mode"

The application securely stores your API key for future sessions.

## Project Structure

When you create a new project, ClaudeQML sets up a standard Qt 6.8 project structure with:
- Main QML file for your interface
- Project organization following Qt best practices
- Ready-to-use development environment

## Acknowledgements

This project leverages the capabilities of:
- [Claude AI by Anthropic](https://www.anthropic.com/claude)
- [Qt/QML](https://www.qt.io/qt-for-python)
- [PySide6](https://doc.qt.io/qtforpython-6/)
