"""Главное окно приложения Digital Fortress"""

import customtkinter
import tkinter as tk
import os
from typing import Optional, Dict, Any

from config.settings import APP_CONFIG, _
from config.colors import COLORS
from core.database import db_manager
from ui.base import ToastMixin
from utils.helpers import center_window, truncate_text, generate_password, get_system_font, get_mono_font


class MainWindow(customtkinter.CTk, ToastMixin):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        ToastMixin.__init__(self)

        self._selected_service_idx: Optional[int] = None
        self._editing_credential_id: Optional[int] = None
        self._form_widgets: Dict[str, Any] = {}
        self._service_cards: list = []

        self._init_window()
        self._setup_ui()
        self._bind_shortcuts()
        self._reset_form()

    def _init_window(self):
        """Инициализировать настройки окна"""
        self.title(_("app_title"))
        self.geometry(f"{APP_CONFIG['WINDOW_SIZE']['width']}x{APP_CONFIG['WINDOW_SIZE']['height']}")
        self.minsize(APP_CONFIG['WINDOW_SIZE']['width'], APP_CONFIG['WINDOW_SIZE']['height'])
        self.maxsize(APP_CONFIG['WINDOW_SIZE']['width'], APP_CONFIG['WINDOW_SIZE']['height'])
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)  # Добавляем обработчик закрытия

        # Устанавливаем иконку окна
        self._set_window_icon()

        self.grid_columnconfigure((0, 1), weight=1, uniform="column")
        self.grid_rowconfigure(0, weight=1)

        self.configure(
            fg_color=COLORS["BG_COLOR"],
            border_color=COLORS["BORDER_COLOR"],
            border_width=0,
            corner_radius=18
        )

        center_window(self, APP_CONFIG['WINDOW_SIZE']['width'], APP_CONFIG['WINDOW_SIZE']['height'])

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
        self._create_left_panel()
        self._create_right_panel()
        self.populate_listbox()

    def _bind_shortcuts(self):
        """Привязать горячие клавиши"""
        self.bind_all("<Control-n>", lambda e: self._reset_form())
        self.bind_all("<Control-s>", lambda e: self._save_credentials())

    def _create_left_panel(self):
        """Создать левую панель со списком паролей"""
        frame = customtkinter.CTkFrame(
            self, corner_radius=16, fg_color=COLORS["PANEL_COLOR"], border_width=0
        )
        frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # Заголовок панели
        header_frame = customtkinter.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 16))

        title_label = customtkinter.CTkLabel(
            header_frame, text="Мои пароли",
            font=customtkinter.CTkFont(size=20, weight="bold", family=get_system_font()),
            text_color=COLORS["ACCENT_COLOR"]
        )
        title_label.pack(side="left")

        # Поле поиска
        self.search_entry = customtkinter.CTkEntry(
            frame, placeholder_text="Поиск", height=40,
            font=(get_system_font(), 14), corner_radius=10,
            fg_color=COLORS["INPUT_BG_COLOR"], text_color=COLORS["TEXT_COLOR"],
            border_color=COLORS["BORDER_COLOR"], border_width=2,
            placeholder_text_color=COLORS["TEXT_SECONDARY_COLOR"]
        )
        self.search_entry.grid(row=1, column=0, padx=20, pady=(0, 14), sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.filter_listbox)

        # Скроллируемый список записей
        self.records_frame = customtkinter.CTkScrollableFrame(
            frame, fg_color=COLORS["PANEL_COLOR"], corner_radius=12, border_width=0
        )
        self.records_frame.grid(row=2, column=0, padx=0, pady=(0, 24), sticky="nsew")
        self.records_frame.grid_columnconfigure(0, weight=1)
        self.records_frame._scrollbar.grid_remove()

    def populate_listbox(self):
        """Заполнить список сохраненных паролей"""
        # Очищаем существующие виджеты
        for widget in self.records_frame.winfo_children():
            widget.destroy()

        try:
            services = db_manager.get_all_credentials()
            self.records_frame._scrollbar.grid_remove()
            self.after_idle(lambda: self._show_scrollbar_if_needed())

            if not services:
                # Показать сообщение о пустом списке
                empty_label = customtkinter.CTkLabel(
                    self.records_frame, text="Нет сохранённых записей",
                    font=customtkinter.CTkFont(size=15, family=get_system_font()),
                    text_color=COLORS["TEXT_SECONDARY_COLOR"]
                )
                empty_label.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
            else:
                # Создать карточки для каждого сервиса
                max_service_len = 28
                for idx, (service, login) in enumerate(services):
                    self._create_service_card(idx, service, login, max_service_len)

        except Exception as e:
            # Показать ошибку загрузки
            error_label = customtkinter.CTkLabel(
                self.records_frame, text="Ошибка загрузки данных",
                font=customtkinter.CTkFont(size=15, family=get_system_font()),
                text_color=COLORS["ERROR_COLOR"]
            )
            error_label.grid(row=0, column=0, sticky="ew", padx=12, pady=8)

    def _create_service_card(self, idx: int, service: str, login: str, max_service_len: int):
        """Создать карточку сервиса в списке"""
        card = customtkinter.CTkFrame(
            self.records_frame, fg_color=COLORS["PANEL_ALT_COLOR"],
            corner_radius=10, border_width=0
        )
        card.grid(row=idx, column=0, sticky="ew", padx=12, pady=6)

        service_label = customtkinter.CTkLabel(
            card, text=truncate_text(service, max_service_len),
            font=customtkinter.CTkFont(size=15, weight="normal", family=get_system_font()),
            text_color=COLORS["ACCENT_COLOR"]
        )
        service_label.grid(row=0, column=0, sticky="w", padx=(12, 4), pady=8)

        login_label = customtkinter.CTkLabel(
            card, text=truncate_text(login, 18),
            font=customtkinter.CTkFont(size=13, family=get_system_font()),
            text_color=COLORS["TEXT_SECONDARY_COLOR"]
        )
        login_label.grid(row=0, column=1, sticky="w", padx=(0, 4), pady=8)

        # Добавить эффекты наведения
        def on_enter(e, c=card):
            c.configure(fg_color=COLORS["PANEL_LIGHT_COLOR"])
        def on_leave(e, c=card):
            c.configure(fg_color=COLORS["PANEL_ALT_COLOR"])

        for widget in [card, service_label, login_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", lambda event, s=service: self.start_edit_mode(s))

    def _show_scrollbar_if_needed(self):
        """Показать полосу прокрутки если нужно"""
        frame_height = self.records_frame.winfo_height()
        content_height = sum(child.winfo_height() for child in self.records_frame.winfo_children())
        if content_height > frame_height:
            self.records_frame._scrollbar.grid()
        else:
            self.records_frame._scrollbar.grid_remove()

    def filter_listbox(self, event=None):
        """Фильтровать список по поисковому запросу с исправленной логикой"""
        search_text = self.search_entry.get().strip().lower()

        # Очистить существующие карточки
        self._clear_service_cards()

        if not search_text:
            # Показать все записи
            self.populate_listbox()
            return

        try:
            # Получить отфильтрованные данные из БД
            services = db_manager.get_all_credentials()
            filtered_services = [
                (service, login) for service, login in services
                if search_text in service.lower() or search_text in login.lower()
            ]

            self._display_filtered_services(filtered_services)

        except Exception as e:
            self.show_toast(f"Ошибка поиска: {str(e)}", COLORS["ERROR_COLOR"])

    def _clear_service_cards(self):
        """Очистить карточки сервисов"""
        for widget in self.records_frame.winfo_children():
            widget.destroy()
        self._service_cards.clear()

    def _display_filtered_services(self, services):
        """Отобразить отфильтрованные сервисы"""
        if not services:
            empty_label = customtkinter.CTkLabel(
                self.records_frame, text="Ничего не найдено",
                font=customtkinter.CTkFont(size=15, family=get_system_font()),
                text_color=COLORS["TEXT_SECONDARY_COLOR"]
            )
            empty_label.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        else:
            max_service_len = 28
            for idx, (service, login) in enumerate(services):
                self._create_service_card(idx, service, login, max_service_len)

    def _reset_form(self):
        """Сбросить форму (замена cancel_edit_mode)"""
        self._editing_credential_id = None
        self._selected_service_idx = None
        self._clear_form_data()
        self._set_form_mode(editing=False)
        if 'service' in self._form_widgets:
            self._form_widgets['service'].focus_set()

    def _set_form_mode(self, editing: bool):
        """Установить режим формы"""
        if editing:
            self.form_title.configure(text="Редактирование")
            self.save_button.grid(row=99, column=0, padx=20, pady=(18, 6), sticky="ew")
            self.delete_cancel_frame.grid(row=100, column=0, padx=20, pady=(0, 12), sticky="ew")
        else:
            self.form_title.configure(text="Новая запись")
            self.save_button.grid(row=99, column=0, padx=20, pady=(18, 14), sticky="ew")
            if hasattr(self, "delete_cancel_frame"):
                self.delete_cancel_frame.grid_forget()

    def start_edit_mode(self, service_name: str):
        """Начать редактирование записи"""
        try:
            credential = db_manager.get_credential(service_name)
            if credential:
                self._editing_credential_id, login, password, comment = credential

                form_data = {
                    'service': service_name,
                    'login': login,
                    'password': password,
                    'comment': comment or ''
                }

                self._set_form_data(form_data)
                self._set_form_mode(editing=True)
                if 'service' in self._form_widgets:
                    self._form_widgets['service'].focus_set()

        except Exception as e:
            self.show_toast(f"Ошибка загрузки записи: {str(e)}", COLORS["ERROR_COLOR"])

    def _save_credentials(self):
        """Сохранить учетные данные (приватный метод)"""
        form_data = self._get_form_data()

        # Валидация
        is_valid, error_msg = self._validate_form_data(form_data)
        if not is_valid:
            self.show_toast(error_msg, COLORS["WARNING_COLOR"])
            return

        try:
            if self._editing_credential_id:
                # Обновление существующей записи
                db_manager.save_credential(
                    form_data['service'], form_data['login'],
                    form_data['password'], form_data['comment'],
                    self._editing_credential_id
                )
                self.populate_listbox()
                self.start_edit_mode(form_data['service'])
                self.show_toast("Запись обновлена", COLORS["SUCCESS_COLOR"])
            else:
                # Создание новой записи
                if db_manager.service_exists(form_data['service']):
                    self.show_toast("Сервис уже существует", COLORS["WARNING_COLOR"])
                    return

                db_manager.save_credential(
                    form_data['service'], form_data['login'],
                    form_data['password'], form_data['comment']
                )
                self.populate_listbox()
                self._reset_form()
                self.show_toast("Запись добавлена", COLORS["SUCCESS_COLOR"])

        except Exception as e:
            self.show_toast(f"Ошибка сохранения: {str(e)}", COLORS["ERROR_COLOR"])

    def _toggle_password_visibility(self, entry_widget):
        """Переключить видимость пароля"""
        if entry_widget.cget("show") == "*":
            entry_widget.configure(show="")
            if 'toggle_btn' in self._form_widgets:
                self._form_widgets['toggle_btn'].configure(text="◎")
            self.show_toast("Пароль показан", COLORS["SUCCESS_COLOR"])
        else:
            entry_widget.configure(show="*")
            if 'toggle_btn' in self._form_widgets:
                self._form_widgets['toggle_btn'].configure(text="◉")
            self.show_toast("Пароль скрыт", COLORS["ACCENT_COLOR"])

    def _generate_password_for_field(self, entry_widget):
        """Сгенерировать пароль для поля"""
        try:
            password = generate_password(16)
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, password)
            self.show_toast("Пароль сгенерирован", COLORS["SUCCESS_COLOR"])
        except Exception as e:
            self.show_toast(f"Ошибка генерации: {str(e)}", COLORS["ERROR_COLOR"])

    def _copy_field_to_clipboard(self, entry_widget):
        """Скопировать содержимое поля в буфер обмена"""
        try:
            text = entry_widget.get()
            if not text:
                self.show_toast("Поле пустое", COLORS["WARNING_COLOR"])
                return

            self.clipboard_clear()
            self.clipboard_append(text)
            self.show_toast("Скопировано в буфер", COLORS["SUCCESS_COLOR"])
        except Exception as e:
            self.show_toast(f"Ошибка копирования: {str(e)}", COLORS["ERROR_COLOR"])

    def _create_right_panel(self):
        """Создать правую панель с формой редактирования"""
        self.form_frame = customtkinter.CTkFrame(
            self, corner_radius=16, fg_color=COLORS["PANEL_COLOR"], border_width=0
        )
        self.form_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        self.form_frame.grid_columnconfigure(0, weight=1)

        # Заголовок формы
        self.form_header_frame = customtkinter.CTkFrame(
            self.form_frame, fg_color=COLORS["PANEL_ALT_COLOR"], corner_radius=10
        )
        self.form_header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 10))

        self.form_title = customtkinter.CTkLabel(
            self.form_header_frame, text="Новая запись",
            font=customtkinter.CTkFont(size=16, weight="bold", family=get_system_font()),
            text_color=COLORS["ACCENT_COLOR"]
        )
        self.form_title.pack(pady=10)

        # Поля формы
        self._create_form_fields()

        # Кнопки управления
        self._create_form_buttons()

    def _create_form_fields(self):
        """Создать поля формы"""
        # Поле сервиса
        self._form_widgets['service'] = self._create_form_input(
            label="Сервис", start_row=1,
            placeholder="Google, GitHub, и т.д."
        )

        # Поле логина
        self._form_widgets['login'] = self._create_form_input(
            label="Логин", start_row=3,
            placeholder="user@example.com",
            copy_button=True
        )

        # Поле пароля
        self._form_widgets['password'] = self._create_form_input(
            label="Пароль", start_row=5,
            placeholder="Введите пароль",
            copy_button=True, toggle_button=True, password_field=True
        )

        # Поле комментария
        self._form_widgets['comment'] = self._create_comment_field()

    def _create_form_input(self, label: str, start_row: int, placeholder: str,
                          copy_button: bool = False, toggle_button: bool = False,
                          password_field: bool = False) -> customtkinter.CTkEntry:
        """Создать поле ввода формы с улучшенной инкапсуляцией"""
        # Метка поля
        customtkinter.CTkLabel(
            self.form_frame, text=label,
            font=customtkinter.CTkFont(size=14, weight="normal", family=get_system_font()),
            text_color=COLORS["TEXT_COLOR"]
        ).grid(row=start_row, column=0, padx=20, pady=(8, 0), sticky="w")

        # Фрейм для поля и кнопок
        field_frame = customtkinter.CTkFrame(self.form_frame, fg_color="transparent")
        field_frame.grid(row=start_row + 1, column=0, padx=20, pady=(4, 0), sticky="ew")
        field_frame.grid_columnconfigure(0, weight=1)

        # Поле ввода
        entry = customtkinter.CTkEntry(
            field_frame, placeholder_text=placeholder, width=300, height=40,
            show="*" if password_field else "",
            font=(get_system_font(), 14), corner_radius=10,
            fg_color=COLORS["INPUT_BG_COLOR"], text_color=COLORS["TEXT_COLOR"],
            border_color=COLORS["BORDER_COLOR"], border_width=2,
            placeholder_text_color=COLORS["TEXT_SECONDARY_COLOR"]
        )
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self._add_field_buttons(field_frame, entry, copy_button, toggle_button, password_field)

        return entry

    def _add_field_buttons(self, parent_frame, entry_widget, copy_button: bool,
                          toggle_button: bool, password_field: bool):
        """Добавить кнопки к полю ввода"""
        btn_col = 1

        if toggle_button and password_field:
            self._create_toggle_button(parent_frame, entry_widget, btn_col)
            btn_col += 1

            self._create_generate_button(parent_frame, entry_widget, btn_col)
            btn_col += 1

        if copy_button:
            self._create_copy_button(parent_frame, entry_widget, btn_col)

    def _create_toggle_button(self, parent, entry, column):
        """Создать кнопку переключения видимости пароля"""
        self._form_widgets['toggle_btn'] = customtkinter.CTkButton(
            parent, text="◉", width=40, height=40,
            fg_color=COLORS["PANEL_ALT_COLOR"], hover_color=COLORS["PANEL_LIGHT_COLOR"],
            text_color=COLORS["TEXT_SECONDARY_COLOR"],
            font=customtkinter.CTkFont(size=14, family=get_system_font()), corner_radius=10,
            command=lambda: self._toggle_password_visibility(entry)
        )
        self._form_widgets['toggle_btn'].grid(row=0, column=column, padx=(3, 0))

    def _create_generate_button(self, parent, entry, column):
        """Создать кнопку генерации пароля"""
        customtkinter.CTkButton(
            parent, text="⚡", width=40, height=40,
            fg_color=COLORS["SUCCESS_COLOR"], hover_color="#28A745", text_color="#FFFFFF",
            font=customtkinter.CTkFont(size=14, family=get_system_font()), corner_radius=10,
            command=lambda: self._generate_password_for_field(entry)
        ).grid(row=0, column=column, padx=(3, 0))

    def _create_copy_button(self, parent, entry, column):
        """Создать кнопку копирования"""
        customtkinter.CTkButton(
            parent, text="📋", width=44, height=44,
            fg_color=COLORS["ACCENT_COLOR"], hover_color=COLORS["ACCENT_HOVER_COLOR"],
            text_color="#FFFFFF",
            font=customtkinter.CTkFont(size=14, family=get_system_font()), corner_radius=10,
            command=lambda: self._copy_field_to_clipboard(entry)
        ).grid(row=0, column=column, padx=(3, 0))

    def _create_comment_field(self) -> customtkinter.CTkTextbox:
        """Создать поле комментария"""
        customtkinter.CTkLabel(
            self.form_frame, text="Комментарий",
            font=customtkinter.CTkFont(size=14, weight="normal", family=get_system_font()),
            text_color=COLORS["TEXT_COLOR"]
        ).grid(row=7, column=0, padx=20, pady=(8, 0), sticky="w")

        comment_field_frame = customtkinter.CTkFrame(self.form_frame, fg_color="transparent")
        comment_field_frame.grid(row=8, column=0, padx=20, pady=(4, 0), sticky="ew")
        comment_field_frame.grid_columnconfigure(0, weight=1)

        comment_entry = customtkinter.CTkTextbox(
            comment_field_frame, width=420, height=70,
            font=(get_mono_font(), 13), corner_radius=10,
            fg_color=COLORS["INPUT_BG_COLOR"], text_color=COLORS["TEXT_COLOR"],
            border_color=COLORS["BORDER_COLOR"], border_width=2, wrap="word"
        )
        comment_entry.grid(row=0, column=0, sticky="ew")

        return comment_entry

    def _create_form_buttons(self):
        """Создать кнопки управления формой"""
        self.form_frame.grid_rowconfigure(99, weight=1)

        # Кнопка сохранения
        self.save_button = customtkinter.CTkButton(
            self.form_frame, text="Сохранить", command=self.save_credentials,
            height=44, corner_radius=10,
            font=customtkinter.CTkFont(size=15, weight="bold", family=get_system_font()),
            fg_color=COLORS["ACCENT_COLOR"], hover_color=COLORS["ACCENT_HOVER_COLOR"],
            text_color="#FFFFFF"
        )
        self.save_button.grid(row=99, column=0, padx=20, pady=(12, 10), sticky="ew")

        # Фрейм для кнопок удаления и отмены
        self.delete_cancel_frame = customtkinter.CTkFrame(self.form_frame, fg_color="transparent")
        self.delete_cancel_frame.grid_columnconfigure(0, weight=1)
        self.delete_cancel_frame.grid_columnconfigure(1, weight=1)

        self.delete_button = customtkinter.CTkButton(
            self.delete_cancel_frame, text="Удалить", command=self.delete_credential,
            fg_color=COLORS["ERROR_COLOR"], hover_color="#CC2E24",
            height=44, corner_radius=10,
            font=customtkinter.CTkFont(size=15, weight="bold", family=get_system_font()),
            text_color="#FFFFFF"
        )
        self.delete_button.grid(row=0, column=0, padx=(0, 6), pady=0, sticky="ew")

        self.cancel_button = customtkinter.CTkButton(
            self.delete_cancel_frame, text="Отмена", command=self.cancel_edit_mode,
            fg_color=COLORS["BUTTON_COLOR"], hover_color=COLORS["PANEL_LIGHT_COLOR"],
            height=44, corner_radius=10,
            font=customtkinter.CTkFont(size=15, weight="bold", family=get_system_font()),
            text_color=COLORS["TEXT_COLOR"]
        )
        self.cancel_button.grid(row=0, column=1, padx=(6, 0), pady=0, sticky="ew")

        self.delete_cancel_frame.grid_forget()

    def _get_form_data(self) -> Dict[str, str]:
        """Получить данные из формы"""
        if not self._form_widgets:
            return {'service': '', 'login': '', 'password': '', 'comment': ''}

        return {
            'service': self._form_widgets.get('service', tk.StringVar()).get() if hasattr(self._form_widgets.get('service', None), 'get') else '',
            'login': self._form_widgets.get('login', tk.StringVar()).get() if hasattr(self._form_widgets.get('login', None), 'get') else '',
            'password': self._form_widgets.get('password', tk.StringVar()).get() if hasattr(self._form_widgets.get('password', None), 'get') else '',
            'comment': self._form_widgets.get('comment', tk.Text()).get("1.0", tk.END).strip() if hasattr(self._form_widgets.get('comment', None), 'get') else ''
        }

    def _set_form_data(self, data: Dict[str, str]):
        """Установить данные в форму"""
        if not self._form_widgets:
            return

        if 'service' in self._form_widgets:
            self._form_widgets['service'].delete(0, tk.END)
            self._form_widgets['service'].insert(0, data.get('service', ''))

        if 'login' in self._form_widgets:
            self._form_widgets['login'].delete(0, tk.END)
            self._form_widgets['login'].insert(0, data.get('login', ''))

        if 'password' in self._form_widgets:
            self._form_widgets['password'].delete(0, tk.END)
            self._form_widgets['password'].insert(0, data.get('password', ''))
            self._form_widgets['password'].configure(show="*")

        if 'comment' in self._form_widgets:
            self._form_widgets['comment'].delete("1.0", tk.END)
            if data.get('comment'):
                self._form_widgets['comment'].insert("1.0", data['comment'])

    def _clear_form_data(self):
        """Очистить данные формы"""
        if not self._form_widgets:
            return

        for field in ['service', 'login', 'password']:
            if field in self._form_widgets:
                self._form_widgets[field].delete(0, tk.END)

        if 'comment' in self._form_widgets:
            self._form_widgets['comment'].delete("1.0", tk.END)

    def _validate_form_data(self, data: Dict[str, str]) -> tuple[bool, str]:
        """Валидировать данные формы"""
        if not data['service'] or not data['login'] or not data['password']:
            return False, "Заполните все обязательные поля"

        if len(data['password']) < APP_CONFIG.get("MIN_PASSWORD_LENGTH", 6):
            return False, "Пароль слишком короткий"

        if len(data['service']) > 100:
            return False, "Название сервиса слишком длинное"

        if len(data['login']) > 100:
            return False, "Логин слишком длинный"

        return True, ""

    def delete_credential(self):
        """Удалить текущую запись"""
        if self._editing_credential_id is None:
            return

        self.show_confirm(
            "Вы уверены, что хотите удалить запись?",
            self._delete_credential_confirmed
        )

    def _delete_credential_confirmed(self):
        """Подтвердить удаление записи"""
        try:
            db_manager.delete_credential(self._editing_credential_id)
            self.populate_listbox()
            self.cancel_edit_mode()
            self.show_toast("Удалено", COLORS["SUCCESS_COLOR"])
        except Exception as e:
            self.show_toast(str(e), COLORS["ERROR_COLOR"])

    def _cancel_all_tkinter_timers(self):
        """Отменить все внутренние таймеры tkinter"""
        try:
            # Убираем update() - он принудительно выполняет ожидающие таймеры
            if hasattr(self, 'tk') and self.tk:
                pass  # Ничего не делаем с внутренними таймерами
        except Exception:
            pass

    def _on_closing(self):
        """Обработчик закрытия окна"""
        try:
            self.cleanup_notifications()
            self.quit()  # Выходим из mainloop
            self.withdraw()  # Скрываем окно
        except Exception:
            pass
        finally:
            # Принудительно завершаем процесс
            import os
            os._exit(0)

    def destroy(self):
        """Переопределяем destroy для очистки ресурсов"""
        try:
            self.cleanup_notifications()
            super().destroy()
        except Exception:
            pass

    # Публичные методы для внешнего API
    def save_credentials(self):
        """Публичный метод сохранения"""
        self._save_credentials()

    def cancel_edit_mode(self):
        """Публичный метод отмены редактирования"""
        self._reset_form()

    def close(self):
        """Закрыть окно"""
        self.destroy()
