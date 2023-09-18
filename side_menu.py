from PySide6.QtWidgets import QToolButton, QVBoxLayout, QWidget, QSpacerItem, QSizePolicy
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
def create_side_menu(stacked_widget, main_window):
    button_height = 120  # 버튼의 높이를 조정합니다.
    button_width = 150

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)  # 버튼 사이의 공간을 없앱니다.
    icon_size = 40  # 아이콘의 크기를 지정합니다.
    font_size = 12  # 폰트의 크기를 지정합니다.

    button0 = QToolButton()
    button0.setText('Quick Setup')
    button0.setIcon(QIcon(":image/icon_setup_w.svg"))  # 아이콘을 설정합니다.
    button0.setIconSize(QSize(icon_size, icon_size))  # 아이콘의 크기를 설정합니다.
    button0.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)  # 아이콘을 글자 위에 배치합니다.
    button0.setFixedHeight(button_height)
    button0.setFixedWidth(button_width)
    button0.setStyleSheet('border: none;background: #B50039; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF; '.format(font_size)),
    button0.clicked.connect(
        lambda: [
            main_window.disconnect_global_camera(),
            main_window.load_screen_from_path('screen/quick/index.py', 'QuickMain'),
            main_window.update_header_text("Quick Setup"),
            main_window.update_header("Quick Setup", "screen/quick/index.py", "QuickMain"),
            button1.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF; '.format(font_size)),
            button2.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button3.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button4.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button0.setStyleSheet('border: none;background: #B50039; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size))
        ]
    )



    button1 = QToolButton()
    button1.setText('학습 이미지 촬영')
    button1.setIcon(QIcon(":image/icon_camera_w.svg"))  # 아이콘을 설정합니다.
    button1.setIconSize(QSize(icon_size, icon_size))  # 아이콘의 크기를 설정합니다.
    button1.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)  # 아이콘을 글자 위에 배치합니다.
    button1.setFixedHeight(button_height)
    button1.setFixedWidth(button_width)
    button1.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF; '.format(font_size)),
    button1.clicked.connect(
        lambda: [
            main_window.disconnect_global_camera(),
            main_window.load_screen_from_path('screen/image_shoot/index.py', 'ImageMain'),
            main_window.update_header_text("이미지 촬영"),
            main_window.update_header("이미지 학습 촬영", "screen/image_shoot/step/step1.py", "GuideScreen"),
            button0.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF; '.format(font_size)),
            button2.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button3.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button4.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button1.setStyleSheet('border: none;background: #B50039; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size))
        ]
    )

    button4 = QToolButton()
    button4.setText('자동 인식')
    button4.setIcon(QIcon(":image/icon_auto_w.svg"))  # 아이콘을 설정합니다.
    button4.setIconSize(QSize(icon_size, icon_size))  # 아이콘의 크기를 설정합니다.
    button4.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)  # 아이콘을 글자 위에 배치합니다.
    button4.setFixedHeight(button_height)
    button4.setFixedWidth(button_width)
    button4.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF; '.format(font_size)),
    button4.clicked.connect(
        lambda: [
            main_window.disconnect_global_camera(),
            main_window.load_screen_from_path('screen/crop/index.py', 'CropMain'),
            main_window.update_header("자동 인식", 'screen/crop/index.py', 'CropMain'),
            main_window.update_header_text("자동 인식"),
            button0.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #ffffff; '.format(font_size)),
            button1.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button2.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button3.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button4.setStyleSheet('border: none;background: #B50039; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size))
        ]
    )

    button2 = QToolButton()
    button2.setText('켈리브레이션')
    button2.setIcon(QIcon(":image/icon_calibraion_w.svg"))  # 아이콘을 설정합니다.
    button2.setIconSize(QSize(icon_size, icon_size))  # 아이콘의 크기를 설정합니다.
    button2.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)  # 아이콘을 글자 위에 배치합니다.
    button2.setFixedHeight(button_height)
    button2.setFixedWidth(button_width)
    button2.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0;font-weight: bold; color: #FFFFFF;'.format(font_size))
    button2.clicked.connect(
        lambda: [
            main_window.disconnect_global_camera(),
            main_window.load_screen_from_path('screen/calibration/index.py', 'CalibrationMain'),
            main_window.update_header_text("캘리브레이션"),
            main_window.update_header("캘리브레이션", "screen/calibration/step/step1.py", "GuideScreen"),
            button0.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #ffffff; '.format(font_size)),
            button1.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button3.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button4.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button2.setStyleSheet('border: none;background: #B50039; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size))
        ]
    )

    button3 = QToolButton()
    button3.setText('실시간 모니터링 & 운영')
    button3.setIcon(QIcon(":image/icon_monitorring_w.svg"))  # 아이콘을 설정합니다.
    button3.setIconSize(QSize(icon_size, icon_size))  # 아이콘의 크기를 설정합니다.
    button3.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)  # 아이콘을 글자 위에 배치합니다.
    button3.setFixedHeight(button_height)
    button3.setFixedWidth(button_width)
    button3.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0;font-weight: bold; color: #FFFFFF;'.format(font_size))
    button3.clicked.connect(
        lambda: [
            main_window.disconnect_global_camera(),
            main_window.load_screen_from_path('screen/inference/category.py', 'Category'),
            main_window.update_header_text("실시간 모니터링 & 운영"),
            main_window.update_header("실시간 모니터링 & 운영", 'screen/inference/category.py', 'Category'),
            button1.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button0.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #ffffff; '.format(font_size)),
            button2.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button4.setStyleSheet('border: none;background: #393939; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size)),
            button3.setStyleSheet('border: none;background: #B50039; font-size: {}px; padding: 20px 0; font-weight: bold; color: #FFFFFF;'.format(font_size))
        ]
    )

    layout.addWidget(button0)
    layout.addWidget(button1)
    layout.addWidget(button4)
    layout.addWidget(button2)
    layout.addWidget(button3)
    layout.setAlignment(Qt.AlignCenter)
    spacer = QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Expanding)
    layout.addItem(spacer)  # 마지막에 스페이서 아이템을 추가합니다.

    widget = QWidget()
    widget.setLayout(layout)

    return widget


