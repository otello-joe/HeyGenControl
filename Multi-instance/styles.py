# styles.py

STYLE_SHEET = """
QMainWindow { background-color: #f0f2f5; }
#LeftSidebar { background-color: #1a2a3a; min-width: 120px; max-width: 250px; }
#LeftSidebar QLabel { color: #ffffff; font-weight: bold; font-size: 13px; }

#CanvaBtn { background: #8e44ad; color: white; border-radius: 4px; padding: 6px; font-weight: bold; margin: 5px; border: none; font-size: 11px; }
#AddAccBtn { background-color: #27ae60; color: white; border-radius: 4px; padding: 4px; font-weight: bold; border: none; font-size: 10px; }
#DelAccBtn { background-color: #e74c3c; color: white; border-radius: 4px; padding: 4px; font-weight: bold; border: none; font-size: 10px; }
#BatchRemoveBtn { background-color: #e67e22; color: white; padding: 6px; font-size: 10px; border:none; border-radius:4px; margin-top:2px; font-weight:bold;}

#AccountList { background-color: transparent; border: none; outline: none; }
#AccountList::item { border-bottom: 1px solid rgba(255,255,255,0.05); }
#AccountList::item:selected { background-color: #3498db; }

#TopBar { background-color: #ffffff; border-bottom: 1px solid #d1d9e6; max-height: 45px; }
#UrlInput { border: 1px solid #e0e6ed; border-radius: 6px; padding: 4px 10px; background: #f8fafc; font-size: 11px; }
#JumpBtn, #RefreshBtn { background-color: #f1f2f6; color: #34495e; border-radius: 4px; padding: 4px 10px; font-size: 11px; border: 1px solid #dcdde1; }

#TopActionBtnBlue { background-color: #3498db; color: white; font-weight: bold; border-radius: 4px; padding: 5px 12px; font-size: 11px; border: none; }
#TopActionBtnPurple { background-color: #f0e6ff; color: #6b21a8; font-weight: bold; border-radius: 4px; padding: 5px 12px; font-size: 11px; border: 1px solid #d1b3ff; }

/* 底部日志区样式 - 统一设为亮绿色 */
#LogArea {
    background-color: #121212;
    color: #2ecc71;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
    padding: 8px;
    border: none;
}

QSplitter::handle { background-color: #d1d9e6; }
"""
REAL_CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
