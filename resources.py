import sys
import os

def resource_path(relative_path):
    """Возвращает путь к файлу (работает и в exe)"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)