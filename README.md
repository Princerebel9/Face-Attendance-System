# Face-Attendance-System
An automated attendance system using facial recognition built with Dlib, OpenCV, Tkinter, and SQLite. It detects and recognizes student faces in real time and stores attendance records efficiently.

🚀 Features
👤 Face registration with student details (Name, Roll No., Branch, Mobile No.)

🎥 Real-time face detection & recognition using webcam

🧠 128D facial feature extraction with Dlib's ResNet model

🗓️ Automatic daily attendance table creation

🗂️ SQLite-based data storage for both registration and attendance

🔒 Duplicate entries avoided using timestamp + roll constraints

⚙️ How It Works
Face Registration (get_faces_from_camera_tkinter.py)

Students enter their info via GUI

Their face is captured and stored as images

Features extracted and saved to features_all.csv

Details stored in a.db

Attendance Marking (attendance_taker.py)

Uses webcam to detect faces

Compares with stored features

If matched, attendance is marked in attendance.db under a table named attendanceYYYY_MM_DD


🧰 Technologies Used
Tool/Library	Purpose
Python	Main language
OpenCV	Face detection & video processing
Dlib	Face recognition (128D feature extraction)
Tkinter	GUI for registration
SQLite	Database for storing data
Pandas	Data manipulation (CSV)
PIL (Pillow)	Image processing


