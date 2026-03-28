import flet as ft
import math
import asyncio
from datetime import datetime, timezone

# ================================================================
#  АСТРОНОМИЧЕСКИЕ ВЫЧИСЛЕНИЯ (замена skyfield — только stdlib)
# ================================================================

def _jd(dt=None):
    """Юлианская дата из UTC-datetime."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    y, m = dt.year, dt.month
    if m <= 2:
        y -= 1
        m += 12
    d = dt.day + (dt.hour + dt.minute / 60.0
                  + dt.second / 3600.0
                  + dt.microsecond / 3.6e9) / 24.0
    A = y // 100
    B = 2 - A + A // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5


def _gmst(jd):
    """Гринвичское среднее звёздное время (°)."""
    T = (jd - 2451545.0) / 36525.0
    return (280.46061837
            + 360.98564736629 * (jd - 2451545.0)
            + 0.000387933 * T * T
            - T ** 3 / 38710000.0) % 360


def radec_to_altaz(ra_h, dec_d, lat, lon):
    """RA (ч) / Dec (°)  +  широта / долгота  →  (alt°, az°)."""
    jd = _jd()
    lst = (_gmst(jd) + lon) % 360
    ha = math.radians(lst - ra_h * 15)
    d  = math.radians(dec_d)
    la = math.radians(lat)
    sin_a = math.sin(d) * math.sin(la) + math.cos(d) * math.cos(la) * math.cos(ha)
    alt = math.asin(max(-1.0, min(1.0, sin_a)))
    c = (math.sin(d) - math.sin(alt) * math.sin(la)) / (math.cos(alt) * math.cos(la) + 1e-12)
    az = math.acos(max(-1.0, min(1.0, c)))
    if math.sin(ha) > 0:
        az = 2 * math.pi - az
    return math.degrees(alt), math.degrees(az)


# --- Орбитальные элементы планет (J2000 + скорости/столетие, JPL) ---
_ELEMS = {
    "MERCURY": {
        "a": (0.38709927, 3.7e-7),     "e": (0.20563593, 1.906e-5),
        "I": (7.00497902, -5.947e-3),   "O": (48.33076593, -0.12534),
        "w": (77.45779628, 0.16048),    "L": (252.25032350, 149472.674)},
    "VENUS": {
        "a": (0.72333566, 3.9e-7),     "e": (0.00677672, -4.107e-5),
        "I": (3.39467605, -7.889e-4),   "O": (76.67984255, -0.27769),
        "w": (131.60246718, 2.683e-3),  "L": (181.97909950, 58517.815)},
    "EARTH": {
        "a": (1.00000261, 5.62e-7),    "e": (0.01671123, -4.392e-5),
        "I": (-1.531e-5, -1.295e-2),    "O": (0.0, 0.0),
        "w": (102.93768193, 0.32327),   "L": (100.46457166, 35999.372)},
    "MARS": {
        "a": (1.52371034, 1.847e-5),   "e": (0.09339410, 7.882e-5),
        "I": (1.84969142, -8.131e-3),   "O": (49.55953891, -0.29257),
        "w": (-23.94362959, 0.44441),   "L": (-4.55343205, 19140.303)},
    "JUPITER BARYCENTER": {
        "a": (5.20288700, -1.161e-4),  "e": (0.04838624, -1.325e-4),
        "I": (1.30439695, -1.837e-3),   "O": (100.47390909, 0.20469),
        "w": (14.72847983, 0.21253),    "L": (34.39644051, 3034.746)},
    "SATURN BARYCENTER": {
        "a": (9.53667594, -1.251e-3),  "e": (0.05386179, -5.099e-4),
        "I": (2.48599187, 1.936e-3),    "O": (113.66242448, -0.28868),
        "w": (92.59887831, -0.41897),   "L": (49.95424423, 1222.494)},
}


def _kepler(M_deg, e):
    """Решение уравнения Кеплера  M = E − e·sin E."""
    M = math.radians(M_deg % 360)
    E = M
    for _ in range(60):
        dE = (M - E + e * math.sin(E)) / (1 - e * math.cos(E))
        E += dE
        if abs(dE) < 1e-12:
            break
    return E


def _helio(pid, T):
    """Гелиоцентрические эклиптические x y z (а.е.)."""
    el = _ELEMS[pid]
    a  = el["a"][0] + el["a"][1] * T
    e  = el["e"][0] + el["e"][1] * T
    Ir = math.radians(el["I"][0] + el["I"][1] * T)
    Or = math.radians(el["O"][0] + el["O"][1] * T)
    wp = el["w"][0] + el["w"][1] * T
    L  = el["L"][0] + el["L"][1] * T
    wr = math.radians(wp - (el["O"][0] + el["O"][1] * T))
    E  = _kepler(L - wp, e)
    xp = a * (math.cos(E) - e)
    yp = a * math.sqrt(max(0, 1 - e * e)) * math.sin(E)
    cw, sw = math.cos(wr), math.sin(wr)
    cO, sO = math.cos(Or), math.sin(Or)
    cI, sI = math.cos(Ir), math.sin(Ir)
    x = (cw*cO - sw*sO*cI)*xp + (-sw*cO - cw*sO*cI)*yp
    y = (cw*sO + sw*cO*cI)*xp + (-sw*sO + cw*cO*cI)*yp
    z = (sw*sI)*xp            + (cw*sI)*yp
    return x, y, z


def planet_radec(pid):
    """Приближённые RA (ч) и Dec (°) планеты на текущий момент."""
    jd = _jd()
    T  = (jd - 2451545.0) / 36525.0
    xp, yp, zp = _helio(pid, T)
    xe, ye, ze = _helio("EARTH", T)
    xg, yg, zg = xp - xe, yp - ye, zp - ze
    eps = math.radians(23.4393 - 3.563e-7 * (jd - 2451545.0))
    xeq = xg
    yeq = yg * math.cos(eps) - zg * math.sin(eps)
    zeq = yg * math.sin(eps) + zg * math.cos(eps)
    ra  = math.atan2(yeq, xeq)
    dec = math.atan2(zeq, math.sqrt(xeq*xeq + yeq*yeq))
    return (math.degrees(ra) / 15) % 24, math.degrees(dec)


# ================================================================
#  БАЗЫ ДАННЫХ  (Звёзды, Галактики, Туманности, Скопления)
# ================================================================
RAW_STARS = [
    ("Полярная","Малая Медведица",37.95,89.26,431),("Вега","Лира",279.23,38.78,25.04),
    ("Арктур","Волопас",213.91,19.18,36.7),("Сириус","Большой Пес",101.29,-16.71,8.6),
    ("Канопус","Киль",95.99,-52.70,310),("Толиман","Центавр",219.90,-60.83,4.37),
    ("Капелла","Возничий",79.17,45.99,42.8),("Ригель","Орион",78.63,-8.20,860),
    ("Процион","Малый Пес",114.82,5.22,11.4),("Ахернар","Эридан",24.43,-57.24,144),
    ("Бетельгейзе","Орион",88.79,7.41,640),("Альтаир","Орел",297.70,8.87,16.7),
    ("Альдебаран","Телец",68.98,16.51,65.3),("Антарес","Скорпион",247.35,-26.43,550),
    ("Спика","Дева",201.30,-11.16,250),("Поллукс","Близнецы",116.33,28.03,33.7),
    ("Фомальгаут","Южная Рыба",344.41,-29.62,25.1),("Денеб","Лебедь",310.36,45.28,2600),
    ("Регул","Лев",152.09,11.97,79.3),("Адара","Большой Пес",104.65,-28.97,430),
    ("Кастор","Близнецы",113.65,31.89,51.5),("Гакрукс","Южный Крест",187.79,-57.11,88.6),
    ("Шаула","Скорпион",263.40,-37.10,570),("Беллатрикс","Орион",81.28,6.35,250),
    ("Эльнат","Телец",81.57,28.61,134),("Миаплацидус","Киль",138.30,-69.72,113),
    ("Альнилам","Орион",84.05,-1.20,2000),("Альнаир","Журавль",332.06,-46.96,101),
    ("Алиот","Большая Медведица",193.47,55.96,82.6),("Мирфак","Персей",51.08,49.86,510),
    ("Дубхе","Большая Медведица",165.93,61.75,123),("Регор","Паруса",122.40,-47.33,1100),
    ("Канкар","Киль",128.55,-59.51,630),("Альнитак","Орион",85.19,-1.94,730),
    ("Каус Аустралис","Стрелец",276.10,-34.38,143),("Мицар","Большая Медведица",199.10,54.93,82.8),
    ("Альфард","Гидра",141.93,-8.66,177),("Хамаль","Овен",31.79,23.46,65.8),
    ("Денебола","Лев",177.26,14.57,35.9),("Альдерамин","Цефей",318.52,62.59,49),
    ("Саиф","Орион",86.94,-9.67,650),("Альхена","Близнецы",99.43,16.39,109),
    ("Менкалинан","Возничий",89.87,44.95,81),("Мирцам","Большой Пес",95.67,-17.96,500),
    ("Рас-Альхаге","Змееносец",263.73,12.56,48.6),("Алголь","Персей",46.21,40.96,90),
    ("Шеат","Пегас",345.94,28.08,196),("Альферац","Андромеда",2.10,29.09,97),
    ("Мирах","Андромеда",17.43,35.62,197),("Альмак","Андромеда",30.97,42.33,350),
    ("Дифда","Кит",10.89,-17.99,96),("Менкар","Кит",45.57,4.09,250),
    ("Анкаа","Феникс",6.55,-42.31,77),("Эниф","Пегас",326.05,9.87,690),
    ("Маркаб","Пегас",346.19,15.21,133),("Зосма","Лев",168.53,20.52,58.4),
    ("Мерак","Большая Медведица",165.46,56.38,79.7),("Фекда","Большая Медведица",178.46,53.69,83.2),
    ("Мегрец","Большая Медведица",183.86,57.03,80.5),("Алькаид","Большая Медведица",206.88,49.31,104),
    ("Кохаб","Малая Медведица",222.68,74.16,131),("Мира","Кит",34.83,-2.98,300),
    ("Денеб Кайтос","Кит",10.89,-17.98,96),("Арнеб","Заяц",83.18,-17.82,2200),
    ("Нихал","Заяц",83.18,-20.84,156),("Муфрид","Волопас",208.67,18.39,37),
    ("Изар","Волопас",221.24,27.07,210),
]
RAW_GALAXIES = [
    ("Андромеда","Андромеда",10.68,41.27,2540000),("Треугольник","Треугольник",23.46,30.66,3000000),
    ("M81 (Боде)","Большая Медведица",148.88,69.07,11800000),
    ("M82 (Сигара)","Большая Медведица",148.96,69.68,11500000),
    ("M51 (Водоворот)","Гончие Псы",202.73,47.19,23000000),
    ("M104 (Сомбреро)","Дева",189.99,-11.62,29000000),
    ("Центавр А","Центавр",201.36,-43.02,11000000),
    ("Южная Вертушка","Гидра",204.25,-29.86,15000000),
    ("Скульптор","Скульптор",11.88,-25.29,11400000),
    ("БМ Облако","Золотая Рыба",80.89,-69.75,163000),
    ("ММ Облако","Тукан",13.18,-72.80,206000),
]
RAW_NEBULAE = [
    ("Ориона","Орион",83.82,-5.39,1344),("Кольцо","Лира",283.39,33.03,2300),
    ("Лагуна","Стрелец",271.00,-24.38,4100),("Омега","Стрелец",275.20,-16.18,5500),
    ("Гантель","Лисичка",299.90,22.72,1360),("Крабовидная","Телец",83.63,22.01,6500),
    ("Орел","Змея",274.70,-13.80,7000),("Киля","Киль",161.26,-59.86,7500),
]
RAW_CLUSTERS = [
    ("Плеяды","Телец",56.75,24.11,444),("Гиады","Телец",66.75,15.86,153),
    ("Ясли","Рак",130.10,19.66,577),("M13","Геркулес",250.42,36.46,22200),
    ("Омега Центавра","Центавр",201.69,-47.48,15800),("Тукан 47","Тукан",6.02,-72.08,13000),
    ("M22","Стреле��",279.10,-23.90,10600),("h/χ Персея","Персей",35.15,57.15,7500),
    ("Дикая Утка","Щит",282.75,-6.27,6200),
]

STARS    = {s[0]: {"ra":s[2]/15,"dec":s[3],"dist":s[4],"const":s[1],"type":"ЗВЕЗДА",   "color":"#00FFCC"} for s in RAW_STARS}
GALAXIES = {g[0]: {"ra":g[2]/15,"dec":g[3],"dist":g[4],"const":g[1],"type":"ГАЛАКТИКА","color":"#FF00FF"} for g in RAW_GALAXIES}
NEBULAE  = {n[0]: {"ra":n[2]/15,"dec":n[3],"dist":n[4],"const":n[1],"type":"ТУМАННОСТЬ","color":"#4488FF"} for n in RAW_NEBULAE}
CLUSTERS = {c[0]: {"ra":c[2]/15,"dec":c[3],"dist":c[4],"const":c[1],"type":"СКОПЛЕНИЕ","color":"#FFAA00"} for c in RAW_CLUSTERS}

PLANETS_NAMES = {
    "Меркурий": "MERCURY", "Венера": "VENUS",
    "Марс": "MARS", "Юпитер": "JUPITER BARYCENTER",
    "Сатурн": "SATURN BARYCENTER",
}


# ================================================================
#  ПРИЛОЖЕНИЕ
# ================================================================
async def main(page: ft.Page):
    page.title = "STARSIS"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.window.width, page.window.height = 420, 900
    page.padding = 0
    center_pos = ft.Alignment(0, 0)

    my_lat, my_lon = "55.75", "37.61"
    current_obj = {"name": "", "ra": 0, "dec": 0,
                   "type": "", "id": "", "const": ""}

    st_name = ft.Text("", size=24, weight="bold", color="#00FFCC")
    st_data = ft.Text("", size=16)
    st_live = ft.Text("", size=16, color="#FFCC00", weight="bold")

    # ---------- живое обновление alt/az ----------
    async def update_live_data():
        while True:
            if bs.open and current_obj["name"]:
                try:
                    if current_obj["type"] == "planet":
                        ra_h, dec_d = planet_radec(current_obj["id"])
                    else:
                        ra_h = float(current_obj["ra"])
                        dec_d = float(current_obj["dec"])
                    alt, az = radec_to_altaz(
                        ra_h, dec_d,
                        float(my_lat), float(my_lon))
                    vis = "ВИДИМО" if alt > 0 else "СКРЫТО"
                    st_live.value = (
                        f"СЕЙЧАС: {vis}\n"
                        f"Высота: {alt:.4f}°\n"
                        f"Азимут: {az:.4f}°")
                    page.update()
                except Exception:
                    pass
            await asyncio.sleep(0.5)

    # ---------- показать детали объекта ----------
    def show_details(name, ra, dec, obj_type,
                     obj_id=None, constellation=""):
        current_obj.update({"name": name, "ra": ra, "dec": dec,
                            "type": obj_type, "id": obj_id,
                            "const": constellation})
        st_name.value = name.upper()
        st_data.value = (f"Созвездие: {constellation}\n"
                         f"Ra: {ra:.2f} ч | Dec: {dec:.2f}°")
        bs.open = True
        page.update()

    # ---------- нижняя панель ----------
    bs_content = ft.GestureDetector(
        on_vertical_drag_update=lambda e: (
            setattr(bs, "open", False) or page.update()
        ) if e.primary_delta and e.primary_delta > 8 else None,
        content=ft.Container(
            content=ft.Column([
                ft.Container(width=50, height=5,
                             bgcolor="white24", border_radius=10),
                ft.Container(height=20),
                st_name,
                ft.Divider(color="white12"),
                st_data,
                ft.Container(height=10),
                st_live,
                ft.Container(expand=True),
            ], horizontal_alignment="center"),
            padding=20, bgcolor="#111111", height=450,
            border_radius=ft.border_radius.only(
                top_left=20, top_right=20),
        ),
    )
    bs = ft.BottomSheet(bs_content, open=False)
    page.overlay.append(bs)

    # ---------- список объектов ----------
    universe_list = ft.ListView(expand=True)

    def add_to_list(name, data, obj_type, obj_id=None):
        universe_list.controls.append(ft.Container(
            content=ft.Row([
                ft.Text(name, size=18, weight="bold"),
                ft.Text(data.get("type", "ПЛАНЕТА"),
                        size=10,
                        color=data.get("color", "#FFCC00")),
            ], alignment="spaceBetween"),
            padding=ft.padding.symmetric(horizontal=20),
            height=60,
            border=ft.border.all(1, "white12"),
            border_radius=10, margin=5, bgcolor="#111111",
            on_click=lambda _, n=name, d=data, ot=obj_type, oi=obj_id:
                show_details(n, d["ra"], d["dec"],
                             ot, oi, d.get("const", "")),
        ))

    # планеты
    for p_name, p_id in PLANETS_NAMES.items():
        try:
            ra_h, dec_d = planet_radec(p_id)
            add_to_list(p_name,
                        {"ra": ra_h, "dec": dec_d},
                        "planet", p_id)
        except Exception:
            pass

    # звёзды / галактики / туманности / скопления
    for catalog in (STARS, GALAXIES, NEBULAE, CLUSTERS):
        for name, data in catalog.items():
            add_to_list(name, data, data["type"].lower())

    # ---------- калькулятор ----------
    calc_res = ft.Text("Результат появится здесь",
                       color="#00FFCC", italic=True)
    ra1   = ft.TextField(label="Ra 1 (ч)", expand=True)
    dec1  = ft.TextField(label="Dec 1 (°)", expand=True)
    ra2   = ft.TextField(label="Ra 2 (ч)", expand=True)
    dec2  = ft.TextField(label="Dec 2 (°)", expand=True)
    ra1_3 = ft.TextField(label="Ra 1", expand=True)
    dec1_3= ft.TextField(label="Dec 1", expand=True)
    pc1   = ft.TextField(label="Pc 1", expand=True)
    ra2_3 = ft.TextField(label="Ra 2", expand=True)
    dec2_3= ft.TextField(label="Dec 2", expand=True)
    pc2   = ft.TextField(label="Pc 2", expand=True)
    par_in= ft.TextField(label="arcsec", expand=True)

    def calc_angle(_):
        try:
            d1, d2 = math.radians(float(dec1.value)), math.radians(float(dec2.value))
            dra = math.radians((float(ra1.value) - float(ra2.value)) * 15)
            cos_a = math.sin(d1)*math.sin(d2) + math.cos(d1)*math.cos(d2)*math.cos(dra)
            calc_res.value = f"Угол: {math.degrees(math.acos(max(-1,min(1,cos_a)))):.4f}°"
        except Exception as ex:
            calc_res.value = f"Ошибка: {ex}"
        page.update()

    def calc_3d(_):
        try:
            r1, r2 = float(pc1.value), float(pc2.value)
            a1, a2 = math.radians(float(ra1_3.value)*15), math.radians(float(ra2_3.value)*15)
            dd1, dd2 = math.radians(float(dec1_3.value)), math.radians(float(dec2_3.value))
            dx = r2*math.cos(dd2)*math.cos(a2) - r1*math.cos(dd1)*math.cos(a1)
            dy = r2*math.cos(dd2)*math.sin(a2) - r1*math.cos(dd1)*math.sin(a1)
            dz = r2*math.sin(dd2) - r1*math.sin(dd1)
            calc_res.value = f"3D Расст: {math.sqrt(dx*dx+dy*dy+dz*dz):.2f} пк"
        except Exception as ex:
            calc_res.value = f"Ошибка: {ex}"
        page.update()

    def calc_par(_):
        try:
            calc_res.value = f"Расст: {1/float(par_in.value):.2f} пк"
        except Exception as ex:
            calc_res.value = f"Ошибка: {ex}"
        page.update()

    calc_view = ft.Column([
        ft.Text("1. УГЛОВОЕ РАССТОЯНИЕ", color="#00FFCC", weight="bold"),
        ft.Container(ft.Row([ra1, dec1])),
        ft.Container(ft.Row([ra2, dec2])),
        ft.ElevatedButton("Считать угол", on_click=calc_angle, bgcolor="#1a1a1a"),
        ft.Divider(color="white12"),
        ft.Text("2. 3D ДИСТАНЦИЯ", color="#00FFCC", weight="bold"),
        ft.Container(ft.Row([ra1_3, dec1_3, pc1])),
        ft.Container(ft.Row([ra2_3, dec2_3, pc2])),
        ft.ElevatedButton("Считать 3D", on_click=calc_3d, bgcolor="#1a1a1a"),
        ft.Divider(color="white12"),
        ft.Text("3. ПАРАЛЛАКС", color="#00FFCC", weight="bold"),
        ft.Container(ft.Row([par_in,
                             ft.ElevatedButton("ОК", on_click=calc_par)])),
        ft.Container(calc_res, padding=15,
                     border=ft.border.all(1, "#00FFCC"),
                     border_radius=10, width=380),
    ], visible=False, horizontal_alignment="center", scroll="auto")

    # ---------- вкладки ----------
    def switch_tab(e):
        is_cat = e.control.data == "cat"
        universe_list.visible = is_cat
        calc_view.visible = not is_cat
        btn_cat.bgcolor  = "#1a1a1a" if is_cat else "#000000"
        btn_calc.bgcolor = "#1a1a1a" if not is_cat else "#000000"
        page.update()

    btn_cat = ft.Container(content=ft.Text("⭐ Каталог"),
                           expand=True, alignment=center_pos,
                           on_click=switch_tab, data="cat",
                           bgcolor="#1a1a1a")
    btn_calc = ft.Container(content=ft.Text("🧮 Расчеты"),
                            expand=True, alignment=center_pos,
                            on_click=switch_tab, data="calc")

    page.add(ft.Column([
        ft.Container(
            content=ft.Text("✨ STARSIS", size=22,
                            weight="bold", color="#00FFCC"),
            padding=20, alignment=center_pos),
        ft.Container(
            content=ft.Column([universe_list, calc_view], expand=True),
            expand=True),
        ft.Container(
            ft.Row([btn_cat, btn_calc], spacing=0),
            height=70,
            border=ft.border.only(
                top=ft.BorderSide(1, "white24"))),
    ], expand=True, spacing=0))

    page.run_task(update_live_data)


if __name__ == "__main__":
    ft.app(target=main)
    ft.app(target=main)
