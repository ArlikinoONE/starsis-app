import flet as ft
import math
import traceback # <--- Это поможет нам увидеть ошибку

def main(page: ft.Page):
    # Настройка страницы
    page.title = "STARSIS Debug"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.scroll = "auto"

    try:
        # --- ТВОЙ КОД НАЧИНАЕТСЯ ЗДЕСЬ ---
        
        # 1. Проверяем импорты (нет ли забытых библиотек)
        import datetime
        
        # 2. Рисуем интерфейс
        page.add(
            ft.Text("Приложение работает!", size=30, color="green", weight="bold"),
            ft.Text("Если ты видишь это, значит Flet запустился.", size=16),
            ft.Divider(color="white"),
        )

        # --- БАЗА ДАННЫХ (LITE версия) ---
        RAW_STARS = [
            ("Полярная", 89.26), ("Вега", 38.78), ("Сириус", -16.71),
            ("Бетельгейзе", 7.41), ("Ригель", -8.20), ("Альтаир", 8.87)
        ]

        # Просто выводим список, чтобы проверить работу
        for name, dec in RAW_STARS:
            page.add(ft.Container(
                content=ft.Text(f"Звезда: {name} | Dec: {dec}°", size=18),
                padding=10,
                bgcolor="#1a1a1a",
                border_radius=5,
                margin=2
            ))

    except Exception as e:
        # --- ЕСЛИ ЕСТЬ ОШИБКА, ПОКАЗЫВАЕМ ЕЁ НА ЭКРАНЕ ---
        page.bgcolor = "red"
        error_text = traceback.format_exc()
        page.add(
            ft.Text("ОШИБКА ЗАПУСКА!", size=30, color="white", weight="bold"),
            ft.Text(f"Текст ошибки:\n{error_text}", size=14, color="white", font_family="monospace")
        )
        print(error_text)
        page.update()

if __name__ == "__main__":
    ft.app(target=main)
