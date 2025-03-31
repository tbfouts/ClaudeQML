"""
Claude API worker thread
"""
import os
import threading
import queue
import time
import requests
import base64


class ClaudeApiWorker(threading.Thread):
    def __init__(self, content_qml_file, controller, reference_image_path=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.content_qml_file = content_qml_file
        self.controller = controller
        self.prompt_queue = queue.Queue()
        self.running = True
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = "claude-3-7-sonnet-20250219"
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.conversation_history = []
        self.reference_image_path = reference_image_path
        self.initial_image_conversion_done = False
        
    def run(self):
        while self.running:
            try:
                # Flag initial image conversion as done since it's now handled before project creation
                if self.reference_image_path and not self.initial_image_conversion_done:
                    self.initial_image_conversion_done = True
                
                try:
                    prompt = self.prompt_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                self.controller.updatePromptStatus("Generating QML code from your prompt...")
                self.controller.set_is_loading(True)
                
                # Read the existing QML code
                existing_code = ""
                if os.path.exists(self.content_qml_file):
                    with open(self.content_qml_file, "r") as f:
                        existing_code = f.read()
                else:
                    # Create a default if no file exists
                    existing_code = """import QtQuick
import QtQuick.Controls

Rectangle {
    anchors.fill: parent
    color: "#f0f0f0"
    
    Text {
        anchors.centerIn: parent
        text: "Hello, QML Generator!"
        font.pixelSize: 24
    }
}"""
                
                # Prepare prompt for Claude
                system_prompt = """You are an expert QML developer assistant. Follow these style guidelines:
1. Don't use version numbers in imports (use "import QtQuick" not "import QtQuick 2.15")
2. Don't start IDs with capital letters (use "id: button" not "id: Button") 
3. Make sure the code is suitable for a Loader component (no Window element)
4. Make sure the root element uses anchors.fill: parent if it doesn't already
5. Make sure to include the necessary QML imports for new types that are added
6. Always use real numbers for decimal values (use 0.5 instead of 0 when appropriate)
7. Always use PathAngleArc instead of PathArc for arcs in Path elements
8. If the user is creating a speedometer or gauge, it should have a start angle of -210 and sweep to 240
9. If the user is creating a speedometer or gauge, the 0 value should have a start angle of -210 and sweep to 240
10. If the user is creating a speedometer or gauge, the tick marks should have a start angle of -210 and sweep to 240

Return ONLY the modified QML code without any explanation or markdown formatting."""
                
                user_message = f"""I need you to modify the following QML code based on this requirement: {prompt}

Existing QML code:
```qml
{existing_code}
```"""
                
                # Prepare the message content
                message_content = [{"type": "text", "text": user_message}]
                
                # Add reference image if provided
                if self.reference_image_path and os.path.exists(self.reference_image_path):
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
                                
                            # Add image to the message content before the text
                            message_content.insert(0, {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_image
                                }
                            })
                            
                            # Add reference to the image in the text
                            message_content[1]["text"] = f"""I need you to modify the following QML code based on this requirement: {prompt}
                            
Please use the reference image provided above for design inspiration.

Existing QML code:
```qml
{existing_code}
```"""
                            
                    except Exception as e:
                        print(f"Error processing reference image: {e}")
                
                # Add the current message to conversation history
                self.conversation_history.append({"role": "user", "content": message_content})
                
                # Make API request using direct Anthropic API
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                
                data = {
                    "model": self.model,
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "system": system_prompt,
                    "messages": self.conversation_history
                }
                
                # Make the API call to Anthropic directly
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data
                )
                
                # Check for errors
                if response.status_code != 200:
                    raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
                
                # Parse the response
                response_data = response.json()
                generated_qml = response_data['content'][0]['text'].strip()
                
                # Add assistant response to conversation history
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": [{"type": "text", "text": generated_qml}]
                })
                
                # Keep conversation history to a reasonable size (last 10 messages)
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]
                
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
                
                # Write to the main content file with explicit UTF-8 encoding
                with open(self.content_qml_file, "w", encoding="utf-8") as f:
                    f.write(generated_qml)
                
                self.controller.updatePromptStatus("QML code updated successfully!")
                self.controller.set_is_loading(False)
                self.prompt_queue.task_done()
                
            except Exception as e:
                self.controller.updatePromptStatus(f"Error: {str(e)}")
                self.controller.set_is_loading(False)
                print(f"Error in Claude API worker: {e}")
                if not self.prompt_queue.empty():
                    self.prompt_queue.task_done()
                time.sleep(1)
    
    def convert_image_to_qml(self):
        """Convert the reference image to QML code automatically"""
        if not self.reference_image_path or not os.path.exists(self.reference_image_path):
            return
            
        self.controller.updatePromptStatus("Analyzing reference image and generating QML...")
        self.controller.set_is_loading(True)
        
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
                
            # Prepare the message content with the image
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
                    "text": """Please create QML code that recreates the UI shown in this reference image.

Your task is to:
1. Analyze the visual elements, layout, colors, and design of the image
2. Create QML code that implements this interface as closely as possible
3. Use standard Qt Quick components and custom elements as needed
4. Ensure all interactive elements are functional
5. Pay special attention to colors, gradients, and visual styling

Please provide ONLY the complete QML code, with no explanation or markdown."""
                }
            ]
            
            # System prompt for image-to-QML conversion
            system_prompt = """You are an expert QML developer assistant who specializes in recreating UI designs from images.

Follow these style guidelines:
1. Don't use version numbers in imports (use "import QtQuick" not "import QtQuick 2.15")
2. Don't start IDs with capital letters (use "id: button" not "id: Button") 
3. Make sure the code is suitable for a Loader component (no Window element)
4. Make sure the root element uses anchors.fill: parent
5. Include all necessary QML imports for the components you use
6. Make generous use of QtQuick.Layouts for proper responsive layout
7. Use QtQuick.Controls 2 components for standard UI elements
8. Implement custom graphics with Canvas when appropriate
9. Be precise with colors, try to match the exact colors from the image
10. Always use real numbers for decimal values (use 0.5 instead of 0 when appropriate)
11. Always use PathAngleArc instead of PathArc for arcs in Path elements

Return ONLY the QML code without any explanation or markdown formatting."""
            
            # Create a new request to Claude
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            data = {
                "model": self.model,
                "max_tokens": 4000,
                "temperature": 0.7,
                "system": system_prompt,
                "messages": [{"role": "user", "content": message_content}]
            }
            
            # Make the API call to Anthropic directly
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data
            )
            
            # Check for errors
            if response.status_code != 200:
                raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
            
            # Parse the response
            response_data = response.json()
            generated_qml = response_data['content'][0]['text'].strip()
            
            # Add this to our conversation history
            self.conversation_history = [
                {"role": "user", "content": message_content},
                {"role": "assistant", "content": [{"type": "text", "text": generated_qml}]}
            ]
            
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
            
            # Write to the main content file with explicit UTF-8 encoding
            with open(self.content_qml_file, "w", encoding="utf-8") as f:
                f.write(generated_qml)
            
            self.controller.updatePromptStatus("QML generated from reference image!")
            self.controller.set_is_loading(False)
            
        except Exception as e:
            self.controller.updatePromptStatus(f"Error generating from image: {str(e)}")
            self.controller.set_is_loading(False)
            print(f"Error in image-to-QML conversion: {e}")
    
    def submit_prompt(self, prompt):
        if not self.api_key:
            self.controller.updatePromptStatus("Error: ANTHROPIC_API_KEY environment variable not set")
            return
        self.prompt_queue.put(prompt)
    
    def stop(self):
        self.running = False