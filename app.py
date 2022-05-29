import os

from flask import Flask, request, url_for, flash, redirect, render_template, send_file, send_from_directory
from mp3stego import Steganography
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.abspath(os.getcwd() + '/uploads')
ALLOWED_EXTENSIONS = {'mp3'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

s = Steganography()


def hide_msg(input_file_name, output_file_path, msg):
    s.hide_message(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path, msg)


def reveal_msg(input_file_name, output_file_path, _):
    s.reveal_massage(os.path.join(app.config['UPLOAD_FOLDER'], input_file_name), output_file_path)


funcs = {'hide_msg': (hide_msg, 'output.mp3'), 'reveal_msg': (reveal_msg, 'reveal.txt')}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/<name>', methods=['GET', 'POST'])
def upload_file(name):
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
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            func, out_path = funcs[name]
            output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], out_path)

            func(filename, output_file_path, request.form.get('message'))

            return redirect(url_for('download_file', name=out_path))
    return render_template(name + '.html')


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)


@app.route('/return-files/')
def return_files_tut():
    return send_file(os.path.join(app.config['UPLOADED_PATH'], '../output/output.mp3'),
                     attachment_filename='hidden.mp3')


if __name__ == '__main__':
    app.run(debug=True)
