import datetime

from flask_socketio import SocketIO
from flask import Flask, json, Response, request, jsonify
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
    date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
    filename = secure_filename(date + ".jpg")
    known_saves = path.join(app.config['saves'], 'known')
    file_path = path.join(known_saves, filename)
    file.save(file_path)


def save_new_face(file):
    create = datetime.datetime.now()

    users = app.db.insert('INSERT INTO users(created) VALUES(?)', [create])
    now = str(users)
    filename = secure_filename(now + ".jpg")

    face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) VALUES(? ,?, ?)',
                            [users, filename, create])

    known_saves = path.join(app.config['saves'], 'known')
    file_path = path.join(known_saves, filename)
    file.seek(0)
    file.save(file_path)

    app.face.store_new(file)


def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)


def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)


def get_user_by_id(user_id):
    user_id = str(user_id)
    user = {}

    results = app.db.select('SELECT users.id, users.created, faces.id, faces.user_id, faces.filename, '
                            'faces.created FROM users INNER JOIN faces ON faces.user_id = users.id WHERE users.id = ?', [user_id])

    index = 0

    # print("find " + len(results))

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


# def get_recommendation_for_user(user_id):
#     message = [
#         {"id": 1, "name": "Americano", "description": "good coffe", "price": 90000, "images": "static/images/kopi.jpeg"},
#         {"id": 2, "name": "Caramel", "description": "good coffe", "price": 91000, "images": "static/images/kopi.jpeg"}
#     ]
#
#     return json.dumps(message)


@app. route('/fav', methods=['GET'])
def get_favourites():
    data = app.db.select('select catalogs.id, catalogs.nama, catalogs.description, catalogs.harga, catalogs.image from catalogs inner join orders on catalogs.id = orders.id_catalog GROUP BY nama ORDER BY (count(*)) desc LIMIT 3')
    results = []
    for d in data:
        results.append({"id": d[0], "name": d[1], "description": d[2], "price": d[3], "images": d[4]})
    resp = json.dumps(results)
    print(resp)
    return resp


@app. route('/rec', methods=['GET'])
def get_recommendation_for_user(user_id = None):
    user_id = request.args.get('user_id')

    data = app.db.select("select catalogs.id, catalogs.nama, catalogs.description, catalogs.harga, catalogs.image from catalogs inner join orders on catalogs.id = orders.id_catalog where orders.id_user = '"+ user_id +"'GROUP BY catalogs.nama ORDER BY (Count(*)) DESC LIMIT 1")
    results = []

    for d in data:
        results.append({"id": d[0], "name": d[1], "description": d[2], "price": d[3], "images": d[4]})
    resp = json.dumps(results)
    print(resp)
    return resp


@app.route('/api/products', methods=['POST'])
def insert_product():
    products = request.get_json()

    return insert_data(products)


def insert_data(products):
    data = app.db.insert('INSERT INTO catalogs(nama, description, harga, image) VALUES(?,?,?,?)', (products['name'], products['description'], products['price'], products['image']))
    return json.dumps("ok")


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


@app.route('/api/order',methods=['POST'])
def order():
    data = request.get_json()
    # product_id =
    return order_data(data)


def order_data(data):
    created = datetime.datetime.now()
    result = app.db.insert('INSERT INTO orders(id_catalog, id_user, jumlah, total_harga, '
                           'id_corp, id_tenant, id_device, created) VALUES (?,?,?,?,?,?,?,?)',
                           (data['catalog_id'], data['user_id'], data['quantity'], data['total_amount'], data['corp_id'], data['tenant_id'], data['device_id'], created))
    return success_handle(json.dumps("ok"))


if __name__ == '__main__':
    socketio.run(app, debug=True, port=8080, host="0.0.0.0")