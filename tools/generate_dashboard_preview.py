from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "dashboard-preview.png"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, radius: int = 24, outline: str | None = None) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int, fill: str, bold: bool = False) -> None:
    draw.text(xy, value, fill=fill, font=font(size, bold=bold))


def metric(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, value: str, caption: str, fill: str = "#fffef7", dark: bool = False) -> None:
    rounded(draw, box, fill, radius=26, outline="#e2e3d8")
    x, y, _, _ = box
    ink = "#fffaf3" if dark else "#101815"
    muted = "#ecd9d3" if dark else "#66736d"
    text(draw, (x + 24, y + 24), title.upper(), 18, muted, bold=True)
    text(draw, (x + 24, y + 58), value, 62, ink, bold=True)
    text(draw, (x + 24, y + 134), caption, 20, muted)


def pill(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, fill: str, ink: str) -> None:
    width = max(76, len(label) * 13 + 24)
    rounded(draw, (x, y, x + width, y + 34), fill, radius=18)
    text(draw, (x + 13, y + 7), label, 16, ink, bold=True)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1440, 930), "#eef1ea")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, 1440, 930), fill="#eef1ea")
    draw.ellipse((-140, -180, 520, 420), fill="#d4eadf")
    draw.ellipse((1030, -170, 1590, 340), fill="#f1d9d2")

    rounded(draw, (42, 30, 1398, 104), "#fffef7", radius=22, outline="#e0e2d8")
    rounded(draw, (66, 48, 112, 86), "#13211d", radius=14)
    text(draw, (128, 42), "PulseLens", 26, "#101815", bold=True)
    text(draw, (128, 72), "Reputation risk command center", 15, "#66736d", bold=True)
    rounded(draw, (1118, 46, 1248, 88), "#ffffff", radius=14, outline="#d4d8cd")
    text(draw, (1142, 58), "Export CSV", 17, "#101815", bold=True)
    rounded(draw, (1264, 46, 1384, 88), "#13211d", radius=14)
    text(draw, (1279, 58), "Report", 17, "#fffef7", bold=True)

    rounded(draw, (42, 130, 1398, 408), "#14231f", radius=34)
    draw.ellipse((700, 90, 1300, 580), fill="#244e43")
    text(draw, (86, 184), "PUBLIC OPINION EARLY WARNING", 18, "#99d7c4", bold=True)
    text(draw, (86, 222), "Monitor risk before", 60, "#fffaf3", bold=True)
    text(draw, (86, 288), "the conversation turns.", 60, "#fffaf3", bold=True)
    text(draw, (90, 360), "Track watched subjects, detect harmful signals, assign L0-L5 risk, and export response-ready reports.", 23, "#cbd7ce")
    rounded(draw, (1114, 170, 1366, 224), "#203b34", radius=28, outline="#375e52")
    draw.ellipse((1134, 190, 1148, 204), fill="#8df1bc")
    text(draw, (1162, 184), "Local analysis online", 19, "#f9f6ea", bold=True)

    metric(draw, (42, 426, 382, 610), "Total mentions", "6", "All monitored items")
    metric(draw, (398, 426, 738, 610), "High alerts", "3", "L3-L5 items for review", fill="#8b2d2e", dark=True)
    metric(draw, (754, 426, 1094, 610), "Average risk", "57.5", "Composite risk score")
    rounded(draw, (1110, 426, 1398, 610), "#fffef7", radius=26, outline="#e2e3d8")
    text(draw, (1134, 450), "RISK MIX", 18, "#66736d", bold=True)
    pill(draw, 1134, 496, "L4 2", "#8b2d2e", "#fffaf3")
    pill(draw, 1212, 496, "L3 1", "#b93d3b", "#fffaf3")
    pill(draw, 1290, 496, "L2 1", "#faecd0", "#8d5a12")
    pill(draw, 1134, 540, "L1 2", "#e5f4ec", "#2e7f57")

    rounded(draw, (42, 628, 460, 892), "#fffef7", radius=28, outline="#e2e3d8")
    text(draw, (72, 662), "WATCHLIST", 17, "#2c7a61", bold=True)
    text(draw, (72, 690), "Watched entities", 30, "#101815", bold=True)
    for i, (name, desc, score) in enumerate([
        ("Acme Cloud", "Cloud productivity platform", "80"),
        ("Polaris Coffee", "Regional coffee brand", "87"),
    ]):
        y = 748 + i * 82
        rounded(draw, (72, y, 430, y + 62), "#f6f7f0", radius=18, outline="#e4e6dc")
        text(draw, (92, y + 12), name, 21, "#101815", bold=True)
        text(draw, (92, y + 38), desc, 15, "#66736d")
        pill(draw, 360, y + 14, score, "#8b2d2e", "#fffaf3")

    rounded(draw, (478, 628, 1398, 892), "#fffef7", radius=28, outline="#e2e3d8")
    text(draw, (508, 662), "TRIAGE QUEUE", 17, "#2c7a61", bold=True)
    text(draw, (508, 690), "Priority mentions", 30, "#101815", bold=True)
    alerts = [
        ("L4 87", "Polaris Coffee / weibo", "Customer complaints about store hygiene and service risk.", "#8b2d2e"),
        ("L4 80", "Acme Cloud / reddit", "Support delay and outage conversation requires response.", "#8b2d2e"),
        ("L3 72", "Acme Cloud / press", "Regulator investigation after possible data breach.", "#b93d3b"),
    ]
    for i, (badge, title, body, color) in enumerate(alerts):
        y = 742 + i * 58
        rounded(draw, (508, y, 1364, y + 54), "#f7f7f0", radius=18, outline="#e5e7dd")
        pill(draw, 526, y + 13, badge, color, "#fffaf3")
        text(draw, (608, y + 10), title, 20, "#101815", bold=True)
        text(draw, (608, y + 34), body, 15, "#66736d")

    image.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
