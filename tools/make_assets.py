"""
make_assets.py - Pipeline reproducible de imagenes para el sitio de Forlex.

Genera:
  assets/img/*.webp          capturas optimizadas (sin barra de tareas)
  assets/og.png              imagen Open Graph 1200x630 (texto + glow violeta/cian)
  assets/favicon/*           favicon.ico, PNGs, apple-touch-icon
  assets/site.webmanifest    manifest PWA basico

Dependencias: Pillow (12.x) + numpy.  Python: runtime DSH.

Uso:
    python tools/make_assets.py
Salida: assets + tools/assets_report.json (dimensiones, KB y layout de og).
"""

from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src-images")
SHOTS = os.path.join(SRC, "shots")
IMG = os.path.join(ROOT, "assets", "img")
FAV = os.path.join(ROOT, "assets", "favicon")

WEBP_QUALITY = 88
WEBP_METHOD = 6
MAX_W = 1600

# Fuentes del sistema (Windows)
F_BLACK = r"C:\Windows\Fonts\seguibl.ttf"      # Segoe UI Black
F_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"      # Segoe UI Bold
F_SEMI = r"C:\Windows\Fonts\seguisb.ttf"       # Segoe UI Semibold
F_REG = r"C:\Windows\Fonts\segoeui.ttf"        # Segoe UI Regular
F_ICON = F_BLACK

# Paleta del sitio
BG = (7, 6, 15)          # #07060f
VIOLET = (139, 92, 246)  # #8b5cf6
CYAN = (34, 211, 238)    # #22d3ee

# Capturas "limpias" (no se recortan). nombre_salida -> (archivo, ancho_max)
CLEAN = {
    "inicio": ("01-inicio.png", 1600),
    "equipo": ("03-equipo.png", 1600),
    "hardware": ("04-hardware.png", 1600),
    "categorias": ("02-categorias.png", None),   # 262x757, no reescalar
    "virustotal": ("05-virustotal.png", 1600),
}

# Capturas de shots/fin_*.png (barra de tareas abajo, se recorta). nombre -> archivo
SHOT_MAP = {
    "tweaks": "fin_tweaks.png",
    "optimizeall": "fin_optimizeall.png",
    "gpu": "fin_gpu.png",
    "gamemode": "fin_gamemode.png",
    "games": "fin_games.png",
    "tests": "fin_tests.png",
    "backups": "fin_backups.png",
    "customize": "fin_customize.png",
    "cleaner": "fin_cleaner.png",
    "diagnose": "fin_diagnose.png",
    "powerplan": "fin_powerplan.png",
    "programs": "fin_programs.png",
    "startup": "fin_startup.png",
    "fixes": "fin_fixes.png",
    "assistant": "fin_assistant.png",
    "profile": "fin_profile.png",
}

REPORT = {"webp": {}, "og": {}, "favicon": {}, "taskbar": {}}


def log(msg: str) -> None:
    print(msg, flush=True)


def kb(path: str) -> float:
    return os.path.getsize(path) / 1024.0


# ---------------------------------------------------------------------------
# Deteccion / recorte de la barra de tareas de Windows
# ---------------------------------------------------------------------------
def detect_taskbar_top(im: Image.Image) -> int | None:
    """Devuelve la Y donde empieza la taskbar (fila del borde superior).

    En estas capturas la taskbar de Windows 11 tiene una fila de 1px casi
    uniforme (~64,64,64) y justo debajo el fondo uniforme (~28,28,28).
    Se busca esa firma en el ultimo 10% de la imagen.
    """
    a = np.asarray(im.convert("RGB"), dtype=np.int16)
    h = a.shape[0]
    for y in range(h - 2, max(0, int(h * 0.90)), -1):
        row = a[y].astype(np.float32)
        if row.std() <= 0.01 and 45.0 <= row.mean() <= 95.0:
            nxt = a[y + 1].astype(np.float32)
            if nxt.std() <= 0.01 and nxt.mean() < 46.0:
                return y
    return None


def crop_taskbar(im: Image.Image, label: str) -> tuple[Image.Image, int | None]:
    top = detect_taskbar_top(im)
    if top is None:
        log(f"  [aviso] {label}: no se detecto taskbar; se usa la imagen completa")
        return im, None
    out = im.crop((0, 0, im.width, top))
    REPORT["taskbar"][label] = {"src": list(im.size), "taskbar_top": top, "cropped": list(out.size)}
    assert out.height <= 1026, f"{label}: recorte sospechoso ({out.size})"
    return out, top


# ---------------------------------------------------------------------------
# Utilidades de imagen
# ---------------------------------------------------------------------------
def resize_width(im: Image.Image, width: int | None, resample=Image.Resampling.LANCZOS) -> Image.Image:
    if width is None or im.width <= width:
        return im.copy()
    h = max(1, round(im.height * width / im.width))
    return im.resize((width, h), resample)


def save_webp(im: Image.Image, dst: str, quality: int = WEBP_QUALITY) -> None:
    im.convert("RGB").save(
        dst,
        "WEBP",
        quality=quality,
        method=WEBP_METHOD,
        lossless=False,
    )


# ---------------------------------------------------------------------------
# Referencias: transformacion esperada de cada captura, SIN compresion.
# Las usa el pipeline y tambien tools/verify_assets.py para comprobar el
# resultado (dimensiones exactas y PSNR frente a la referencia).
# ---------------------------------------------------------------------------
def clean_reference(name: str) -> Image.Image:
    """Captura limpia tal cual (solo reescalado si supera 1600 px)."""
    fname, max_w = CLEAN[name]
    im = Image.open(os.path.join(SRC, fname)).convert("RGB")
    return resize_width(im, max_w)


def shot_reference(name: str) -> tuple[Image.Image, int | None]:
    """Captura de shots/ recortada por encima de la barra de tareas + reescalado."""
    fname = SHOT_MAP[name]
    im = Image.open(os.path.join(SHOTS, fname))
    cropped, top = crop_taskbar(im, fname)
    return resize_width(cropped.convert("RGB"), MAX_W), top


def hero_reference() -> Image.Image:
    """01-inicio ampliada a 1800 px de ancho con enfoque suave."""
    im = Image.open(os.path.join(SRC, "01-inicio.png")).convert("RGB")
    w = 1800
    h = round(im.height * w / im.width)
    out = im.resize((w, h), Image.Resampling.LANCZOS)
    return out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=55, threshold=2))


# ---------------------------------------------------------------------------
# 1) Capturas limpias -> webp
# ---------------------------------------------------------------------------
def build_clean() -> None:
    log("\n[1] Capturas limpias")
    for name, (fname, max_w) in CLEAN.items():
        out = clean_reference(name)
        dst = os.path.join(IMG, f"{name}.webp")
        save_webp(out, dst)
        REPORT["webp"][f"{name}.webp"] = {
            "size": list(out.size), "kb": round(kb(dst), 1), "src": fname, "quality": WEBP_QUALITY,
        }
        log(f"  {name}.webp  {out.size[0]}x{out.size[1]}  {kb(dst):6.1f} KB  <- {fname}")


# ---------------------------------------------------------------------------
# 2) Shots (con taskbar) -> recorte -> webp
# ---------------------------------------------------------------------------
def build_shots() -> None:
    log("\n[2] Capturas de shots/ recortando la barra de tareas")
    tops = {}
    for name, fname in SHOT_MAP.items():
        out, top = shot_reference(name)
        tops[fname] = top
        dst = os.path.join(IMG, f"{name}.webp")
        save_webp(out, dst)
        REPORT["webp"][f"{name}.webp"] = {
            "size": list(out.size), "kb": round(kb(dst), 1), "src": f"shots/{fname}",
            "crop_top": top, "quality": WEBP_QUALITY,
        }
        log(f"  {name}.webp  {out.size[0]}x{out.size[1]}  {kb(dst):6.1f} KB  <- {fname}  (crop y={top})")
    detected = sorted({v for v in tops.values() if v is not None})
    assert len(detected) == 1 and 1000 <= detected[0] <= 1030, f"taskbar inconsistente: {detected}"
    REPORT["taskbar"]["_summary"] = {
        "detected_tops": detected, "files": len(tops),
        "cropped_size": [1920, detected[0]],
        "note": "todas las tomas recortadas en la misma Y; alto final 850 px",
    }
    log(f"  taskbar detectada en y={detected[0]} para las {len(tops)} tomas -> {1920}x{detected[0]}")


# ---------------------------------------------------------------------------
# 3) Hero de inicio (upscale controlado a 1800 px de ancho, q=90)
# ---------------------------------------------------------------------------
def build_hero() -> None:
    log("\n[3] inicio-hero.webp")
    out = hero_reference()
    dst = os.path.join(IMG, "inicio-hero.webp")
    save_webp(out, dst, quality=90)
    REPORT["webp"]["inicio-hero.webp"] = {
        "size": list(out.size), "kb": round(kb(dst), 1), "src": "01-inicio.png (upscale 1800)",
        "quality": 90,
    }
    log(f"  inicio-hero.webp  {out.size[0]}x{out.size[1]}  {kb(dst):6.1f} KB  (q=90)")


# ---------------------------------------------------------------------------
# 4) Icono de marca (cuadrado redondeado con degradado + monograma F)
# ---------------------------------------------------------------------------
def gradient_square(px: int, radius_ratio: float = 0.225) -> Image.Image:
    """Cuadrado redondeado con degradado violeta->cian y brillo radial."""
    yy, xx = np.mgrid[0:px, 0:px].astype(np.float32)
    # degradado diagonal (arriba-izquierda violeta -> abajo-derecha cian)
    t = np.clip((xx * 0.58 + yy * 0.42) / (px * 0.92), 0.0, 1.0) ** 1.05
    arr = np.zeros((px, px, 3), dtype=np.float32)
    for i in range(3):
        arr[..., i] = VIOLET[i] * (1.0 - t) + CYAN[i] * t
    # brillo radial arriba-izquierda
    d = np.sqrt((xx - px * 0.26) ** 2 + (yy - px * 0.16) ** 2) / (px * 0.80)
    hi = np.clip(1.0 - d, 0.0, 1.0)[..., None] ** 2.2
    arr = arr * (1.0 - 0.18 * hi) + 255.0 * 0.20 * hi
    # sombra inferior suave
    shade = 1.0 - 0.14 * (yy / px)[..., None]
    arr = arr * shade
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    icon = Image.fromarray(arr, "RGB").convert("RGBA")
    mask = Image.new("L", (px, px), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, px - 1, px - 1], radius=int(px * radius_ratio), fill=255
    )
    icon.putalpha(mask)
    # borde interior sutil
    d = ImageDraw.Draw(icon)
    inset = max(1, px // 220)
    d.rounded_rectangle(
        [inset, inset, px - 1 - inset, px - 1 - inset],
        radius=max(1, int(px * radius_ratio) - inset),
        outline=(255, 255, 255, 46),
        width=max(1, px // 256),
    )
    return icon


def icon_with_monogram(px: int = 1024, rounded: bool = True, letter: str = "F") -> Image.Image:
    """Icono de marca: cuadrado degradado + monograma blanco centrado."""
    base = gradient_square(px) if rounded else _opaque_gradient_square(px)
    # tamano de la F: altura del glifo ~52% del lienzo
    size = int(px * 0.74)
    font = ImageFont.truetype(F_ICON, size)
    while font.getbbox(letter)[3] - font.getbbox(letter)[1] > int(px * 0.53) and size > 10:
        size -= 4
        font = ImageFont.truetype(F_ICON, size)
    bb = font.getbbox(letter)
    gw = bb[2] - bb[0]
    gh = bb[3] - bb[1]
    x = (px - gw) / 2.0 - bb[0]
    y = (px - gh) / 2.0 - bb[1]
    # sombra suave de la letra
    shadow = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text(
        (x + px * 0.012, y + px * 0.018), letter, font=font, fill=(12, 8, 28, 150)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(1.0, px * 0.014)))
    base = Image.alpha_composite(base, shadow)
    ImageDraw.Draw(base).text((x, y), letter, font=font, fill=(255, 255, 255, 255))
    return base


def _opaque_gradient_square(px: int) -> Image.Image:
    """Igual que gradient_square pero sin transparencia (para apple-touch-icon)."""
    tmp = gradient_square(px)
    flat = Image.new("RGBA", (px, px), BG + (255,))
    return Image.alpha_composite(flat, tmp)


def build_favicons() -> None:
    log("\n[4] Favicons")
    master = icon_with_monogram(1024, rounded=True)

    def save_png(size: int, name: str) -> None:
        im = master.resize((size, size), Image.Resampling.LANCZOS)
        dst = os.path.join(FAV, name)
        im.save(dst, "PNG", optimize=True)
        REPORT["favicon"][name] = {"size": [size, size], "kb": round(kb(dst), 1)}
        log(f"  {name:20s} {size}x{size}  {kb(dst):6.1f} KB")

    save_png(32, "favicon-32.png")
    save_png(192, "favicon-192.png")
    save_png(512, "favicon-512.png")

    # apple-touch-icon: iOS ya aplica su squircle -> se entrega opaca 180x180
    apple_master = icon_with_monogram(720, rounded=False)
    apple = apple_master.resize((180, 180), Image.Resampling.LANCZOS)
    dst = os.path.join(FAV, "apple-touch-icon.png")
    apple.save(dst, "PNG", optimize=True)
    REPORT["favicon"]["apple-touch-icon.png"] = {"size": [180, 180], "kb": round(kb(dst), 1)}
    log(f"  apple-touch-icon.png 180x180  {kb(dst):6.1f} KB")

    # favicon.ico multi-resolucion 16/32/48 (se genera desde el master 1024)
    ico_dst = os.path.join(FAV, "favicon.ico")
    master.save(ico_dst, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    ico = Image.open(ico_dst)
    sizes = sorted(ico.ico.sizes()) if hasattr(ico, "ico") else []
    REPORT["favicon"]["favicon.ico"] = {"sizes": [list(s) for s in sizes], "kb": round(kb(ico_dst), 1)}
    log(f"  favicon.ico          16/32/48  {kb(ico_dst):6.1f} KB  {sizes}")


# ---------------------------------------------------------------------------
# 5) OG image 1200x630
# ---------------------------------------------------------------------------
def radial_glow(w: int, h: int, cx: float, cy: float, r: float, strength: float, gamma: float = 2.2):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    return (np.clip(1.0 - d, 0.0, 1.0) ** gamma) * strength


def og_background(w: int, h: int) -> Image.Image:
    bg = np.zeros((h, w, 3), dtype=np.float32)
    bg[..., 0], bg[..., 1], bg[..., 2] = BG

    g_v1 = radial_glow(w, h, w * 0.17, h * 0.88, w * 0.55, 0.60, 2.1)
    g_v2 = radial_glow(w, h, w * 0.40, h * -0.10, w * 0.46, 0.26, 2.0)
    g_c1 = radial_glow(w, h, w * 0.99, h * 0.92, w * 0.48, 0.50, 2.2)
    g_c2 = radial_glow(w, h, w * 0.84, h * -0.14, w * 0.38, 0.20, 2.0)

    for i in range(3):
        bg[..., i] += VIOLET[i] * g_v1 + VIOLET[i] * g_v2 + CYAN[i] * g_c1 + CYAN[i] * g_c2

    # vineta suave para que los bordes queden oscuros
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xx - w / 2) / (w / 2)
    ny = (yy - h / 2) / (h / 2)
    vig = np.clip(1.0 - 0.34 * (nx ** 2 + ny ** 2), 0.0, 1.0)[..., None]
    bg *= 0.72 + 0.28 * vig

    # grano fino determinista: evita banding en los degradados
    rng = np.random.default_rng(20251030)
    bg += rng.normal(0.0, 1.0, (h, w, 1))
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def fit_font(text: str, font_path: str, max_width: int, start: int = 120, minimum: int = 12) -> ImageFont.FreeTypeFont:
    size = start
    while size > minimum:
        font = ImageFont.truetype(font_path, size)
        if font.getlength(text) <= max_width:
            return font
        size -= 1
    return ImageFont.truetype(font_path, minimum)


def measure_tracking(font: ImageFont.FreeTypeFont, text: str, tracking: float) -> float:
    return sum(font.getlength(ch) for ch in text) + tracking * max(0, len(text) - 1)


def draw_tracking(draw: ImageDraw.ImageDraw, xy, text, font, fill, tracking: float) -> None:
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking


def draw_gradient_text(base: Image.Image, text: str, font, pos, color_a, color_b) -> tuple[int, tuple]:
    """Texto con degradado horizontal; devuelve (ancho, bbox global)."""
    mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(mask).text(pos, text, font=font, fill=255)
    bb = mask.getbbox()
    if bb is None:
        return 0, (0, 0, 0, 0)
    m = mask.crop(bb)
    gw, gh = m.size
    t = np.linspace(0.0, 1.0, gw, dtype=np.float32)[None, :].repeat(gh, axis=0)
    arr = np.zeros((gh, gw, 3), dtype=np.float32)
    for i in range(3):
        arr[..., i] = color_a[i] * (1.0 - t) + color_b[i] * t
    grad = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    grad.putalpha(m)
    base.alpha_composite(grad, dest=(bb[0], bb[1]))
    return bb[2] - bb[0], bb


def build_og() -> None:
    log("\n[5] og.png 1200x630")
    W, H = 1200, 630
    M = 68                        # margen general
    panel_w = 540                 # captura enmarcada
    gap = 52                      # separacion texto <-> captura
    panel_x = W - M - panel_w
    left_w = panel_x - M - gap    # ancho disponible para texto

    og = og_background(W, H)

    # --- captura "inicio" enmarcada a la derecha (marco redondeado + sombra) ---
    shot = Image.open(os.path.join(SRC, "01-inicio.png")).convert("RGB")
    panel_h = round(shot.height * panel_w / shot.width)
    panel_y = (H - panel_h) // 2
    radius = 16
    panel_rect = [panel_x, panel_y, panel_x + panel_w, panel_y + panel_h]

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [panel_rect[0] + 8, panel_rect[1] + 20, panel_rect[2] + 8, panel_rect[3] + 20],
        radius=radius + 4, fill=(0, 0, 0, 210),
    )
    og = Image.alpha_composite(og, shadow.filter(ImageFilter.GaussianBlur(30)))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(
        [panel_rect[0] - 10, panel_rect[1] - 10, panel_rect[2] + 10, panel_rect[3] + 10],
        radius=radius + 12, fill=VIOLET + (120,),
    )
    og = Image.alpha_composite(og, glow.filter(ImageFilter.GaussianBlur(42)))

    panel = shot.resize((panel_w, panel_h), Image.Resampling.LANCZOS)
    mask = Image.new("L", (panel_w, panel_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, panel_w - 1, panel_h - 1], radius=radius, fill=255)
    og.paste(panel, (panel_rect[0], panel_rect[1]), mask)
    d = ImageDraw.Draw(og)
    d.rounded_rectangle(
        [panel_rect[0], panel_rect[1], panel_rect[2] - 1, panel_rect[3] - 1],
        radius=radius, outline=(255, 255, 255, 40), width=1,
    )
    # filete superior brillante para sensacion de cristal
    d.rounded_rectangle(
        [panel_rect[0] + 1, panel_rect[1] + 1, panel_rect[2] - 2, panel_rect[1] + 14],
        radius=radius - 2, outline=(255, 255, 255, 26), width=1,
    )

    # --- bloque de texto (medido para evitar recortes) ---
    eyebrow_text = "OPTIMIZADOR PARA WINDOWS"
    eyebrow_tracking = 2.6
    f_eyebrow = ImageFont.truetype(F_SEMI, 15)
    eyebrow_w = measure_tracking(f_eyebrow, eyebrow_text, eyebrow_tracking)

    f_title = fit_font("OPTIMIZER", F_BLACK, left_w, start=110, minimum=40)
    title_size = f_title.size
    title_adv = int(title_size * 1.04)

    f_sub = ImageFont.truetype(F_REG, 26)
    sub_lines = ["393 tweaks · 16 categorías", "Windows 10/11 · 64 bits"]
    sub_adv = int(26 * 1.46)

    accent_h = 5
    total_h = (
        int(f_eyebrow.size * 1.35) + 16 + 2 * title_adv + 24 + accent_h + 30
        + sub_adv * len(sub_lines)
    )
    y = (H - total_h) // 2 + 2

    blocks = {}
    # eyebrow
    eb_h = int(f_eyebrow.size * 1.35)
    draw_tracking(d, (M, y), eyebrow_text, f_eyebrow, (198, 190, 234, 255), eyebrow_tracking)
    blocks["eyebrow"] = [M, y, M + int(eyebrow_w), y + eb_h]
    y += eb_h + 16

    # titulo: FORLEX (blanco) + OPTIMIZER (degradado violeta->cian)
    b1 = f_title.getbbox("FORLEX")
    d.text((M, y), "FORLEX", font=f_title, fill=(248, 247, 255, 255))
    blocks["title1"] = [M, y + b1[1], M + int(f_title.getlength("FORLEX")), y + b1[3]]
    y2 = y + title_adv
    b2 = f_title.getbbox("OPTIMIZER")
    _, bb2 = draw_gradient_text(
        og, "OPTIMIZER", f_title, (M, y2),
        (196, 168, 255), (56, 224, 246),
    )
    blocks["title2"] = list(bb2)
    y = y2 + title_adv

    # linea de acento con degradado
    y += 24
    accent_w = 118
    grad = Image.new("RGBA", (accent_w, accent_h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for i in range(accent_w):
        t = i / (accent_w - 1)
        col = tuple(int(VIOLET[k] * (1 - t) + CYAN[k] * t) for k in range(3)) + (255,)
        gd.line([(i, 0), (i, accent_h)], fill=col)
    am = Image.new("L", (accent_w, accent_h), 0)
    ImageDraw.Draw(am).rounded_rectangle([0, 0, accent_w - 1, accent_h - 1], radius=accent_h // 2, fill=255)
    grad.putalpha(am)
    og.alpha_composite(grad, dest=(M, y))
    blocks["accent"] = [M, y, M + accent_w, y + accent_h]
    y += accent_h + 30

    # subtitulo en dos lineas (mismo string requerido, repartido)
    for i, line in enumerate(sub_lines):
        color = (219, 215, 240, 255) if i == 0 else (174, 168, 206, 255)
        d.text((M, y), line, font=f_sub, fill=color)
        bb = f_sub.getbbox(line)
        blocks[f"subtitle{i + 1}"] = [M, y + bb[1], M + int(f_sub.getlength(line)), y + bb[3]]
        y += sub_adv

    # --- comprobaciones de layout (sin recortes ni solapes) ---
    for name, box in blocks.items():
        assert box[0] >= 24 and box[1] >= 20, f"og: {name} fuera por arriba/izquierda {box}"
        assert box[2] <= W - 24 and box[3] <= H - 20, f"og: {name} fuera por abajo/derecha {box}"
    for name in ("title1", "title2", "subtitle1", "subtitle2", "eyebrow"):
        box = blocks[name]
        assert box[2] < panel_rect[0] - 20, f"og: {name} choca con la captura: {box}"
    assert blocks["title2"][2] <= M + left_w + 4, "og: titulo mas ancho que la columna"
    log(f"  textos dentro de margenes; bloque {int(total_h)}px; columnas {left_w}px; mejor no recortar")

    dst = os.path.join(ROOT, "assets", "og.png")
    og.convert("RGB").save(dst, "PNG", optimize=True, compress_level=9)
    REPORT["og"] = {
        "size": [W, H], "kb": round(kb(dst), 1),
        "panel": panel_rect, "text_blocks": blocks,
        "left_column_width": left_w, "font": os.path.basename(F_BLACK),
    }
    log(f"  og.png  1200x630  {kb(dst):6.1f} KB")


# ---------------------------------------------------------------------------
# 6) site.webmanifest
# ---------------------------------------------------------------------------
def build_manifest() -> None:
    log("\n[6] site.webmanifest")
    manifest = {
        "name": "Forlex Optimizer",
        "short_name": "Forlex",
        "description": "Optimizador de Windows: 393 tweaks en 16 categorías para Windows 10/11 (64 bits).",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#07060f",
        "theme_color": "#07060f",
        "lang": "es",
        "icons": [
            {"src": "favicon/favicon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "favicon/favicon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        ],
    }
    dst = os.path.join(ROOT, "assets", "site.webmanifest")
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    REPORT["manifest"] = {"size": [None, None], "kb": round(kb(dst), 1)}
    log(f"  site.webmanifest  {kb(dst):6.1f} KB")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> None:
    for d in (IMG, FAV):
        os.makedirs(d, exist_ok=True)

    build_clean()
    build_shots()
    build_hero()
    build_og()
    build_favicons()
    build_manifest()

    # total y reporte
    files = []
    for base, _, names in os.walk(os.path.join(ROOT, "assets")):
        for n in names:
            p = os.path.join(base, n)
            files.append(p)
    total = sum(os.path.getsize(p) for p in files)
    REPORT["total_bytes"] = total
    REPORT["total_kb"] = round(total / 1024.0, 1)
    REPORT["files"] = sorted(os.path.relpath(p, ROOT).replace("\\", "/") for p in files)

    report_path = os.path.join(ROOT, "tools", "assets_report.json")
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(REPORT, fh, ensure_ascii=False, indent=2)

    log("\n" + "=" * 74)
    log(f"TOTAL assets: {total / (1024 * 1024):.2f} MB  ({len(files)} archivos)")
    log(f"reporte: {report_path}")
    assert total < 3.5 * 1024 * 1024, f"peso total {total/(1024*1024):.2f} MB >= 3.5 MB"
    log("OK: peso total < 3.5 MB")


if __name__ == "__main__":
    main()
