"""
Digital Fortress - Менеджер паролей
Точка входа в приложение
"""

from utils.helpers import setup_theme
from ui.main_window import MainWindow
from ui.login_window import LoginWindow


def main():
    """Главная функция приложения"""
    import signal
    import sys
    import os
    import tkinter

    def signal_handler(sig, frame):
        """Обработчик сигналов для принудительного завершения"""
        os._exit(0)

    # Устанавливаем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Подавляем ошибки Tcl/Tk
    def suppress_tcl_errors(*args):
        pass

    try:
        # Настроить тему интерфейса
        setup_theme()

        # Переменная для хранения ссылки на главное окно
        main_app = None

        def on_login_success():
            """Callback для успешного входа"""
            nonlocal main_app
            # Создать главное окно
            main_app = MainWindow()
            # Подавляем ошибки для главного окна
            if hasattr(main_app, 'tk'):
                main_app.tk.call('set', 'tcl_traceExec', 0)

        # Создать и показать окно входа
        login = LoginWindow(success_callback=on_login_success)

        # Подавляем ошибки для окна логина
        if hasattr(login, 'tk'):
            login.tk.call('set', 'tcl_traceExec', 0)

        login.mainloop()

        # После закрытия окна логина, запустить главное окно если оно создано
        if main_app:
            main_app.mainloop()

    except KeyboardInterrupt:
        # Обработка Ctrl+C
        pass
    except Exception as e:
        print(f"Критическая ошибка приложения: {e}")
    finally:
        # Принудительно завершаем все процессы
        os._exit(0)  # Используем только os._exit


if __name__ == "__main__":
    main()
