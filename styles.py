# styles.py
STYLE_SHEET = """
QMainWindow { background-color: #f0f2f5; }

/* 左侧边栏 - 允许拉到极窄 */
#LeftSidebar {
    background-color: #1a2a3a;
    min-width: 40px;
    max-width: 300px;
}
#LeftSidebar QLabel { color: #ffffff; font-weight: bold; font-size: 13px; }

#CanvaBtn { background: #8e44ad; color: white; border-radius: 4px; padding: 6px; font-weight: bold; margin: 2px 5px; border: none; font-size: 10px; }
#AddAccBtn { background-color: #27ae60; color: white; border-radius: 4px; padding: 4px; font-weight: bold; border: none; font-size: 10px; }
#DelAccBtn { background-color: #c0392b; color: white; border-radius: 4px; padding: 4px; font-weight: bold; border: none; font-size: 10px; }
#BatchRemoveBtn { background-color: #e67e22; color: white; padding: 4px; font-size: 10px; border:none; border-radius:4px; font-weight:bold;}

#AccountList { background-color: transparent; border: none; outline: none; }
#AccountList::item { border-bottom: 1px solid rgba(255,255,255,0.05); }
#AccountList::item:selected { background-color: #3498db; }

#TopBar { background-color: #ffffff; border-bottom: 1px solid #d1d9e6; max-height: 45px; }
#UrlInput { border: 1px solid #e0e6ed; border-radius: 6px; padding: 4px 10px; background: #f8fafc; font-size: 11px; }

#TopActionBtnBlue { background-color: #3498db; color: white; font-weight: bold; border-radius: 4px; padding: 5px 12px; font-size: 11px; border: none; }
#TopActionBtnPurple { background-color: #f0e6ff; color: #6b21a8; font-weight: bold; border-radius: 4px; padding: 5px 12px; font-size: 11px; border: 1px solid #d1b3ff; }

/* 底部日志区样式 */
#LogArea {
    background-color: #121212;
    color: #ecf0f1;
    font-family: 'Consolas', monospace;
    font-size: 11px;
    padding: 5px;
    border: none;
}

/* 分割线美化 - 增加抓取宽度 */
QSplitter::handle { background-color: #d1d9e6; }
QSplitter::handle:horizontal { width: 6px; }
QSplitter::handle:vertical { height: 6px; }
"""
REAL_CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
