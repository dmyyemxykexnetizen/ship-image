from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from PIL import Image, ImageDraw
import requests
import io
import os


TEMPLATE_URL = "https://ik.imagekit.io/uspr1zfl0/324%20sin%20t%C3%ADtulo_20260813205458.png"


DIGITS = {
    "0": [
        "111",
        "101",
        "101",
        "101",
        "111"
    ],
    "1": [
        "010",
        "110",
        "010",
        "010",
        "111"
    ],
    "2": [
        "111",
        "001",
        "111",
        "100",
        "111"
    ],
    "3": [
        "111",
        "001",
        "111",
        "001",
        "111"
    ],
    "4": [
        "101",
        "101",
        "111",
        "001",
        "001"
    ],
    "5": [
        "111",
        "100",
        "111",
        "001",
        "111"
    ],
    "6": [
        "111",
        "100",
        "111",
        "101",
        "111"
    ],
    "7": [
        "111",
        "001",
        "001",
        "001",
        "001"
    ],
    "8": [
        "111",
        "101",
        "111",
        "101",
        "111"
    ],
    "9": [
        "111",
        "101",
        "111",
        "001",
        "111"
    ],
    "%": [
        "10001",
        "00010",
        "00100",
        "01000",
        "10001"
    ]
}


def get_image(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return Image.open(
        io.BytesIO(response.content)
    ).convert("RGBA")


def make_circle(image, size):
    image = image.resize((size, size))

    mask = Image.new(
        "L",
        (size, size),
        0
    )

    mask_draw = ImageDraw.Draw(mask)

    mask_draw.ellipse(
        (0, 0, size - 1, size - 1),
        fill=255
    )

    result = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0)
    )

    result.paste(
        image,
        (0, 0),
        mask
    )

    return result


def draw_pixel_text_centered(
    image,
    text,
    center_x,
    center_y,
    scale=10
):

    draw = ImageDraw.Draw(image)

    total_width = 0

    for character in text:

        pattern = DIGITS.get(character)

        if pattern:

            total_width += (
                len(pattern[0]) + 1
            ) * scale

    total_width -= scale

    current_x = int(
        center_x - total_width / 2
    )

    text_height = 5 * scale

    start_y = int(
        center_y - text_height / 2
    )

    for character in text:

        pattern = DIGITS.get(character)

        if not pattern:
            current_x += scale
            continue

        for row in range(
            len(pattern)
        ):

            for column in range(
                len(pattern[row])
            ):

                if pattern[row][column] == "1":

                    draw.rectangle(
                        (
                            current_x + column * scale,
                            start_y + row * scale,
                            current_x + column * scale + scale - 1,
                            start_y + row * scale + scale - 1
                        ),
                        fill=(255, 255, 255, 255)
                    )

        current_x += (
            len(pattern[0]) + 1
        ) * scale


def upload_to_imagekit(image_data):

    private_key = os.environ.get(
        "IMAGEKIT_PRIVATE_KEY"
    )

    if not private_key:
        raise Exception(
            "IMAGEKIT_PRIVATE_KEY no está configurada"
        )

    response = requests.post(
        "https://upload.imagekit.io/api/v1/files/upload",
        auth=(private_key, ""),
        files={
            "file": (
                "ship.png",
                image_data,
                "image/png"
            )
        },
        data={
            "fileName": "ship.png",
            "folder": "/ship-generated"
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()["url"]


class handler(BaseHTTPRequestHandler):

    def do_GET(self):

        try:

            query = parse_qs(
                urlparse(self.path).query
            )

            left_url = query.get(
                "left",
                [None]
            )[0]

            right_url = query.get(
                "right",
                [None]
            )[0]

            rate = query.get(
                "rate",
                ["75"]
            )[0]

            if not left_url or not right_url:

                self.send_response(400)
                self.end_headers()

                self.wfile.write(
                    b"Missing left or right"
                )

                return

            template = get_image(
                TEMPLATE_URL
            )

            left = make_circle(
                get_image(left_url),
                150
            )

            right = make_circle(
                get_image(right_url),
                156
            )

            # Avatar izquierdo
            template.alpha_composite(
                left,
                (50, 25)
            )

            # Avatar derecho
            template.alpha_composite(
                right,
                (410, 22)
            )

            # Porcentaje centrado en la plantilla 610x200
            draw_pixel_text_centered(
                template,
                str(rate) + "%",
                center_x=305,
                center_y=100,
                scale=10
            )

            output = io.BytesIO()

            template.save(
                output,
                format="PNG"
            )

            image_data = output.getvalue()

            image_url = upload_to_imagekit(
                image_data
            )

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/plain"
            )

            self.send_header(
                "Content-Length",
                str(len(image_url))
            )

            self.end_headers()

            self.wfile.write(
                image_url.encode()
            )

        except Exception as e:

            error = str(e)

            self.send_response(500)
            self.end_headers()

            self.wfile.write(
                error.encode()
            )
