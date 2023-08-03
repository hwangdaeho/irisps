import sys
import numpy as np
import cv2
import pyrealsense2 as rs
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer

class RealSenseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

        # 카메라 세팅
        self.pipeline = rs.pipeline()
        config = rs.config()
        # config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.pipeline.start(config)

        # 마스크 초기화 함수
        self.mask = None

        # 드래그 상태 관련 변수
        self.mouse_pressed = False
        self.x1, self.y1, self.x2, self.y2 = -1, -1, -1, -1

        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30ms마다 프레임 업데이트

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)

        # 왼쪽 화면 - 실시간 화면
        self.left_label = QLabel(self)
        self.layout.addWidget(self.left_label)

        # 오른쪽 화면 - 크롭된 결과
        self.right_label = QLabel(self)
        self.layout.addWidget(self.right_label)

        # 윈도우 제목
        self.setWindowTitle("RealSense App")

    def mousePressEvent(self, event):
        self.mouse_pressed = True
        self.x1, self.y1 = event.x(), event.y()
        self.x2, self.y2 = event.x(), event.y()

    def mouseMoveEvent(self, event):
        if self.mouse_pressed:  # 드래그 중에는 초록색 박스를 업데이트하여 표시
            self.x2, self.y2 = event.x(), event.y()

    def mouseReleaseEvent(self, event):
        self.mouse_pressed = False
        self.update_frame()

    def update_frame(self):
        # 카메라로부터 프레임 획득
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            return

        # 프레임을 Numpy 배열로 변환
        color_image = np.asanyarray(color_frame.get_data())

        # 워터셰드 알고리즘을 이용하여 이미지 분할
        dilated_mask = self.watershed_segmentation(color_image)
        masked_frame = cv2.bitwise_and(color_image, color_image, mask=dilated_mask)

        # 드래그하는 동안에만 초록색 사각형을 표시
        temp_frame = color_image.copy()
        if self.mouse_pressed and self.x1 != -1 and self.y1 != -1:
            cv2.rectangle(temp_frame, (self.x1, self.y1), (self.x2, self.y2), (0, 255, 0), 2)

        # 드래그가 끝나면 해당 영역을 선택
        if not self.mouse_pressed and self.x1 != -1 and self.y1 != -1 and self.x2 != -1 and self.y2 != -1:
            cropped_color_image = color_image[self.y1:self.y2, self.x1:self.x2]
            cropped_masked_frame = masked_frame[self.y1:self.y2, self.x1:self.x2]

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

                    # 중심 좌표 출력
                    print("Center Coordinates:", center_x, center_y)

            # 선택된 영역을 오른쪽 화면에 표시
            self.display_frame(self.right_label, cropped_masked_frame)
        else:
            # 마우스 드래그 영역에 대한 이미지를 왼쪽 화면에 표시
            self.display_frame(self.left_label, temp_frame)

        # 실시간 화면을 왼쪽 화면에 표시
        self.display_frame(self.left_label, color_image)

    # 마스크 초기화 함수
    def init_mask(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 255, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return thresh

    # 워터셰드 함수
    def watershed_segmentation(self, frame):
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        edged = cv2.Canny(blurred, 30, 150)

        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edged, kernel, iterations=1)
        return dilated

    # OpenCV 이미지를 QLabel에 표시
    def display_frame(self, label, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        q_pixmap = QPixmap.fromImage(q_img)
        label.setPixmap(q_pixmap)

    def closeEvent(self, event):
        # 종료 시 리소스 해제
        self.pipeline.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RealSenseApp()
    window.show()
    sys.exit(app.exec_())