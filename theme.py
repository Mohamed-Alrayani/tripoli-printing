from PyQt5.QtCore import QObject, pyqtSignal

DARK = {
    "name": "dark",
    "bg": "#1e1e2e",
    "card": "#252538",
    "input": "#313244",
    "input_focus": "#363649",
    "border": "#45475a",
    "border_focus": "#89b4fa",
    "text": "#cdd6f4",
    "text_sec": "#a6adc8",
    "accent": "#89b4fa",
    "green": "#a6e3a1",
    "red": "#f38ba8",
    "orange": "#fab387",
    "purple": "#cba6f7",
    "teal": "#94e2d5",
    "accent_hover": "#74b3f0",
    "green_hover": "#8fcf8a",
    "red_hover": "#dd7f95",
    "orange_hover": "#e8a070",
    "purple_hover": "#b4b0e0",
    "btn_neutral": "#585b70",
    "btn_neutral_hover": "#6c6f86",
    "table_header": "#313244",
    "table_alt": "#2e2e44",
    "selection": "rgba(137, 180, 250, 0.25)",
    "tab_bg": "#313244",
    "tab_hover": "#3a3a4f",
    "header_red": "#f38ba8",
}

LIGHT = {
    "name": "light",
    "bg": "#f4f6f9",
    "card": "#ffffff",
    "input": "#ffffff",
    "input_focus": "#f0f7ff",
    "border": "#d1d5db",
    "border_focus": "#2563eb",
    "text": "#1f2937",
    "text_sec": "#4b5563",
    "accent": "#2563eb",
    "green": "#16a34a",
    "red": "#dc2626",
    "orange": "#ea580c",
    "purple": "#7c3aed",
    "teal": "#0d9488",
    "accent_hover": "#1d4ed8",
    "green_hover": "#15803d",
    "red_hover": "#b91c1c",
    "orange_hover": "#c2410c",
    "purple_hover": "#6d28d9",
    "btn_neutral": "#6b7280",
    "btn_neutral_hover": "#4b5563",
    "table_header": "#374151",
    "table_alt": "#f0f4f8",
    "selection": "rgba(37, 99, 235, 0.15)",
    "tab_bg": "#e5e7eb",
    "tab_hover": "#d1d5db",
    "header_red": "#dc2626",
}


class ThemeManager(QObject):
    DARK = DARK
    LIGHT = LIGHT
    theme_changed = pyqtSignal(dict)
    _instance = None
    _current = DARK

    def __init__(self):
        super().__init__()
        if ThemeManager._instance is None:
            ThemeManager._instance = self

    @classmethod
    def get(cls):
        if cls._instance is None:
            ThemeManager()
        return cls._instance

    @classmethod
    def current(cls):
        return cls._current

    @classmethod
    def toggle(cls):
        cls._current = cls.LIGHT if cls._current is cls.DARK else cls.DARK
        cls.get().theme_changed.emit(cls._current)

    @classmethod
    def set_dark(cls):
        if cls._current is not cls.DARK:
            cls._current = cls.DARK
            cls.get().theme_changed.emit(cls._current)

    @classmethod
    def set_light(cls):
        if cls._current is not cls.LIGHT:
            cls._current = cls.LIGHT
            cls.get().theme_changed.emit(cls._current)
