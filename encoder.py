import numpy as np
import cv2
import datetime
import sys
import os

def file_to_binary_video(input_file, output_video, frame_width=1280, frame_height=720, border_size=10):
    # Extract the filename from the input_file path
    filename = os.path.basename(input_file)
    
    # Convert the filename to bytes
    filename_bytes = filename.encode('utf-8')
    
    # Add the filename length (1 byte) and filename to the header
    filename_header = bytes([len(filename_bytes)]) + filename_bytes
    
    # Read the file in binary mode
    with open(input_file, "rb") as f:
        data = f.read()

    # Convert binary data to a numpy array of uint8 (0-255)
    data_array = np.frombuffer(data, dtype=np.uint8)

    # Get the size of the original file (in bytes)
    file_size = len(data_array)

    # Convert the file size to a 4-byte header (32-bit unsigned integer)
    file_size_header = np.array([file_size], dtype=np.uint32).tobytes()

    # Combine the header and the file data
    data_with_header = np.frombuffer(file_size_header + filename_header + data, dtype=np.uint8)
    print(len(data_with_header))

    # Convert the data to binary (0s and 1s)
    binary_data = np.unpackbits(data_with_header)

    # Calculate the number of pixels needed per frame (excluding the border)
    pixels_per_frame = (frame_width - 2 * border_size) * (frame_height - 2 * border_size)

    # Calculate the number of frames required
    num_frames = (len(binary_data) + pixels_per_frame - 1) // pixels_per_frame

    # Pad the binary data to fit exactly into the frames
    padding = num_frames * pixels_per_frame - len(binary_data)
    if padding > 0:
        binary_data = np.append(binary_data, np.zeros(padding, dtype=np.uint8))

    # Reshape the binary data into frames (excluding the border)
    frames = binary_data.reshape((num_frames, frame_height - 2 * border_size, frame_width - 2 * border_size))

    # Convert binary frames to black and white images
    framed_frames = []
    for frame in frames:
        # Convert 0s to black (0) and 1s to white (255)
        image = frame * 255
        # Add a border around the frame
        framed_frame = cv2.copyMakeBorder(image, border_size, border_size, border_size, border_size, cv2.BORDER_CONSTANT, value=255)
        framed_frames.append(framed_frame)

    # Create a unique start marker (checkerboard pattern)
    checkerboard = np.zeros((frame_height, frame_width), dtype=np.uint8)
    checkerboard[::10, ::10] = 255  # 10x10 checkerboard pattern

    # Create end marker (white frame)
    end_marker = np.full((frame_height, frame_width), 255, dtype=np.uint8)

    # Repeat each frame 2 times for robustness
    #repeated_frames = framed_frames
    #for frame in framed_frames:
    #    repeated_frames.extend([frame] * 2)

    # Add a random frame after the end marker
    random_frame = np.random.randint(0, 256, (frame_height, frame_width), dtype=np.uint8)

    # Combine start marker, repeated frames, end marker, and random frame
    #video_frames = [checkerboard] + repeated_frames + [end_marker] + [end_marker] + [end_marker] + [end_marker] + [random_frame]
    video_frames = [checkerboard] + framed_frames + [end_marker] + [end_marker] + [end_marker] + [end_marker] + [random_frame]


    # Write frames to a video file
    fourcc = cv2.VideoWriter_fourcc(*"FFV1")  # Lossless codec
    out = cv2.VideoWriter(output_video, fourcc, 5, (frame_width, frame_height))  # 5 FPS

    for frame in video_frames:
        # Convert grayscale to BGR for video writing
        out.write(cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR))

    out.release()
    print(f"Video saved to {output_video}")

# Example usage
start = datetime.datetime.now()
print(f"""Started encoding : {start}""")
input_file = sys.argv[1]  # Input file to be encoded
output_video = sys.argv[2]
file_to_binary_video(input_file, output_video)
end = datetime.datetime.now()
print(f"""Encoded in : {end - start}""")
