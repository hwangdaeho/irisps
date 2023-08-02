from PySide6.QtCore import QThread, QTimer, QMutex, Signal, Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QMessageBox
import pyrealsense2 as rs
import numpy as np
import cv2
import time
import os
class VideoManager:
    _instance = None
    print('VideoManager')
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print('cls._instance is None')
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.video_thread = VideoThread()  # Move this line to here
        return cls._instance

    def get_video_thread(self):
        return self.video_thread



class VideoThread(QThread):
    changePixmap = Signal(QImage)
    # inference 에서 사용함
    changePixmapRaw = Signal(QImage)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mutex = QMutex()  # Add a mutex
        self.is_recording = False  # Add a flag for recording
        self.is_connected = False
        self.video_writer = None  # Add a video writer
        self.timer = QTimer()  # Add a timer
        self.timer.timeout.connect(self.update_frame)  # Connect the timer timeout signal to the update_frame method
        self.timer.start(1000 / 30)  # Start the timer to call update_frame 30 times per second
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.profile = None
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

        print('VideoThread')
    def update_frame(self):
        self.mutex.lock()  # Lock the mutex
        is_connected = self.is_connected  # Store the flag value in a local variable
        is_recording = self.is_recording  # Store the flag value in a local variable
        self.mutex.unlock()  # Unlock the mutex

        if is_connected:
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()

            if not color_frame:
                return

            color_image = np.asanyarray(color_frame.get_data())
            rgbImage = color_image
            h, w, ch = rgbImage.shape
            bytesPerLine = ch * w
            convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
            p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
            self.changePixmap.emit(p)
            if is_recording and self.video_writer is not None:
                bgr_frame = cv2.cvtColor(rgbImage, cv2.COLOR_RGB2BGR)
                # If we are recording, write the frame into the video writer
                self.video_writer.write(bgr_frame)
    def connect_camera(self, camera_name):
        self.mutex.lock()  # Lock the mutex
        try:
            self.profile = self.pipeline.start(self.config)
            self.is_connected = True
            return True  # Add this line
        except RuntimeError as e:
            QMessageBox.information(self, "Connection failed", "Could not connect to the selected camera: {}".format(e))
        finally:
            self.mutex.unlock()  # Unlock the mutex in a finally block to ensure it gets unlocked

    def disconnect_camera(self):
        self.mutex.lock()  # Lock the mutex
        if self.is_connected:
            self.pipeline.stop()
            self.is_connected = False  # Set this flag to False after stopping the pipeline
        self.mutex.unlock()  # Unlock the mutex


    def get_is_recording(self):
        self.mutex.lock()  # Lock the mutex
        is_recording = self.is_recording
        self.mutex.unlock()  # Unlock the mutex
        return is_recording


    def start_recording(self, video_path):
        self.mutex.lock()  # Lock the mutex
        if self.is_connected:
            # Create a video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))
            self.is_recording = True  # Set this flag to True when starting recording
            print('start')
        self.mutex.unlock()  # Unlock the mutex

    def stop_recording(self):
        self.mutex.lock()  # Lock the mutex
        if self.is_recording:
            self.is_recording = False  # Set this flag to False when stopping recording
            # Release the video writer
            self.video_writer.release()
            self.video_writer = None
            print('stop')
        self.mutex.unlock()  # Unlock the mutex

    # 켈리브레이션 코드
    def get_camera_data(self):
        # Create a config and configure the pipeline to stream
        # different resolutions of color and depth streams
        config = rs.config()
        t = time.time()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
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

        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

        if device_product_line == 'L500':
            config.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, 30)
        else:
            config.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, 30)

        # Start streaming
        # profile = self.pipeline.start(config)

        # Getting the depth sensor's depth scale (see rs-align example for explanation)
        depth_sensor = self.profile.get_device().first_depth_sensor()
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
        frames = self.pipeline.wait_for_frames()
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
        os.path.join("/home/ubuntu/DD", f"calibration_image.png")
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
            print_np(total_cam[:,:,0])

        # robot_pose = rob.getl()
        # robot_position = robot_pose[:3]
        print(robot_pose)
        # R_inv = cal_R_inv(robot_pose)

        images = color_image

        calibration_image = Image.fromarray(images)




        # Assuming the ids, corners and depth_image are the required data
        return calibration_image, total_cam, R_inv, robot_position