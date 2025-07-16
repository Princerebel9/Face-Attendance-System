import dlib
import numpy as np
import cv2
import csv
import os
import time
import logging
import tkinter as tk
from tkinter import font as tkFont
from PIL import Image, ImageTk
import sqlite3

# from features_extraction_to_csv import return_features_mean_personX

# Use frontal face detector of Dlib
detector = dlib.get_frontal_face_detector()

#  Get face landmarks
predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')

#  Use Dlib resnet50 model to get 128D face descriptor
face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

conn = sqlite3.connect("a.db")
cursor = conn.cursor()

table_name = "student" 
create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (SNO INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT, branch TEXT,Roll_no INTEGER, number INTEGER)"
cursor.execute(create_table_sql)
conn.commit()
conn.close()

class Face_Register:
    def __init__(self):
        # Tkinter GUI
        self.win = tk.Tk()
        self.win.title("Face Register")

        # PLease modify window size here if needed
        self.win.geometry("1000x500")

        # GUI left part
        # 
        
        self.frame_left_camera = tk.Frame(self.win)
        self.label = tk.Label(self.win)
        self.label.pack(side=tk.LEFT)
        self.frame_left_camera.pack()
        # GUI right part
        self.frame_right_info = tk.Frame(self.win)
        #self.label_cnt_face_in_database = tk.Label(self.frame_right_info, text=str(self.existing_faces_cnt))
        #self.label_fps_info = tk.Label(self.frame_right_info, text="")
        self.input_name = tk.Entry(self.frame_right_info,text="" )
        self.input_branch = tk.Entry(self.frame_right_info,text="")
        self.input_roll = tk.Entry(self.frame_right_info)
        self.input_number = tk.Entry(self.frame_right_info)
        self.ss_cnt = 0 
        self.file = False
        self.label_warning = tk.Label(self.frame_right_info)
        self.label_face_cnt = tk.Label(self.frame_right_info, text="Faces in current frame: ")
        self.log_all = tk.Label(self.frame_right_info)

        self.font_title = tkFont.Font(family='Helvetica', size=20, weight='bold')
        self.font_step_title = tkFont.Font(family='Helvetica', size=15, weight='bold')
        self.font_warning = tkFont.Font(family='Helvetica', size=15, weight='bold')

        self.path_photos_from_camera = "data/data_faces_from_camera/"
        self.current_face_dir = ""
        self.font = cv2.FONT_ITALIC

        # Current frame and face ROI position
        self.current_frame = np.ndarray
        self.face_ROI_image = np.ndarray
        self.face_ROI_width_start = 0
        self.face_ROI_height_start = 0
        self.face_ROI_width = 0
        self.face_ROI_height = 0
        self.ww = 0
        self.hh = 0

        self.out_of_range_flag = False
        self.face_folder_created_flag = False

        # FPS
        self.frame_time = 0
        self.frame_start_time = 0
        self.fps = 0
        self.fps_show = 0
        self.start_time = time.time()

        self.cap = cv2.VideoCapture(0)  # Get video stream from camera

       

    def GUI_get_input_name(self):
        self.input_name_char = self.input_name.get()
        self.create_face_folder()
        # self.label_cnt_face_in_database['text'] = str(self.existing_faces_cnt)

    def GUI_info(self):
        tk.Label(self.frame_right_info,
                 text="Face register",
                 font=self.font_title).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=2, pady=20)

       
        tk.Label(self.frame_right_info,
                 text="Faces in current frame: ").grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        self.label_face_cnt.grid(row=3, column=2, columnspan=3, sticky=tk.W, padx=5, pady=2)

        self.label_warning.grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)

       
        tk.Label(self.frame_right_info,
                 font=self.font_step_title,
                 text="Input Student Details").grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=5, pady=20)

        tk.Label(self.frame_right_info, text="Name: ").grid(row=8, column=0, sticky=tk.W, padx=5, pady=0)
        self.input_name.grid(row=8, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Label(self.frame_right_info, text="Branch: ").grid(row=9, column=0, sticky=tk.W, padx=5, pady=0)
        self.input_branch.grid(row=9, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Label(self.frame_right_info, text="Roll No.: ").grid(row=10, column=0, sticky=tk.W, padx=5, pady=0)
        self.input_roll.grid(row=10, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Label(self.frame_right_info, text="Mob.No: ").grid(row=11, column=0, sticky=tk.W, padx=5, pady=0)
        self.input_number.grid(row=11, column=1, sticky=tk.W, padx=0, pady=2)
       
        tk.Button(self.frame_right_info,
                  text='Save data',
                  command=self.create_face_folder).grid(row=13, column=0, columnspan=3, sticky=tk.W)
        
        tk.Button(self.frame_right_info,
                  text='Save Img',
                  command=self.save_current_face).grid(row=13, column=1, columnspan=3, sticky=tk.W)

        # Show log in GUI
        self.log_all.grid(row=12, column=0, columnspan=20, sticky=tk.W, padx=5, pady=20)

        self.frame_right_info.pack()

    # Mkdir for saving photos and csv
    def pre_work_mkdir(self):
        # Create folders to save face images and csv
        if os.path.isdir(self.path_photos_from_camera):
            pass
        else:
            os.mkdir(self.path_photos_from_camera)

    
    def create_face_folder(self):
        name = self.input_name.get()
        branch = self.input_branch.get()
        roll = self.input_roll.get()
        conn = sqlite3.connect("a.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM student WHERE Roll_no = ? AND branch = ?", (roll, branch))
        existing_entry = cursor.fetchone()
        conn.close()
        if existing_entry:
            self.log_all["text"] = "Already there"
            self.file=False;
        else:
            self.current_face_dir = self.path_photos_from_camera + \
                                        name+"_"+ roll + "_" + \
                                        branch
            os.makedirs(self.current_face_dir)
            self.log_all["text"] = "\"" + self.current_face_dir + "/\" created!"
            logging.info("\n%-40s %s", "Create folders:", self.current_face_dir)

            name = self.input_name.get()
            branch = self.input_branch.get()
            no = int(self.input_number.get())
            roll = int(self.input_roll.get())
            conn = sqlite3.connect("a.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO student (name, branch,Roll_no ,number) VALUES (?, ?, ?,?)", (name,branch,roll,no))
            conn.commit()
            conn.close()




            self.ss_cnt = 0  #  Clear the cnt of screen shots
            # Face folder already created
            self.file=True;
    def save_current_face(self):
        if(self.file):
            if (self.input_branch.get() != "") and (self.input_name.get !=""):
                if self.current_frame_faces_cnt == 1:
                    if not self.out_of_range_flag:
                        self.ss_cnt += 1
                        #  Create blank image according to the size of face detected
                        self.face_ROI_image = np.zeros((int(self.face_ROI_height * 2), self.face_ROI_width * 2, 3),
                                                    np.uint8)
                        for ii in range(self.face_ROI_height * 2):
                            for jj in range(self.face_ROI_width * 2):
                                self.face_ROI_image[ii][jj] = self.current_frame[self.face_ROI_height_start - self.hh + ii][
                                    self.face_ROI_width_start - self.ww + jj]
                        self.log_all["text"] = "\"" + self.current_face_dir + "/img_face_" + str(
                            self.ss_cnt) + ".jpg\"" + " saved!"
                        self.face_ROI_image = cv2.cvtColor(self.face_ROI_image, cv2.COLOR_BGR2RGB)

                        cv2.imwrite(self.current_face_dir + "/img_face_" + str(self.ss_cnt) + ".jpg", self.face_ROI_image)
                        logging.info("%-40s %s/img_face_%s.jpg", "Save into：",
                                    str(self.current_face_dir), str(self.ss_cnt) + ".jpg")
                        
                        
                        
                        self.features()
                    else:
                        self.log_all["text"] = "Please do not out of range!"
                else:
                    self.log_all["text"] = "No face in current frame!"
            else:
                self.log_all["text"] = "Please Enter Complete Student details!"
        

    def get_frame(self):
        try:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                frame = cv2.resize(frame, (640,480))
                return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except:
            print("Error: No video input!!!")






    #just trying something from 275 to 312
    
    def features(self):
        with open("data/features_all.csv", "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            
                # Get the mean/average features of face/personX, it will be a list with a length of 128D
            
            features_mean_personX = self.return_features_mean_personX(self.current_face_dir)
            person_name = self.input_name.get()+"_"+self.input_roll.get()
            features_mean_personX = np.insert(features_mean_personX, 0, person_name, axis=0)
            # features_mean_personX will be 129D, person name + 128 features
            writer.writerow(features_mean_personX)
            logging.info('\n')
            logging.info("Save all the features of faces registered into: data/features_all.csv")
    
    def return_128d_features(self,path_img):
        img_rd = cv2.imread(path_img)
        faces = detector(img_rd, 1)

        logging.info("%-40s %-20s", " Image with faces detected:", path_img)

        # For photos of faces saved, we need to make sure that we can detect faces from the cropped images
        if len(faces) != 0:
            shape = predictor(img_rd, faces[0])
            face_descriptor = face_reco_model.compute_face_descriptor(img_rd, shape)
        else:
            face_descriptor = 0
            logging.warning("no face")
        return face_descriptor


    def return_features_mean_personX(self,path_face_personX):
        features_list_personX = []
        photos_list = os.listdir(path_face_personX)
        if photos_list:
            for i in range(len(photos_list)):
                #  return_128d_features()  128D  / Get 128D features for single image of personX
                logging.info("%-40s %-20s", " / Reading image:", path_face_personX + "/" + photos_list[i])
                name=path_face_personX + "/" + photos_list[i]
                features_128d =self.return_128d_features(name)
                #  Jump if no face detected from image
                if features_128d == 0:
                    i += 1
                else:
                    features_list_personX.append(features_128d)
        else:
            logging.warning(" Warning: No images in%s/", path_face_personX)

    
        if features_list_personX:
            features_mean_personX = np.array(features_list_personX, dtype=object).mean(axis=0)
        else:
            features_mean_personX = np.zeros(128, dtype=object, order='C')
        return features_mean_personX


    #  Main process of face detection and saving
    def process(self):
        ret, self.current_frame = self.get_frame()
        faces = detector(self.current_frame, 0)
        # Get frame
        if ret:
            # self.update_fps()
            self.label_face_cnt["text"] = str(len(faces))
            #  Face detected
            if len(faces) != 0:
                #   Show the ROI of faces
                for k, d in enumerate(faces):
                    self.face_ROI_width_start = d.left()
                    self.face_ROI_height_start = d.top()
                    #  Compute the size of rectangle box
                    self.face_ROI_height = (d.bottom() - d.top())
                    self.face_ROI_width = (d.right() - d.left())
                    self.hh = int(self.face_ROI_height / 2)
                    self.ww = int(self.face_ROI_width / 2)

                    # If the size of ROI > 480x640
                    if (d.right() + self.ww) > 640 or (d.bottom() + self.hh > 480) or (d.left() - self.ww < 0) or (
                            d.top() - self.hh < 0):
                        self.label_warning["text"] = "OUT OF RANGE"
                        self.label_warning['fg'] = 'red'
                        self.out_of_range_flag = True
                        color_rectangle = (255, 0, 0)
                    else:
                        self.out_of_range_flag = False
                        self.label_warning["text"] = ""
                        color_rectangle = (255, 255, 255)
                    self.current_frame = cv2.rectangle(self.current_frame,
                                                       tuple([d.left() - self.ww, d.top() - self.hh]),
                                                       tuple([d.right() + self.ww, d.bottom() + self.hh]),
                                                       color_rectangle, 2)
            self.current_frame_faces_cnt = len(faces)

            # Convert PIL.Image.Image to PIL.Image.PhotoImage
            img_Image = Image.fromarray(self.current_frame)
            img_PhotoImage = ImageTk.PhotoImage(image=img_Image)
            self.label.img_tk = img_PhotoImage
            self.label.configure(image=img_PhotoImage)

        # Refresh frame
        self.win.after(20, self.process)

    def run(self):
        if os.path.isdir(self.path_photos_from_camera):
            pass
        else:
            os.mkdir(self.path_photos_from_camera)
        # self.check_existing_faces_cnt()
        self.GUI_info()
        self.process()
        self.win.mainloop()


def main():
    logging.basicConfig(level=logging.INFO)
    Face_Register_con = Face_Register()
    Face_Register_con.run()


if __name__ == '__main__':
    main()
