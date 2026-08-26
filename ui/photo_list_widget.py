"""
ui/photo_list_widget.py

Icon-grid list of loaded photos.
"""
from __future__ import annotations

from typing import List, Dict

from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, pyqtSignal

from core.models import PhotoItem


class PhotoListWidget(QListWidget):
    photo_double_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(96, 96))
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)
        self.setSpacing(10)
        self.setWrapping(True)
        self.setUniformItemSizes(True)
        self._photos: List[PhotoItem] = []
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def set_photos(self, photos: List[PhotoItem], thumbnail_paths: Dict[str, str]):
        self._photos = photos
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

    def _on_item_double_clicked(self, item: QListWidgetItem):
        row = self.row(item)
        if 0 <= row < len(self._photos):
            self.photo_double_clicked.emit(self._photos[row].index)
