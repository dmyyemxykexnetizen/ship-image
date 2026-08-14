from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from PIL import Image
import requests
import io

TEMPLATE_URL = "https://ik.imagekit.io/uspr1zfl0/324%20sin%20t%C3%ADtulo_20260813205458.png"


def get_image(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGBA")


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            query = parse_qs(urlparse(self.path).query)

            left_url = query.get("left", [None])[0]
            right_url = query.get("right", [None])[0]

            if not left_url or not right_url:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing left or right")
                return

            template = get_image(TEMPLATE_URL)
            left = get_image(left_url)
            right = get_image(right_url)

            left = left.resize((150, 150))
            right = right.resize((156, 156))

            template.alpha_composite(left, (50, 25))
            template.alpha_composite(right, (410, 22))

            output = io.BytesIO()
            template.save(output, "PNG")
            output.seek(0)

            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(output.read())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
