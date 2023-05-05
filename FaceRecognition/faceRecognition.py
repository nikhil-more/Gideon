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

    def load_encodings(self, encodings_location: Path = DEFAULT_ENCODINGS_PATH):
        with encodings_location.open(mode="rb") as f:
            self.face_encodings = pickle.load(f)

    def show_video_feed(self, frame, isFailed:False):
        if(isFailed):
            pass
        cv2.imshow('Face Recognition', frame)

    def run_recognition(self, model: str = "hog", encodings_location: Path = DEFAULT_ENCODINGS_PATH):    
        video_capture = cv2.VideoCapture(0)

        if(not video_capture.isOpened()):
            sys.exit('Video source was not found')

        face_match_found = True
        countDown = 10

        while True:
            if(countDown <= 0):
                print("Face Recognized")
                break

            ret, frame = video_capture.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                if(self.process_current_frame):
                    # small_frame = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
                    rgb_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)   
                    #Find all the faces in current frame
                    self.face_locations = face_recognition.face_locations(rgb_image)
                    if self.face_locations == []:
                        self.show_video_feed(frame, True)
                        continue
                    self.face_encodings = face_recognition.face_encodings(rgb_image, self.face_locations)
                    if self.face_encodings == []:
                        self.show_video_feed(frame, True)
                        continue
                    face_encoding = self.face_encodings[0]
                    self.face_names = []
                    # for face_encoding in self.face_encodings:
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    name = 'Unknown'
                    confidence = 0

                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)

                    if(matches[best_match_index]):
                        name = self.known_face_names[best_match_index]
                        confidence = face_confidence(face_distances[best_match_index])
                        confidence = float(confidence[-2]) / 100

                    if(face_match_found):
                        print(countDown)
                    if(confidence > 95):
                        face_match_found = True
                        
                    self.face_names.append(name[:-4])

                self.process_current_frame = not self.process_current_frame

                # Display Animations
                for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                    top *= 1
                    right *= 1
                    bottom *= 1
                    left *= 1

                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), -1)
                    cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_COMPLEX, 0.8, (255, 255, 255), 1)

                cv2.imshow('Face Recognition', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()