from contextlib import redirect_stdout
from io import StringIO
import webview
from msms_autox_generator.gui import app
from msms_autox_generator import VERSION


def main():
    stream = StringIO()
    with redirect_stdout(stream):
        webview.settings['ALLOW_DOWNLOADS'] = True
        window = webview.create_window(f'fleX MS/MS AutoXecute Generator {VERSION}', app.server)
        webview.start()


if __name__ == '__main__':
    main()
