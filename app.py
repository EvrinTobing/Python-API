import datetime

from flask_socketio import SocketIO
from flask import Flask, json, Response, request
from werkzeug.utils import secure_filename
from os import path, getcwd
from db import Database
from face import Face

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdewq123'
socketio = SocketIO(app)
app.config['file_allowed'] = ['image/png', 'image/jpeg']
app.config['saves'] = path.join(getcwd(), 'saves')
app.db = Database()
app.face = Face(app)

date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
create = datetime.datetime.now()

filename = secure_filename(date + ".jpg")


def file_allowed():
    if 'file' not in request.files:
        print("Image required")
        return error_handle("image require")
    else:
        print("File Req", request.files)
        file = request.files['file']
        if file.mimetype not in app.config['file_allowed']:
            print("file extension not allowed")
            return error_handle("File not Allowed")


def saved(file):
    known_saves = path.join(app.config['saves'], 'known')
    file_path = path.join(known_saves, filename)
    file.save(file_path)


def save_new_face(file):

    users = app.db.insert('INSERT INTO users(created) VALUES(?)', [create])
    # filename = secure_filename(str(users) + ".jpg")
    date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
    filename = secure_filename(date + ".jpg")

    face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) VALUES(? ,?, ?)',
                            [users, filename, create])

    known_saves = path.join(app.config['saves'], 'known')
    file_path = path.join(known_saves, filename)
    file.save(file_path)

    app.face.store_new(file)


def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)


def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)


def get_user_by_id(user_id):
    user = {}

    results = app.db.select('SELECT users.id, users.created, faces.id, faces.user_id, faces.filename, '
                            'faces.created FROM users LEFT JOIN faces ON faces.user_id WHERE users.id = ?', [user_id])
    index = 0
    for row in results:
        print(row)
        face = {
            "id": row[2],
            "user_id": row[3],
            "filename": row[4],
            "created": row[5]
        }
        if index == 0:
            user = {
                "id": row[0],
                # "name": row[1],
                "created": row[1],
                "faces": []
            }
        if 3 in row:
            user["faces"].append(face)
        index = index + 1
    if 'id' in user:
        return user
    return None


@app. route('/', methods=['GET'])
def homepage():
    print("Welcome")

    output = json.dumps({"api": '1.0'})
    return Response(output, status=200, mimetype='application/json')


def get_recommendation_for_user(user_id):
    message = [
        {"id": 1, "name": "Americano", "description": "good coffe", "price": 90000},
        {"id": 2, "name": "Caramel", "description": "good coffe", "price": 91000}
    ]

    return json.dumps(message)


def get_favourites():
    message = [
        {"id": 3, "name": "Chocolate", "description": "good drik", "price": 90000},
        {"id": 4, "name": "Tea", "description": "good coffe", "price": 91000}
    ]

    return json.dumps(message)


@app.route('/api/recommendation', methods=['POST'])
def recommendation():
    file_allowed()
    file = request.files['file']
    user_id = app.face.recognize(file)
    user = get_user_by_id(user_id)

    if user:
        print("Existing customer")
        return get_recommendation_for_user(user_id)
    else:
        print("New customer")
        save_new_face(file)

        return get_favourites()


@app.route('/api/recognize', methods=['POST'])
def recognition():
    file = request.files['file']
    file_allowed()
    saved(file)
    usered = app.face.recognize(file)
    # encoding = app.face.encoding(file)
    if usered:

        user = get_user_by_id(usered)
        message = {"message": "Found {0}".format(user["id"]), "user": user}
        return success_handle(json.dumps(message))
    else:

        print("new filename is", filename)

        users = app.db.insert('INSERT INTO users(created) VALUES(?)', [create])

        app.face.store_new(file)

        if users:
            print("SAVED", users, create)
            face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) VALUES(? ,?, ?)',
                                            [users, filename, create])
            # encode_id = app.db.save('INSERT INTO face_encoding(user_id, encode) VALUES(?, ?)', [users, encoding])
            #
            # if encode_id:
            #     print("success")
            # return success_handle(json.dumps("success"))
            if face_id:
                print("face saved")
                face_data = {"id": face_id, "filename": filename, "created": create}
                return_output = json.dumps({"id": users, "face": [face_data]})
                return success_handle(return_output)
            else:
                print("error while save image")
                return error_handle("error save face")
        else:
            print("Failed")
            return error_handle("Error")


if __name__ == '__main__':
    socketio.run(app, debug=True, port=8080, host="0.0.0.0")