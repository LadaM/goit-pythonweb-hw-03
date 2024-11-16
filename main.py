import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from datetime import datetime
import json
import time
from jinja2 import Environment, FileSystemLoader

DATA_PATH = 'storage/data.json'
PORT = 3000
env = Environment(loader=FileSystemLoader('.'))

class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        elif pr_url.path == '/read':
            self.send_message_list()
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            form_data = urllib.parse.parse_qs(post_data)

            username = form_data.get('username', [''])[0]
            message = form_data.get('message', [''])[0]
            timestamp = str(int(time.time()))

            data_file = pathlib.Path(DATA_PATH)
            data_file.parent.mkdir(parents=True, exist_ok=True)
            if data_file.exists():
                with data_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}

            new_entry = {
                timestamp: {
                    "username": username,
                    "message": message
                }
            }

            data.update(new_entry)

            with data_file.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)

            self.send_response(302)
            self.send_header('Location', '/message')
            self.end_headers()
        else:
            self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_message_list(self):
        data_file = pathlib.Path('storage/data.json')
        if data_file.exists():
            with data_file.open('r', encoding='utf-8') as f:
                messages = json.load(f)
        else:
            messages = {}

        formatted_messages = {
            datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S'): content
            for ts, content in messages.items()
        }

        template = env.get_template('read.html')
        rendered_page = template.render(messages=formatted_messages)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(rendered_page.encode('utf-8'))

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', PORT)
    http = server_class(server_address, handler_class)
    try:
        print(f"Server running at http://localhost:{PORT}")
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    run()
