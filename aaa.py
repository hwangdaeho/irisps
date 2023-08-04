import pyrealsense2 as rs

# Realsense Intrinsic 확인 ##

pipeline = rs.pipeline()
cfg = pipeline.start() # Start pipeline and get the configuration it found
profile = cfg.get_stream(rs.stream.color) # Fetch stream profile for depth stream
# intr = profile.as_video_stream_profile().get_intrinsics() # Downcast to video_stream_profile and fetch intrinsics
# print(intr.ppx)

depth_intrinsic = profile.as_video_stream_profile().get_intrinsics()
print(depth_intrinsic.width)
print(depth_intrinsic.height)
print(depth_intrinsic.ppx)
print(depth_intrinsic.ppy)
print(depth_intrinsic.fx)
print(depth_intrinsic.fy)
print(depth_intrinsic.model)
print(depth_intrinsic.coeffs)