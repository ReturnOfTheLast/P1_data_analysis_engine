from PIL import Image, ImageDraw
from math import sqrt

color_gradient = [
                    [0, 0, 255, 0],
                    [50, 255, 255, 0],
                    [100, 255, 0, 0]
                 ]

def getcolor(color_gradient: list, percent: int) -> tuple:
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
    return Image.new("RGB", (width, height), color=(0, 0, 0))

def draw_heat_circles(im: Image.Image, ap: tuple, scans: list) -> None:
    scan_dists = []
    for scan in scans:
        dist = int(sqrt((ap[0] - scan[0])**2 + (ap[1] - scan[1])**2))
        scan_dists.append((dist, int((-scan[2]/90) * 100)))

    scan_dists.sort(key=lambda x: x[0], reverse=True)

    draw = ImageDraw.Draw(im)

    for dist in scan_dists:
        color = getcolor(color_gradient, dist[1])
        draw.ellipse([(ap[0] - dist[0], ap[1] - dist[0]), (ap[0] + dist[0], ap[1] + dist[0])], fill=color)

def draw_scanning_points(im: Image.Image, scans: list) -> None:
    draw = ImageDraw.Draw(im)
    for scan in scans:
        draw.ellipse([(scan[0] - 5, scan[1] - 5), (scan[0] + 5, scan[1] + 5)], fill=(127, 127, 127))
        draw.text((scan[0] + 10, scan[1]), scan[3], fill=(0, 255, 255), anchor="ls")

def draw_accesspoint(im: Image.Image, ap: tuple) -> None:
    draw = ImageDraw.Draw(im)
    draw.ellipse([(ap[0] - 5, ap[1] - 5), (ap[0] + 5, ap[1] + 5)], fill=(50, 50, 50))
    draw.text((ap[0] + 10, ap[1]), ap[2], fill=(50, 50, 50), anchor="ls")
