"""Вспомогательные функции для приложения Digital Fortress"""

import string
import random
import platform
import customtkinter
try:
    from ctypes import windll, byref, sizeof, c_int
except ImportError:
    windll = None

from config.colors import COLORS


def get_system_font() -> str:
    """Получить системный шрифт для интерфейса"""
    return "Manrope, Montserrat, Segoe UI, Arial, sans-serif"


def get_mono_font() -> str:
    """Получить моноширинный шрифт"""
    return "JetBrains Mono, Fira Mono, Consolas, monospace"


def set_dark_title_bar(window):
    """Установить темную строку заголовка для Windows"""
    if platform.system() == "Windows" and windll:
        try:
            HWND = windll.user32.GetParent(window.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = c_int(2)
            windll.dwmapi.DwmSetWindowAttribute(HWND, DWMWA_USE_IMMERSIVE_DARK_MODE, byref(value), sizeof(value))
        except Exception:
            pass


def apply_panel_style(panel):
    """Применить стиль панели"""
    panel.configure(fg_color=COLORS["PANEL_COLOR"], border_width=0)


def center_window(window, width: int, height: int):
    """Центрировать окно на экране"""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.configure(
        borderwidth=0,
        highlightthickness=0,
        highlightbackground=COLORS["BORDER_COLOR"]
    )
    try:
        window.wm_attributes("-alpha", 0.99)
    except Exception:
        pass
    set_dark_title_bar(window)


def truncate_text(text: str, max_length: int) -> str:
    """Обрезать текст до указанной длины"""
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def generate_password(length: int = 16) -> str:
    """Сгенерировать случайный пароль"""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))


# Настройка темы CustomTkinter
def setup_theme():
    """Настроить тему приложения"""
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("dark-blue")
