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

FUNC_NAME_TO_TAB_NUM = {
    'decode': 1,
    'encode': 2,
    'hide': 3,
    'reveal': 4,
    'clear': 5,
}


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


funcs = {'hide': (hide_msg, 'output.mp3'), 'reveal': (reveal_msg, 'reveal.txt'),
         'clear': (clear_file, 'cleared_file.mp3'), 'encode': (wav_to_mp3, 'output.mp3'),
         'decode': (mp3_to_wav, 'output.wav')}


def allowed_file(filename, func_name):
    return '.' in filename and \
           (filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS) or (
               filename.rsplit('.', 1)[1].lower() == "wav" if func_name == 'wav_to_mp3' else False)


def upload_file(func_name):
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(f'/#tab{FUNC_NAME_TO_TAB_NUM[func_name]}')  # todo add error message, or redirect to error page
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        # todo redirect to same page, with this error message
        return error_page(title='FILE UPLOAD ERROR',
                          error_description='You must upload file for using the website functions')
    if file and allowed_file(file.filename, func_name):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        func, out_path = funcs[func_name]
        output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], out_path)

        try:
            func(filename, output_file_path,
                 request.form.get('message') if func_name == 'hide' else request.form.get('bitrate'))
        except BaseException as err:
            # todo redirect to same page, with this error message
            return error_page(title='ERROR ON SERVER', error_description=str(err))

        return render_template('index.html', file_path=out_path, display_download=True)
    # try:
    #     return render_template(func_name + '.html', file_path="", display_download=False)
    # except TemplateNotFound as err:
    #     return not_found(f'Page {str(err)} not found on server')


@app.route('/', methods=['POST'])
def form_handler():
    func_name = request.form['submit']
    return upload_file(func_name)


@app.route('/', methods=['GET'])
def load_home_page():
    return render_template('index.html')


@app.route('/download/<file_path>')
def download(file_path):
    return send_from_directory(app.config["UPLOAD_FOLDER"], file_path, as_attachment=True)


app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)
app.add_url_rule(
    "/stego/<name>", endpoint="upload_file", build_only=True
)


@app.errorhandler(404)
def not_found(e):
    return error_page(title="ERROR 404 - Page Not Found", error_description=e)


# @app.route('/error?title=<title>&description=<error_description>')
def error_page(title, error_description):
    return render_template("error.html", title=title, error_description=error_description)


@app.route('/style.css')
def style():
    return render_template('../static/style.css')


@app.route('/error.css')
def error():
    return render_template('../static/error.css')


if __name__ == '__main__':
    app.run(debug=True)
