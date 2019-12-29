from flask import Flask, request, redirect, url_for, flash, render_template, session
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import os
from wand.image import Image as wi
from flask import send_file
import pandas as pd
from flask_mysqldb import MySQL

#tesseract path start
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/Cellar/tesseract/4.0.0_1/bin/tesseract'
#tessaract path end

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'santoshocr'

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'ocr'

mysql = MySQL(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @app.route("/")
# def hello():
#     return render_template('index.html')

@app.route("/")
def login():
    if 'username' in session:
        return render_template("index.html")
    return render_template('login.html')

@app.route("/register")
def register():
    return render_template('register.html')


@app.route("/registeration", methods = ['GET', 'POST'])
def registeration():
    email = request.form['email']
    password = request.form['password']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users(email, password) VALUES (%s, %s)", (email, password))
    mysql.connection.commit()
    cur.close()
    return render_template('login.html')


@app.route("/logged", methods = ['GET', 'POST'])
def checklogin():
    if 'username' in session:
        return render_template("index.html")
    else:
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(1) FROM users where (email, password) = (%s, %s)", (email, password))
        # df = pd.read_csv("users.csv")
        # d2 = df[(df["email"] == email) & (df["password"]  == password )]
        if not cur.fetchone()[0]:
            return render_template("login_with_failure.html")
        else:
            session['username'] = email
            return render_template("index.html")
   


@app.route("/upload", methods = ['GET', 'POST'])
def filesaver():
    if request.method == 'POST':
        if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.split('.')[1]
            filenamme = os.path.join(app.config['UPLOAD_FOLDER'], filename.split('.')[0])
            if ext == 'pdf':
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                uploaded_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pages = wi(filename=uploaded_file, resolution=300) 
                image_counter = 0
                fulltext = ''
                for page in pages.sequence:
                    pdf_image = wi(image=page)
                    filen = "page_"+str(image_counter)+".jpg"
                    path_to_save = os.path.join(app.config['UPLOAD_FOLDER'], filen)
                    pdf_image.format = 'jpeg'
                    pdf_image.save(filename=path_to_save) 
                    image_counter = image_counter + 1
                text_file_name = filenamme+".txt"
                file1 = open(text_file_name,"w") 
                for i in range(0, image_counter): 
                    filenames = "uploads/page_"+str(i)+".jpg"
                    text = str(((pytesseract.image_to_string(Image.open(filenames)))))
                    text = text.replace('-\n', '')
                    fulltext += text 
                file1.write(fulltext) 
                file1.close()       
                return send_file(text_file_name, as_attachment=True)
            else:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                text = pytesseract.image_to_string(Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))).encode('utf-8')
                filenamme = os.path.join(app.config['UPLOAD_FOLDER'], filename.split('.')[0])
                text_file_name = filenamme+".txt"
                file1 = open(text_file_name,"w") 
                file1.write(text) 
                file1.close()
                return send_file(text_file_name, as_attachment=True)


@app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
    return send_from_directory(directory=uploads, filename=filename)

@app.route("/logout", methods = ['GET', 'POST'])
def logout():
    session.pop('username', None)
    return render_template('login.html')

if __name__ == '__main__':
   app.run(debug = True)