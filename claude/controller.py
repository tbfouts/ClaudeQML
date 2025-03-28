"""
QML reloader controller module
"""
from PySide6.QtCore import QObject, Signal, Slot, Property


class QmlReloaderController(QObject):
    contentChanged = Signal()
    promptStatusChanged = Signal(str)
    isLoadingChanged = Signal(bool)
    isImageProcessingChanged = Signal(bool)
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self._content_source = ""
        self._is_loading = False
        self._is_image_processing = False
        
    def get_content_source(self): 
        return self._content_source
    
    def set_content_source(self, source):
        if self._content_source != source:
            self._content_source = source
            self.contentChanged.emit()
    
    def get_is_loading(self): 
        return self._is_loading
    
    def set_is_loading(self, loading):
        if self._is_loading != loading:
            self._is_loading = loading
            self.isLoadingChanged.emit(loading)
            
    def get_is_image_processing(self):
        return self._is_image_processing
    
    def set_is_image_processing(self, processing):
        if self._is_image_processing != processing:
            self._is_image_processing = processing
            self.isImageProcessingChanged.emit(processing)
    
    contentSource = Property(str, get_content_source, set_content_source, notify=contentChanged)
    isLoading = Property(bool, get_is_loading, set_is_loading, notify=isLoadingChanged)
    isImageProcessing = Property(bool, get_is_image_processing, set_is_image_processing, notify=isImageProcessingChanged)
    
    @Slot(str)
    def updatePromptStatus(self, status): 
        self.promptStatusChanged.emit(status)