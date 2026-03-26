import flet as ft
import math
import asyncio
import time
from datetime import datetime, timezone

# --- БАЗЫ ДАННЫХ (Те же, что у тебя были) ---
RAW_STARS = [
    ("Полярная", "Малая Медведица", 37.95, 89.26, 431.0), ("Вега", "Лира", 279.23, 38.78, 25.04),
    ("Арктур", "Волопас", 213.91, 19.18, 36.7), ("Сириус", "Большой Пес", 101.29, -16.71, 8.6),
    ("Бетельгейзе", "Орион", 88.79, 7.41, 640.0), ("Ригель", "Орион", 78.63, -8.20, 860.0),
    ("Альтаир", "Орел", 297.70, 8.87, 16.7), ("Альдебаран", "Телец", 68.98, 16.51, 65.3),
    ("Антарес", "Скорпион", 247.35, -26.43, 550.0), ("Спика", "Дева", 201.30, -11.16, 250.0),
    ("Денеб", "Лебедь", 310.36, 45.28, 2600.0), ("Регул", "Лев", 152.09, 11.97, 79.3)
]

# Простая математика вместо Skyfield
def calculate_alt_az(ra_deg, dec_deg, lat_deg, lon_deg):
    # Текущее время UTC
    now = datetime.now(timezone.utc)
    
    # 1. Считаем звездное время (GMST) приблизительно
    t = (now.timestamp() / 86400.0) + 2440587.5 - 2451545.0
    gmst = 280.46061837 + 360.98564736629 * t
    gmst %= 360.0
    
    # 2. Местное звездное время (LST)
    lst = gmst + lon_deg
    
    # 3. Часовой угол (HA)
    ha = lst - ra_deg
    
    # Переводим в радианы
    ha_rad = math.radians(ha)
    dec_rad = math.radians(dec_deg)
    lat_rad = math.radians(lat_deg)
    
    # 4. Формулы высоты (Alt) и азимута (Az)
    sin_alt = math.sin(dec_rad) * math.sin(lat_rad) + math.cos(dec_rad) * math.cos(lat_rad) * math.cos(ha_rad)
    alt_rad = math.asin(max(-1, min(1, sin_alt)))
    
    cos_az = (math.sin(dec_rad) - math.sin(alt_rad) * math.sin(lat_rad)) / (math.cos(alt_rad) * math.cos(lat_rad) + 1e-10)
    az_rad = math.acos(max(-1, min(1, cos_az)))
    
    if math.sin(ha_rad) > 0:
        az_rad = 2 * math.pi - az_rad
        
    return math.degrees(alt_rad), math.degrees(az_rad)

async def main(page: ft.Page):
    page.title = "STARSIS (Lite)"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.padding = 0
    
    my_lat, my_lon = 55.75, 37.61 # Москва
    current_obj = {"name": "", "ra": 0, "dec": 0}

    st_name = ft.Text("", size=24, weight="bold", color="#00FFCC")
    st_data = ft.Text("", size=16)
    st_live = ft.Text("", size=16, color="#FFCC00", weight="bold")

    async def update_live_data():
        while True:
            if bs.open and current_obj["name"]:
                try:
                    alt, az = calculate_alt_az(current_obj["ra"], current_obj["dec"], my_lat, my_lon)
                    status = "ВИДИМО" if alt > 0 else "СКРЫТО"
                    st_live.value = f"СЕЙЧАС: {status}\nВысота: {alt:.2f}°\nАзимут: {az:.2f}°"
                    page.update()
                except Exception as e:
                    print(e)
            await asyncio.sleep(1)

    def show_details(name, ra, dec, const):
        current_obj.update({"name": name, "ra": ra, "dec": dec})
        st_name.value = name.upper()
        st_data.value = f"Созвездие: {const}\nRA: {ra:.2f}° | Dec: {dec:.2f}°"
        bs.open = True
        page.update()

    bs_content = ft.Container(
        content=ft.Column([
            ft.Container(width=50, height=5, bgcolor="white24", border_radius=10),
            ft.Container(height=20),
            st_name,
            ft.Divider(color="white12"),
            st_data,
            ft.Container(height=10),
            st_live
        ], horizontal_alignment="center"),
        padding=20, bgcolor="#111111", height=300, 
        border_radius=ft.border_radius.only(top_left=20, top_right=20)
    )
    bs = ft.BottomSheet(bs_content)
    page.overlay.append(bs)

    star_list = ft.ListView(expand=True, padding=10)
    
    for name, const, ra, dec, dist in RAW_STARS:
        star_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text(name, size=18, weight="bold"),
                    ft.Text(const, size=12, color="white54")
                ], alignment="spaceBetween"),
                padding=15, margin=5, bgcolor="#1a1a1a", border_radius=10,
                on_click=lambda e, n=name, r=ra, d=dec, c=const: show_details(n, r, d, c)
            )
        )

    page.add(
        ft.Container(content=ft.Text("✨ STARSIS", size=22, weight="bold", color="#00FFCC"), padding=15, alignment=ft.alignment.center),
        star_list
    )
    
    page.run_task(update_live_data)

if __name__ == "__main__":
    ft.app(target=main)
