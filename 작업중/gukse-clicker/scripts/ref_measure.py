"""참고 사진 실측 그림: 사용자 사진 2장 위에 읽은 픽셀 선과 mm 환산을 그린다.

사진 1(sample/gukse_turtle_ref.jpg, 682×650, 박물관 정측면): 거북 뉴 : 인면 비례.
사진 2(sample/gukse_clicker_wadiz.jpg, 1440×3120 → 거북 제품 잘라냄 380,1300~920,1850, 3/4 원근): 하부·국새·거북 비례.
기준 = 사용자 치수 "하부 80 mm 정사각" (사진 2 하부 앞 모서리 폭). 원근이라 뒤쪽 요소는 ±10 % 오차 — 비례만 쓴다.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / "figures"
FONT = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"


def font(n):
    try:
        return ImageFont.truetype(FONT, n)
    except OSError:
        return ImageFont.load_default()


def hline(d, x0, x1, y, col, txt, f, up=True):
    d.line([(x0, y), (x1, y)], fill=col, width=3)
    for x in (x0, x1):
        d.line([(x, y - 8), (x, y + 8)], fill=col, width=3)
    d.text(((x0 + x1) / 2 - 60, y - 34 if up else y + 8), txt, fill=col, font=f)


def vline(d, x, y0, y1, col, txt, f):
    d.line([(x, y0), (x, y1)], fill=col, width=3)
    for y in (y0, y1):
        d.line([(x - 8, y), (x + 8, y)], fill=col, width=3)
    d.text((x + 10, (y0 + y1) / 2 - 12), txt, fill=col, font=f)


def main():
    OUT.mkdir(exist_ok=True)
    f = font(22)
    # --- 사진 2 (제품) : 잘라낸 좌표(px) 그대로 2배 확대해 그림
    im = Image.open(ROOT / "sample/gukse_clicker_wadiz.jpg").convert("RGB").crop((380, 1300, 920, 1850))
    im = im.resize((im.width * 2, im.height * 2))
    d = ImageDraw.Draw(im)
    s = 80.0 / (478 - 80)  # mm/px(잘라낸 좌표) — 하부 앞 모서리 80 mm
    Y, C, M, G = (255, 220, 0), (0, 230, 255), (255, 80, 200), (120, 255, 120)
    hline(d, 160, 956, 940, Y, f"하부 80.0 (398 px, {s:.3f} mm/px)", f, up=False)
    vline(d, 975, 760, 924, Y, f"아래단 {164 / 2 * s:.1f}", f)
    hline(d, 290, 840, 560, C, f"윗단 위 {(420 - 145) * s:.1f}", f)
    vline(d, 870, 570, 740, C, f"윗단 {(370 - 285) * s:.1f}", f)
    hline(d, 300, 750, 330, M, f"국새 {(375 - 150) * s:.1f}", f, up=False)
    vline(d, 290, 320, 550, M, f"국새 보이는 높이 {(275 - 160) * s:.1f}", f)
    hline(d, 240, 770, 30, G, f"거북 {(385 - 120) * s:.1f}", f, up=False)
    im.save(OUT / "ref_wadiz_measure.png")
    # --- 사진 1 (정측면) : 비례
    im = Image.open(ROOT / "sample/gukse_turtle_ref.jpg").convert("RGB")
    im = im.resize((im.width * 2, im.height * 2))
    d = ImageDraw.Draw(im)
    hline(d, 2 * 143, 2 * 625, 2 * 140, G, "거북 482 px = 인면 ×1.17", f)
    hline(d, 2 * 122, 2 * 533, 2 * 520, M, "인면 411 px (=1)", f, up=False)
    vline(d, 2 * 650, 2 * 165, 2 * 383, G, "거북 높이 218 px = ×0.53", f)
    vline(d, 2 * 560, 2 * 383, 2 * 503, M, "인 몸통 120 px = ×0.29", f)
    im.save(OUT / "ref_turtle_measure.png")
    print("ok", OUT)


if __name__ == "__main__":
    main()
