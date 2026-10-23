"""Tripo 입력 그림 만들기 — 사진 2(제품 3/4 뷰)에서 국새 클리커 한 개만 남긴다.

빨간 끈·술, 뒤·옆의 다른 제품, 고리를 지운다:
 - 배경 구역(다른 제품 자리)은 배경색으로 칠하고,
 - 제품 위를 지나는 빨간 끈은 OpenCV inpaint(Telea)로 주변 색을 채운다.
좌표는 잘라낸 그림(사진 2 의 380,1300 ~ 920,1850) 기준 px.
"""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]


def main():
    im = cv2.imread(str(ROOT / "sample/gukse_clicker_wadiz.jpg"))[1300:1850, 380:920].copy()
    h, w = im.shape[:2]
    bgc = np.median(im[500:550, 0:540].reshape(-1, 3), axis=0).astype(np.uint8)
    b, g, r = [im[..., i].astype(int) for i in range(3)]
    red = (r > 120) & (r - g > 60) & (r - b > 50)
    red = cv2.dilate(red.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    bg = np.zeros((h, w), bool)
    bg[:, :56] = True                      # 왼쪽 다른 제품
    bg[:300, 452:] = True                  # 오른쪽 뒤 다른 제품
    bg[:, 484:] = True                     # 고리·끈 고리
    bg[:135, 388:] = True                  # 뒤 국새
    bg[:118, :118] = True                  # 술(거북 머리 왼쪽 위)
    bg[110:225, :148] = True               # 왼쪽 뒤 다른 받침
    bg[110:270, 380:] = True               # 오른쪽 뒤 다른 받침
    bg[:40, 330:] = True                   # 뒤 국새 윗부분
    bg[:95, 372:] = True
    bg[:22, :] = True                      # 술 위쪽 끝
    bg[470:, :] = True                     # 바닥 그림자 아래
    keep_red_bg = red & (np.arange(h)[:, None] < 125) & (np.arange(w)[None, :] < 200)
    im[bg | keep_red_bg] = bgc
    fill = red & ~bg & ~keep_red_bg
    im = cv2.inpaint(im, fill.astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA)
    side = max(h, w) + 40
    canvas = np.full((side, side, 3), bgc, np.uint8)
    y0, x0 = (side - h) // 2, (side - w) // 2
    canvas[y0:y0 + h, x0:x0 + w] = im
    canvas = cv2.resize(canvas, (1024, 1024), interpolation=cv2.INTER_LANCZOS4)
    out = HERE / "tripo/clicker_full.png"
    cv2.imwrite(str(out), canvas)
    print(out)


if __name__ == "__main__":
    main()
