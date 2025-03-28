import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: mainWindow
    visible: true
    width: 450
    height: 450
    title: "QML Preview"
    color: "#000000"
    
    // Fixed size to match our container
    minimumWidth: 450
    minimumHeight: 450
    maximumWidth: 450
    maximumHeight: 450
    
    // Content loader with proper sizing
    Rectangle {
        id: contentContainer
        anchors.fill: parent
        anchors.margins: 0
        color: "#000000"
        border.color: "#444444"
        border.width: 1
        
        Loader {
            id: contentLoader
            anchors.fill: parent
            anchors.margins: 0
            source: reloaderController.contentSource
            visible: !loadingIndicator.visible
            
            // Handle loading errors
            onStatusChanged: {
                if (status === Loader.Error) {
                    console.error("Error loading content:", source)
                }
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
            color: "#000000"
            opacity: 0.9
        }
        
        ColumnLayout {
            anchors.centerIn: parent
            spacing: 20
            
            BusyIndicator {
                id: busyIndicator
                Layout.alignment: Qt.AlignHCenter
                running: reloaderController.isLoading || reloaderController.isImageProcessing
                width: 80
                height: 80
            }
            
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: reloaderController.isImageProcessing ? 
                      "Analyzing image and generating QML..." : 
                      "Generating QML..."
                font.pixelSize: 14
                color: "#ffffff"
            }
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
        visible: statusLabel.text !== ""
        
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
}