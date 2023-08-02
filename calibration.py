# First import the library
import pyrealsense2.pyrealsense2 as rs
# Import Numpy for easy array manipulation
import numpy as np
# Import OpenCV for easy image rendering
import cv2
import pandas as pd
from datetime import datetime
import numpy.linalg as lin
from PIL import Image
from PIL import ImageDraw
import socket
import time
# import URBasic
import os
import urx
import matplotlib.pyplot as plt
import math
import time
import sys

def print_np(x):
    print("Type is %s" %(type(x)))
    print("Shape is %s" % (x.shape,))
    print("Values are: \n%s" % (x))

def cal_R_inv(robot_pose):
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
this_aruco_dictionary = cv2.aruco.Dictionary_get(ARUCO_DICT[desired_aruco_dictionary])
this_aruco_parameters = cv2.aruco.DetectorParameters_create()

rob = self.robot

# Create a pipeline
t = time.time()
pipeline = rs.pipeline()

# Create a config and configure the pipeline to stream
#  different resolutions of color and depth streams
config = rs.config()

# Get device product line for setting a supporting resolution
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
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
profile = pipeline.start(config)

# Getting the depth sensor's depth scale (see rs-align example for explanation)
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: " , depth_scale)

# We will be removing the background of objects more than
#  clipping_distance_in_meters meters away
clipping_distance_in_meters = 1 #1 meter
clipping_distance = clipping_distance_in_meters / depth_scale * 1000

# Create an align objectrobot
# rs.align allows us to perform alignment of depth frames to others frames
# The "align_to" is the stream type to which we plan to align depth frames.

align_to = rs.stream.color
align = rs.align(align_to)

elapsed_time_1 = time.time() - t
print(elapsed_time_1)

try:
    while True:
        # Get frameset of color and depth
        frames = pipeline.wait_for_frames()
        # frames.get_depth_frame() is a 640x360 depth image

        # Align the depth frame to color frame
        aligned_frames = align.process(frames)


        now = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame() # aligned_depth_frame is a 640x480 depth image
        color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(aligned_depth_frame.get_data()) * depth_scale
        color_image = np.asanyarray(color_frame.get_data())

        break

    #Detect ArUco markers in the video frame
    (corners_, ids_, rejected) = cv2.aruco.detectMarkers(
      color_image, this_aruco_dictionary, parameters=this_aruco_parameters)

    ids_ = ids_.flatten()

    df = pd.DataFrame([ids_, corners_]).transpose()
    df.columns = ['ids', 'corners']
    df.sort_values(by ='ids', inplace=True)

    ids = np.array(df['ids'])
    corners = np.array(df['corners'])

    # Check that at least one ArUco marker was detected
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

    robot_pose = rob.getl()
    robot_position = robot_pose[:3]
    print(robot_pose)
    R_inv = cal_R_inv(robot_pose)

    images = color_image

    calibration_image = Image.fromarray(images)

    now = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

    calibration_image.save('C:/Users/Administrator/Robot/calibration_result_image/test' + now + '.png')


    np.save('C:/Users/Administrator/Robot/calibration_numpy/total_cam' + now ,total_cam)
    time.sleep(0.5)
    np.save('C:/Users/Administrator/Robot/robot_R/R_inv' + now ,R_inv)
    time.sleep(0.5)
    np.save('C:/Users/Administrator/Robot/robot_position/robot_position' + now ,robot_position)


#     cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)
#     cv2.imshow('Align Example', images)
#     key = cv2.waitKey(1)
#     cv2.destroyAllWindows()


finally:
    pipeline.stop()

# elapsed_time =  time.time() - t
# print(elapsed_time)




ROOT_DIR = os.path.abspath("")
print(ROOT_DIR)

data_cam_list = os.listdir(os.path.join(ROOT_DIR, 'calibration_numpy'))
data_robot_list = os.listdir(os.path.join(ROOT_DIR, 'robot_position'))
data_R_list = os.listdir(os.path.join(ROOT_DIR, 'robot_R'))
data_cam_list.sort()
data_robot_list.sort()
data_R_list.sort()
print(data_R_list)

for i in range(len(data_cam_list)):
# for i in range(1):
    total_cam = np.load(os.path.join('C:/Users/Administrator/Robot/calibration_numpy',data_cam_list[i]))
    R_inv = np.load(os.path.join('C:/Users/Administrator/Robot/robot_R',data_R_list[i]))
    robot_position = np.load(os.path.join('C:/Users/Administrator/Robot/robot_position',data_robot_list[i]))
    cal_position_x = np.array(robot_position[0]*1000)
    cal_position_y = np.array(robot_position[1]*1000)
    cal_position_z = np.array(robot_position[2]*1000)
    print("cal_position_x :" , cal_position_x)
    print("cal_position_y :" , cal_position_y)
    print("cal_position_z :" , cal_position_z)


#     top_right = total_cam[:,:,0]
#     top_left = total_cam[:,:,1]
#     bottom_right = total_cam[:,:,2]
    bottom_left = total_cam[:,:,3]
#     cam_data_mat_ = np.hstack((top_right,top_left,bottom_right,bottom_left))

#     cam_data_mat_ = top_right
    cam_data_mat_ = bottom_left
#     cam_data_mat_ = bottom_right
#     robot_data_x = np.array([85,85,85,85,155,155,155,155,225,225,225,225,295,295,295,295]) + cal_position_x
#     robot_data_y = np.array([75,5,-65,-135,75,5,-65,-135,75,5,-65,-135,75,5,-65,-135]) + cal_position_y

#     robot_data_z = np.ones(len(robot_data_x)) * 10 + cal_position_z
#     robot_data_x = np.array([85,85,85,85,155,155,155,155,225,225,225,225,295,295,295,295])
#     robot_data_y = np.array([75,5,-65,-135,75,5,-65,-135,75,5,-65,-135,75,5,-65,-135])

#     robot_data_x = np.array([75,5,-65,-135,75,5,-65,-135,75,5,-65,-135,75,5,-65,-135])
#     robot_data_y = np.array([-85,-85,-85,-85,-155,-155,-155,-155,-225,-225,-225,-225,-295,-295,-295,-295])
    #bottom_left
    robot_data_x = np.array([135 ,65,-5,-75,135 ,65,-5,-75,135 ,65,-5,-75,135 ,65,-5,-75])
    robot_data_y = np.array([-175,-175,-175,-175,-245,-245,-245,-245,-315,-315,-315,-315,-385,-385,-385,-385])
#     robot_data_x = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
#     robot_data_y = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])

#     robot_data_x = np.array([85,85,85,85,155,155,155,155,225,225,225,225,295,295,295,295,\
#                             85,85,85,85,155,155,155,155,225,225,225,225,295,295,295,295,\
#                             145,145,145,145,215,215,215,215,285,285,285,285,355,355,355,355,\
#                             145,145,145,145,215,215,215,215,285,285,285,285,355,355,355,355])
#     robot_data_y = np.array([75,5,-65,-135,75,5,-65,-135,75,5,-65,-135,75,5,-65,-135,\
#                              135,65,-5,-75,135,65,-5,-75,135,65,-5,-75,135,65,-5,-75,\
#                              75,5,-65,-135,75,5,-65,-135,75,5,-65,-135,75,5,-65,-135,\
#                              135,65,-5,-75,135,65,-5,-75,135,65,-5,-75,135,65,-5,-75])


    robot_data_z = np.ones(len(robot_data_x)) * 10

    robot_data_mat_ = np.vstack([robot_data_x,robot_data_y,robot_data_z, np.ones(len(robot_data_x))])
    print("robot_data_mat_ :", robot_data_mat_)
#     robot_data_mat_ = robot_data_mat_[:,1:]

    robot_data_mat_ = np.matmul(R_inv, robot_data_mat_)
    print("robot_data_mat_ :", robot_data_mat_)
    robot_data_mat_[0,:] = robot_data_mat_[0,:] + cal_position_x
    robot_data_mat_[1,:] = robot_data_mat_[1,:] + cal_position_y
    robot_data_mat_[2,:] = robot_data_mat_[2,:] + cal_position_z


    if i == 0:
        cam_data_mat = cam_data_mat_
        robot_data_mat = robot_data_mat_
    else:
        cam_data_mat = np.hstack((cam_data_mat, cam_data_mat_))
        robot_data_mat = np.hstack((robot_data_mat, robot_data_mat_))


print_np(cam_data_mat)
print_np(robot_data_mat)

# l515 1280 x 720
cam_intrin_mat = np.array([[906.3367309570312, 0, 659.4196166992188, 0],[0,906.8651123046875,351.5494384765625,0],[0,0,1,0],[0,0,0,1]])
print_np(cam_intrin_mat)

# l515 1920 x 1080
# cam_intrin_mat = np.array([[1359.57080078125, 0, 976.2681274414062, 0],[0,1359.7188720703125,545.0499267578125,0],[0,0,1,0],[0,0,0,1]])
# print_np(cam_intrin_mat)

inv_cam_intrin_mat = lin.inv(cam_intrin_mat)
# print_np(inv_cam_intrin_mat)
inv_robot_data_mat = lin.pinv(robot_data_mat)


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