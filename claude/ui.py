"""
UI and window creation utilities
"""
import os


def create_main_window_qml(file_path):
    """
    Create the main window QML file
    """
    with open(file_path, "w") as f:
        f.write("""import QtQuick
import QtQuick.Window
import QtQuick.Controls

Window {
    id: mainWindow
    visible: true
    width: 800
    height: 600
    title: "QML Generator"
    
    // Content loader
    Loader {
        id: contentLoader
        anchors.fill: parent
        source: reloaderController.contentSource
        visible: !loadingIndicator.visible
        
        // Handle loading errors
        onStatusChanged: {
            if (status === Loader.Error) {
                console.error("Error loading content:", source)
            }
        }
    }
    
    // Loading indicator
    Item {
        id: loadingIndicator
        anchors.fill: parent
        visible: reloaderController.isLoading || reloaderController.isImageProcessing
        
        Rectangle {
            anchors.fill: parent
            color: "#f0f0f0"
            opacity: 0.7
        }
        
        BusyIndicator {
            id: busyIndicator
            anchors.centerIn: parent
            running: reloaderController.isLoading || reloaderController.isImageProcessing
            width: 100
            height: 100
        }
        
        Text {
            anchors.top: busyIndicator.bottom
            anchors.topMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
            text: reloaderController.isImageProcessing ? "Analyzing image and generating QML..." : "Generating QML..."
            font.pixelSize: 16
            color: "#333333"
        }
    }
    
    // Status indicator overlay
    Rectangle {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: statusLabel.width + 20
        height: statusLabel.height + 10
        color: "#80000000"  // Semi-transparent background
        radius: 5
        
        Label {
            id: statusLabel
            anchors.centerIn: parent
            color: "white"
            font.pixelSize: 12
            
            Connections {
                target: reloaderController
                function onPromptStatusChanged(status) {
                    statusLabel.text = status
                }
            }
        }
    }
}""")