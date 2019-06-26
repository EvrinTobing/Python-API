import datetime
import time

from flask import Flask, json, Response, request
from werkzeug.utils import secure_filename
from os import path, getcwd
from db import Database
from face import Face

app = Flask(__name__)

app.config['file_allowed'] = ['image/png', 'image/jpeg']
app.config['saves'] = path.join(getcwd(), 'saves')
app.db = Database()
app.face = Face(app)

date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
create = datetime.datetime.now()

def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)


def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)


def get_user_by_id(user_id):
    user = {}

    results = app.db.select('SELECT users.id, users.name, users.created, faces.id, faces.user_id, faces.filename, '
                            'faces.created FROM users LEFT JOIN faces ON faces.user_id WHERE users.id = ?', [user_id])
    index = 0
    for row in results:
        print(row)
        face = {
            "id": row[3],
            "user_id": row[4],
            "filename": row[5],
            "created": row[6]
        }
        if index == 0:
            user = {
                "id": row[0],
                "name": row[1],
                "created": row[2],
                "faces": []
            }
        if 3 in row:
            user["faces"].append(face)
        index = index + 1
    if 'id' in user:
        return user
    return None


def delete_user_by_id(user_id):
    app.db.delete('DELETE FROM users WHERE users.id = ?', [user_id])
    app.db.delete('DELETE FROM faces WHERE faces.user_id = ?', [user_id])


@app.route('/', methods=['GET'])
def homepage():
    print("Welcome")

    output = json.dumps({"api": '1.0'})
    return Response(output, status=200, mimetype='application/json')


@app.route('/api/train', methods=['GET', 'POST'])
def train():
    # output = json.dumps({"success": True})

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

            filename = secure_filename(date + ".jpg")
            known_saves = path.join(app.config['saves'], 'known')
            file.save(path.join(known_saves, filename))

            print("new filename is", filename)

            created = create

            user_id = app.db.insert('INSERT INTO users(name, created) VALUES(?,?)', [name, created])

            if user_id:
                print("SAVED", name, user_id, created)

                face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) VALUES(? ,?, ?)',
                                        [user_id, filename, created])

                if face_id:

                    print("face saved")
                    face_data = {"id": face_id, "filename": filename, "created": created}
                    return_output = json.dumps({"id": user_id, "name": name, "face": [face_data]})
                    return success_handle(return_output)

                else:

                    print("error while save image")
                    return error_handle("error save face")
            else:
                print("FAILED")
                return error_handle("Error")

        print("Success")
    return success_handle(json.dumps({"success": True}))


@app.route('/api/users/<int:user_id>', methods=['GET', 'DELETE'])
def user_profile(user_id):
    if request.method == 'GET':
        user = get_user_by_id(user_id)

        if user:
            return success_handle(json.dumps(user), 200)
        else:
            return error_handle("User Not Found")
    if request.method == 'DELETE':
        delete_user_by_id(user_id)
        return success_handle(json.dumps({"deleted": True}))


@app.route('/api/recognize', methods=['POST'])
def recognition():
    if 'file' not in request.files:
        return error_handle("image require")
    else:
        file = request.files['file']
        if file.mimetype not in app.config['file_allowed']:
            return error_handle("File not Allowed")
        else:
            filename = secure_filename(date + ".jpg")
            unknown_saves = path.join(app.config['saves'], 'unknown')
            file_path = path.join(unknown_saves, filename)
            file.save(file_path)

            user_id = app.face.recognize(filename)
            if user_id:
                user = get_user_by_id(user_id)
                message = {"message": "Found {0}".format(user["name"]), "user": user}
                return success_handle(json.dumps(message))
            else:
                return error_handle("Sorry Can't Found any people match, try again")


if __name__ == '__main__':
    app.run(port=5050)
