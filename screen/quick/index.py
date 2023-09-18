from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,QSizePolicy, QLineEdit
from PySide6.QtGui import QPixmap, QFont, QIcon, QImage
from PySide6.QtCore import Qt, QSize, QThread, Signal, QMutex
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
import pyrealsense2 as rs
import numpy as np
class QuickMain(QWidget):
    def __init__(self, parent=None, stacked_widget=None, main_window=None):
        super(QuickMain, self).__init__(parent)
        self.current_step = 1  # 현재 단계를 나타내는 변수

        self.header_widget = QWidget(self)

        # self.header_widget.setStyleSheet("background-color: red;")
        self.header_widget.setFixedHeight(80)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 0, 0)

        self.header_widget.setLayout(header_layout)

        # Quick Setup 라인 생성
        icon_text_layout = QHBoxLayout()
        # icon_text_layout.setSpacing(5)

        icon_label = QLabel(self)
        # icon_size = QSize(30, 30)
        icon_pixmap = QPixmap(":image/icon_setup_b.svg")
        icon_label.setPixmap(icon_pixmap)
        # icon_label.setContentsMargins(0, 0, 0, 0)  # 상, 우, 하, 좌 마진을 모두 0으로 설정

        # "Quick Setup" 라벨 생성
        quick_setup_label = QLabel("Quick Setup", self)
        quick_setup_label.setStyleSheet("font-size: 18pt;")
        icon_text_layout.addWidget(icon_label, alignment=Qt.AlignLeft)
        icon_text_layout.addWidget(quick_setup_label, alignment=Qt.AlignLeft)
        icon_text_layout.addStretch(1)
        description_label = QLabel("자동으로 켈리브레이션을 진행하여 실시간 뷰를 통해 인식된 객체 결과를 보여줍니다.")

        # 헤더 내부 레이아웃
        header_text_layout = QVBoxLayout()
        header_text_layout.addLayout(icon_text_layout)
        header_text_layout.addWidget(description_label)
        header_layout.addLayout(header_text_layout)
        # 여기서 빈 공간 추가
        # header_layout.addStretch(1)

        # 다음 단계 버튼 설정
        next_button = QPushButton()
        next_button_layout = QHBoxLayout(next_button)  # 버튼에 레이아웃 추가
        next_button_layout.addWidget(QLabel("다음 단계"))
        icon_label_for_button = QLabel()
        icon_pixmap_for_button = QPixmap(":image/icon_arrow.svg")
        icon_label_for_button.setPixmap(icon_pixmap_for_button.scaled(QSize(20, 20)))
        next_button_layout.addWidget(icon_label_for_button)
        next_button.setFixedSize(120, 50)  # 조금 더 넓게 설정
        next_button.setStyleSheet("border:none;background-color:#B50039; color:#FFFFFF; ")

        exit_button = QPushButton("종료")
        exit_button.setFixedSize(80, 50)
        exit_button.setStyleSheet("border:none;background-color:#393939; color:#FFFFFF; margin-right: 20px;")
        next_button.setCursor(Qt.PointingHandCursor)
        exit_button.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(next_button, alignment=Qt.AlignRight)
        header_layout.addWidget(exit_button, alignment=Qt.AlignRight)



        self.main_content_widget = QWidget(self)  # 메인 컨텐츠 위젯
        self.main_layout = QVBoxLayout()  # 메인 레이아웃 변경
        self.main_layout.addWidget(self.header_widget)
        self.main_layout.addWidget(self.main_content_widget)

        self.content_layout = QVBoxLayout()  # 메인 컨텐츠 위젯의 내부 레이아웃 변경
        # 드롭 쉐도우 효과를 main_content_widget에 추가
        shadow2 = QGraphicsDropShadowEffect(self)
        shadow2.setBlurRadius(15)
        shadow2.setOffset(5, 5)
        shadow2.setColor(QColor(0, 0, 0, 80))  # 흑색의 80 투명도
        self.main_content_widget.setGraphicsEffect(shadow2)
        self.main_content_widget.setLayout(self.content_layout)  # 추가한 코드



        # 프로그레스 바 이미지 추가
        self.progress_images = [":image/Progressbar1.svg",
                                ":image/Progressbar2.svg",
                                ":image/Progressbar3.svg",
                                ":image/Progressbar4.svg"]
        self.progress_label = QLabel(self)
        self.progress_label.setFixedHeight(60)
        self.update_progress_image()  # 초기 이미지 설정
        self.content_layout.addWidget(self.progress_label, alignment=Qt.AlignHCenter)
        # self.progress_label.setStyleSheet('margin-top:10px;')
        # 이미지
        self.bottom_horizontal_layout = QHBoxLayout()
        self.content_layout.addLayout(self.bottom_horizontal_layout)

        self.auto_button = QPushButton("Auto calibration", self)  # "Auto calibration"이라는 텍스트의 버튼 생성
        self.auto_button.setStyleSheet('border:none; background-color: #B50039; color: white; min-height: 50px; margin-bottom:20px;')
        self.auto_button.setFixedWidth(260)  # 버튼의 너비 설정
        self.auto_button.setCursor(Qt.PointingHandCursor)  # 마우스 커서를 손가락 모양으로 변경
        self.content_layout.addWidget(self.auto_button, alignment=Qt.AlignHCenter)  # content_layout에 버튼을 추가하고 가운데 정렬
        # self.content_label = QLabel("Step 1: Initial Content", self)
        # self.content_layout.addWidget(self.content_label)

        # "다음 단계" 버튼 연결
        next_button.clicked.connect(self.on_next_clicked)

        self.left_label = QLabel(self)  # 이미지 라벨 예제
        self.bottom_horizontal_layout.addWidget(self.left_label, alignment=Qt.AlignRight)
        self.left_label.setPixmap(QPixmap(":image/null.png"))
        self.left_label.setStyleSheet('margin-left:200px;')
        # right_label 대신 right_layout에 위젯 추가

        self.camera_thread = CameraThread()
        self.camera_thread.signal.connect(self.update_image)
        self.auto_button.clicked.connect(self.start_camera)
        self.right_widget = QWidget(self)  # QWidget 생성
        # self.right_widget.setFixedHeight(480)
        self.right_widget.setFixedSize(280,480)
        self.bottom_horizontal_layout.addWidget(self.right_widget,alignment=Qt.AlignLeft)  # bottom_horizontal_layout에 위젯으로 추가

        self.right_layout = QVBoxLayout(self.right_widget)  # right_widget을 parent로 하는 QVBoxLayout 생성
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        # Robot 연결 텍스트 추가
        # Robot 연결 텍스트 설정
        robot_label = QLabel("Robot 연결", self.right_widget)
        robot_label.setFixedHeight(40)
        robot_label.setStyleSheet('margin-left:10px; margin-top:10px; font-size:18px; font-weight: bold;')  # 굵게 만들려면 'font-weight: bold;' 추가
        self.right_layout.addWidget(robot_label, alignment=Qt.AlignLeft)

        # IP 연결 & 아이콘 & OK Connection 부분 설정
        ip_layout = QHBoxLayout()
        ip_label = QLabel("IP 연결", self.right_widget)
        ip_label.setFixedHeight(30)
        ip_label.setStyleSheet('margin-left:10px; font-size:15px; ')  # 굵게 만들려면 'font-weight: bold;' 추가
        icon_pixmap_for_ip = QPixmap(":image/icon_for_ip.svg")
        icon_label_for_ip = QLabel(self.right_widget)
        icon_label_for_ip.setPixmap(icon_pixmap_for_ip)
        connection_label = QLabel("OK Connection", self.right_widget)
        connection_label.setStyleSheet('font-size:15px;')

        ip_layout.addWidget(ip_label, alignment=Qt.AlignLeft)
        ip_layout.addWidget(icon_label_for_ip, alignment=Qt.AlignRight)
        ip_layout.addWidget(connection_label, alignment=Qt.AlignRight)
        self.right_layout.addLayout(ip_layout)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(5, 5)
        shadow.setColor(QColor(0, 0, 0, 80))  # 흑색의 80 투명도
        self.right_widget.setGraphicsEffect(shadow)
        self.right_widget.setLayout(self.right_layout)  # 추가한 코드
        self.right_layout.addLayout(ip_layout)

        # input 박스 추가
        self.ip_input = QLineEdit(self.right_widget)  # parent 설정
        self.ip_input.setPlaceholderText("IP 주소")  # 플레이스홀더 텍스트 설정
        self.ip_input.setStyleSheet('background-color: #F3F4F5;min-height: 30px;')  # 배
        self.ip_input.setFixedWidth(260)
        self.right_layout.addWidget(self.ip_input,alignment=Qt.AlignCenter)
        self.right_layout.addStretch(1)
        self.my_button = QPushButton("연결", self.right_widget)  # "버튼"이라는 텍스트의 버튼 생성
        self.my_button.setStyleSheet('border:none; background-color: #393939; color: white; width:40px;  min-height: 40px; margin-bottom:20px;')
        self.my_button.setFixedWidth(260)  # 스타일 설정 (예: 파란색 배경 및 흰색 텍스트)
        self.my_button.setCursor(Qt.PointingHandCursor)
        self.right_layout.addWidget(self.my_button,alignment=Qt.AlignCenter)

        # 2단계 레이아웃 오른쪽 화면
        self.right_label = QLabel(self)
        self.right_label.hide()  # 초기에는 숨기기
        self.bottom_horizontal_layout.addWidget(self.right_label, alignment=Qt.AlignLeft)

        self.setLayout(self.main_layout)


    def update_progress_image(self):
        """현재 스텝에 따라 프로그레스 이미지를 업데이트합니다."""
        if 1 <= self.current_step <= 4:
            pixmap = QPixmap(self.progress_images[self.current_step - 1])
            self.progress_label.setPixmap(pixmap)

    def on_next_clicked(self):
        self.current_step += 1  # 단계 증가
        if self.current_step == 2:
            print(self.current_step)

            self.left_label.setPixmap(QPixmap(":image/null.png"))

            # right_layout에서 모든 위젯을 제거합니다
            for i in reversed(range(self.right_layout.count())):
                widget = self.right_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            # 버튼의 부모를 None으로 설정하고 버튼을 삭제
            self.auto_button.setParent(None)
            self.auto_button.deleteLater()  # 위젯 완전히 제거
            # right_widget을 제거하고 새로 생성합니다
            self.right_widget.setParent(None)
            self.right_widget = QWidget(self)
            self.right_widget.setFixedSize(640, 480)
            self.left_label.setStyleSheet('margin-left:30px;')
            self.bottom_horizontal_layout.addWidget(self.right_widget, alignment=Qt.AlignLeft)  # 수정된 코드

            # 새 right_layout을 생성하고 설정합니다
            self.right_layout = QVBoxLayout(self.right_widget)
            self.right_layout.setContentsMargins(0, 0, 0, 0)

            # 여기에서 새 right_label을 생성하고 이미지를 설정합니다
            self.right_label = QLabel(self.right_widget)
            self.right_label.setPixmap(QPixmap(":image/null.png"))  # 이미지 파일 경로로 변경해야 합니다
            self.right_layout.addWidget(self.right_label)

            # 새로운 레이아웃을 화면에 표시합니다
            self.right_widget.setLayout(self.right_layout)
        elif self.current_step == 3:
             # 기존 right_widget와 그 내용을 제거
            self.right_widget.setParent(None)
            self.right_widget.deleteLater()  # 위젯 완전히 제거
            # self.left_label.setStyleSheet('margin-left:350px;')

            self.bottom_horizontal_layout.addWidget(self.left_label, alignment=Qt.AlignHCenter)
            self.button1 = QPushButton("학습이미지 촬영", self)
            self.button1.setStyleSheet('border:none; background-color: #B50039; color: white; min-height: 50px; margin-bottom:20px;')
            self.button1.setFixedWidth(260)
            self.button1.setCursor(Qt.PointingHandCursor)

            self.button2 = QPushButton("이미지 학습하기", self)
            self.button2.setStyleSheet('border:none; background-color: #393939; color: white; min-height: 50px; margin-bottom:20px;')
            self.button2.setFixedWidth(260)
            self.button2.setCursor(Qt.PointingHandCursor)

            new_horizontal_layout = QHBoxLayout()
             # 버튼들을 bottom_horizontal_layout에 추가
            new_horizontal_layout.addWidget(self.button1)
            new_horizontal_layout.addWidget(self.button2)
            self.content_layout.addLayout(new_horizontal_layout)
            self.content_layout.setAlignment(new_horizontal_layout, Qt.AlignHCenter)
            # # bottom_horizontal_layout을 content_layout에 추가
            # self.content_layout.addLayout(new_horizontal_layout, alignment=Qt.AlignHCenter)

            print(self.current_step)
            # self.content_label.setText("Step 3: Another Content")
        elif self.current_step == 4:
            print(self.current_step)

            # 기존 3단계 요소 제거
            self.button1.setParent(None)
            self.button1.deleteLater()
            self.button2.setParent(None)
            self.button2.deleteLater()


            self.right_widget = QWidget(self)
            self.right_widget.setFixedSize(640, 480)
            self.left_label.setStyleSheet('margin-left:30px;')
             # 새 right_layout을 생성하고 설정합니다
            self.right_layout = QVBoxLayout(self.right_widget)
            self.right_layout.setContentsMargins(0, 0, 0, 0)

            # 여기에서 새 right_label을 생성하고 이미지를 설정합니다
            self.right_label = QLabel(self.right_widget)
            self.right_label.setPixmap(QPixmap(":image/null.png"))  # 이미지 파일 경로로 변경해야 합니다
            self.right_layout.addWidget(self.right_label)

            self.bottom_horizontal_layout.addWidget(self.right_widget, alignment=Qt.AlignLeft)  # 수정된 코드


            # 새 버튼 생성
            self.final_button = QPushButton("모델 등록", self)
            self.final_button.setStyleSheet('border:none; background-color: #B50039; color: white; min-height: 50px; margin-bottom:20px;')
            self.final_button.setFixedWidth(260)
            self.final_button.setCursor(Qt.PointingHandCursor)

            new_horizontal_layout = QHBoxLayout()
             # 버튼들을 bottom_horizontal_layout에 추가
            new_horizontal_layout.addWidget(self.final_button)
            self.content_layout.addLayout(new_horizontal_layout)
            self.content_layout.setAlignment(new_horizontal_layout, Qt.AlignHCenter)

        self.update_progress_image()


    def resizeEvent(self, event):
        super(QuickMain, self).resizeEvent(event)  # 원래의 resizeEvent 기능도 유지

    def start_camera(self):
        self.camera_thread.start()
        self.camera_thread.is_connected = True

    def update_image(self, image):
        pixmap = QPixmap.fromImage(image)
        self.left_label.setPixmap(pixmap)



class CameraThread(QThread):
    signal = Signal(QImage)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mutex = QMutex()  # Add a mutex
        self.is_connected = False
        self.pipeline = rs.pipeline()
        self.config = rs.config()
    def run(self):
        # 리얼센스 카메라 파이프라인 구성
        pipeline = self.pipeline
        config = self.config
        config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)

        # 카메라 파이프라인 시작
        pipeline.start(config)

        try:
            while True:
                # 카메라 프레임 가져오기
                frames = pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                if not color_frame:
                    continue

                color_image = np.asanyarray(color_frame.get_data())
                rgbImage = color_image
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)

                # p = convertToQtFormat.scaled(self.rs_color_width, self.rs_color_height, Qt.KeepAspectRatio)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)

                # 신호 발송
                self.signal.emit(p)

        finally:
            self.pipeline.stop()
    def disconnect_camera(self):
        self.mutex.lock()  # Lock the mutex
        print('qewqe')
        if self.is_connected:
            print('sadasdasdasdasd')
            self.pipeline.stop()
            self.is_connected = False  # Set this flag to False after stopping the pipeline
        self.mutex.unlock()  # Unlock the mutex