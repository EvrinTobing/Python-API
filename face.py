import face_recognition
from os import path
import numpy as np
from PIL import Image
import cv2

faces_to_compare = []
filenames_to_compare = []


class Face:
    def __init__(self, app):
        self.saves = app.config["saves"]
        self.db = app.db
        self.faces = []
        self.known_encoding_faces = []
        self.face_user_keys = {}
        self.load_all()

    def load_user_by_index_key(self, index_key=0):

        key_str = str(index_key)

        if key_str in self.face_user_keys:
            return self.face_user_keys[key_str]

        return None

    def load_known_file_by_name(self, name):
        saves_known = path.join(self.saves, 'known')
        return path.join(saves_known, name)

    def load_all(self):
        results = self.db.select('SELECT faces.id, faces.user_id, faces.filename, faces.created FROM faces')

        for row in results:
            print(row)
            user_id = row[1]
            filename = row[2]
            face = {
                "id": row[0],
                "user_id": user_id,
                "filename": filename,
                "created": row[3]
            }
            self.faces.append(face)
            face_image = face_recognition.load_image_file(self.load_known_file_by_name(filename))
            face_image_encoding = face_recognition.face_encodings(face_image)[0]

            index_key = len(self.known_encoding_faces)
            self.known_encoding_faces.append(face_image_encoding)
            index_key_string = str(index_key)
            self.face_user_keys['{0}'.format(index_key_string)] = user_id

    def recognize(self, file_stream):
        file_stream.seek(0)
        unknown_image = face_recognition.load_image_file(file_stream)
        unknown_encoding_images = face_recognition.face_encodings(unknown_image)[0]

        match_results = face_recognition.face_distance(self.known_encoding_faces, unknown_encoding_images)

        if len(match_results) == 0:
            return -1

        minIdx = np.argmin(match_results)

        print(minIdx)

        minValue = np.min(match_results)
        print(minValue)

        if minValue > 0.5:
            return -1

        return minIdx + 1

    def store_new(self, file_stream):
        file_stream.seek(0)
        unknown_image = face_recognition.load_image_file(file_stream)
        unknown_encoding_images = face_recognition.face_encodings(unknown_image)[0]
        self.known_encoding_faces.append(unknown_encoding_images)

    # def video(self, file_stream):
    #     file_stream.seek(0)
    #     file_stream = cv2.VideoCapture()
    #     length = int(file_stream.get(cv2.CAP_PROP_FRAME_COUNT))
    #     unknown_image = face_recognition.load_image_file(file_stream)
    #     unknown_encoding_images = face_recognition.face_encodings(unknown_image)[0]
    #
    #     face_locations = []
    #     face_encodings = []
    #     face_names = []
    #     frame_number = 0
    #
    #     while True:
    #         # Grab a single frame of video
    #         ret, frame = file_stream.read()
    #         frame_number += 1
    #
    #         # Quit when the input video file ends
    #         if not ret:
    #             break
    #
    #         # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    #         rgb_frame = frame[:, :, ::-1]
    #
    #         # Find all the faces and face encodings in the current frame of video
    #         face_locations = face_recognition.face_locations(rgb_frame)
    #         face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    #
    #         face_names = []
    #         for face_encoding in face_encodings:
    #             # See if the face is a match for the known face(s)
    #             match = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.50)
    #
    #             # If you had more than 2 faces, you could make this logic a lot prettier
    #             # but I kept it simple for the demo
    #             name = None
    #             if match[0]:
    #                 name = "Lin-Manuel Miranda"
    #             elif match[1]:
    #                 name = "Alex Lacamoire"
    #
    #             face_names.append(name)
    #
    #         # Label the results
    #         for (top, right, bottom, left), name in zip(face_locations, face_names):
    #             if not name:
    #                 continue
    #
    #             # Draw a box around the face
    #             cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
    #
    #             # Draw a label with a name below the face
    #             cv2.rectangle(frame, (left, bottom - 25), (right, bottom), (0, 0, 255), cv2.FILLED)
    #             font = cv2.FONT_HERSHEY_DUPLEX
    #             cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)
    #
    #         # Write the resulting image to the output video file
    #         print("Writing frame {} / {}".format(frame_number, length))
    #         output_movie.write(frame)


    def face_locate(self, file_stream):
        file_stream.seek(0)
        image = face_recognition.load_image_file(file_stream)
        face_locations = face_recognition.face_locations(image)
        print("I found {} face(s) in this photograph.".format(len(face_locations)))
        for face_location in face_locations:
            top, right, bottom, left = face_location
            print("A face is located at pixel location Top: {}, Left: {}, Bottom: {}, Right: {}".format(top, left, bottom, right))

            face_image = image[top:bottom, left:right]
            pil_image = Image.fromarray(face_image)
