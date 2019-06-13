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


@app.route('/api/train', methods=['GET', 'POST'])
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

            user_id = app.db.insert('INSERT INTO users(name, created) VALUES(?,?)', [name, created])

            if user_id:
                print("SAVED", name, user_id, created)

                face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) VALUES(?, ?, ?)', [user_id, filename, created])

                if face_id:

                    print("face saved")
                    face_data = {"id": face_id, "filename":filename, "created":created}
                    return_output = json.dumps({"id": user_id, "name": name, "face":[face_data]})
                    return success_handle(return_output)

                else:

                    print("error while save image")
                    return error_handle("error save face")
            else:
                print("FAILED")
                return error_handle("Error")

        print("Success")
    return success_handle(output)

# @app.route('/api/users/<int:user)id>')
# def user_profile()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)