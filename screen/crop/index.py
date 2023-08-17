import sys
import numpy as np
import cv2
import pyrealsense2 as rs
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QToolButton, QInputDialog
from PySide6.QtGui import QImage, QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer, Slot, QSize, QThread
from screen.video_manager import VideoManager
from PySide6.QtCore import Signal
from threading import Lock
class CropMain(QWidget):
    def __init__(self, parent=None, stacked_widget=None, main_window=None):
        super().__init__(parent)
           # 카메라 관련 변수
        self.initUI()

        self.camera_connected = False
        self.thread = VideoThread(self)  # Pass the inference_main instance to the VideoThread constructor
        self.thread.changePixmap.connect(self.setImage)
        # self.thread.changePixmapRaw.connect(self.setImageRaw)
        self.thread.start()


    def initUI(self):
        # Define a main vertical layout
        main_layout = QVBoxLayout()
        main_layout.addSpacing(50)

        image_layout = QHBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)  # Align the image to the center
        image_layout.addWidget(self.image_label)  # Add it to the main layout


        self.image_label_raw = QLabel()
        self.image_label_raw.setAlignment(Qt.AlignCenter)  # Align the image to the center
        image_layout.addWidget(self.image_label_raw)  # Add it to the main layout

        button_layout = QHBoxLayout()
        self.button = QToolButton()
        self.button.setText("카메라 연결")
        self.button.setStyleSheet('background-color: #2F2F2F; color: white; font-size:15px; padding: 19px 16px;border-top: 1.5px solid #2F2F2F;border-right: 1.5px solid #2F2F2F;border-bottom: 1.5px solid #2F2F2F;')  # Set the background to black and text to white
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setIconSize(QSize(24, 24))  # Set the icon size
        self.button.setFixedSize(QSize(160, 70))  # Set the button size
        self.button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.button.clicked.connect(self.connect_camera)  #


        main_layout.addLayout(image_layout)
        main_layout.setSpacing(0)  # Set the space between the image label and the button layout
        button_layout.addWidget(self.button)

        button_layout.setSpacing(0)  # Set the space between the buttons
        button_layout.setAlignment(Qt.AlignCenter)  # Align the image to the center
        button_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addLayout(button_layout)
        # Set the main layout
        self.setLayout(main_layout)

        self.show_placeholder_image()
        self.show_placeholder_image_raw()


    @Slot(QImage)
    def setImage(self, image):
        self.current_image = image
        self.image_label.setPixmap(QPixmap.fromImage(image))
        self.image_label.setContentsMargins(0, 0, 0, 0)

    @Slot(QImage)
    def setImageRaw(self, image):
        self.current_image_raw = image
        self.image_label_raw.setPixmap(QPixmap.fromImage(image))
        self.image_label_raw.setContentsMargins(0, 0, 0, 0)

    def connect_camera(self):
        # If the camera is already connected, disconnect it
        if self.thread.is_connected:
            self.thread.disconnect_camera()
            self.button.setText("카메라 연결")
            self.thread.is_connected = False
            self.show_placeholder_image()  # Add this line
        else:
            # Display a dialog with the available cameras
            cameras = rs.context().devices
            camera_names = [camera.get_info(rs.camera_info.name) for camera in cameras]

            if camera_names:
                camera_name, ok = QInputDialog.getItem(self, "Connect to camera", "Choose a camera:", camera_names, 0, False)

                if ok and camera_name:
                    print('커넥트 카메라 연결진입')
                    connected = self.thread.connect_camera(camera_name)
                    if connected:
                        self.button.setText("연결 해제")
                        self.thread.is_connected = True

            else:
                QMessageBox.information(self, "No cameras found", "No cameras were found. Please connect a camera and try again.")
                self.show_placeholder_image()  # Add this line


    def show_placeholder_image(self):
        # Load your placeholder image
        placeholder = QImage(":image/null.png")

        # Display the placeholder image
        self.setImage(placeholder)
    def show_placeholder_image_raw(self):
        # Load your placeholder image
        placeholder = QImage(":image/null.png")
        # Display the placeholder image
        self.setImageRaw(placeholder)

    def mousePressEvent(self, event):
        self.mouse_pressed = True
        label_position = self.image_label.mapFromGlobal(event.globalPos())
        self.thread.x1, self.thread.y1 = self.scale_coordinates(label_position.x(), label_position.y())
        self.thread.x2, self.thread.y2 = self.scale_coordinates(label_position.x(), label_position.y())

    def mouseMoveEvent(self, event):
        if self.mouse_pressed:  # 드래그 중에는 초록색 박스를 업데이트하여 표시
            self.thread.x2, self.thread.y2 = self.scale_coordinates(event.x(), event.y())

    def mouseReleaseEvent(self, event):
        self.mouse_pressed = False
        self.thread.update_frame()

    def scale_coordinates(self, x, y):
        label_width = self.image_label.width()
        label_height = self.image_label.height()
        frame_height, frame_width, _ = self.color_image.shape # color_image를 클래스 변수로 접근한다고 가정

        scale_x = frame_width / label_width
        scale_y = frame_height / label_height

        return int(x * scale_x), int(y * scale_y)




class VideoThread(QThread):

    changePixmap = Signal(QImage)  # For the processed image

    def __init__(self, CropMain, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.CropMain = CropMain
        self.lock = Lock()
        self.video_writer = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000 / 30)  # Start the timer to call update_frame 30 times per second
        self.is_connected = False  # Initialize the attribute
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.mask = None
        self.mouse_pressed = False
        self.x1, self.y1, self.x2, self.y2 = -1, -1, -1, -1


    def update_frame(self):
        with self.lock:
            is_connected = self.is_connected

        if is_connected:
            # 카메라로부터 프레임 획득
            frames = self.pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not color_frame:
                return

            # 프레임을 Numpy 배열로 변환
            color_image = np.asanyarray(color_frame.get_data())
            self.CropMain.color_image = color_image
            # 워터셰드 알고리즘을 이용하여 이미지 분할
            dilated_mask = self.watershed_segmentation(color_image)
            masked_frame = cv2.bitwise_and(color_image, color_image, mask=dilated_mask)
            label_width = self.CropMain.image_label.width()
            label_height = self.CropMain.image_label.height()
            frame_height, frame_width, _ = color_image.shape

            # 드래그하는 동안에만 초록색 사각형을 표시
            temp_frame = color_image.copy()
            if self.mouse_pressed and self.x1 != -1 and self.y1 != -1:
                # cv2.rectangle(temp_frame, (self.x1, self.y1), (self.x2, self.y2), (0, 255, 0), 2)
                cv2.rectangle(color_image, (self.x1, self.y1), (self.x2, self.y2), (0, 255, 0), 2)
            self.display_frame(self.CropMain.image_label, color_image)
            # 드래그가 끝나면 해당 영역을 선택

            if not self.mouse_pressed and self.x1 != -1 and self.y1 != -1 and self.x2 != -1 and self.y2 != -1:
                cropped_color_image = color_image[self.y1:self.y2, self.x1:self.x2]

                cropped_masked_frame = masked_frame[self.y1:self.y2, self.x1:self.x2]

                # 크롭된 이미지를 오른쪽 화면 크기로 확대
                target_width, target_height = self.CropMain.image_label_raw.width(), self.CropMain.image_label_raw.height()


                # 마스크 초기화
                if self.mask is None:
                    self.mask = self.init_mask(cropped_color_image)

                # 이진화된 마스크
                gray_mask = cv2.cvtColor(cropped_masked_frame, cv2.COLOR_BGR2GRAY)
                _, binary_mask = cv2.threshold(gray_mask, 1, 255, cv2.THRESH_BINARY)

                # 각각의 분할된 객체를 찾음
                contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                min_area = 7000
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area >= min_area:
                        moments = cv2.moments(contour)
                        center_x = int(moments["m10"] / moments["m00"]) if moments["m00"] != 0 else 0
                        center_y = int(moments["m01"] / moments["m00"]) if moments["m00"] != 0 else 0

                        # 빨간색 원으로 중심 좌표 표시
                        radius = 5
                        center_point = (center_x, center_y)
                        color = (0, 0, 255)  # 빨간색 (BGR 순서)
                        cv2.circle(cropped_masked_frame, center_point, radius, color, -1)

                resized_cropped_masked_frame = cv2.resize(cropped_masked_frame, (target_width, target_height))
                # 선택된 영역을 오른쪽 화면에 표시
                self.display_frame(self.CropMain.image_label_raw, resized_cropped_masked_frame)
            else:
                # 마우스 드래그 영역에 대한 이미지를 왼쪽 화면에 표시
                self.display_frame(self.CropMain.image_label, temp_frame)

            # 실시간 화면을 왼쪽 화면에 표시
            color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            self.display_frame(self.CropMain.image_label, color_image)

    def connect_camera(self, camera_name):
        with self.lock:
            try:

                self.pipeline.start(self.config)
                self.is_connected = True
                print('crop Cameara 연결')
                print(self.is_connected)
                print('crop Cameara 연결')
                return True
            except RuntimeError as e:
                QMessageBox.information(self, "Connection failed", "Could not connect to the selected camera: {}".format(e))
        # OpenCV 이미지를 QLabel에 표시

    def display_frame(self, label, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        q_pixmap = QPixmap.fromImage(q_img)
        label.setPixmap(q_pixmap)

     # 워터셰드 함수
    def watershed_segmentation(self, frame):
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        edged = cv2.Canny(blurred, 30, 150)

        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edged, kernel, iterations=1)
        return dilated


    # 마스크 초기화 함수
    def init_mask(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 255, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return thresh

    def disconnect_camera(self):
        print('crop Cameara 중단')
        print(self.is_connected)
        print('crop Cameara 중단')
        with self.lock:
            if self.is_connected:
                self.pipeline.stop()
                self.is_connected = False