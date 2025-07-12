#!/usr/bin/env python3
"""
Daily Tech News - メインエントリーポイント

新しいディレクトリ構造に対応したメインスクリプト
既存のfetch_news.pyと同等の機能を提供
"""

import sys
import os

# src ディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# メインモジュールをインポートして実行
from main import main

if __name__ == "__main__":
    main()