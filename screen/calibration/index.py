from PySide6.QtWidgets import (QWidget, QStackedWidget, QLabel, QVBoxLayout, QToolButton,
                             QLineEdit, QPushButton, QHBoxLayout, QGridLayout, QMessageBox, QSlider)
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QIcon, QColor, QShortcut
from PySide6.QtCore import Qt, QThread, Signal, QSize, QTimer, QMutex
from screen.calibration.step.step1 import GuideScreen
import socket
from pynput.mouse import Listener as MouseListener
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import QInputDialog
# import threading
from urx import Robot
import numpy as np
import time
import math
from PySide6.QtGui import QKeySequence
import pyrealsense2 as rs
import sys
import os
from screen.video_manager import VideoManager
import datetime
from toast import Toast
import pandas as pd
import numpy.linalg as lin
from PIL import Image
from PIL import ImageDraw
import time
import subprocess
# import URBasic
import cv2
import matplotlib.pyplot as plt
class CalibrationMain(QWidget):
    def __init__(self, parent=None, stacked_widget=None, main_window=None):
        print("Initializing CalibrationMain...")
        super().__init__(parent)

        self.ip_address = None
        self.check_connection_thread = None
        self.connection_circle = None  # 새로운 변수 추가
        self.connection_label = None  # 새로운 변수 추가
        self.is_connected = False  # 로봇이 연결되었는지
        self.camera_connected = False
        self.folder_created = False
        self.buttons = []  # Button list
        self.camera_buttons = []
        self.robot = None

        # self.setup_emergency_stop()
        # Set up layouts
        main_layout = QHBoxLayout()
        main_left_layout = QVBoxLayout()
        main_right_layout = QVBoxLayout()
        main_right_layout.setAlignment(Qt.AlignCenter)
        # Set up left panel
        self.setup_left_panel(main_left_layout)
        self.update_camera_button_states()
        # Set up right panel
        self.setup_right_panel(main_right_layout)

        # Add left and right panels to main layout
        main_layout.addLayout(main_left_layout)
        main_layout.addLayout(main_right_layout)
        self.setLayout(main_layout)

        self.pi=math.pi
        self.VELOCITY = 5
        self.ACCELERATION = self.VELOCITY * 2
        self.move_val = self.VELOCITY / 100
        self.rot_val = self.VELOCITY / 100

        self.video_manager = VideoManager()
        self.video_thread = self.video_manager.get_video_thread()

        # Connect the changePixmap signal to the setImage method
        self.video_thread.changePixmap.connect(self.setImage)

        # Start the video thread
        self.video_thread.start()

        self.update_button_states()

        self.camera_update_button_states()
        self.calv_img()
    def calv_img(self):
        # 켈리브레이션 이미지 저장
        desired_aruco_dictionary = "DICT_7X7_50"
        # The different ArUco dictionaries built into the OpenCV library.
        ARUCO_DICT = {
            "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
            "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
            "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
            "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
            "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
            "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
            "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
            "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
            "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
            "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
            "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
            "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
            "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
            "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
            "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
            "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
            "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL
        }

        if ARUCO_DICT.get(desired_aruco_dictionary, None) is None:
            print("[INFO] ArUCo tag of '{}' is not supported".format(args["type"]))
            sys.exit(0)
        #opencv 4.6 이하에서 동작, 4.7 이상 X

        # Load the ArUco dictionary
        print("[INFO] detecting '{}' markers...".format(desired_aruco_dictionary))
        self.this_aruco_dictionary = cv2.aruco.Dictionary_get(ARUCO_DICT[desired_aruco_dictionary])
        self.this_aruco_parameters = cv2.aruco.DetectorParameters_create()

    def setup_left_panel(self, layout):
        layout.addSpacing(50)

        # This is where the image will go
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)  # Align the image to the center
        self.show_placeholder_image()
        layout.addWidget(self.image_label)

        button_layout = self.setup_button_layout()
        layout.addLayout(button_layout)
        layout.setSpacing(0)

    def setup_right_panel(self, layout):
        layout.addSpacing(0)
        ip_text = QHBoxLayout()
        ip_text.setContentsMargins(0, 0, 0, 0)  # No margins
        ip_label = QLabel("IP 연결")
        ip_label.setFixedHeight(30)
        ip_text.addWidget(ip_label)

        ip_input_line = QHBoxLayout()
        ip_input_line.setContentsMargins(0, 0, 0, 0)  # No margins
        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("IP 주소 입력")
        self.connect_button = QPushButton()
        self.connect_button.setStyleSheet('background-color: #B50039; border: none; color: white; font-size:15px')
        self.connect_button.setFixedSize(QSize(80, 30))  # Set fixed size for the button
        self.connect_button.setText('연결')
        self.connect_button.clicked.connect(self.on_connect_button_clicked)
        ip_input_line.addWidget(self.ip_input)
        ip_input_line.addWidget(self.connect_button)

        layout.addLayout(ip_text)
        layout.addLayout(ip_input_line)

        # Create a widget that will contain the layout
        right_sub_widget = QWidget()

        # Set the widget's background color
        right_sub_widget.setStyleSheet("background-color: #393939;")
        right_sub_widget.setFixedHeight(550)

        # Create the layout
        right_sub_layout = QVBoxLayout()

        right_sub_layout.addWidget(self.connection_layout())
        # Then add the text with a black background
        self.black_background_text = QLabel()
        self.black_background_text.setStyleSheet("background-color: black; color: white;")
        self.black_background_text.setFixedHeight(170)
        right_sub_layout.addWidget(self.black_background_text)

        right_sub_layout.addLayout(self.grid_header())

        # Finally add the grid layout
        grid_layout = self.setup_grid_layout()
        right_sub_layout.addLayout(grid_layout)
        # Assign the layout to the widget

        right_sub_layout.addLayout(self.speed_header())
        slider = QSlider(Qt.Horizontal)  # Create a horizontal slider
        slider.setMinimum(1)  # Set the minimum value to 1
        slider.setMaximum(5)  # Set the maximum value to 100
        slider.setValue(5)  # Set the initial value to 50 (in the middle)
        slider.valueChanged.connect(self.handle_slider_value_changed)
        right_sub_layout.addWidget(slider)  # Add the slider to the layout
        right_sub_widget.setLayout(right_sub_layout)
        # Add the widget to the main layout
        layout.addWidget(right_sub_widget)

    def handle_slider_value_changed(self, value):
        self.VELOCITY = value
        self.ACCELERATION = self.VELOCITY * 2
        self.move_val = self.VELOCITY / 100
        self.rot_val = self.VELOCITY / 100
        print(self.VELOCITY)


    def connection_layout(self):
        # Create a horizontal layout
        connection_line = QHBoxLayout()
        connection_line.setSpacing(3)
        # Create a label
        self.connection_label = QLabel("Connection Fail")  # 수정된 부분
        self.connection_label.setStyleSheet('color: white;')
        self.connection_label.setFixedHeight(25)
        self.connection_label.setAlignment(Qt.AlignTop)
        # Create a circle widget
        self.connection_circle = CircleWidget("red")  # 수정된 부분
        self.connection_circle.setFixedHeight(10)  # adjust the size as needed
        self.connection_circle.setFixedWidth(10)  # adjust the size as needed

        # Add circle widget and label to the layout
        connection_line.addWidget(self.connection_circle)
        connection_line.addWidget(self.connection_label)
        connection_line.addStretch(1)  # push everything to the left

        # Create a new widget to hold the layout
        connection_widget = QWidget()
        connection_widget.setFixedHeight(30)
        connection_widget.setLayout(connection_line)

        return connection_widget

    def set_connection_state(self, connected):  # 새로운 메서드 추가
        self.is_connected = connected
        if connected:
            self.connection_circle.setColor("green")
            self.connection_label.setText("Connection OK")
        else:
            self.connection_circle.setColor("red")
            self.connection_label.setText("Connection Fail")
        self.update_button_states()

    def setup_emergency_stop(self):
        self.shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.shortcut.activated.connect(self.emergency_stop)

    def emergency_stop(self):
        try:
            self.robot.secmon.close()  # Emergency stop the robot
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop the robot: {str(e)}")

    def on_connect_button_clicked(self):
        ...
        self.start_check_connection_thread()

    def start_check_connection_thread(self):
        self.check_connection_thread = QThread(target=self.check_connection)
        self.check_connection_thread.start()

    def check_connection(self):
        while True:
            if not self.robot.is_program_running():
                QMessageBox.critical(self, "Error", "Lost connection to the robot.")
                break

            time.sleep(1)  # Check connection every second
    def setup_grid_layout(self):

        grid_layout = QGridLayout()

        # Specify which positions to have buttons and their associated image paths

        button_positions = {
            (0, 0): { "image": ":image/Orientation/button-down.svg", "start_function": self.start_move_plus_Z, "stop_function": self.stop_move_plus_Z, "icon_size": QSize(80, 80) },
            (0, 2): { "image": ":image/Orientation/button-up.svg", "start_function": self.start_move_minus_Z, "stop_function": self.stop_move_minus_Z, "icon_size": QSize(80, 80)},

            (0, 4): { "image": ":image/position/turn-left.svg", "start_function": self.start_rotate_plus_Z, "stop_function": self.stop_rotate_plus_Z, "icon_size": QSize(80, 80)},
            (0, 6): { "image": ":image/position/turn-right.svg", "start_function": self.start_rotate_minus_Z, "stop_function": self.stop_rotate_minus_Z, "icon_size": QSize(80, 80)},

            (1, 1): { "image": ":image/position/arrow-up.svg", "start_function": self.start_move_minus_X, "stop_function": self.stop_move_minus_X, "icon_size": QSize(80, 40) },
            (1, 5): { "image": ":image/Orientation/arrow-up.svg", "start_function": self.start_rotate_plus_Y, "stop_function": self.stop_rotate_plus_Y, "icon_size": QSize(80, 40)},

            (2, 0): { "image": ":image/position/arrow-left.svg", "start_function": self.start_move_minus_Y, "stop_function": self.stop_move_minus_Y, "icon_size": QSize(40, 96), "alignment": Qt.AlignRight},
            (2, 2): { "image": ":image/position/arrow-right.svg", "start_function": self.start_move_plus_Y, "stop_function": self.stop_move_plus_Y, "icon_size": QSize(40, 96) },

            (2, 4): { "image": ":image/Orientation/arrow-left.svg", "start_function": self.start_rotate_plus_X, "stop_function": self.stop_rotate_plus_X, "icon_size": QSize(40, 96), "alignment": Qt.AlignRight},
            (2, 6): { "image": ":image/Orientation/arrow-right.svg", "start_function": self.start_rotate_minus_X, "stop_function": self.stop_rotate_minus_X, "icon_size": QSize(40, 96)},

            (3, 1): { "image": ":image/position/arrow-down.svg", "start_function": self.start_move_plus_X, "stop_function": self.stop_move_plus_X, "icon_size": QSize(80, 40)},
            (3, 3): { "image": ":image/position/button-Free.svg", "start_function": self.start_move_plus_X, "stop_function": self.stop_move_plus_X, "icon_size": QSize(80, 40)},
            (3, 5): { "image": ":image/Orientation/arrow-down.svg", "start_function": self.start_rotate_minus_Y, "stop_function": self.stop_rotate_minus_Y, "icon_size": QSize(80, 40)},
        }


        # Create a 4x6 grid of buttons
        for i in range(4):
            for j in range(7):
                if (i, j) in button_positions:
                    button_info = button_positions[(i, j)]
                    button = self.create_button(button_info, button_info['icon_size'])
                    if 'start_function' in button_info and 'stop_function' in button_info:
                        button.pressed.connect(button_info['start_function'])
                        button.released.connect(button_info['stop_function'])
                    grid_layout.addWidget(button, i, j)
                    if "alignment" in button_info:
                        grid_layout.setAlignment(button, button_info["alignment"])

        # grid_layout.setColumnStretch(0, 3)

        grid_layout.setSpacing(0)
        grid_layout.setHorizontalSpacing(0)
        grid_layout.setVerticalSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        return grid_layout


    def grid_header(self):
        # Create a QVBoxLayout for the TCP Position icon and text
        tcp_position_layout = QHBoxLayout()
        tcp_position_layout.setAlignment(Qt.AlignLeft)  # Align the image to the center
        # Create a label for the icon
        tcp_position_icon_label = QLabel()
        pixmap = QPixmap(":image/position/TCP-Position.svg")
        tcp_position_icon_label.setPixmap(pixmap)

        # Create a label for the text
        tcp_position_text_label = QLabel("TCP Position")
        tcp_position_text_label.setStyleSheet("color:white")
        # Add the icon and text labels to the layout
        tcp_position_layout.addWidget(tcp_position_icon_label)
        tcp_position_layout.addWidget(tcp_position_text_label)

        # Do the same for the TCP Orientation icon and text
        tcp_orientation_layout = QHBoxLayout()
        tcp_orientation_layout.setAlignment(Qt.AlignLeft)  # Align the image to the center
        tcp_orientation_icon_label = QLabel()
        pixmap = QPixmap(":image/Orientation/TCP-Orientation.svg")
        tcp_orientation_icon_label.setPixmap(pixmap)

        tcp_orientation_text_label = QLabel("TCP Orientation")
        tcp_orientation_text_label.setStyleSheet("color:white")
        tcp_orientation_layout.addWidget(tcp_orientation_icon_label)
        tcp_orientation_layout.addWidget(tcp_orientation_text_label)

        # Create a QHBoxLayout to hold the two QVBoxLayouts
        grid_header_layout = QHBoxLayout()
        # Add the QVBoxLayouts to the QHBoxLayout
        grid_header_layout.addLayout(tcp_position_layout)
        grid_header_layout.addLayout(tcp_orientation_layout)

        return grid_header_layout


    def speed_header(self):
        # Create a QVBoxLayout for the TCP Position icon and text
        tcp_position_layout = QHBoxLayout()
        tcp_position_layout.setAlignment(Qt.AlignLeft)  # Align the image to the center
        # Create a label for the icon
        tcp_position_icon_label = QLabel()
        pixmap = QPixmap(":image/Speed.svg")
        tcp_position_icon_label.setPixmap(pixmap)

        # Create a label for the text
        tcp_position_text_label = QLabel("Speed")
        tcp_position_text_label.setStyleSheet("color:white")
        # Add the icon and text labels to the layout
        tcp_position_layout.addWidget(tcp_position_icon_label)
        tcp_position_layout.addWidget(tcp_position_text_label)

        return tcp_position_layout

    def setup_button_layout(self):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)  # Set the space between the buttons
        button_layout.setAlignment(Qt.AlignCenter)  # Align the image to the center
        button_layout.setContentsMargins(0, 0, 0, 0)

        button_names = ["카메라 연결", "경로설정", "이미지 저장", "켈리브레이션",  "데이터 보기"]
        self.enabled_icons = [":image/camera.svg", ":image/folder-add.svg", ":image/gallery.svg", ":image/video.svg", ":image/video-octagon.svg"]
        self.disabled_icons = [":image/camera2.svg", ":image/folder-add2.svg", ":image/gallery2.svg", ":image/video2.svg", ":image/video-octagon2.svg"]

        # Create the buttons and add them to the layout
        for i, name in enumerate(button_names):
            button = self.create_tool_button(name, self.enabled_icons[i])

            self.camera_buttons.append(button)
            button_layout.addWidget(button)
        self.camera_buttons[0].clicked.connect(self.connect_camera)  # '카메라 연결' 버튼을 connect_camera 함수에 연결
        self.camera_buttons[1].clicked.connect(self.create_folder)  # '카메라 연결' 버튼을 connect_camera 함수에 연결
        self.camera_buttons[2].clicked.connect(self.save_image)  # '카메라 연결' 버튼을 connect_camera 함수에 연결
        self.camera_buttons[3].clicked.connect(self.calibration_connect)  # '카메라 연결' 버튼을 connect_camera 함수에 연결
        self.camera_buttons[4].clicked.connect(self.folder_open)  # '카메라 연결' 버튼을 connect_camera 함수에 연결
        return button_layout
    def folder_open(self):
        try:  # 윈도우
            os.startfile(self.folder_path)
        except AttributeError:  # 리눅스
            subprocess.call(['xdg-open', self.folder_path])





    def calibration_connect(self):
        if hasattr(self, 'folder_path'):
            first_directory = True
            for root, dirs, files in os.walk(self.folder_path):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    data_list = sorted(os.listdir(dir_path))

                    # 키워드를 기반으로 파일 경로 찾기
                    total_cam_path = [os.path.join(dir_path, file) for file in os.listdir(dir_path) if 'total_cam' in file][0]
                    R_inv_path = [os.path.join(dir_path, file) for file in os.listdir(dir_path) if 'R_inv' in file][0]
                    robot_position_path = [os.path.join(dir_path, file) for file in os.listdir(dir_path) if 'robot_position' in file][0]
                    print("Total Cam Path:", total_cam_path)
                    print("R_inv Path:", R_inv_path)
                    print("Robot Position Path:", robot_position_path)
                    total_cam = np.load(total_cam_path)
                    R_inv = np.load(R_inv_path)
                    robot_position = np.load(robot_position_path)
                    cal_position_x = np.array(robot_position[0]*1000)
                    cal_position_y = np.array(robot_position[1]*1000)
                    cal_position_z = np.array(robot_position[2]*1000)
                    # print("cal_position_x :" , cal_position_x)
                    # print("cal_position_y :" , cal_position_y)
                    # print("cal_position_z :" , cal_position_z)

                    bottom_left = total_cam[:,:,3]
                #     cam_data_mat_ = np.hstack((top_right,top_left,bottom_right,bottom_left))

                #     cam_data_mat_ = top_right
                    cam_data_mat_ = bottom_left

                    #bottom_left
                    robot_data_x = np.array([135 ,65,-5,-75,135 ,65,-5,-75,135 ,65,-5,-75,135 ,65,-5,-75])
                    robot_data_y = np.array([-175,-175,-175,-175,-245,-245,-245,-245,-315,-315,-315,-315,-385,-385,-385,-385])


                    robot_data_z = np.ones(len(robot_data_x)) * 10

                    robot_data_mat_ = np.vstack([robot_data_x,robot_data_y,robot_data_z, np.ones(len(robot_data_x))])
                    print("robot_data_mat_ :", robot_data_mat_)

                    robot_data_mat_ = np.matmul(R_inv, robot_data_mat_)
                    print("robot_data_mat_ :", robot_data_mat_)
                    robot_data_mat_[0,:] = robot_data_mat_[0,:] + cal_position_x
                    robot_data_mat_[1,:] = robot_data_mat_[1,:] + cal_position_y
                    robot_data_mat_[2,:] = robot_data_mat_[2,:] + cal_position_z


                    if first_directory:
                        cam_data_mat = cam_data_mat_
                        robot_data_mat = robot_data_mat_
                        first_directory = False
                    else:
                        cam_data_mat = np.hstack((cam_data_mat, cam_data_mat_))
                        robot_data_mat = np.hstack((robot_data_mat, robot_data_mat_))

            self.print_np(cam_data_mat)
            self.print_np(robot_data_mat)


            # l515 1280 x 720
            cam_intrin_mat = np.array([[self.video_thread.rs_color_fx, 0, self.video_thread.rs_color_ppx, 0],[0,self.video_thread.rs_color_fy,self.video_thread.rs_color_ppy,0],[0,0,1,0],[0,0,0,1]])
            self.print_np(cam_intrin_mat)

            # l515 1920 x 1080
            # cam_intrin_mat = np.array([[1359.57080078125, 0, 976.2681274414062, 0],[0,1359.7188720703125,545.0499267578125,0],[0,0,1,0],[0,0,0,1]])
            # print_np(cam_intrin_mat)

            inv_cam_intrin_mat = lin.inv(cam_intrin_mat)
            # print_np(inv_cam_intrin_mat)
            inv_robot_data_mat = lin.pinv(robot_data_mat)
            print("Shape of cal_mat_tmp:", cam_data_mat.shape)
            print("Shape of inv_robot_data_mat:", inv_robot_data_mat.shape)

            cal_mat_tmp = np.matmul(inv_cam_intrin_mat,cam_data_mat)
            cal_mat = np.matmul(cal_mat_tmp,inv_robot_data_mat) #Extrinsic
            # print_np(cal_mat)

            inv_cal_mat = lin.inv(cal_mat) #최종 아웃풋
            # print_np(inv_cal_mat)

            cam_data_mat_calculated_tmp = np.matmul(inv_cam_intrin_mat,cam_data_mat)
            cam_data_mat_calculated = np.matmul(inv_cal_mat,cam_data_mat_calculated_tmp)
            # print_np(robot_data_mat)
            # print_np(cam_data_mat_calculated)

            dif_cam_robot = (robot_data_mat - cam_data_mat_calculated)**2
            # dif_cam_robot = (robot_data_mat[:1,:] - cam_data_mat_calculated[:1,:])**2
            # dif_cam_robot = (robot_data_mat[1:2,:] - cam_data_mat_calculated[1:2,:])**2
            # dif_cam_robot = (robot_data_mat[2:3,:] - cam_data_mat_calculated[2:3,:])**2
            dif_cam_robot_distance = np.sqrt(np.sum(dif_cam_robot,axis=0))
            # dif_cam_robot_distance = np.sqrt(dif_cam_robot)
            print("Min difference: {} mm".format(np.min(dif_cam_robot_distance)))
            print("Max difference: {} mm".format(np.max(dif_cam_robot_distance)))
            print("Mean difference: {} mm".format(np.mean(dif_cam_robot_distance)))
            # 가운데 정렬
            self.black_background_text.setAlignment(Qt.AlignCenter)
            # 텍스트
            text = "글자 여기"
            self.black_background_text.setText(np.max(dif_cam_robot_distance))
        else:
            QMessageBox.information(self, "No folder selected", "Please create a folder first.")
            # 나머지 로직은 위에서 주어진 코드와 동일합니다.

        # 결과를 반환하거나 저장합니다.





    def create_folder(self):
        if self.camera_connected:  # Only allow to create a folder when the camera is connected
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly
            options |= QFileDialog.DontUseNativeDialog
            folder_path = QFileDialog.getExistingDirectory(self, 'Select Directory',options=options)
            if folder_path:
                self.folder_path = folder_path
                self.folder_created = True
                self.camera_update_button_states()  # Update button states

    def camera_update_button_states(self):
        self.camera_buttons[0].setEnabled(True)  # '카메라 연결' button
        self.camera_buttons[1].setEnabled(self.camera_connected)  # '생성' button
        self.camera_buttons[2].setEnabled(self.camera_connected and self.folder_created)  # '이미지 저장' button
        self.camera_buttons[3].setEnabled(self.camera_connected and self.folder_created)  # '켈리브레이션' button

        # Update button colors
        for i, button in enumerate(self.camera_buttons):
            if button.isEnabled():
                button.setEnabled(True)
                button.setIcon(QIcon(self.enabled_icons[i]))  # Change this line
                button.setStyleSheet('background-color: #2F2F2F; color: white; font-size:15px; padding: 19px 16px;border-top: 1.5px solid #2F2F2F;border-right: 1.5px solid #2F2F2F;border-bottom: 1.5px solid #2F2F2F;')  # Set the enabled button color
            else:
                button.setEnabled(False)
                button.setIcon(QIcon(self.disabled_icons[i]))  # Change this line
                button.setStyleSheet('background-color: #2F2F2F; color: #525252; font-size:15px; padding: 19px 16px;border-top: 1.5px solid #2F2F2F;border-right: 1.5px solid #2F2F2F;border-bottom: 1.5px solid #2F2F2F;')  # Set the disabled button color

    def save_image(self):
        if hasattr(self, 'folder_path'):
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            calibration_image, total_cam, R_inv, robot_position = self.get_camera_data()

            # Make a directory for this timestamp
            timestamp_dir = os.path.join(self.folder_path, timestamp)
            os.makedirs(timestamp_dir)

            # Save calibration image
            image_path = os.path.join(timestamp_dir, f"calibration_image_{timestamp}.png")
            calibration_image.save(image_path)

            # Save data to the directory
            np.save(os.path.join(timestamp_dir, f"total_cam_{timestamp}.npy"), total_cam)
            np.save(os.path.join(timestamp_dir, f"R_inv_{timestamp}.npy"), R_inv)
            np.save(os.path.join(timestamp_dir, f"robot_position_{timestamp}.npy"), robot_position)

            self.toast = Toast(self, "이미지 촬영이 완료되었습니다.") # Make toast a class attribute
            self.toast.show()
        else:
            QMessageBox.information(self, "No folder selected", "Please create a folder first.")

    def create_button(self, button_info, icon_size):

        button = QToolButton()

        image = QImage(button_info["image"])
        button.setStyleSheet("border:none")
        button.setCursor(Qt.PointingHandCursor)
        aspect_ratio = image.width() / image.height()

        # We assume that the button size is set here, for example to 200x120.
        # button.setFixedSize(QSize(80, 80))

        button.setIcon(QIcon(QPixmap.fromImage(image)))
        button.setIconSize(icon_size)  # Set the icon size

        button.pressed.connect(button_info['start_function'])
        button.released.connect(button_info['stop_function'])
        self.buttons.append(button)  # Add button to list

        # button.clicked.connect(button_info["function"])  # Connect the button's clicked signal to the associated function

        return button
    def update_button_states(self):
        for button in self.buttons:
            button.setEnabled(self.is_connected)

    def set_connected(self, connected):
        self.is_connected = connected
        self.update_button_states()

    def create_tool_button(self, name, icon_path):
        button = QToolButton()
        button.setText(name)
        button.setStyleSheet('background-color: #2F2F2F; color: white; font-size:15px; padding: 19px 16px;border-top: 1.5px solid #2F2F2F;border-right: 1.5px solid #2F2F2F;border-bottom: 1.5px solid #2F2F2F;')  # Set the background to black and text to white
        button.setCursor(Qt.PointingHandCursor)
        button.setIcon(QIcon(icon_path))  # Set the icon
        button.setIconSize(QSize(24, 24))  # Set the icon size
        button.setFixedSize(QSize(128, 100))  # Set the button size
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        return button


    def show_placeholder_image(self):
        # Load your placeholder image
        placeholder = QImage(":image/null.png")
        # Display the placeholder image
        self.setImage(placeholder)

    def setImage(self, image):
        self.current_image = image
        self.image_label.setPixmap(QPixmap.fromImage(image))
        self.image_label.setContentsMargins(0, 0, 0, 0)

    def connect_camera(self):
        # If the camera is already connected, disconnect it
        if self.video_thread.is_connected:
            self.video_thread.disconnect_camera()
            self.camera_buttons[0].setText("카메라 연결")
            self.camera_connected = False
            self.show_placeholder_image()  # Add this line
        else:
            # Display a dialog with the available cameras
            cameras = rs.context().devices
            camera_names = [camera.get_info(rs.camera_info.name) for camera in cameras]

            if camera_names:
                camera_name, ok = QInputDialog.getItem(self, "Connect to camera", "Choose a camera:", camera_names, 0, False)

                if ok and camera_name:
                    connected = self.video_thread.connect_camera(camera_name)
                    if connected:
                        self.camera_buttons[0].setText("연결 해제")  # Change the button text
                        self.camera_connected = True
            else:
                QMessageBox.information(self, "No cameras found", "No cameras were found. Please connect a camera and try again.")
                self.show_placeholder_image()  # Add this line

        self.update_camera_button_states()  # Update button states

    def update_camera_button_states(self):
        self.camera_buttons[0].setEnabled(True)  # '카메라 연결' button
        # self.camera_buttons[1].setEnabled(True)  # '카메라 연결' button
        # self.camera_buttons[2].setEnabled(True)  # '카메라 연결' button
        self.camera_buttons[1].setEnabled(self.camera_connected)  # '생성' button
        self.camera_buttons[2].setEnabled(self.camera_connected and self.folder_created)  # '이미지 저장' button
        self.camera_buttons[3].setEnabled(True)  # '카메라 연결' button
        # self.buttons[3].setEnabled(self.camera_connected and self.folder_created)  # '영상 저장' button

        # Update button colors
        for i, button in enumerate(self.camera_buttons):
            if button.isEnabled():
                button.setEnabled(True)
                button.setIcon(QIcon(self.enabled_icons[i]))  # Change this line
                button.setStyleSheet('background-color: #2F2F2F; color: white; font-size:15px; padding: 19px 16px;border-top: 1.5px solid #2F2F2F;border-right: 1.5px solid #2F2F2F;border-bottom: 1.5px solid #2F2F2F;')  # Set the enabled button color
            else:
                button.setEnabled(False)
                button.setIcon(QIcon(self.disabled_icons[i]))  # Change this line
                button.setStyleSheet('background-color: #2F2F2F; color: #525252; font-size:15px; padding: 19px 16px;border-top: 1.5px solid #2F2F2F;border-right: 1.5px solid #2F2F2F;border-bottom: 1.5px solid #2F2F2F;')  # Set the disabled button color

    # 로봇 연결했는지 안했는지
    def on_connect_button_clicked(self):
        if not self.is_connected:  # 연결 안된 상태라면 연결 시도
            ip_address = self.ip_input.text()  # Get the entered IP address

            try:
                # Try to connect to the robot at the specified IP address
                print("VELOCITY : ", self.VELOCITY)
                print("ACCELERATION : ", self.ACCELERATION)
                print("move_val : ", self.move_val)
                print("rot_val : ", self.rot_val)

                self.robot = Robot(ip_address)
                robot_pose = self.robot.getl()
                print(robot_pose)

                QMessageBox.information(self, "Success", f"Connected to the robot at {ip_address}")
                self.set_connection_state(True)
                self.is_connected = True  # 성공적으로 연결된 경우
                self.ip_address = ip_address
                self.connect_button.setText('해제')  # Button text 변경
                # self.connect_button.disconnect()  # disconnect all slots
                self.connect_button.clicked.connect(self.on_disconnect_button_clicked)  # Button action 변경
                # print("moving to initial pose")
                # self.robot.movej((90*(self.pi/180), -90*(self.pi/180), -90*(self.pi/180), -90*(self.pi/180), 90*(self.pi/180), 0*(self.pi/180)), acc=self.ACCELERATION, vel=self.VELOCITY, wait=False)
                # print("Waiting 1s for end move")
                # time.sleep(1)
            except Exception as e:
                # If the connection failed, show an error message
                QMessageBox.critical(self, "Error", f"Failed to connect to the robot at {ip_address}: {str(e)}")
                self.set_connection_state(False)


    def on_disconnect_button_clicked(self):
        # 로봇 연결 해제 로직 작성
        # (코드 작성)
        self.robot.close()
        # listener.stop()
        self.is_connected = False  # 연결 해제 후
        self.connect_button.setText('연결')  # Button text 변경
        # self.connect_button.disconnect()
        self.set_connection_state(False)
        self.connect_button.clicked.connect(self.on_connect_button_clicked)  # Button action 변경

    # 켈리브레이션 이미지 저장 코드
    def get_camera_data(self):
        # Create a config and configure the pipeline to stream
        # different resolutions of color and depth streams
        config = self.video_thread.config
        t = time.time()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.video_thread.pipeline)
        pipeline_profile = config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))

        found_rgb = False
        for s in device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                found_rgb = True
                break
        if not found_rgb:
            print("The demo requires Depth camera with Color sensor")
            exit(0)

        config.enable_stream(rs.stream.depth, self.video_thread.rs_depth_width, self.video_thread.rs_depth_height, rs.format.z16, 30)

        if device_product_line == 'L500':
            config.enable_stream(rs.stream.color, self.video_thread.rs_color_width, self.video_thread.rs_color_height, rs.format.rgb8, 30)
        else:
            config.enable_stream(rs.stream.color, self.video_thread.rs_color_width, self.video_thread.rs_color_height, rs.format.rgb8, 30)

        # Start streaming
        # profile = self.pipeline.start(config)

        # Getting the depth sensor's depth scale (see rs-align example for explanation)
        depth_sensor = self.video_thread.profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        print("Depth Scale is: " , depth_scale)

        # We will be removing the background of objects more than
        # clipping_distance_in_meters meters away
        clipping_distance_in_meters = 1 #1 meter
        clipping_distance = clipping_distance_in_meters / depth_scale

        # Create an align object
        # rs.align allows us to perform alignment of depth frames to others frames
        # The "align_to" is the stream type to which we plan to align depth frames.
        align_to = rs.stream.color
        align = rs.align(align_to)

        elapsed_time_1 = time.time() - t
        print(elapsed_time_1)

        # Get frameset of color and depth
        frames = self.video_thread.pipeline.wait_for_frames()
        # frames.get_depth_frame() is a 640x360 depth image

        # Align the depth frame to color frame
        aligned_frames = align.process(frames)
        print(aligned_frames)
        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame() # aligned_depth_frame is a 640x480 depth image
        print(aligned_depth_frame)
        color_frame = aligned_frames.get_color_frame()
        print(color_frame)

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            return None, None, None

        depth_image = np.asanyarray(aligned_depth_frame.get_data()) * depth_scale
        color_image = np.asanyarray(color_frame.get_data())

        #Detect ArUco markers in the video frame
        (corners_, ids_, rejected) = cv2.aruco.detectMarkers(
            color_image, self.this_aruco_dictionary, parameters=self.this_aruco_parameters)

        ids_ = ids_.flatten()

        df = pd.DataFrame([ids_, corners_]).transpose()
        df.columns = ['ids', 'corners']
        df.sort_values(by ='ids', inplace=True)

        ids = np.array(df['ids'])
        corners = np.array(df['corners'])

        if len(corners) > 0:

            # Flatten the ArUco IDs list
            ids = ids.flatten()
            top_right_cam =[]
            top_left_cam =[]
            bottom_right_cam = []
            bottom_left_cam = []

            # Loop over the detected ArUco corners
            for (marker_corner, marker_id) in zip(corners, ids):

                # Extract the marker corners
                corners = marker_corner.reshape((4, 2))
                (top_left, top_right, bottom_right, bottom_left) = corners

                # Convert the (x,y) coordinate pairs to integers
                top_right = (int(top_right[0]), int(top_right[1]))
                bottom_right = (int(bottom_right[0]), int(bottom_right[1]))
                bottom_left = (int(bottom_left[0]), int(bottom_left[1]))
                top_left = (int(top_left[0]), int(top_left[1]))
                print("marker_id:",marker_id)
                print("top_right:",top_right)
    #             print("top_left:",top_left)
    #             print("bottom_right:",bottom_right)


                # Convert (x,y,z) cam data in list
                top_right_cam_tmp = [top_right[0]*depth_image[top_right[1],top_right[0]],top_right[1]*depth_image[top_right[1],top_right[0]],depth_image[top_right[1],top_right[0]]]
                top_left_cam_tmp = [top_left[0]*depth_image[top_left[1],top_left[0]],top_left[1]*depth_image[top_left[1],top_left[0]],depth_image[top_left[1],top_left[0]]]
                bottom_right_cam_tmp = [bottom_right[0]*depth_image[bottom_right[1],bottom_right[0]],bottom_right[1]*depth_image[bottom_right[1],bottom_right[0]],depth_image[bottom_right[1],bottom_right[0]]]
                bottom_left_cam_tmp = [bottom_left[0]*depth_image[bottom_left[1],bottom_left[0]] ,bottom_left[1]*depth_image[bottom_left[1],bottom_left[0]] ,depth_image[bottom_left[1],bottom_left[0]]]

                top_right_cam.append(top_right_cam_tmp)
                top_left_cam.append(top_left_cam_tmp)
                bottom_right_cam.append(bottom_right_cam_tmp)
                bottom_left_cam.append(bottom_left_cam_tmp)

                # Draw the bounding box of the ArUco detection
                cv2.line(color_image, top_left, top_right, (0, 255, 0), 2)
                cv2.line(color_image, top_right, bottom_right, (0, 255, 0), 2)
                cv2.line(color_image, bottom_right, bottom_left, (0, 255, 0), 2)
                cv2.line(color_image, bottom_left, top_left, (0, 255, 0), 2)

                # Calculate and draw the center of the ArUco marker
                center_x = int((top_left[0] + bottom_right[0]) / 2.0)
                center_y = int((top_left[1] + bottom_right[1]) / 2.0)
                cv2.circle(color_image, (center_x, center_y), 4, (0, 0, 255), -1)

                # Draw the ArUco marker ID on the video frame
                # The ID is always located at the top_left of the ArUco marker
                cv2.putText(color_image, str(marker_id),
                (top_left[0], top_left[1] - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 255, 0), 2)

        # total_cam data size 4x16x4 , 1st 4 : x,y,z,1 // 2nd 16 : # of marker // 3rd 4 : corner point top_r, top_l, bot_r, bot_l
            top_right_cam = np.array(top_right_cam)
            top_left_cam = np.array(top_left_cam)
            bottom_right_cam = np.array(bottom_right_cam)
            bottom_left_cam = np.array(bottom_left_cam)
            total_cam__ = np.dstack((top_right_cam, top_left_cam,bottom_right_cam, bottom_left_cam))
            total_cam_ = np.transpose(total_cam__, (1,0,2))
            total_cam = np.vstack((total_cam_, np.ones((1,np.size(total_cam_,1),np.size(total_cam_,2)))))
            self.print_np(total_cam[:,:,0])

        # robot_pose = rob.getl()
        robot_pose = self.robot.getl()

        print(robot_pose)
        robot_position = robot_pose[:3]
        R_inv = self.cal_R_inv(robot_pose)

        images = color_image

        calibration_image = Image.fromarray(images)




        # Assuming the ids, corners and depth_image are the required data
        return calibration_image, total_cam, R_inv, robot_position

    def cal_R_inv(self,robot_pose):
        position = robot_pose[:3]
        rxryrz = robot_pose[3:]
        theta = np.sqrt((rxryrz[0] ** 2) + (rxryrz[1] ** 2) + (rxryrz[2] ** 2))
        if rxryrz[0] < 0:
            rxryrz[0] = -rxryrz[0]
            rxryrz[1] = -rxryrz[1]
            rxryrz[2] = -rxryrz[2]
        else:
            pass

        ux = rxryrz[0] / theta
        uy = rxryrz[1] / theta
        uz = rxryrz[2] / theta

        c = math.cos(theta)
        s = math.sin(theta)
        C = 1 - c
        R = np.array([[ux*ux*C+c, ux*uy*C - uz*s, ux*uz*C +uy*s,0],
                [uy*ux*C +uz*s, uy*uy*C + c, uy*uz*C - ux*s,0],
                [uz*ux*C -uy*s, uz*uy*C + ux*s, uz*uz*C + c,0],
                    [0,0,0,1]])

        R_inv = lin.inv(R)

        return R_inv
    def print_np(self,x):
        print("Type is %s" %(type(x)))
        print("Shape is %s" % (x.shape,))
        print("Values are: \n%s" % (x))

    # 로봇 좌표 움직임 컨트롤러

    def start_move_minus_X(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.move_minus_X)
        self.timer.start(100)  # 100ms마다 반복 실행.
    def stop_move_minus_X(self):
        self.timer.stop()

    def start_move_plus_X(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.move_plus_X)
        self.timer.start(100)

    def stop_move_plus_X(self):
        self.timer.stop()

    def start_move_minus_Y(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.move_minus_Y)
        self.timer.start(100)

    def stop_move_minus_Y(self):
        self.timer.stop()

    def start_move_plus_Y(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.move_plus_Y)
        self.timer.start(100)

    def stop_move_plus_Y(self):
        self.timer.stop()

    def start_move_minus_Z(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.move_minus_Z)
        self.timer.start(100)

    def stop_move_minus_Z(self):
        self.timer.stop()

    def start_move_plus_Z(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.move_plus_Z)
        self.timer.start(100)

    def stop_move_plus_Z(self):
        self.timer.stop()

    def start_rotate_minus_X(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate_minus_X)
        self.timer.start(100)

    def stop_rotate_minus_X(self):
        self.timer.stop()

    def start_rotate_plus_X(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate_plus_X)
        self.timer.start(100)

    def stop_rotate_plus_X(self):
        self.timer.stop()

    def start_rotate_minus_Y(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate_minus_Y)
        self.timer.start(100)

    def stop_rotate_minus_Y(self):
        self.timer.stop()

    def start_rotate_plus_Y(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate_plus_Y)
        self.timer.start(100)

    def stop_rotate_plus_Y(self):
        self.timer.stop()

    def start_rotate_minus_Z(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate_minus_Z)
        self.timer.start(100)

    def stop_rotate_minus_Z(self):
        self.timer.stop()

    def start_rotate_plus_Z(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate_plus_Z)
        self.timer.start(100)

    def stop_rotate_plus_Z(self):
        self.timer.stop()


    def move_minus_X(self):
        print(-1*self.move_val)
        self.robot.movel((-1*self.move_val, 0, 0, 0, 0, 0), acc=self.ACCELERATION, vel=self.VELOCITY, relative=True, wait=False)

    def move_plus_X(self):
        self.robot.movel((self.move_val, 0, 0, 0, 0, 0), acc=self.ACCELERATION, vel=self.VELOCITY, relative=True, wait=False)

    def move_minus_Y(self):
        self.robot.movel((0, -1*self.move_val, 0, 0, 0, 0), acc=self.ACCELERATION, vel=self.VELOCITY, relative=True, wait=False)

    def move_plus_Y(self):
        self.robot.movel((0, self.move_val, 0, 0, 0, 0), acc=self.ACCELERATION, vel=self.VELOCITY, relative=True, wait=False)

    def move_minus_Z(self):
        self.robot.movel((0, 0, -1*self.move_val, 0, 0, 0), acc=self.ACCELERATION, vel=self.VELOCITY, relative=True, wait=False)

    def move_plus_Z(self):
        self.robot.movel((0, 0, self.move_val, 0, 0, 0), acc=self.ACCELERATION, vel=self.VELOCITY, relative=True, wait=False)

    def rotate_minus_X(self):
        self.robot.movel_tool((0, 0, 0, -1*self.rot_val, 0, 0), acc=self.ACCELERATION, vel=self.VELOCITY, wait=False) # tool 기준

    def rotate_plus_X(self):
        self.robot.movel_tool((0, 0, 0, self.rot_val, 0, 0), acc=self.ACCELERATION, vel=self.VELOCITY, wait=False) # tool 기준

    def rotate_minus_Y(self):
        self.robot.movel_tool((0, 0, 0, 0, -1*self.rot_val, 0), acc=self.ACCELERATION, vel=self.VELOCITY, wait=False) # tool 기준

    def rotate_plus_Y(self):
        self.robot.movel_tool((0, 0, 0, 0, self.rot_val, 0), acc=self.ACCELERATION, vel=self.VELOCITY, wait=False) # tool 기준

    def rotate_minus_Z(self):
        self.robot.movel_tool((0, 0, 0, 0, 0, -1*self.rot_val), acc=self.ACCELERATION, vel=self.VELOCITY, wait=False) # tool 기준

    def rotate_plus_Z(self):
        self.robot.movel_tool((0, 0, 0, 0, 0, self.rot_val), acc=self.ACCELERATION, vel=self.VELOCITY, wait=False) # tool 기준

    def freedrive(self):
        print("change to freedive mode")
        freedrive_duration = 10 # freedrive 모드 유지 시간 (초)
        self.robot.set_freedrive(True)



class CircleWidget(QWidget):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self._color = color

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setBrush(QColor(self._color))
        qp.drawEllipse(0, 0, self.width(), self.height())

    def setColor(self, color):
        self._color = color
        self.update()  # Notify the system that the widget needs to be redrawn