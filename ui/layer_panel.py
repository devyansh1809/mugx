"""
Phase 4: Layer Editor - Layer Panel UI
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel, QMenu, QToolButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
import io


class LayerPanel(QWidget):
    layer_selected = pyqtSignal(str)
    layer_visibility_toggled = pyqtSignal(str, bool)
    layer_deleted = pyqtSignal(str)
    layer_duplicated = pyqtSignal(str)
    order_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = None
        self.renderer = None
        self._building = False
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        header = QLabel("Layers")
        header.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(header)
        self.layer_list = QListWidget()
        self.layer_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.layer_list.customContextMenuRequested.connect(self._show_context_menu)
        self.layer_list.itemClicked.connect(self._on_item_clicked)
        self.layer_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.layer_list.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self.layer_list)
        controls_layout = QHBoxLayout()
        self.add_layer_btn = QToolButton()
        self.add_layer_btn.setText("+ Add")
        self.add_layer_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.add_layer_btn.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        add_menu = QMenu(self)
        add_menu.addAction("Photo", lambda: self._add_layer_requested("photo"))
        add_menu.addAction("Text", lambda: self._add_layer_requested("text"))
        add_menu.addAction("Background", lambda: self._add_layer_requested("background"))
        add_menu.addAction("Clip Art", lambda: self._add_layer_requested("clip_art"))
        add_menu.addAction("Overlay", lambda: self._add_layer_requested("overlay"))
        self.add_layer_btn.setMenu(add_menu)
        controls_layout.addWidget(self.add_layer_btn)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        controls_layout.addWidget(self.delete_btn)
        self.duplicate_btn = QPushButton("Duplicate")
        self.duplicate_btn.clicked.connect(self._on_duplicate_clicked)
        controls_layout.addWidget(self.duplicate_btn)
        layout.addLayout(controls_layout)
    
    def set_engine(self, engine) -> None:
        self.engine = engine
        self.refresh()
    
    def refresh(self) -> None:
        if not self.engine: return
        self._building = True
        self.layer_list.clear()
        layers = list(reversed(self.engine.get_layers_in_order()))
        for layer in layers:
            item = self._create_layer_item(layer)
            self.layer_list.addItem(item)
        self._building = False
    
    def _create_layer_item(self, layer) -> QListWidgetItem:
        item = QListWidgetItem()
        icon_map = {"photo": "📷", "text": "T", "background": "🎨", "clip_art": "✂️", "overlay": "✨"}
        icon = icon_map.get(layer.type, "📄")
        item.setText(f"{icon} {layer.type.title()}")
        if hasattr(layer, "image_path") and layer.image_path:
            try:
                from PIL import Image
                img = Image.open(layer.image_path)
                img.thumbnail((32, 32))
                data = io.BytesIO()
                img.save(data, format="PNG")
                pixmap = QPixmap()
                pixmap.loadFromData(data.getvalue(), "PNG")
                item.setIcon(QIcon(pixmap))
            except: pass
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if layer.properties.visible else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole, layer.id)
        if self.engine and layer.id == self.engine.document.active_layer_id: item.setSelected(True)
        return item
    
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        if self._building: return
        layer_id = item.data(Qt.ItemDataRole.UserRole)
        if layer_id: self.layer_selected.emit(layer_id)
    
    def _on_rows_moved(self, parent, start, end, dest, row) -> None:
        if self._building or not self.engine: return
        item = self.layer_list.itemAt(row)
        if item:
            layer_id = item.data(Qt.ItemDataRole.UserRole)
            if layer_id:
                current_row = self.layer_list.row(item)
                new_index = len(self.layer_list) - 1 - current_row
                self.engine.document.move_layer(layer_id, new_index)
                self.order_changed.emit()
    
    def _show_context_menu(self, position) -> None:
        item = self.layer_list.itemAt(position)
        if not item: return
        layer_id = item.data(Qt.ItemDataRole.UserRole)
        if not layer_id: return
        menu = QMenu(self)
        menu.addAction("Duplicate", lambda: self.layer_duplicated.emit(layer_id))
        menu.addAction("Delete", lambda: self.layer_deleted.emit(layer_id))
        menu.addSeparator()
        menu.addAction("Bring to Front", lambda: self._bring_to_front(layer_id))
        menu.addAction("Send to Back", lambda: self._send_to_back(layer_id))
        menu.exec_(self.layer_list.mapToGlobal(position))
    
    def _bring_to_front(self, layer_id: str) -> None:
        if self.engine:
            self.engine.bring_to_front(layer_id)
            self.refresh()
            self.order_changed.emit()
    
    def _send_to_back(self, layer_id: str) -> None:
        if self.engine:
            self.engine.send_to_back(layer_id)
            self.refresh()
            self.order_changed.emit()
    
    def _add_layer_requested(self, layer_type: str) -> None: pass
    
    def _on_delete_clicked(self) -> None:
        current_item = self.layer_list.currentItem()
        if current_item:
            layer_id = current_item.data(Qt.ItemDataRole.UserRole)
            if layer_id: self.layer_deleted.emit(layer_id)
    
    def _on_duplicate_clicked(self) -> None:
        current_item = self.layer_list.currentItem()
        if current_item:
            layer_id = current_item.data(Qt.ItemDataRole.UserRole)
            if layer_id: self.layer_duplicated.emit(layer_id)
    
    def get_selected_layer_id(self) -> str:
        current_item = self.layer_list.currentItem()
        if current_item: return current_item.data(Qt.ItemDataRole.UserRole)
        return None
