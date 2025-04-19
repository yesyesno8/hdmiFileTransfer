import numpy as np
import cv2
import datetime
import sys
import hashlib

def detect_start_marker(frame, checkerboard_pattern):
    """
    Detect the start marker by comparing the frame to the checkerboard pattern.
    """
    # Calculate the difference between the frame and the checkerboard pattern
    diff = np.mean(np.abs(frame - checkerboard_pattern))
    return diff < 10  # Allow for small variations

def binary_video_to_file(input_video, output_file, border_size=10, threshold=128):
    # Open the video file
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        raise Exception("Could not open video file")

    # Get the video resolution
    frame_width = 1280
    frame_height = 720
    
    # Define the checkerboard pattern for the start marker
    checkerboard_pattern = np.zeros((frame_height, frame_width), dtype=np.uint8)
    checkerboard_pattern[::10, ::10] = 255  # 10x10 checkerboard pattern
    # Define expected marker colors (grayscale)
    start_marker_color = 0    # Black
    end_marker_color = 255    # White

    # Tolerance for marker detection (adjust as needed)
    color_tolerance = 50  # Allow for deviations in pixel values

    # Extract frames and collect binary data
    binary_data = []
    in_file_data = False
    frame_count = 0
    previous_data_frame = None
    previous_data_correlation = 50
    handled = False
    unique_data_frames = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        ###print(f"Processing frame {frame_count}...")

        # Convert frame to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.resize(gray_frame, (1280, 720))

        # Calculate the average color of the frame
        average_color = np.mean(gray_frame)

        # Detect start marker (black frame)
        if detect_start_marker(gray_frame, checkerboard_pattern):
            print("Start marker detected!")
            in_file_data = True
            continue  # Skip the start marker frame

        # Detect end marker (white frame)
        if np.abs(average_color - end_marker_color) < color_tolerance:
            print("End marker detected!")
            if not handled:
                binary_frame = (previous_data_frame > threshold).astype(np.uint8)
                binary_data.append(binary_frame.flatten())
                handled = True
            break  # Stop processing after the end marker

        # If inside the file data, detect the border and crop the frame
        if in_file_data:
            cropped_frame = gray_frame[border_size:720 - border_size, border_size:1280 - border_size]
            if previous_data_frame is not None:
                data_correlation = np.mean(cropped_frame - previous_data_frame)
                ###print(f"""Correlation : {data_correlation}""")
                if(data_correlation>5):
                    if(not handled):
                        binary_frame = (previous_data_frame > threshold).astype(np.uint8)
                        binary_data.append(binary_frame.flatten())
                        ###unique_data_frames += 1
                        ###print(f"""Got a unique data frame : {unique_data_frames}""")
                        ###name = f"""./data/frame{unique_data_frames}.jpg"""
                        ###cv2.imwrite(name, cropped_frame)
                    handled = False
                elif((np.mean(cropped_frame - previous_data_frame)<0.1) and not handled):
                    unique_data_frames += 1
                    ###print(f"""Got a unique data frame : {unique_data_frames}""")
                    ###name = f"""./data/frame{unique_data_frames}.jpg"""
                    ###cv2.imwrite(name, cropped_frame)
                    binary_frame = (cropped_frame > threshold).astype(np.uint8)
                    binary_data.append(binary_frame.flatten())
                    handled = True
                previous_data_frame = cropped_frame
            else:
                previous_data_frame = cropped_frame

    # Release the video capture object
    cap.release()

    if not binary_data:
        raise Exception("No file data found in the video")

    # Combine all binary data into a single array
    binary_array = np.concatenate(binary_data)

    # Convert binary data back to bytes
    byte_array = np.packbits(binary_array)

    # Initialize headers cursor
    cursor = 0
    file_size_length = 4
    # Extract the file size from the first 4 bytes (header)
    file_size = int.from_bytes(byte_array[cursor:cursor+file_size_length], byteorder="little")
    print(f"Original file size: {file_size} bytes")
    
    cursor = cursor + file_size_length
    # Debug: Verify the file size is reasonable
    if file_size == 4294967295:  # 0xFFFFFFFF, indicates a corrupted header
        raise Exception("Corrupted file size header detected!")
    
    # Extract the filename length (1 byte)
    filename_length = int(byte_array[cursor])
    
    # Advance 1 byte
    cursor = cursor + 1

    # Extract the filename
    try:
        filename = byte_array[cursor:cursor + filename_length].tobytes().decode('utf-8')
    except:
        raise Exception("Corrupted file name header detected!")

    # Advance cursor with filename_length
    cursor = cursor + filename_length
    file_md5_length = 16

    # Extract the file MD5 hash
    try:
        file_md5_hash = byte_array[cursor:cursor+file_md5_length].tobytes().hex()
    except:
        raise Exception("Corrupted file hash header detected!")
        
    ###print(f"""File size : {file_size}""")
    ###print(f"""File name : {filename}""")
    ###print(f"""File name length : {filename_length}""")
    ###print(f"""File MD5 Hash : {file_md5_hash}""")

    # Advance custor with file_md5_length
    cursor = cursor + file_md5_length
    
    # Extract the file data (after the filename)
    print(f"""Extracting data from {cursor} to {cursor + file_size}""")
    file_data = byte_array[cursor:cursor + file_size]
    calculated_md5 = hashlib.md5(file_data).hexdigest()
    if(calculated_md5 == file_md5_hash):
        print(f"Success!! Received and calculated MD5 hashes match : {calculated_md5}")
    else:
        print(f"Error!! MD5 mismatch with the received hash.")
        print(f"Received MD5 : {file_md5_hash}")
        print(f"Calculated MD5 : {calculated_md5}")
    
    if output_file is None:
        output_file = f"""received_{filename}"""

    # Write the data to the output file
    with open(output_file, "wb") as f:
        f.write(file_data)

    print(f"File saved to {output_file}")

# Example usage
start = datetime.datetime.now()
print(f"""Started decoding : {start}""")
input_video = sys.argv[1]  # your screen-recorded video
try:
    output_file = sys.argv[2]
except:
    output_file = None
binary_video_to_file(input_video, output_file)
end = datetime.datetime.now()
print(f"""Decoded in : {end - start}""")
