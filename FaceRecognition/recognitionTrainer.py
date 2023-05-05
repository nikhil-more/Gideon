import face_recognition
import cv2
import os, sys
import numpy as np
import math
from pathlib import Path
import pickle

DEFAULT_ENCODINGS_PATH = Path("encodings.pkl")

def face_confidence(face_distance, face_match_threshold=0.6):
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if(face_distance > face_match_threshold):
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + (1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2)) * 100
        return str(round(value * 100, 2)) + '%'

class FaceRecognition:
    face_locations = []
    face_encodings = []
    face_names = []
    known_face_encodings = []
    known_face_names = []
    process_current_frame = True

    def __init__(self):
        self.encode_faces()
        

    def encode_faces(self, model: str = "hog", encodings_location: Path = DEFAULT_ENCODINGS_PATH):
        for name in os.listdir('UserPics'):
            face_image = face_recognition.load_image_file(f'UserPics/{name}')
            face_locations = face_recognition.face_locations(face_image, model=model)
            
            face_encoding = face_recognition.face_encodings(face_image, face_locations)[0]
            self.known_face_names.append(name)   
            self.known_face_encodings.append(face_encoding)

        print(self.known_face_names)
        name_encodings = {"names": self.known_face_names, "encodings": self.known_face_encodings}
        with encodings_location.open(mode="wb") as f:
            pickle.dump(name_encodings, f)

if __name__ == "__main__":
    fr = FaceRecognition()
