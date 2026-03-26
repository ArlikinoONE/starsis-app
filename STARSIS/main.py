import flet as ft
import math
import warnings
import asyncio
from skyfield.api import Star, load, Topos

import os # Не забудьте этот импорт!

# ... (ваши импорты)

# Получаем путь к папке assets внутри телефона
assets_path = os.path.join(os.path.dirname(__file__), "assets")
bsp_path = os.path.join(assets_path, "de421.bsp")

# Загружаем данные
ts = load.timescale()

# Проверяем, есть ли файл, и загружаем
if os.path.exists(bsp_path):
    planets_data = load(bsp_path)
else:
    # Если файла нет, пытаемся скачать (резервный вариант)
    planets_data = load('de421.bsp')

earth = planets_data['earth']

# --- БАЗЫ ДАННЫХ (Звезды, Галактики, Туманности, Скопления) ---
RAW_STARS = [
    ("Полярная", "Малая Медведица", 37.95, 89.26, 431.0), ("Вега", "Лира", 279.23, 38.78, 25.04),
    ("Арктур", "Волопас", 213.91, 19.18, 36.7), ("Сириус", "Большой Пес", 101.29, -16.71, 8.6),
    ("Канопус", "Киль", 95.99, -52.70, 310.0), ("Толиман", "Центавр", 219.90, -60.83, 4.37),
    ("Капелла", "Возничий", 79.17, 45.99, 42.8), ("Ригель", "Орион", 78.63, -8.20, 860.0),
    ("Процион", "Малый Пес", 114.82, 5.22, 11.4), ("Ахернар", "Эридан", 24.43, -57.24, 144.0),
    ("Бетельгейзе", "Орион", 88.79, 7.41, 640.0), ("Альтаир", "Орел", 297.70, 8.87, 16.7),
    ("Альдебаран", "Телец", 68.98, 16.51, 65.3), ("Антарес", "Скорпион", 247.35, -26.43, 550.0),
    ("Спика", "Дева", 201.30, -11.16, 250.0), ("Поллукс", "Близнецы", 116.33, 28.03, 33.7),
    ("Фомальгаут", "Южная Рыба", 344.41, -29.62, 25.1), ("Денеб", "Лебедь", 310.36, 45.28, 2600.0),
    ("Регул", "Лев", 152.09, 11.97, 79.3), ("Адара", "Большой Пес", 104.65, -28.97, 430.0),
    ("Кастор", "Близнецы", 113.65, 31.89, 51.5), ("Гакрукс", "Южный Крест", 187.79, -57.11, 88.6),
    ("Шаула", "Скорпион", 263.40, -37.10, 570.0), ("Беллатрикс", "Орион", 81.28, 6.35, 250.0),
    ("Эльнат", "Телец", 81.57, 28.61, 134.0), ("Миаплацидус", "Киль", 138.30, -69.72, 113.0),
    ("Альнилам", "Орион", 84.05, -1.20, 2000.0), ("Альнаир", "Журавль", 332.06, -46.96, 101.0),
    ("Алиот", "Большая Медведица", 193.47, 55.96, 82.6), ("Мирфак", "Персей", 51.08, 49.86, 510.0),
    ("Дубхе", "Большая Медведица", 165.93, 61.75, 123.0), ("Регор", "Паруса", 122.40, -47.33, 1100.0),
    ("Канкар", "Киль", 128.55, -59.51, 630.0), ("Альнитак", "Орион", 85.19, -1.94, 730.0),
    ("Каус Аустралис", "Стрелец", 276.10, -34.38, 143.0), ("Мицар", "Большая Медведица", 199.10, 54.93, 82.8),
    ("Альфард", "Гидра", 141.93, -8.66, 177.0), ("Хамаль", "Овен", 31.79, 23.46, 65.8),
    ("Денебола", "Лев", 177.26, 14.57, 35.9), ("Альдерамин", "Цефей", 318.52, 62.59, 49.0),
    ("Саиф", "Орион", 86.94, -9.67, 650.0), ("Альхена", "Близнецы", 99.43, 16.39, 109.0),
    ("Менкалинан", "Возничий", 89.87, 44.95, 81.0), ("Мирцам", "Большой Пес", 95.67, -17.96, 500.0),
    ("Рас-Альхаге", "Змееносец", 263.73, 12.56, 48.6), ("Алголь", "Персей", 46.21, 40.96, 90.0),
    ("Шеат", "Пегас", 345.94, 28.08, 196.0), ("Альферац", "Андромеда", 2.10, 29.09, 97.0),
    ("Мирах", "Андромеда", 17.43, 35.62, 197.0), ("Альмак", "Андромеда", 30.97, 42.33, 350.0),
    ("Дифда", "Кит", 10.89, -17.99, 96.0), ("Менкар", "Кит", 45.57, 4.09, 250.0),
    ("Анкаа", "Феникс", 6.55, -42.31, 77.0), ("Эниф", "Пегас", 326.05, 9.87, 690.0),
    ("Маркаб", "Пегас", 346.19, 15.21, 133.0), ("Зосма", "Лев", 168.53, 20.52, 58.4),
    ("Мерак", "Большая Медведица", 165.46, 56.38, 79.7), ("Фекда", "Большая Медведица", 178.46, 53.69, 83.2),
    ("Мегрец", "Большая Медведица", 183.86, 57.03, 80.5), ("Алькаид", "Большая Медведица", 206.88, 49.31, 104.0),
    ("Кохаб", "Малая Медведица", 222.68, 74.16, 131.0), ("Мира", "Кит", 34.83, -2.98, 300.0),
    ("Денеб Кайтос", "Кит", 10.89, -17.98, 96.0), ("Арнеб", "Заяц", 83.18, -17.82, 2200.0),
    ("Нихал", "Заяц", 83.18, -20.84, 156.0), ("Муфрид", "Волопас", 208.67, 18.39, 37.0),
    ("Изар", "Волопас", 221.24, 27.07, 210.0),
]

RAW_GALAXIES = [
    ("Андромеда", "Андромеда", 10.68, 41.27, 2540000.0), ("Треугольник", "Треугольник", 23.46, 30.66, 3000000.0),
    ("M81 (Боде)", "Большая Медведица", 148.88, 69.07, 11800000.0), ("M82 (Сигара)", "Большая Медведица", 148.96, 69.68, 11500000.0),
    ("M51 (Водоворот)", "Гончие Псы", 202.73, 47.19, 23000000.0), ("M104 (Сомбреро)", "Дева", 189.99, -11.62, 29000000.0),
    ("Центавр А", "Центавр", 201.36, -43.02, 11000000.0), ("Южная Вертушка", "Гидра", 204.25, -29.86, 15000000.0),
    ("Скульптор", "Скульптор", 11.88, -25.29, 11400000.0), ("БМ Облако", "Золотая Рыба", 80.89, -69.75, 163000.0), ("ММ Облако", "Тукан", 13.18, -72.80, 206000.0),
]

RAW_NEBULAE = [
    ("Ориона", "Орион", 83.82, -5.39, 1344.0), ("Кольцо", "Лира", 283.39, 33.03, 2300.0),
    ("Лагуна", "Стрелец", 271.00, -24.38, 4100.0), ("Омега", "Стрелец", 275.20, -16.18, 5500.0),
    ("Гантель", "Лисичка", 299.90, 22.72, 1360.0), ("Крабовидная", "Телец", 83.63, 22.01, 6500.0),
    ("Орел", "Змея", 274.70, -13.80, 7000.0), ("Киля", "Киль", 161.26, -59.86, 7500.0),
]

RAW_CLUSTERS = [
    ("Плеяды", "Телец", 56.75, 24.11, 444.0), ("Гиады", "Телец", 66.75, 15.86, 153.0),
    ("Ясли", "Рак", 130.10, 19.66, 577.0), ("M13", "Геркулес", 250.42, 36.46, 22200.0),
    ("Омега Центавра", "Центавр", 201.69, -47.48, 15800.0), ("Тукан 47", "Тукан", 6.02, -72.08, 13000.0),
    ("M22", "Стрелец", 279.10, -23.90, 10600.0), ("h/χ Персея", "Персей", 35.15, 57.15, 7500.0),
    ("Дикая Утка", "Щит", 282.75, -6.27, 6200.0)
]

# Словари данных
STARS = {s[0]: {"ra": s[2]/15, "dec": s[3], "dist": s[4], "const": s[1], "type": "ЗВЕЗДА", "color": "#00FFCC"} for s in RAW_STARS}
GALAXIES = {g[0]: {"ra": g[2]/15, "dec": g[3], "dist": g[4], "const": g[1], "type": "ГАЛАКТИКА", "color": "#FF00FF"} for g in RAW_GALAXIES}
NEBULAE = {n[0]: {"ra": n[2]/15, "dec": n[3], "dist": n[4], "const": n[1], "type": "ТУМАННОСТЬ", "color": "#4488FF"} for n in RAW_NEBULAE}
CLUSTERS = {c[0]: {"ra": c[2]/15, "dec": c[3], "dist": c[4], "const": c[1], "type": "СКОПЛЕНИЕ", "color": "#FFAA00"} for c in RAW_CLUSTERS}

PLANETS_NAMES = {"Меркурий": "MERCURY", "Венера": "VENUS", "Марс": "MARS", "Юпитер": "JUPITER BARYCENTER", "Сатурн": "SATURN BARYCENTER"}

async def main(page: ft.Page):
    page.title = "STARSIS"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.window.width, page.window.height = 420, 900
    page.padding = 0
    center_pos = ft.Alignment(0, 0)
    my_lat, my_lon = "55.75", "37.61"
    current_obj = {"name": "", "ra": 0, "dec": 0, "type": "", "id": "", "const": ""}

    st_name, st_data, st_live = ft.Text("", size=24, weight="bold", color="#00FFCC"), ft.Text("", size=16), ft.Text("", size=16, color="#FFCC00", weight="bold")

    async def update_live_data():
        while True:
            if bs.open and current_obj["name"] != "":
                try:
                    t = ts.now()
                    observer = earth + Topos(latitude_degrees=float(my_lat), longitude_degrees=float(my_lon))
                    if current_obj["type"] != "planet":
                        obj = Star(ra_hours=float(current_obj["ra"]), dec_degrees=float(current_obj["dec"]))
                    else:
                        obj = planets_data[current_obj["id"]]
                    alt, az, _ = observer.at(t).observe(obj).apparent().altaz()
                    st_live.value = f"СЕЙЧАС: {'ВИДИМО' if alt.degrees > 0 else 'СКРЫТО'}\nВысота: {alt.degrees:.4f}°\nАзимут: {az.degrees:.4f}°"
                    page.update()
                except: pass
            await asyncio.sleep(0.5)

    def show_details(name, ra, dec, obj_type, obj_id=None, constellation=""):
        current_obj.update({"name": name, "ra": ra, "dec": dec, "type": obj_type, "id": obj_id, "const": constellation})
        st_name.value = name.upper()
        st_data.value = f"Созвездие: {constellation}\nRa: {ra:.2f} ч | Dec: {dec:.2f}°"
        bs.open = True
        page.update()

    bs_content = ft.GestureDetector(
        on_vertical_drag_update=lambda e: (setattr(bs, "open", False) or page.update()) if e.primary_delta and e.primary_delta > 8 else None,
        content=ft.Container(
            content=ft.Column([ft.Container(width=50, height=5, bgcolor="white24", border_radius=10), ft.Container(height=20), st_name, ft.Divider(color="white12"), st_data, ft.Container(height=10), st_live, ft.Container(expand=True)], horizontal_alignment="center"),
            padding=20, bgcolor="#111111", height=450, border_radius=ft.border_radius.only(top_left=20, top_right=20)
        )
    )
    bs = ft.BottomSheet(bs_content, open=False); page.overlay.append(bs)

    universe_list = ft.ListView(expand=True)
    t_now = ts.now()
    
    def add_to_list(name, data, obj_type, obj_id=None):
        universe_list.controls.append(ft.Container(
            content=ft.Row([ft.Text(name, size=18, weight="bold"), ft.Text(data.get("type", "ПЛАНЕТА"), size=10, color=data.get("color", "#FFCC00"))], alignment="spaceBetween"),
            padding=ft.padding.symmetric(horizontal=20), height=60, border=ft.border.all(1, "white12"), border_radius=10, margin=5, bgcolor="#111111",
            on_click=lambda _: show_details(name, data["ra"], data["dec"], obj_type, obj_id, data.get("const", ""))
        ))

    for p_n, p_id in PLANETS_NAMES.items():
        try:
            ra, dec, _ = earth.at(t_now).observe(planets_data[p_id]).radec()
            add_to_list(p_n, {"ra": ra.hours, "dec": dec.degrees}, "planet", p_id)
        except: pass

    for d in [STARS, GALAXIES, NEBULAE, CLUSTERS]:
        for n, data in d.items():
            add_to_list(n, data, data["type"].lower())

    calc_res = ft.Text("Результат появится здесь", color="#00FFCC", italic=True)
    ra1, dec1 = ft.TextField(label="Ra 1 (ч)", expand=True), ft.TextField(label="Dec 1 (°)", expand=True)
    ra2, dec2 = ft.TextField(label="Ra 2 (ч)", expand=True), ft.TextField(label="Dec 2 (°)", expand=True)
    ra1_3, dec1_3, pc1 = ft.TextField(label="Ra 1", expand=True), ft.TextField(label="Dec 1", expand=True), ft.TextField(label="Pc 1", expand=True)
    ra2_3, dec2_3, pc2 = ft.TextField(label="Ra 2", expand=True), ft.TextField(label="Dec 2", expand=True), ft.TextField(label="Pc 2", expand=True)
    par_in = ft.TextField(label="arcsec", expand=True)

    calc_view = ft.Column([
        ft.Text("1. УГЛОВОЕ РАССТОЯНИЕ", color="#00FFCC", weight="bold"), ft.Container(ft.Row([ra1, dec1])), ft.Container(ft.Row([ra2, dec2])), ft.ElevatedButton("Считать угол", on_click=lambda _: (setattr(calc_res, "value", f"Угол: {math.degrees(math.acos(max(-1, min(1, math.sin(math.radians(float(dec1.value)))*math.sin(math.radians(float(dec2.value))) + math.cos(math.radians(float(dec1.value)))*math.cos(math.radians(float(dec2.value)))*math.cos(math.radians(float(ra1.value)*15 - float(ra2.value)*15)))))):.4f}°") or page.update()), bgcolor="#1a1a1a"),
        ft.Divider(color="white12"), ft.Text("2. 3D ДИСТАНЦИЯ", color="#00FFCC", weight="bold"), ft.Container(ft.Row([ra1_3, dec1_3, pc1])), ft.Container(ft.Row([ra2_3, dec2_3, pc2])), ft.ElevatedButton("Считать 3D", on_click=lambda _: (setattr(calc_res, "value", f"3D Расст: {math.sqrt((float(pc2.value)*math.cos(math.radians(float(dec2_3.value)))*math.cos(math.radians(float(ra2_3.value)*15)) - float(pc1.value)*math.cos(math.radians(float(dec1_3.value)))*math.cos(math.radians(float(ra1_3.value)*15)))**2 + (float(pc2.value)*math.cos(math.radians(float(dec2_3.value)))*math.sin(math.radians(float(ra2_3.value)*15)) - float(pc1.value)*math.cos(math.radians(float(dec1_3.value)))*math.sin(math.radians(float(ra1_3.value)*15)))**2 + (float(pc2.value)*math.sin(math.radians(float(dec2_3.value))) - float(pc1.value)*math.sin(math.radians(float(dec1_3.value))))**2):.2f} пк") or page.update()), bgcolor="#1a1a1a"),
        ft.Divider(color="white12"), ft.Text("3. ПАРАЛЛАКС", color="#00FFCC", weight="bold"), ft.Container(ft.Row([par_in, ft.ElevatedButton("ОК", on_click=lambda _: (setattr(calc_res, "value", f"Расст: {1/float(par_in.value):.2f} пк") or page.update()))])), ft.Container(calc_res, padding=15, border=ft.border.all(1, "#00FFCC"), border_radius=10, width=380)
    ], visible=False, horizontal_alignment="center", scroll="auto")

    def switch_tab(e): universe_list.visible, calc_view.visible, btn_cat.bgcolor, btn_calc.bgcolor = (e.control.data == "cat"), (e.control.data == "calc"), ("#1a1a1a" if e.control.data=="cat" else "#000000"), ("#1a1a1a" if e.control.data=="calc" else "#000000"); page.update()
    btn_cat, btn_calc = ft.Container(content=ft.Text("⭐ Каталог"), expand=True, alignment=center_pos, on_click=switch_tab, data="cat", bgcolor="#1a1a1a"), ft.Container(content=ft.Text("🧮 Расчеты"), expand=True, alignment=center_pos, on_click=switch_tab, data="calc")

    page.add(ft.Column([ft.Container(content=ft.Text("✨ STARSIS", size=22, weight="bold", color="#00FFCC"), padding=20, alignment=center_pos), ft.Container(content=ft.Column([universe_list, calc_view], expand=True), expand=True), ft.Container(ft.Row([btn_cat, btn_calc], spacing=0), height=70, border=ft.border.only(top=ft.BorderSide(1, "white24")))], expand=True, spacing=0))
    page.run_task(update_live_data)

if __name__ == "__main__":
    ft.app(target=main)
