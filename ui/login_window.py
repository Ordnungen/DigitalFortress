"""Окно входа в систему и создания хранилища"""

import customtkinter
import os

from config.settings import APP_CONFIG, KDF_PATH, _
from config.colors import COLORS
from core.crypto import crypto_manager
from core.database import db_manager
from ui.base import ToastMixin
from utils.helpers import center_window, get_system_font, get_mono_font


class LoginWindow(customtkinter.CTk, ToastMixin):
    """Окно входа в систему"""

    def __init__(self, success_callback=None):
        super().__init__()
        ToastMixin.__init__(self)

        self._success_callback = success_callback
        self._overlay_frame = None
        self._active_timers = []  # Добавляем отслеживание таймеров
        self._is_destroying = False  # Флаг для предотвращения повторных вызовов

        self._init_window()
        self._setup_ui()

        if not KDF_PATH.exists():
            self._setup_mode()
        else:
            self._login_mode()

    def _init_window(self):
        """Инициализировать настройки окна"""
        self.title(_("app_title"))
        self.geometry(f"{APP_CONFIG['LOGIN_WINDOW_SIZE']['width']}x{APP_CONFIG['LOGIN_WINDOW_SIZE']['height']}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Устанавливаем иконку окна
        self._set_window_icon()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3), weight=0)
        self.grid_rowconfigure(4, weight=1)

        self.configure(
            fg_color=COLORS["BG_COLOR"],
            border_color=COLORS["BORDER_COLOR"],
            border_width=0
        )

        center_window(self, APP_CONFIG['LOGIN_WINDOW_SIZE']['width'], APP_CONFIG['LOGIN_WINDOW_SIZE']['height'])

    def _set_window_icon(self):
        """Установить иконку окна"""
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            # Игнорируем ошибки установки иконки
            pass

    def _setup_ui(self):
        """Настроить пользовательский интерфейс"""
        # Заголовок приложения
        self._create_title()

        # Подпись к полю пароля
        self._create_password_label()

        # Поле ввода пароля
        self._create_password_entry()

        # Кнопка входа/создания
        self._create_action_button()

    def _create_title(self):
        """Создать заголовок приложения"""
        self.title_label = customtkinter.CTkLabel(
            self, text="Digital Fortress",
            font=customtkinter.CTkFont(size=26, weight="bold", family=get_system_font()),
            text_color=COLORS["ACCENT_COLOR"]
        )
        self.title_label.grid(row=0, column=0, pady=(40, 12), sticky="")

    def _create_password_label(self):
        """Создать подпись к полю пароля"""
        self.password_label = customtkinter.CTkLabel(
            self, text="",
            font=customtkinter.CTkFont(size=14, family=get_system_font()),
            text_color=COLORS["TEXT_SECONDARY_COLOR"]
        )
        self.password_label.grid(row=1, column=0, pady=(0, 16), sticky="")

    def _create_password_entry(self):
        """Создать поле ввода пароля"""
        self.password_entry = customtkinter.CTkEntry(
            self, show="*", width=320, height=44,
            font=(get_mono_font(), 15), corner_radius=12,
            fg_color=COLORS["INPUT_BG_COLOR"], text_color=COLORS["TEXT_COLOR"],
            border_color=COLORS["BORDER_COLOR"], border_width=2,
            placeholder_text="Введите пароль..."
        )
        self.password_entry.grid(row=2, column=0, pady=(0, 24), sticky="")
        self.password_entry.focus()

    def _create_action_button(self):
        """Создать кнопку действия"""
        self.login_button = customtkinter.CTkButton(
            self, text=_("login"), width=200, height=44,
            font=customtkinter.CTkFont(size=15, weight="bold", family=get_system_font()),
            corner_radius=12, fg_color=COLORS["ACCENT_COLOR"], hover_color=COLORS["ACCENT_HOVER_COLOR"],
            text_color="#FFFFFF", border_width=0
        )
        self.login_button.grid(row=3, column=0, pady=(0, 30), sticky="")

    def _setup_mode(self):
        """Режим создания нового хранилища"""
        self.password_label.configure(text="Придумайте мастер-пароль")
        self._show_setup_warning()
        self.login_button.configure(text=_("create_vault"), command=self._create_new_vault)
        self.password_entry.bind("<Return>", self._create_new_vault)

    def _show_setup_warning(self):
        """Показать предупреждение при создании хранилища"""
        self._overlay_frame = customtkinter.CTkFrame(
            self, fg_color=COLORS["PANEL_COLOR"], corner_radius=18, height=300, border_width=2,
            border_color=COLORS["WARNING_COLOR"]
        )
        self._overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._overlay_frame.grid_columnconfigure(0, weight=1)
        self._overlay_frame.grid_rowconfigure((0, 1, 2), weight=0)
        self._overlay_frame.grid_rowconfigure(1, weight=1)

        icon_label = customtkinter.CTkLabel(
            self._overlay_frame, text="!",
            font=customtkinter.CTkFont(size=36, weight="bold", family=get_system_font()),
            text_color=COLORS["WARNING_COLOR"]
        )
        icon_label.grid(row=0, column=0, pady=(30, 10), sticky="")

        warning_label = customtkinter.CTkLabel(
            self._overlay_frame,
            text="ВАЖНО!\nСохраните мастер-пароль в надёжном месте.\nВосстановление невозможно!",
            font=customtkinter.CTkFont(size=14, weight="normal", family=get_system_font()),
            text_color=COLORS["WARNING_COLOR"],
            justify="center"
        )
        warning_label.grid(row=1, column=0, padx=25, sticky="nsew")

        ok_btn = customtkinter.CTkButton(
            self._overlay_frame,
            text="Понятно",
            width=180,
            height=40,
            font=customtkinter.CTkFont(size=15, weight="bold", family=get_system_font()),
            fg_color=COLORS["WARNING_COLOR"],
            hover_color="#CC7A00",
            text_color="#FFFFFF",
            corner_radius=12,
            command=self._hide_overlay
        )
        ok_btn.grid(row=2, column=0, pady=(0, 30), sticky="")

    def _hide_overlay(self):
        """Скрыть оверлей с предупреждением"""
        if self._overlay_frame:
            self._overlay_frame.destroy()
            self._overlay_frame = None

    def _login_mode(self):
        """Режим входа в существующее хранилище"""
        self.password_label.configure(text="Введите мастер-пароль")
        self.login_button.configure(text=_("login"), command=self._check_login)
        self.password_entry.bind("<Return>", self._check_login)

    def _check_login(self, event=None):
        """Проверить пароль и войти в систему"""
        if self._is_destroying:
            return

        password = self.password_entry.get()

        try:
            if crypto_manager.verify_password(password):
                self.password_label.configure(
                    text="Вход выполнен успешно",
                    text_color=COLORS["SUCCESS_COLOR"]
                )
                # Уменьшаем задержку до 800ms для быстрого отклика
                timer_id = self.after(800, self._delayed_success)
                self._active_timers.append(timer_id)
            else:
                self.password_label.configure(
                    text="Неверный пароль",
                    text_color=COLORS["ERROR_COLOR"]
                )
                self.password_entry.delete(0, "end")
                # Восстанавливаем текст через 3 секунды
                timer_id = self.after(3000, lambda: self._restore_label_text(
                    "Введите мастер-пароль",
                    COLORS["TEXT_SECONDARY_COLOR"]
                ))
                self._active_timers.append(timer_id)
        except Exception as e:
            self.password_label.configure(
                text=f"Ошибка: {str(e)[:30]}...",
                text_color=COLORS["ERROR_COLOR"]
            )

    def _create_new_vault(self, event=None):
        """Создать новое хранилище"""
        if self._is_destroying:
            return

        password = self.password_entry.get()
        if len(password) < APP_CONFIG["MASTER_PASSWORD_LENGTH"]:
            # Используем простое сообщение вместо toast для окна логина
            self.password_label.configure(
                text="Пароль должен быть не менее 6 символов",
                text_color=COLORS["WARNING_COLOR"]
            )
            timer_id = self.after(3000, lambda: self._restore_label_text(
                "Придумайте мастер-пароль",
                COLORS["TEXT_SECONDARY_COLOR"]
            ))
            self._active_timers.append(timer_id)
            return

        # Показываем предупреждение через заголовок
        self.password_label.configure(
            text="Сохраните мастер-пароль! Если потеряете - доступ невозможен",
            text_color=COLORS["WARNING_COLOR"]
        )

        try:
            crypto_manager.create_vault(password)
            db_manager.setup_database(clear=True)

            self.password_label.configure(
                text="Хранилище создано!",
                text_color=COLORS["SUCCESS_COLOR"]
            )

            if crypto_manager.verify_password(password):
                # Уменьшаем задержку до 1 секунды для создания хранилища
                timer_id = self.after(1000, self._delayed_success)
                self._active_timers.append(timer_id)
            else:
                self.password_label.configure(
                    text="Ошибка при создании хранилища",
                    text_color=COLORS["ERROR_COLOR"]
                )
        except Exception as e:
            self.password_label.configure(
                text=f"Ошибка: {str(e)[:50]}...",
                text_color=COLORS["ERROR_COLOR"]
            )

    def _restore_label_text(self, text: str, color: str):
        """Восстановить текст метки (с проверкой на уничтожение)"""
        if not self._is_destroying and self.winfo_exists():
            self.password_label.configure(text=text, text_color=color)

    def _delayed_success(self):
        """Отложенный вызов callback и закрытие окна"""
        if self._is_destroying:
            return

        try:
            if self._success_callback:
                self._success_callback()
        except Exception as e:
            print(f"Ошибка callback: {e}")
        finally:
            self._safe_destroy()

    def _cancel_all_timers(self):
        """Отменить все активные таймеры"""
        for timer_id in self._active_timers:
            try:
                if self.winfo_exists():
                    self.after_cancel(timer_id)
            except Exception:
                pass
        self._active_timers.clear()

    def _cancel_all_tkinter_timers(self):
        """Отменить все внутренние таймеры tkinter"""
        try:
            # Убираем update() - он принудительно выполняет ожидающие таймеры
            if hasattr(self, 'tk') and self.tk:
                pass  # Ничего не делаем с внутренними таймерами
        except Exception:
            pass

    def _safe_destroy(self):
        """Безопасное уничтожение окна"""
        if self._is_destroying:
            return

        self._is_destroying = True
        self._cancel_all_timers()
        self.cleanup_notifications()

        if self._overlay_frame:
            try:
                self._overlay_frame.destroy()
            except Exception:
                pass
            self._overlay_frame = None

        try:
            if self.winfo_exists():
                self.quit()  # Просто выходим из mainloop
                self.withdraw()  # Скрываем окно
        except Exception:
            pass

    def destroy(self):
        """Переопределяем destroy для очистки ресурсов"""
        self._safe_destroy()
