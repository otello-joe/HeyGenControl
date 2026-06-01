# ui_components.py
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QListWidget, QLineEdit, QDoubleSpinBox, QAbstractItemView)
from PyQt6.QtCore import Qt

class LeftSidebar(QFrame):
    def __init__(self, switch_cb, add_cb, del_cb, canva_cb):
        super().__init__()
        self.setObjectName("LeftSidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 15, 5, 10); layout.setSpacing(5)

        title = QLabel("HeyGen 群控 v1.0")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(title)

        self.btn_canva_root = QPushButton("🎨 公共 Canva 母本"); self.btn_canva_root.setObjectName("CanvaBtn")
        self.btn_canva_root.clicked.connect(canva_cb); layout.addWidget(self.btn_canva_root)

        btn_grid = QVBoxLayout(); h1 = QHBoxLayout()
        self.btn_add = QPushButton("+添加"); self.btn_add.setObjectName("AddAccBtn"); self.btn_add.clicked.connect(add_cb)
        self.btn_del = QPushButton("-移除"); self.btn_del.setObjectName("DelAccBtn"); self.btn_del.clicked.connect(del_cb)
        h1.addWidget(self.btn_add); h1.addWidget(self.btn_del); btn_grid.addLayout(h1)

        self.btn_batch = QPushButton("📦 批量移除显示"); self.btn_batch.setObjectName("BatchRemoveBtn")
        self.btn_batch.clicked.connect(del_cb)
        layout.addLayout(btn_grid); layout.addWidget(self.btn_batch)

        self.account_list = QListWidget(); self.account_list.setObjectName("AccountList")
        self.account_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.account_list.itemClicked.connect(lambda i: switch_cb(i.data(Qt.ItemDataRole.UserRole)))
        layout.addWidget(self.account_list)

class TopBar(QFrame):
    # 增加了一个 clear_canva_cb 回调
    def __init__(self, jump_cb, refresh_cb, zoom_cb, heygen_home_cb, sync_canva_cb, clear_canva_cb):
        super().__init__()
        self.setObjectName("TopBar")
        layout = QHBoxLayout(self); layout.setContentsMargins(10, 0, 10, 0); layout.setSpacing(8)

        self.url_input = QLineEdit("https://app.heygen.com/login"); self.url_input.setObjectName("UrlInput")
        self.url_input.returnPressed.connect(lambda: jump_cb(self.url_input.text()))
        self.btn_jump = QPushButton("跳转"); self.btn_jump.setObjectName("JumpBtn")
        self.btn_jump.clicked.connect(lambda: jump_cb(self.url_input.text()))
        self.btn_refresh = QPushButton("刷新"); self.btn_refresh.setObjectName("RefreshBtn")
        self.btn_refresh.clicked.connect(refresh_cb)

        # 导航按钮组
        self.btn_heygen = QPushButton("🏠 HeyGen 首页"); self.btn_heygen.setObjectName("TopActionBtnBlue"); self.btn_heygen.clicked.connect(heygen_home_cb)
        self.btn_sync = QPushButton("🎨 同步至 Canva"); self.btn_sync.setObjectName("TopActionBtnPurple"); self.btn_sync.clicked.connect(sync_canva_cb)

        # 【新增】：重置 Canva 按钮
        self.btn_clear_canva = QPushButton("🗑️ 重置 Canva"); self.btn_clear_canva.setObjectName("TopActionBtnRed"); self.btn_clear_canva.clicked.connect(clear_canva_cb)

        self.zoom_spin = QDoubleSpinBox(); self.zoom_spin.setRange(0.1, 2.0); self.zoom_spin.setValue(0.75); self.zoom_spin.setObjectName("ZoomSpin"); self.zoom_spin.valueChanged.connect(zoom_cb)

        layout.addWidget(self.url_input, stretch=1); layout.addWidget(self.btn_jump); layout.addWidget(self.btn_refresh)
        layout.addWidget(self.btn_heygen); layout.addWidget(self.btn_sync); layout.addWidget(self.btn_clear_canva); layout.addWidget(self.zoom_spin)
