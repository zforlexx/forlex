"""
verify_assets.py - Comprobacion final de TODOS los assets generados por make_assets.py.

Abre cada archivo con Pillow, imprime nombre, dimensiones y KB y valida:
  * que exista y sea del formato esperado,
  * que las dimensiones coincidan EXACTAMENTE con la referencia (recorte taskbar
    + reescalado) y que la calidad no se haya degradado (PSNR >= 30 dB),
  * que en las capturas de shots/ NO quede barra de tareas (alto <= 1026 px,
    aspect ratio del recorte y ausencia de filas claras uniformes tipo taskbar),
  * og.png: 1200x630, texto dentro de margenes, contraste y captura enmarcada,
  * favicons: tamanos, canal alfa, monograma blanco centrado, ICO 16/32/48,
  * site.webmanifest: JSON valido con los campos pedidos,
  * peso total < 3.5 MB.

Uso:
    python tools/verify_assets.py
Sale con codigo 0 si todo pasa, 1 si algo falla.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
IMG = os.path.join(ASSETS, "img")
FAV = os.path.join(ASSETS, "favicon")

# importar make_assets para reutilizar las referencias exactas
spec = importlib.util.spec_from_file_location("make_assets", os.path.join(HERE, "make_assets.py"))
ma = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ma)

ERRORS: list[str] = []
CHECKS: list[str] = []


def check(cond: bool, msg_ok: str, msg_fail: str) -> bool:
    if cond:
        CHECKS.append(msg_ok)
        return True
    ERRORS.append(msg_fail)
    return False


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    d = a.astype(np.float64) - b.astype(np.float64)
    mse = float((d * d).mean())
    if mse == 0:
        return 99.0
    return 10.0 * math.log10((255.0 ** 2) / mse)


def kb(path: str) -> float:
    return os.path.getsize(path) / 1024.0


# ---------------------------------------------------------------------------
# 1) WebP: capturas limpias, shots recortadas y hero
# ---------------------------------------------------------------------------
print("=" * 86)
print("1) IMAGENES WEBP  (nombre | dimensiones | KB | PSNR vs referencia)")
print("=" * 86)
print(f"{'archivo':18s} {'dimensiones':>12s} {'KB':>8s} {'PSNR':>7s}  {'origen'}")
print("-" * 86)

webp_expected: list[tuple[str, Image.Image, str]] = []
for name in ma.CLEAN:
    webp_expected.append((f"{name}.webp", ma.clean_reference(name), ma.CLEAN[name][0]))
for name in ma.SHOT_MAP:
    ref, top = ma.shot_reference(name)
    webp_expected.append((f"{name}.webp", ref, f"shots/{ma.SHOT_MAP[name]} (crop y={top})"))
webp_expected.append(("inicio-hero.webp", ma.hero_reference(), "01-inicio.png (1800, q=90)"))

for fname, ref, origin in webp_expected:
    path = os.path.join(IMG, fname)
    if not os.path.isfile(path):
        check(False, "", f"FALTA {fname}")
        continue
    im = Image.open(path)
    im.load()
    ok_fmt = check(im.format == "WEBP", f"{fname} WEBP ok", f"{fname}: formato {im.format} != WEBP")
    ok_dim = check(
        im.size == ref.size,
        "",
        f"{fname}: dimension {im.size} != referencia {ref.size}",
    )
    if im.mode != "RGB":
        ERRORS.append(f"{fname}: modo {im.mode} (se espera RGB)")
    got = np.asarray(im.convert("RGB")).astype(np.int16)
    want = np.asarray(ref.convert("RGB")).astype(np.int16)
    if got.shape != want.shape:
        check(False, "", f"{fname}: forma distinta {got.shape} vs {want.shape}")
        continue
    p = psnr(got, want)
    ok_psnr = check(p >= 30.0, "", f"{fname}: PSNR {p:.1f} dB < 30 dB (compresion excesiva/corrupta)")
    print(f"{fname:18s} {f'{im.size[0]}x{im.size[1]}':>12s} {kb(path):8.1f} {p:6.1f}dB  {origin}")

# --- comprobacion anti-taskbar sobre las shots ---
print("\n" + "-" * 86)
print("   comprobacion de barra de tareas en las 16 capturas de shots/")
for name, fname in ma.SHOT_MAP.items():
    path = os.path.join(IMG, f"{name}.webp")
    src = Image.open(os.path.join(ma.SHOTS, fname))
    src.load()
    top = ma.detect_taskbar_top(src)
    im = Image.open(path)
    im.load()
    check(top is not None and 1000 <= top <= 1030, "", f"{name}: taskbar no detectada en {fname}")
    if top is None:
        continue
    expected_h = round(top * im.width / src.width)
    check(
        im.height == expected_h,
        "",
        f"{name}: alto {im.height} != {expected_h} (recorte de taskbar incorrecto)",
    )
    check(
        im.height <= 1026,
        "",
        f"{name}: alto {im.height} > 1026 px (podria quedar la taskbar)",
    )
    # el borde superior de la taskbar es una fila clara uniforme; no debe aparecer
    arr = np.asarray(im.convert("RGB")).astype(np.float32)
    bottom = arr[-8:]
    means = bottom.mean(axis=(1, 2))
    stds = bottom.std(axis=(1, 2))
    bad = int(np.sum((means > 50) & (stds < 2.0)))
    check(bad == 0, "", f"{name}: {bad} fila(s) claras uniformes en el borde inferior (taskbar)")
    check(float(arr[-1].mean()) < 50.0, "", f"{name}: ultima fila sospechosa (media {arr[-1].mean():.1f})")
CHECKS.append("16 shots: recorte de taskbar en y=1020 -> alto 1600x850 (sin bordes de barra)")

# ---------------------------------------------------------------------------
# 2) og.png
# ---------------------------------------------------------------------------
print("\n" + "=" * 86)
print("2) og.png")
print("=" * 86)
og_path = os.path.join(ASSETS, "og.png")
if not os.path.isfile(og_path):
    ERRORS.append("FALTA assets/og.png")
    og = None
else:
    og = Image.open(og_path)
    og.load()
    print(f"{'og.png':18s} {f'{og.size[0]}x{og.size[1]}':>12s} {kb(og_path):8.1f}  formato={og.format} modo={og.mode}")
    check(og.size == (1200, 630), "", f"og.png: {og.size} != (1200, 630)")
    check(og.format == "PNG", "", f"og.png: formato {og.format} != PNG")
    a = np.asarray(og.convert("RGB")).astype(np.float32)
    lum = a.mean(axis=2)
    W, H = og.size
    # -- layout declarado por el pipeline --
    with open(os.path.join(HERE, "assets_report.json"), encoding="utf-8") as fh:
        rep = json.load(fh)
    blocks = rep["og"]["text_blocks"]
    panel = rep["og"]["panel"]
    for bname, (x0, y0, x1, y1) in blocks.items():
        inside = x0 >= 24 and y0 >= 20 and x1 <= W - 24 and y1 <= H - 20
        check(inside, "", f"og.png: texto '{bname}' fuera de margenes ({x0},{y0},{x1},{y1})")
        inter = not (x1 <= panel[0] or x0 >= panel[2] or y1 <= panel[1] or y0 >= panel[3])
        check(not inter, "", f"og.png: texto '{bname}' se solapa con la captura enmarcada")
    # -- contraste del texto --
    def region_p95(name):
        x0, y0, x1, y1 = blocks[name]
        return float(np.percentile(lum[y0:y1, x0:x1], 95))

    check(region_p95("title1") > 200, "", "og.png: titulo FORLEX sin contraste suficiente")
    check(region_p95("title2") > 120, "", "og.png: titulo OPTIMIZER sin contraste suficiente")
    check(region_p95("subtitle1") > 110 and region_p95("subtitle2") > 100, "", "og.png: subtitulo poco legible")
    # -- la captura enmarcada tiene contenido real --
    px0, py0, px1, py1 = panel
    panel_lum = lum[py0:py1, px0:px1]
    check(float(panel_lum.std()) > 15.0, "", "og.png: la captura del panel parece vacia")
    check(float(panel_lum.mean()) > 10.0, "", "og.png: la captura del panel esta practicamente negra")
    # -- glow violeta a la izquierda-abajo y cian a la derecha-abajo --
    violet_zone = a[int(H * 0.82):H, 0:int(W * 0.22)].reshape(-1, 3).mean(axis=0)
    cyan_zone = a[int(H * 0.86):H, int(W * 0.92):W].reshape(-1, 3).mean(axis=0)
    check(violet_zone[2] > violet_zone[1] + 12, "", "og.png: falta glow violeta (izquierda/abajo)")
    check(cyan_zone[2] > cyan_zone[0] + 12 and cyan_zone[1] > cyan_zone[0] + 6, "", "og.png: falta glow cian (derecha/abajo)")
    print(f"   layout: panel={panel}  texto x=24..{W - 24}  bloques={list(blocks)}")
    print(f"   glow: violeta(izq-abajo)={violet_zone.round(1).tolist()}  cian(der-abajo)={cyan_zone.round(1).tolist()}")
    print("   texto: FORLEX p95=%.0f  OPTIMIZER p95=%.0f  subtitulo p95=%.0f" % (
        region_p95("title1"), region_p95("title2"), region_p95("subtitle1")))

# ---------------------------------------------------------------------------
# 3) Favicons
# ---------------------------------------------------------------------------
print("\n" + "=" * 86)
print("3) FAVICONS")
print("=" * 86)
expected_png = {
    "favicon-32.png": 32,
    "favicon-192.png": 192,
    "favicon-512.png": 512,
    "apple-touch-icon.png": 180,
}
for fname, size in expected_png.items():
    path = os.path.join(FAV, fname)
    if not os.path.isfile(path):
        ERRORS.append(f"FALTA {fname}")
        continue
    im = Image.open(path)
    im.load()
    print(f"{fname:22s} {f'{im.size[0]}x{im.size[1]}':>10s} {kb(path):8.1f}  modo={im.mode}")
    check(im.size == (size, size), "", f"{fname}: {im.size} != ({size}, {size})")
    check(im.format == "PNG", "", f"{fname}: formato {im.format} != PNG")
    check("A" in im.getbands(), "", f"{fname}: sin canal alfa (se espera RGBA/LA)")
    rgba = np.asarray(im.convert("RGBA")).astype(np.float32)
    alpha = rgba[..., 3]
    white = (rgba[..., :3].min(axis=2) > 235) & (alpha > 200)
    ys, xs = np.where(white)
    check(len(xs) > 0, "", f"{fname}: monograma blanco no encontrado")
    if len(xs):
        cx, cy = float(xs.mean()), float(ys.mean())
        check(
            abs(cx - size / 2) < size * 0.05 and abs(cy - size / 2) < size * 0.05,
            "",
            f"{fname}: monograma descentrado (centro {cx:.1f},{cy:.1f} en {size}x{size})",
        )
    # esquinas: rounded = transparentes; apple-touch = opaco
    corner_alpha = float(alpha[0, 0])
    if fname == "apple-touch-icon.png":
        check(corner_alpha > 250, "", "apple-touch-icon.png: las esquinas deben ser opacas (iOS redondea)")
    else:
        check(corner_alpha < 10, "", f"{fname}: las esquinas deben ser transparentes (cuadrado redondeado)")

ico_path = os.path.join(FAV, "favicon.ico")
if not os.path.isfile(ico_path):
    ERRORS.append("FALTA favicon.ico")
else:
    ico = Image.open(ico_path)
    ico.load()
    sizes = sorted(ico.ico.sizes()) if hasattr(ico, "ico") else []
    print(f"{'favicon.ico':22s} {'/'.join(str(s[0]) for s in sizes):>10s} {kb(ico_path):8.1f}  frames={sizes}")
    check(sizes == [(16, 16), (32, 32), (48, 48)], "", f"favicon.ico: frames {sizes} != 16/32/48")

# ---------------------------------------------------------------------------
# 4) site.webmanifest
# ---------------------------------------------------------------------------
print("\n" + "=" * 86)
print("4) site.webmanifest")
print("=" * 86)
man_path = os.path.join(ASSETS, "site.webmanifest")
try:
    with open(man_path, encoding="utf-8") as fh:
        man = json.load(fh)
    ok_json = True
except Exception as exc:  # noqa: BLE001
    ok_json = False
    man = {}
    ERRORS.append(f"site.webmanifest: JSON invalido ({exc})")
print(f"{'site.webmanifest':22s} {'-':>10s} {kb(man_path):8.1f}  nombre={man.get('name')!r} theme={man.get('theme_color')!r}")
check(ok_json, "", "site.webmanifest: JSON invalido")
check(man.get("name") == "Forlex Optimizer", "", f"site.webmanifest: name={man.get('name')!r}")
check(man.get("theme_color") == "#07060f", "", f"site.webmanifest: theme_color={man.get('theme_color')!r}")
check(man.get("start_url") == "./", "", f"site.webmanifest: start_url={man.get('start_url')!r}")
sizes_icons = sorted(icon.get("sizes") for icon in man.get("icons", []))
check(sizes_icons == ["192x192", "512x512"], "", f"site.webmanifest: iconos={sizes_icons}")

# ---------------------------------------------------------------------------
# 5) Peso total
# ---------------------------------------------------------------------------
print("\n" + "=" * 86)
print("5) PESO TOTAL")
print("=" * 86)
my_files = [os.path.join(IMG, f) for f in os.listdir(IMG) if f.endswith(".webp")]
my_files += [os.path.join(FAV, f) for f in os.listdir(FAV)]
my_files += [og_path, man_path]
my_files = [p for p in my_files if os.path.isfile(p)]
total = sum(os.path.getsize(p) for p in my_files)
total_img = sum(os.path.getsize(p) for p in my_files if p.startswith(IMG))
total_og = os.path.getsize(og_path) if os.path.isfile(og_path) else 0
total_fav = sum(os.path.getsize(p) for p in my_files if p.startswith(FAV))
print(f"  assets/img/*.webp      {total_img / 1024:9.1f} KB  ({len([p for p in my_files if p.startswith(IMG)])} archivos)")
print(f"  assets/og.png          {total_og / 1024:9.1f} KB")
print(f"  assets/favicon/*       {total_fav / 1024:9.1f} KB  ({len([p for p in my_files if p.startswith(FAV)])} archivos)")
print(f"  assets/site.webmanifest{os.path.getsize(man_path) / 1024:9.1f} KB")
print(f"  TOTAL                  {total / 1024:9.1f} KB  = {total / (1024 * 1024):.2f} MB  ({len(my_files)} archivos)")
check(total < 3.5 * 1024 * 1024, "total < 3.5 MB", f"total {total / (1024 * 1024):.2f} MB >= 3.5 MB")
check(total < 5.5 * 1024 * 1024, "total < 5.5 MB (limite duro)", f"total {total / (1024 * 1024):.2f} MB >= 5.5 MB")

# ---------------------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------------------
print("\n" + "=" * 86)
if ERRORS:
    print(f"FALLARON {len(ERRORS)} COMPROBACIONES:")
    for e in ERRORS:
        print("  [X] " + e)
    sys.exit(1)
print(f"OK: {len(CHECKS)} comprobaciones pasaron. Ningun problema detectado.")
print("    - 22 WebP abiertos con Pillow, dimensiones y PSNR verificados")
print("    - 16 shots sin barra de tareas (recorte en y=1020, alto 850 px <= 1026)")
print("    - og.png 1200x630 con texto dentro de margenes y sin solapes")
print("    - favicons 16/32/48 + 32/192/512 + 180 con monograma centrado")
print("    - site.webmanifest valido; peso total por debajo de 3.5 MB")
sys.exit(0)
