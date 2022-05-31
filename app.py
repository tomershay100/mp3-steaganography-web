import os

from flask import Flask, request, flash, redirect, render_template, send_from_directory
from mp3stego import Steganography
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.abspath(os.getcwd() + '/uploads')
ALLOWED_EXTENSIONS = {'mp3'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

s = Steganography()

ERR_TEMPLATE_BEFORE_ERR = f'<!DOCTYPE html><html><body><p>Error: '
ERR_TEMPLATE_AFTER_ERR = '</p></body></html>'


def hide_msg(input_file_name, output_file_path, msg):
    s.hide_message(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path, msg)


def reveal_msg(input_file_name, output_file_path, _):
    s.reveal_massage(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path)


def clear_file(input_file_name, output_file_path, _):
    s.clear_file(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path)


def wav_to_mp3(input_file_name, output_file_path, bitrate):
    try:
        bitrate = int(bitrate)
    except:
        bitrate = 320
    bitrate = bitrate if bitrate < 1000 else bitrate // 1000
    s.encode_wav_to_mp3(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path, bitrate)


def mp3_to_wav(input_file_name, output_file_path, _):
    s.decode_mp3_to_wav(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path)


funcs = {'hide_msg': (hide_msg, 'output.mp3'), 'reveal_msg': (reveal_msg, 'reveal.txt'),
         'clear_file': (clear_file, 'cleared.mp3'), 'wav_to_mp3': (wav_to_mp3, 'output.mp3'),
         'mp3_to_wav': (mp3_to_wav, 'output.wav')}


def allowed_file(filename, func_name):
    return '.' in filename and \
           (filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS) or (
               filename.rsplit('.', 1)[1].lower() == "wav" if func_name == 'wav_to_mp3' else False)


@app.route('/stego/<func_name>', methods=['GET', 'POST'])
def upload_file(func_name):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename, func_name):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            func, out_path = funcs[func_name]
            output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], out_path)

            try:
                func(filename, output_file_path,
                     request.form.get('message') if func_name == 'hide_msg' else request.form.get('bitrate'))
            except BaseException as err:
                return ERR_TEMPLATE_BEFORE_ERR + str(err) + ERR_TEMPLATE_AFTER_ERR

            return render_template('download.html', file_path=out_path)
    return render_template(func_name + '.html')


@app.route('/')
def load_home_page():
    return render_template('index.html')


# @app.route('/uploads/<name>')
# def download_file(name):
#     return send_from_directory(app.config["UPLOAD_FOLDER"], name, as_attachment=True)


@app.route('/download/<file_path>')
def download(file_path):
    return send_from_directory(app.config["UPLOAD_FOLDER"], file_path, as_attachment=True)


app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)
app.add_url_rule(
    "/stego/<name>", endpoint="upload_file", build_only=True
)


@app.route('/style.css')
def style():
    return render_template('static/style.css')


if __name__ == '__main__':
    app.run(debug=True)
