"""Selectable thumbnail dialog for customer photos."""
from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QDialogButtonBox,
)

from core.models import PhotoItem
from core.photo_import_service import PhotoImportService


class PhotoSelectionDialog(QDialog):
    """Lets an operator select the exact photos to use after scanning a folder.

    Selected items preserve their visible source order. This prevents the former
    behavior where Auto Fill silently used the first N files in a folder.
    """

    def __init__(self, photos: List[PhotoItem], photo_service: PhotoImportService, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Customer Photos")
        self.resize(860, 600)
        self._photos = photos
        self._service = photo_service
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        info = QLabel("Tick the exact photos to use. Their order below is the Auto Fill order.")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QPixmap(110, 110).size())
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(12)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        layout.addWidget(self.list_widget, 1)

        for photo in self._photos:
            item = QListWidgetItem(f"{photo.sequence_name}\n{Path(photo.original_path).name}")
            item.setData(Qt.ItemDataRole.UserRole, photo.index)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            thumb = self._service.get_thumbnail(photo)
            if thumb:
                pixmap = QPixmap(thumb)
                if not pixmap.isNull():
                    item.setIcon(QIcon(pixmap))
            self.list_widget.addItem(item)

        controls = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        controls.addWidget(self.select_all_button)
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
        controls.addWidget(self.clear_button)
        controls.addStretch()
        self.count_label = QLabel()
        controls.addWidget(self.count_label)
        layout.addLayout(controls)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept_if_selected)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.list_widget.itemChanged.connect(self._update_count)
        self._update_count()

    def _set_all(self, state: Qt.CheckState):
        for row in range(self.list_widget.count()):
            self.list_widget.item(row).setCheckState(state)

    def _update_count(self, *_):
        count = len(self.selected_photos())
        self.count_label.setText(f"{count} photo(s) selected")

    def _accept_if_selected(self):
        if self.selected_photos():
            self.accept()
        else:
            self.count_label.setText("Select at least one photo.")

    def selected_photos(self) -> List[PhotoItem]:
        selected_indexes = []
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                selected_indexes.append(item.data(Qt.ItemDataRole.UserRole))
        by_index = {p.index: p for p in self._photos}
        return [by_index[i] for i in selected_indexes if i in by_index]
