from PIL import Image, ImageDraw, ImageFont
from math import sqrt

"""
ap = {
    "coords": (0, 0),
    "label": "Access Point"
}

scans = [
    {
        "coords": (0, 0),
        "rssi": -45,
        "label": "scanning point 1"
    },
    ...
]
"""

fnt = ImageFont.truetype("LiberationMono-Regular.ttf", 20)

color_gradient = [
                    [0, 0, 255, 0],
                    [50, 255, 255, 0],
                    [100, 255, 0, 0]
                 ]

def getcolor(color_gradient: list[list], percent: int) -> tuple[int, int, int]:
    index = 0
    for i in range(len(color_gradient)):
        if percent < color_gradient[i][0]:
            index = i
            break

    lower = color_gradient[index - 1]
    upper = color_gradient[index]
    range_ = upper[0] - lower[0]
    range_percent = (percent - lower[0]) / range_
    percent_lower = 1 - range_percent
    percent_upper = range_percent
    return (
        int(lower[1] * percent_lower + upper[1] * percent_upper),
        int(lower[2] * percent_lower + upper[2] * percent_upper),
        int(lower[3] * percent_lower + upper[3] * percent_upper)
    )

def make_image(width: int, height: int) -> Image.Image:
    # Make new pillow image
    return Image.new("RGB", (width, height), color=(255, 255, 255))

def draw_heat_circles(im: Image.Image, ap: dict, scans: list[dict]) -> None:
    scan_dists = []
    for scan in scans:
        dist = int(
            sqrt(
                (ap["coords"][0] - scan["coords"][0])**2 +
                (ap["coords"][1] - scan["coords"][1])**2
            )
        )
        scan_dists.append((dist, -scan["rssi"]))

    scan_dists.sort(key=lambda x: x[1], reverse=True)

    draw = ImageDraw.Draw(im)

    for dist in scan_dists:
        color = getcolor(color_gradient, dist[1])
        draw.ellipse(
            [
                (ap["coords"][0] - dist[0], ap["coords"][1] - dist[0]),
                (ap["coords"][0] + dist[0], ap["coords"][1] + dist[0])
            ],
            fill=color
        )

def draw_scanning_points(im: Image.Image, scans: list[dict]) -> None:
    draw = ImageDraw.Draw(im)
    for scan in scans:
        draw.ellipse(
            [
                (scan["coords"][0] - 5, scan["coords"][1] - 5),
                (scan["coords"][0] + 5, scan["coords"][1] + 5)
            ],
            fill=(102, 51, 153)
        )
        draw.text(
            (scan["coords"][0] + 10, scan["coords"][1]),
            scan["label"],
            fill=(102, 51, 153),
            font=fnt,
            anchor="ls"
        )

def draw_accesspoint(im: Image.Image, ap: dict) -> None:
    draw = ImageDraw.Draw(im)
    draw.ellipse(
        [
            (ap["coords"][0] - 5, ap["coords"][1] - 5),
            (ap["coords"][0] + 5, ap["coords"][1] + 5)
        ],
        fill=(50, 50, 50)
    )
    draw.text(
        (ap["coords"][0] + 10, ap["coords"][1]),
        ap["label"],
        fill=(50, 50, 50),
        font=fnt,
        anchor="ls"
    )

def draw_scale_guide(im: Image.Image) -> None:
    
    draw = ImageDraw.Draw(im)
    draw.rectangle(
        [(0, im.height-40), (im.width, im.height)],
        fill=(255, 255, 255)
    )

    for i in range(im.width - 40):
        percent = (i/(im.width - 40)) * 100
        draw.line(
            [(i+20, im.height-30), (i+20, im.height-20)],
            fill=getcolor(color_gradient, percent),
            width=1
        )
