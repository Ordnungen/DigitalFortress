"""Базовые UI компоненты и функции"""

import customtkinter
from typing import Callable, Optional, Protocol
from abc import ABC, abstractmethod

from config.colors import COLORS
from config.settings import APP_CONFIG
from utils.helpers import get_system_font


class ToastCapable(Protocol):
    """Протокол для объектов, способных отображать toast сообщения"""
    def after(self, ms: int, func: Callable) -> str: ...
    def after_cancel(self, id: str) -> None: ...


class NotificationDisplay(ABC):
    """Абстрактный класс для отображения уведомлений"""

    @abstractmethod
    def show_notification(self, message: str, color: str, duration: int) -> None:
        """Показать уведомление"""
        pass

    @abstractmethod
    def hide_notification(self) -> None:
        """Скрыть уведомление"""
        pass


class FormTitleNotification(NotificationDisplay):
    """Уведомления через заголовок формы"""

    def __init__(self, form_title_widget, form_header_widget=None):
        self._form_title = form_title_widget
        self._form_header = form_header_widget
        self._original_title = None
        self._original_color = None
        self._is_showing = False

    def show_notification(self, message: str, color: str, duration: int) -> None:
        """Показать уведомление в заголовке формы"""
        if not self._form_title or not hasattr(self._form_title, 'configure'):
            return

        # Сохранить оригинальные значения только если не показываем уведомление
        if not self._is_showing:
            try:
                self._original_title = self._form_title.cget("text")
                self._original_color = self._form_title.cget("text_color")
            except Exception:
                # Fallback если виджет не поддерживает эти свойства
                self._original_title = "Заголовок"
                self._original_color = COLORS.get("TEXT_COLOR", "#000000")

        try:
            self._form_title.configure(
                text=message,
                text_color="#FFFFFF",
                font=customtkinter.CTkFont(size=16, weight="bold", family=get_system_font())
            )

            if self._form_header and hasattr(self._form_header, 'configure'):
                self._form_header.configure(fg_color=color)

            self._is_showing = True

        except Exception as e:
            print(f"Ошибка отображения уведомления: {e}")

    def hide_notification(self) -> None:
        """Скрыть уведомление и восстановить оригинальный заголовок"""
        if not self._is_showing or not self._form_title:
            return

        try:
            if self._original_title is not None and self._original_color is not None:
                self._form_title.configure(
                    text=self._original_title,
                    text_color=self._original_color
                )

            if self._form_header and hasattr(self._form_header, 'configure'):
                self._form_header.configure(fg_color=COLORS.get("PANEL_ALT_COLOR", "#333333"))

            self._is_showing = False

        except Exception as e:
            print(f"Ошибка скрытия уведомления: {e}")


class ToastMixin:
    """Миксин для отображения уведомлений с улучшенной инкапсуляцией"""

    def __init__(self):
        self._toast_timers = {}
        self._notification_frames = {}
        self._notification_display = None
        self._is_initialized = False

    def _initialize_notifications(self):
        """Инициализировать систему уведомлений"""
        if self._is_initialized:
            return

        # Попытать найти элементы формы для уведомлений
        form_title = getattr(self, 'form_title', None)
        form_header = getattr(self, 'form_header_frame', None)

        if form_title:
            self._notification_display = FormTitleNotification(form_title, form_header)

        self._is_initialized = True

    def show_toast(self, message: str, color: str = None, important: bool = False):
        """Показать всплывающее уведомление с улучшенной валидацией"""
        # Проверяем, что окно еще существует
        if not self.winfo_exists():
            return

        if not message or not isinstance(message, str):
            return

        message = message.strip()
        if not message:
            return

        color = color or COLORS.get("ACCENT_COLOR", "#007ACC")

        # Для важных или длинных сообщений использовать предупреждение
        if important or len(message) > 50:
            self.show_warning(message)
            return

        self._initialize_notifications()

        if self._notification_display:
            self._show_form_toast(message, color)
        else:
            # Fallback - показать как предупреждение
            self.show_warning(message)

    def _destroy_notification_frame(self, frame_key: str):
        """Уничтожить фрейм уведомления по ключу"""
        # Отменить таймер
        self._cancel_timer(frame_key)

        # Уничтожить фрейм если он существует
        if frame_key in self._notification_frames:
            try:
                frame = self._notification_frames[frame_key]
                if frame and hasattr(frame, 'winfo_exists'):
                    if frame.winfo_exists():
                        frame.destroy()
                del self._notification_frames[frame_key]
            except Exception:
                # Игнорируем ошибки при уничтожении
                pass

    def show_warning(self, message: str):
        """Показать предупреждение с улучшенным управлением ресурсами"""
        # Проверяем, что окно еще существует
        if not self.winfo_exists():
            return

        if not message or not isinstance(message, str):
            return

        message = message.strip()
        if not message:
            return

        # Очистить предыдущее предупреждение
        self._destroy_notification_frame('warning')

        try:
            warning_frame = self._create_warning_frame(message)
            self._notification_frames['warning'] = warning_frame

            # Установить таймер на автоскрытие
            if hasattr(self, 'after') and self.winfo_exists():
                timer_id = self.after(
                    APP_CONFIG.get("WARNING_DURATION", 5000),
                    lambda: self._destroy_notification_frame('warning')
                )
                self._toast_timers['warning'] = timer_id

        except Exception as e:
            print(f"Ошибка создания предупреждения: {e}")

    def _show_form_toast(self, message: str, color: str):
        """Показать toast в заголовке формы"""
        # Проверяем, что окно еще существует
        if not self.winfo_exists():
            return

        # Отменить предыдущий таймер
        self._cancel_timer('toast')

        # Показать уведомление
        self._notification_display.show_notification(
            message, color, APP_CONFIG.get("TOAST_DURATION", 3000)
        )

        # Установить таймер на скрытие
        if hasattr(self, 'after') and self.winfo_exists():
            timer_id = self.after(
                APP_CONFIG.get("TOAST_DURATION", 3000),
                self._hide_form_toast
            )
            self._toast_timers['toast'] = timer_id

    def _hide_form_toast(self):
        """Скрыть toast в заголовке формы"""
        if self._notification_display:
            self._notification_display.hide_notification()
        self._toast_timers.pop('toast', None)

    def show_warning(self, message: str):
        """Показать предупреждение с улучшенным управлением ресурсами"""
        # Проверяем, что окно еще существует
        if not self.winfo_exists():
            return

        if not message or not isinstance(message, str):
            return

        message = message.strip()
        if not message:
            return

        # Очистить предыдущее предупреждение
        self._destroy_notification_frame('warning')

        try:
            warning_frame = self._create_warning_frame(message)
            self._notification_frames['warning'] = warning_frame

            # Установить таймер на автоскрытие
            if hasattr(self, 'after') and self.winfo_exists():
                timer_id = self.after(
                    APP_CONFIG.get("WARNING_DURATION", 5000),
                    lambda: self._destroy_notification_frame('warning')
                )
                self._toast_timers['warning'] = timer_id

        except Exception as e:
            print(f"Ошибка создания предупреждения: {e}")

    def _create_warning_frame(self, message: str) -> customtkinter.CTkFrame:
        """Создать фрейм предупреждения"""
        warning_frame = customtkinter.CTkFrame(
            self, fg_color=COLORS.get("WARNING_COLOR", "#FF8C00"),
            corner_radius=12, border_width=0
        )

        content_frame = customtkinter.CTkFrame(warning_frame, fg_color="transparent")
        content_frame.pack(padx=16, pady=12)

        icon_label = customtkinter.CTkLabel(
            content_frame, text="!",
            font=customtkinter.CTkFont(size=18, weight="bold", family=get_system_font()),
            text_color="#FFFFFF"
        )
        icon_label.pack(side="left", padx=(0, 8))

        # Ограничить длину сообщения для отображения
        display_message = message[:200] + "..." if len(message) > 200 else message

        label = customtkinter.CTkLabel(
            content_frame, text=display_message,
            font=customtkinter.CTkFont(size=14, weight="normal", family=get_system_font()),
            text_color="#FFFFFF", wraplength=300
        )
        label.pack(side="left")

        # Позиционировать фрейм
        warning_frame.update_idletasks()
        warning_frame.place(relx=0.5, y=20, anchor="n")

        return warning_frame

    def show_confirm(self, message: str, on_yes: Callable, on_no: Optional[Callable] = None):
        """Показать диалог подтверждения с улучшенной валидацией"""
        if not message or not isinstance(message, str) or not callable(on_yes):
            return

        message = message.strip()
        if not message:
            return

        # Очистить предыдущий диалог
        self._destroy_notification_frame('confirm')

        try:
            confirm_frame = self._create_confirm_frame(message, on_yes, on_no)
            self._notification_frames['confirm'] = confirm_frame

            # Установить таймер на автоскрытие
            if hasattr(self, 'after'):
                timer_id = self.after(
                    APP_CONFIG.get("WARNING_DURATION", 10000),
                    lambda: self._destroy_notification_frame('confirm')
                )
                self._toast_timers['confirm'] = timer_id

        except Exception as e:
            print(f"Ошибка создания диалога подтверждения: {e}")

    def _create_confirm_frame(self, message: str, on_yes: Callable,
                            on_no: Optional[Callable]) -> customtkinter.CTkFrame:
        """Создать фрейм подтверждения"""
        confirm_frame = customtkinter.CTkFrame(
            self, fg_color=COLORS.get("PANEL_COLOR", "#2B2B2B"),
            corner_radius=16, border_width=2,
            border_color=COLORS.get("BORDER_COLOR", "#404040")
        )

        content_frame = customtkinter.CTkFrame(confirm_frame, fg_color="transparent")
        content_frame.pack(padx=20, pady=(16, 0))

        icon_label = customtkinter.CTkLabel(
            content_frame, text="?",
            font=customtkinter.CTkFont(size=18, weight="bold", family=get_system_font()),
            text_color=COLORS.get("WARNING_COLOR", "#FF8C00")
        )
        icon_label.pack(side="left", padx=(0, 8))

        # Ограничить длину сообщения
        display_message = message[:150] + "..." if len(message) > 150 else message

        label = customtkinter.CTkLabel(
            content_frame, text=display_message,
            font=customtkinter.CTkFont(size=14, weight="normal", family=get_system_font()),
            text_color=COLORS.get("TEXT_COLOR", "#FFFFFF"), wraplength=250
        )
        label.pack(side="left")

        btn_frame = customtkinter.CTkFrame(confirm_frame, fg_color="transparent")
        btn_frame.pack(pady=(12, 16))

        yes_btn = customtkinter.CTkButton(
            btn_frame, text="Да", width=90, height=36,
            fg_color=COLORS.get("SUCCESS_COLOR", "#32CD32"), hover_color="#28A745",
            corner_radius=8, font=customtkinter.CTkFont(size=14, weight="bold", family=get_system_font()),
            command=lambda: self._handle_confirm_response('confirm', on_yes)
        )
        yes_btn.pack(side="left", padx=(0, 8))

        no_btn = customtkinter.CTkButton(
            btn_frame, text="Нет", width=90, height=36,
            fg_color=COLORS.get("BUTTON_COLOR", "#404040"),
            hover_color=COLORS.get("PANEL_LIGHT_COLOR", "#505050"),
            corner_radius=8, font=customtkinter.CTkFont(size=14, weight="bold", family=get_system_font()),
            command=lambda: self._handle_confirm_response('confirm', on_no)
        )
        no_btn.pack(side="left")

        # Позиционировать фрейм
        confirm_frame.update_idletasks()
        confirm_frame.place(relx=0.5, y=20, anchor="n")

        return confirm_frame

    def _handle_confirm_response(self, frame_key: str, callback: Optional[Callable]):
        """Обработать ответ в диалоге подтверждения"""
        self._destroy_notification_frame(frame_key)

        if callback and callable(callback):
            try:
                callback()
            except Exception as e:
                print(f"Ошибка выполнения callback: {e}")

    def _cancel_timer(self, timer_key: str):
        """Отменить таймер по ключу"""
        if timer_key in self._toast_timers:
            try:
                if hasattr(self, 'winfo_exists') and self.winfo_exists() and hasattr(self, 'after_cancel'):
                    self.after_cancel(self._toast_timers[timer_key])
            except Exception:
                pass
            del self._toast_timers[timer_key]

    def cleanup_notifications(self):
        """Очистить все уведомления (вызывать при закрытии окна)"""
        try:
            # Отменить все таймеры
            for timer_key in list(self._toast_timers.keys()):
                self._cancel_timer(timer_key)

            # Уничтожить все фреймы
            for frame_key in list(self._notification_frames.keys()):
                self._destroy_notification_frame(frame_key)

            # Скрыть уведомление в заголовке
            if self._notification_display:
                try:
                    self._notification_display.hide_notification()
                except Exception:
                    pass

            # Очистить все ссылки
            self._toast_timers.clear()
            self._notification_frames.clear()
            self._notification_display = None

            # Дополнительная очистка для customtkinter
            if hasattr(self, 'after_idle'):
                try:
                    # Отменяем все idle задачи
                    self.after_idle(lambda: None)
                except Exception:
                    pass

        except Exception:
            # Игнорируем все ошибки при очистке
            pass

    # Методы обратной совместимости (deprecated)
    def _restore_form_title(self):
        """Устаревший метод - используйте _hide_form_toast"""
        self._hide_form_toast()

    def _destroy_warning_frame(self):
        """Устаревший метод - используйте _destroy_notification_frame"""
        self._destroy_notification_frame('warning')

    def _destroy_confirm_frame(self):
        """Устаревший метод - используйте _destroy_notification_frame"""
        self._destroy_notification_frame('confirm')

    def _confirm_yes(self, callback: Callable):
        """Устаревший метод - используйте _handle_confirm_response"""
        self._handle_confirm_response('confirm', callback)

    def _confirm_no(self, callback: Optional[Callable]):
        """Устаревший метод - используйте _handle_confirm_response"""
        self._handle_confirm_response('confirm', callback)
