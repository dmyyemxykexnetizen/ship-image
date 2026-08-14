from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from PIL import Image, ImageDraw, ImageFont
import requests
import io
import os


TEMPLATE_URL = "https://ik.imagekit.io/uspr1zfl0/324%20sin%20t%C3%ADtulo_20260813205458.png"


def get_image(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGBA")


def make_circle(image, size):
    image = image.resize((size, size))

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)

    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(image, (0, 0), mask)

    return result


def get_font(size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
    ]

    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def upload_to_imagekit(image_data):
    private_key = os.environ.get("IMAGEKIT_PRIVATE_KEY")

    if not private_key:
        raise Exception("IMAGEKIT_PRIVATE_KEY no está configurada")

    response = requests.post(
        "https://upload.imagekit.io/api/v1/files/upload",
        auth=(private_key, ""),
        files={
            "file": ("ship.png", image_data, "image/png")
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
            query = parse_qs(urlparse(self.path).query)

            left_url = query.get("left", [None])[0]
            right_url = query.get("right", [None])[0]
            rate = int(query.get("rate", ["75"])[0])

            if not left_url or not right_url:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing left or right")
                return

            template = get_image(TEMPLATE_URL)

            left = make_circle(get_image(left_url), 150)
            right = make_circle(get_image(right_url), 156)

            template.alpha_composite(left, (50, 25))
            template.alpha_composite(right, (410, 22))

            # --------------------------------
            # PRUEBA DEL PORCENTAJE
            # --------------------------------

            draw = ImageDraw.Draw(template)

            # Rectángulo de prueba
            draw.rectangle(
                (250, 150, 410, 310),
                fill=(255, 0, 0, 255)
            )

            font = get_font(70)

            draw.text(
                (330, 230),
                str(rate) + "%",
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=3,
                stroke_fill=(0, 0, 0, 255),
                anchor="mm"
            )

            # --------------------------------

            output = io.BytesIO()
            template.save(output, format="PNG")

            image_data = output.getvalue()

            image_url = upload_to_imagekit(image_data)

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(image_url)))
            self.end_headers()

            self.wfile.write(image_url.encode())

        except Exception as e:

            error = str(e)

            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()

            self.wfile.write(error.encode())
