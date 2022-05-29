import os

from flask import Flask, request, url_for, flash, redirect, render_template, send_from_directory
from mp3stego import Steganography
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.abspath(os.getcwd() + '/uploads')
ALLOWED_EXTENSIONS = {'mp3'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

s = Steganography()

Bitrates = [_ for _ in range(64, 480, 32)]



def hide_msg(input_file_name, output_file_path, msg):
    s.hide_message(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path, msg)


def reveal_msg(input_file_name, output_file_path, _):
    s.reveal_massage(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path)


def clear_file(input_file_name, output_file_path, _):
    s.clear_file(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path)


def wav_to_mp3(input_file_name, output_file_path, bitrate):
    bitrate = int(bitrate)//1000
    if bitrate not in Bitrates:
        raise Exception('Bitrate not valid')
    if bitrate in Bitrates_K:
        bitrate //= 1000

    s.encode_wav_to_mp3(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path, bitrate)


funcs = {'hide_msg': (hide_msg, 'output.mp3'), 'reveal_msg': (reveal_msg, 'reveal.txt'),
         'clear_file': (clear_file, 'cleared_file.mp3'), 'wav_to_mp3': (wav_to_mp3, 'output.mp3')}


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

            func(filename, output_file_path,
                 request.form.get('message') if func_name == 'hide_msg' else request.form.get('bitrate'))

            return redirect(url_for('download_file', name=out_path))
    return render_template(func_name + '.html')


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


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
