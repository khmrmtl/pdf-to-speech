from flask import Flask, render_template, redirect, flash, request, send_from_directory
from PyPDF2 import PdfFileReader
from werkzeug.utils import secure_filename
import os
from gtts import gTTS
from apscheduler.schedulers.background import BackgroundScheduler


UPLOAD_FOLDER = 'uploads/'
MP3_FOLDER = 'generated-mp3s/'

app = Flask(__name__)
app.config['SECRET_KEY'] = "Z0dRqQija7MlfAb2DBM8fg"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MP3_FOLDER'] = MP3_FOLDER
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ALLOWED_EXTENSIONS = ["txt", "pdf"]

# remove all files every 6 hours
def clear_directory():
    directory1 = 'generated-mp3s'
    directory2 = 'uploads'
    for f in os.listdir(directory1):
        os.remove(os.path.join(directory1, f))
    for f in os.listdir(directory2):
        os.remove(os.path.join(directory2, f))

    print("Scheduler is alive!")


sched = BackgroundScheduler(daemon=True)
sched.add_job(clear_directory, 'interval', minutes=360)
sched.start()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=["GET", "POST"])
def home():
    waiting = False
    filename = " "
    if request.method == 'POST':
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
            waiting = True
            filename = secure_filename(file.filename)
            print(type(filename))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("Processing ... ")
        else:
            flash("Not a valid file type")
    return render_template("index.html", waiting=waiting, filename=filename)


@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(app.config['MP3_FOLDER'], filename, as_attachment=True)
    except:
        return "Sorry that file no longer exist"


@app.route("/converting/<filename>")
def convert_to_mp3(filename):
    try:
        pdf_file_obj = open(f"uploads/{filename}", 'rb')
        files = []

        # creating a pdf reader object
        pdf_reader = PdfFileReader(pdf_file_obj)

        # printing number of pages in pdf file
        print(pdf_reader.numPages)
        for index in range(pdf_reader.numPages):
            # creating a page object
            page_obj = pdf_reader.getPage(0)

            # extracting text from page
            tts = gTTS(page_obj.extractText())
            mp3file = f'{filename.split(".")[0]}_Page{index + 1}.mp3'
            tts.save(os.path.join(app.config['MP3_FOLDER'], mp3file))
            files.append(mp3file)
        # closing the pdf file object
        pdf_file_obj.close()
        return render_template("download-page.html", files=files)
    except Exception as e:
        print(e)
        return "It seems like we cannot create an mp3 version from the given file<hr> Please try another file"



if __name__ == "__main__":
    app.run(debug=True)
