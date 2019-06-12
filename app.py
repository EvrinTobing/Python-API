import time

from flask import Flask, json, Response, request
from werkzeug.utils import secure_filename
from os import path, getcwd
from db import Database


app = Flask(__name__)

app.config['file_allowed'] = ['image/png','image/jpeg']
app.config['saves'] = path.join(getcwd(), 'saves')
app.db = Database()


def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)


def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)


@app.route('/', methods=['GET'])
def homepage():
    print("Welcome")

    output = json.dumps({"api": '1.0'})
    return Response(output, status=200, mimetype='application/json')


@app.route('/api/train', methods=['POST'])
def train():

    output = json.dumps({"success": True})

    if 'file' not in request.files:

        print("Image required")
        return error_handle("Face image is required")

    else:

        print("File Req", request.files)
        file = request.files['file']

        if file.mimetype not in app.config['file_allowed']:

            print("file extension not allowed")
            return error_handle("only allow *.png and *.jpeg")

        else:

            name = request.form['name']

            print("information image: ", name)

            print("file allowed and save in", app.config['saves'])

            filename = secure_filename(file.filename)

            file.save(path.join(app.config['saves'], filename))

            print("new filename is", filename)

            created = int(time.time())

            users_id = app.db.insert('INSERT INTO users(name, created) values(?,?)', [name, created])

        print("Success")
    return success_handle(output)


if __name__ == '__main__':
    app.run()