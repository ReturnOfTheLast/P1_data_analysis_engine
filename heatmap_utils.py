"""Utility functions for heatmap generation
"""

# Import Modules
from PIL import Image, ImageDraw, ImageFont
from math import sqrt

# Make font object to use for text
fnt = ImageFont.truetype("LiberationMono-Regular.ttf", 20)

# Define color gradient for heatmap
color_gradient = [
                    [0, 0, 255, 0],
                    [50, 255, 255, 0],
                    [100, 255, 0, 0]
                 ]

def getcolor(color_gradient: list[list], percent: int) -> tuple[int, int, int]:
    """The the color from the color gradient for percent.

    Args:
        color_gradient (list[list]): The color gradient
        percent (int): The percent to get the color for

    Returns:
        tuple[int, int, int]: The color in (R, G, B)
    """

    # Make index variable
    index = 0

    # Loop over gradient sections in the gradient
    for i in range(len(color_gradient)):
        if percent < color_gradient[i][0]:
            # If the provided percent is lower then gradient section set the
            # index to the section we reached and break out of the loop
            index = i
            break

    # Set the lower and upper color from the gradient
    lower = color_gradient[index - 1]
    upper = color_gradient[index]

    # Calculate the range between the colors
    range_ = upper[0] - lower[0]

    # Calculate the percentage between the colors that we want
    range_percent = (percent - lower[0]) / range_

    # Calculate how many percent each of the colors effect the final color
    percent_lower = 1 - range_percent
    percent_upper = range_percent

    # Calculate and return the final color
    return (
        int(lower[1] * percent_lower + upper[1] * percent_upper),
        int(lower[2] * percent_lower + upper[2] * percent_upper),
        int(lower[3] * percent_lower + upper[3] * percent_upper)
    )

def make_image(width: int, height: int) -> Image.Image:
    """Make a new pillow image.

    Args:
        width (int): The width of the image
        height (int): The height of the image

    Returns:
        Image.Image: The generated image
    """

    # Make the image and return it, we add an extra 100 pixels to the height
    # so we have space for a gradient bar the bottom
    return Image.new("RGB", (width, height+100), color=(255, 255, 255))

def draw_heat_circles(im: Image.Image, ap: dict, scans: list[dict]) -> None:
    """Draw the heatmap circles.

    Args:
        im (Image.Image): Image to draw on
        ap (dict): Access Point data
        scans (list[dict]): List of scan data

    Returns:
        None:
    """

    # Initiate a list for the distances of scans
    scan_dists = []

    # Loop over all scans
    for scan in scans:

        # Calculate the distance from the access point to the
        # scan location
        dist = int(
            sqrt(
                (ap["coords"][0] - scan["coords"][0])**2 +
                (ap["coords"][1] - scan["coords"][1])**2
            )
        )

        # Append the calculated distance to the scan distance list
        # And mark the negated (-(-dBm)) signal strengh with it
        scan_dists.append((dist, -scan["rssi"]))

    # Sort the distances from worst signal strengh (dBm) to best
    scan_dists.sort(key=lambda x: x[1], reverse=True)

    # Make pillow image drawing tool
    draw = ImageDraw.Draw(im)

    # Loop over the scan distances
    for dist in scan_dists:

        # Get the color based on the signal strengh
        color = getcolor(color_gradient, dist[1])

        # Draw the heat circle
        draw.ellipse(
            [
                (ap["coords"][0] - dist[0], ap["coords"][1] - dist[0]),
                (ap["coords"][0] + dist[0], ap["coords"][1] + dist[0])
            ],
            fill=color
        )

def draw_scanning_points(im: Image.Image, scans: list[dict]) -> None:
    """Draw the scanning points and write a label for them.

    Args:
        im (Image.Image): The image to draw on
        scans (list[dict]): List of scan data

    Returns:
        None:
    """

    # Make pillow image drawing tool
    draw = ImageDraw.Draw(im)

    # Loop over all scans
    for scan in scans:

        # Draw a royal purple dot for scan location
        draw.ellipse(
            [
                (scan["coords"][0] - 5, scan["coords"][1] - 5),
                (scan["coords"][0] + 5, scan["coords"][1] + 5)
            ],
            fill=(102, 51, 153)
        )

        # Write caption for dot
        draw.multiline_text(
            (scan["coords"][0] + 10, scan["coords"][1]),
            scan["label"],
            fill=(102, 51, 153),
            font=fnt,
            anchor="ls"
        )

def draw_accesspoint(im: Image.Image, ap: dict) -> None:
    """Draw the access point on the heatmap with a label.

    Args:
        im (Image.Image): Image to draw on
        ap (dict): Access Point data

    Returns:
        None:
    """

    # Make pillow image drawing tool
    draw = ImageDraw.Draw(im)

    # Draw dot for access point location
    draw.ellipse(
        [
            (ap["coords"][0] - 5, ap["coords"][1] - 5),
            (ap["coords"][0] + 5, ap["coords"][1] + 5)
        ],
        fill=(50, 50, 50)
    )

    # Write caption
    draw.multiline_text(
        (ap["coords"][0] + 10, ap["coords"][1]),
        ap["label"],
        fill=(50, 50, 50),
        font=fnt,
        anchor="ls"
    )

def draw_scale_guide(im: Image.Image) -> None:
    """Draw a scale gradient guide bar at the bottom.

    Args:
        im (Image.Image): Image to draw on

    Returns:
        None:
    """

    # Make pillow image drawing tool
    draw = ImageDraw.Draw(im)

    # Make white backdrop
    draw.rectangle(
        [(0, im.height-100), (im.width, im.height)],
        fill=(255, 255, 255)
    )
    
    # Loop over all pixels in width from 40 to width - 40
    for i in range(im.width - 40):

        # Calculate percentage
        percent = int((i/(im.width - 40)) * 100)
        
        # Draw a line which color based on gradient and percentage
        draw.line(
            [(i+20, im.height-80), (i+20, im.height-30)],
            fill=getcolor(color_gradient, percent),
            width=1
        )

    # Draw text to mark 0, -50 and -100 dBm
    draw.text(
        (40, im.height-25),
        "0 dBm",
        fill=(50, 50, 50),
        font=fnt,
        anchor="mt"
    )
    
    draw.text(
        (int(im.width/2), im.height-25),
        "-50 dBm",
        fill=(50, 50, 50),
        font=fnt,
        anchor="mt"
    )
    
    draw.text(
        (im.width-40, im.height-25),
        "-100 dBm",
        fill=(50, 50, 50),
        font=fnt,
        anchor="mt"
    )
