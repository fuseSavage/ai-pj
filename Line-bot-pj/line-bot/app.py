from flask import Flask, request, abort, send_from_directory
import errno
import os
import sys
import tempfile
from argparse import ArgumentParser
from werkzeug.middleware.proxy_fix import ProxyFix

import face_recognition

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    ImageMessage, ImageSendMessage)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)



line_bot_api = LineBotApi('0PBLaVVig/Y7d5+soF3X0QR3JJwjz1oJlHD36gDN+xNeFd4I58fSyx+76escMJg3+JewN8p5nrIMIGcH9wQ1qdc9C0zkhDmYbFJ28RjHbKWjYJXr3zjMmGs7IbUwx/e5vv0x+s50nLV/aqpjx0ujbwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('d982179e58eeed7f41a2e6cb485b58cb')

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')



def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=(ImageMessage))
def handle_content_message(event):
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    print('dist pate', dist_path)
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)


    import face_recognition

    image_mr_p = face_recognition.load_image_file('static/img/mr_p.jpg')
    mr_p_face_encoding = face_recognition.face_encodings(image_mr_p)[0]

    image_mr_k = face_recognition.load_image_file('static/img/mr_k.jpg')
    mr_k_face_encoding = face_recognition.face_encodings(image_mr_k)[0]

    image_mr_wichit = face_recognition.load_image_file('static/img/mr_wichit.jpg')
    mr_wichit_face_encoding = face_recognition.face_encodings(image_mr_wichit)[0]
    

    known_face_encodings = [
        mr_p_face_encoding,
        mr_k_face_encoding,
        mr_wichit_face_encoding
    ]

    known_face_names = [
        "อาจารย์ไพชยนต์ คงไชย",
        "อาจารย์เกรียงศักดิ์ ตรีประพิณ",
        "อาจารย์วิชิต สมบัติ"
         
    ]


    test_image = face_recognition.load_image_file(f'static/tmp/{dist_name}')

    face_locations = face_recognition.face_locations(test_image)
    face_encodings = face_recognition.face_encodings(test_image, face_locations)

    for(top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
        else:
            name = "Unknown person"    
        

    url = request.url_root + f'static/tmp/{dist_name}'
    line_bot_api.reply_message(
        event.reply_token, [
            ImageSendMessage(url, url),
            TextSendMessage(text=name)                
        ])



if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    # create tmp dir for download content
    make_static_tmp_dir()
    app.run(debug=options.debug, port=options.port)
