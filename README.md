# ClaudeQML

ClaudeQML combines the powerful capabilities of Claude AI with QML and PySide6 to generate and iterate on QML interfaces based on text prompts or reference images.

## Features

- Generate QML interfaces by describing what you want in plain text
- Optionally use a reference image as inspiration for your QML UI
- Interactive development environment with real-time QML updates
- Create complete Qt 6.8 projects with proper structure
- Command-line interface for iterative QML generation

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

The application will guide you through:
1. Setting up your API key (if not already set as an environment variable)
2. Choosing whether to use a reference image
3. Naming your project
4. Creating the project structure
5. Launching the QML generator interface

Once launched, you can type QML generation prompts at the `QML>` prompt. The QML interface will update in real-time based on your instructions.

Example prompts:
- "Create a login form with username and password fields"
- "Add a gradient background from blue to purple"
- "Make the buttons rounded with a hover effect"

Type `exit` to quit the application.

## Project Structure

When you create a new project, ClaudeQML sets up a standard Qt 6.8 project structure with:
- Main QML file for your interface
- Project organization following Qt best practices
- Ready-to-use development environment

## License

[MIT License](LICENSE)

## Acknowledgements

This project leverages the capabilities of:
- [Claude AI by Anthropic](https://www.anthropic.com/claude)
- [Qt/QML](https://www.qt.io/qt-for-python)
- [PySide6](https://doc.qt.io/qtforpython-6/)