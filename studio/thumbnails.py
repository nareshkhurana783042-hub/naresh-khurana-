"""Smart AI Thumbnail Generator for clips:
Creates high-CTR, vibrant viral thumbnails with eye-catching typography,
contrast enhancement, and viral hook overlays.
"""
import os
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

FONT_DIR = Path(__file__).resolve().parent / "fonts"
ANTON_FONT = FONT_DIR / "Anton-Regular.ttf"
POPPINS_FONT = FONT_DIR / "Poppins-ExtraBold.ttf"
ARCHIVO_FONT = FONT_DIR / "ArchivoBlack-Regular.ttf"


def _get_font(font_path: Path, size: int):
    try:
        if font_path.is_file():
            return ImageFont.truetype(str(font_path), size)
    except Exception:
        pass
    return ImageFont.load_default()


def _draw_gradient_vignette(img: Image.Image) -> Image.Image:
    """Adds a subtle top and bottom dark gradient for high text readability."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Top gradient (height ~ 28%)
    top_h = int(h * 0.28)
    for y in range(top_h):
        alpha = int(180 * (1 - (y / top_h) ** 0.8))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
        
    # Bottom gradient (height ~ 32%)
    bot_h = int(h * 0.32)
    start_y = h - bot_h
    for y in range(bot_h):
        alpha = int(210 * ((y / bot_h) ** 0.8))
        draw.line([(0, start_y + y), (w, start_y + y)], fill=(0, 0, 0, alpha))
        
    img = img.convert("RGBA")
    return Image.alpha_composite(img, overlay).convert("RGB")


def _enhance_visuals(img: Image.Image) -> Image.Image:
    """Boosts colors, contrast and sharpness for viral thumbnail punch."""
    img = ImageEnhance.Color(img).enhance(1.25)       # rich vibrant colors
    img = ImageEnhance.Contrast(img).enhance(1.18)    # punchy contrast
    img = ImageEnhance.Sharpness(img).enhance(1.30)   # crisp details
    return img


def _wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list:
    """Wraps headline text into at most 3 punchy lines."""
    words = text.strip().split()
    if not words:
        return []
    lines = []
    cur = []
    for w in words:
        test = " ".join(cur + [w])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines[:3]


def render_thumbnail(
    frame_path: Path,
    out_path: Path,
    headline: str = "",
    badge: str = "",
    style: str = "viral"
) -> Path:
    """Draws viral typography, badge, and enhancements onto a video frame."""
    img = Image.open(frame_path).convert("RGB")
    w, h = img.size
    
    # 1. Enhance colors & contrast
    img = _enhance_visuals(img)
    
    # 2. Add cinematic top & bottom gradient
    img = _draw_gradient_vignette(img)
    draw = ImageDraw.Draw(img)
    
    # 3. Top Badge (e.g. "WAIT FOR IT" or "😱 MUST WATCH")
    badge_text = (badge or "").strip().upper()
    if badge_text:
        badge_font_size = max(24, int(w * 0.048))
        b_font = _get_font(POPPINS_FONT if POPPINS_FONT.is_file() else ANTON_FONT, badge_font_size)
        bbox = draw.textbbox((0, 0), badge_text, font=b_font)
        bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad_x, pad_y = int(bw * 0.12), int(bh * 0.35)
        
        # Pill coordinates
        bx0 = (w - (bw + pad_x * 2)) // 2
        by0 = int(h * 0.06)
        bx1 = bx0 + bw + pad_x * 2
        by1 = by0 + bh + pad_y * 2
        
        # Draw pill shadow & background (Vibrant Red or Gold)
        draw.rounded_rectangle([bx0 + 3, by0 + 4, bx1 + 3, by1 + 4], radius=14, fill=(0, 0, 0, 160))
        draw.rounded_rectangle([bx0, by0, bx1, by1], radius=14, fill=(230, 20, 50), outline=(255, 255, 255), width=3)
        draw.text((bx0 + pad_x, by0 + pad_y - 2), badge_text, font=b_font, fill=(255, 255, 255))
        
    # 4. Main Headline at Bottom
    hl = (headline or "").strip().upper()
    if hl:
        # Scale font to fit width nicely
        font_size = max(42, int(w * 0.10))
        font = _get_font(ANTON_FONT if ANTON_FONT.is_file() else ARCHIVO_FONT, font_size)
        max_w = int(w * 0.88)
        lines = _wrap_text(hl, font, max_w, draw)
        
        # Calculate block height
        line_heights = []
        for l in lines:
            bb = draw.textbbox((0, 0), l, font=font)
            line_heights.append(bb[3] - bb[1])
            
        spacing = int(font_size * 0.22)
        total_text_h = sum(line_heights) + spacing * (len(lines) - 1)
        
        # Position near bottom (around 70%-75% of height)
        curr_y = int(h * 0.82) - total_text_h
        
        # Alternating high-CTR colors: Gold / Yellow and White
        colors = [(255, 230, 0), (255, 255, 255), (255, 230, 0)]
        
        for idx, (l, lh) in enumerate(zip(lines, line_heights)):
            bb = draw.textbbox((0, 0), l, font=font)
            lw = bb[2] - bb[0]
            lx = (w - lw) // 2
            
            # Thick black outline for maximum readability on any background
            stroke_w = max(5, int(font_size * 0.10))
            draw.text(
                (lx, curr_y),
                l,
                font=font,
                fill=colors[idx % len(colors)],
                stroke_width=stroke_w,
                stroke_fill=(0, 0, 0)
            )
            curr_y += lh + spacing
            
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path), "JPEG", quality=95, optimize=True)
    return out_path


def create_clip_thumbnail(
    clip_video: Path,
    out_cover: Path,
    headline: str = "",
    badge: str = "",
    time_offset: float | None = None
) -> Path:
    """Extracts a high quality frame from the clip video and renders a viral thumbnail."""
    work_frame = out_cover.with_name(f"{out_cover.stem}_raw.jpg")
    
    # Pick a good moment (e.g. 2.0s or 25% into the video)
    t = 2.0 if time_offset is None else max(0.5, float(time_offset))
    
    # Extract frame with ffmpeg
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", f"{t:.2f}",
        "-i", str(clip_video),
        "-frames:v", "1",
        "-q:v", "2",
        str(work_frame)
    ]
    try:
        subprocess.run(cmd, check=True, timeout=15)
        if not work_frame.is_file() or work_frame.stat().st_size == 0:
            # Fallback to 0.5s if 2.0s failed
            cmd[4] = "0.50"
            subprocess.run(cmd, check=True, timeout=10)
    except Exception as e:
        if not work_frame.is_file():
            raise RuntimeError(f"Could not extract frame for thumbnail: {e}")
            
    try:
        render_thumbnail(work_frame, out_cover, headline=headline, badge=badge)
    finally:
        if work_frame.is_file():
            try:
                work_frame.unlink()
            except OSError:
                pass
                
    return out_cover
