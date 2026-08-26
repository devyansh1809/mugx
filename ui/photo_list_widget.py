"""
ui/photo_list_widget.py

A QListWidget subclass configured for icon-grid display of loaded photos.
Kept as its own file/class so main_window.py doesn't get cluttered with
widget-configuration details.
"""

from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize

from core.models import PhotoItem


class PhotoListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(96, 96))
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)
        self.setSpacing(10)
        self.setWrapping(True)
        self.setUniformItemSizes(True)

    def set_photos(self, photos: list[PhotoItem], thumbnail_paths: dict[str, str]):
        """
        Populate the list. thumbnail_paths maps original_path -> thumbnail file path
        (the caller — main_window — is responsible for generating thumbnails via
        PhotoImportService; this widget only renders what it's given).
        """
        self.clear()
        for photo in photos:
            item = QListWidgetItem(photo.sequence_name)
            thumb_path = thumbnail_paths.get(photo.original_path)
            if thumb_path:
                pixmap = QPixmap(thumb_path)
                if not pixmap.isNull():
                    item.setIcon(QIcon(pixmap))
            item.setToolTip(photo.original_path)
            self.addItem(item)
