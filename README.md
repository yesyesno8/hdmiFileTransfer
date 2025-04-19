# hdmiFileTransfer
Send files with HDMI (Proof of Concept)

A PoC python script that encodes a file into a 720p 5fps QR code video, uses a HDMI capture device to transmit video via HDMI, and decodes the video on the other side.

![Sketch](https://raw.githubusercontent.com/yesyesno8/hdmiFileTransfer/refs/heads/main/sketch.png)

## Usage
### encoder.py (On Source PC)
```
python encoder.py <inputfile.zip> <output.mkv>
```
### decoder.py (On Destination PC)
```
python decoder.py <output.mp4>
```
The filename will be restored from headers of the video. Or
```
python decoder.py <output.mp4> <outputfile.zip>
```
The filename will be forced to be <outputfile.zip>

### (Optional) capture_video.cmd (on Destination PC)
To programmatically stop OBS and start ffmpeg (I needed it to apply a timeout to make sure HDMI Capture USB usage is freed by OBS)

## Prerequisites
On Source PC you must have :
- Python with Numpy and OpenCV
- VLC

On destination PC you must have :
- Python with Numpy and OpenCV
- ffmpeg
- (Optional) OBS Studio

## Important : Rename the HDMI EDID
A HDMI capture device is used to transmit the video via HDMI.
The video is played (VLC for example) on the source PC.
As a prerequisite, modify the HDMI capture firmware to replace EDID to appear as a regular PC Monitor such as a Dell S2721HN or whatever.
Choose any EDID from this list https://github.com/bsdhw/EDID and modify the HDMI capture firmware.
If you have the HDMI Capture device based on MacroSilicon MS2130 or MS2109 chip, I used MS21XX&91XXDownloadTool_1.7.0_BUILD20221024.exe to dump the current firmware, WinHex to modify the firmware, and again the MS21XX tool to flash the modified firmware.
You can use tutorials on the Internet for this.
TEST IT by going to Settings > System > Display > Advanced Display and make sure the HDMI appears as a Dell S2721HN.

The HDMI Capture is plugged with USB on the destination PC (personal fully-controlled PC) and HDMI on the source PC.
Make sure you remove overlay screen options from VLC to make it easy.
Go to Tools > Preferences and untick:
-	Enabled On Screen Display
-	Show media title on Video Start


This is needed because at this first version of the script, data is written in raw (1px = 1 bit), without any redundancy nor error correction.
On destination PC, have these tools ready:
-	ffmpeg: used to capture the incoming video of USB HDMI Capture
-	Python with numpy and opencv-python
-	(Optional): OBS Studio to preview the USB HDMI input (to make sure your VLC is in full screen, without overlays etc, video is paused at the start. OBS must be closed when recording begins)
Note: Don’t use OBS to capture the incoming video as it distorts the video and renders the content unusable to decode. Even when ticking “Lossless Quality” there’re still problems.

## Encoder
The encoder script does the following :
- a checkerboard frame to signal the start of the video
- calculates number of frames (in 720p minus border) needed, according to the transmitted file size
- a first frame containing the file name, the file size, and binary data stream of the file encoded in bits (0s to black pixels, 1s to white pixels)
- saves all to a video file

## Decoder
The decoder script does the following :
- resize the frames to 720p (in case capture was done in a higher resolution)
- detect the begin market
- retrieves the file name, file size, and reads the binary stream pixel by pixel, frame by frame, and save it to a file


## Procedure:
-	Compress all the files you need in a zip file on Source PC (split it into chucks of 200MB if needed and transmit every chunk separately)
-	Run the encoder.py to generate an output.mkv video of the file with the command:
```
python encoder.py inputfile.zip output.mkv
```
-	Plug the HDMI device, HDMI end into Source PC, USB end into Destination PC.
-	On destination PC: Open OBS with HDMI Capture as input to display the incoming signal
-	On source PC: Open the output.mkv with VLC, pause with Space bar, go back to beginning of video with arrow left keyboard key, move the VLC window to the “second monitor”, put the video full screen by double click on the video, move the mouse cursor out of the “second monitor”, and wait for all overlays to disappear.
-	On destination PC: 
Automatic: run the capture_video.cmd (stop OBS and open the ffmpeg capture)
Manual: Stop OBS Studio and launch ffmpeg capture (change video param to the USB device name, “USB Video” is the device name of the HDMI Capture device I bought)
-	Wait until ffmpeg capture counters begin counting such as:
frame=	16	fps=6.2	q=29.0	size=	512KiB	time=00:00:00.46	bitrate=4494.7kbits/s	speed=0.182x
-	On Source PC: resume VLC by clicking Space bar
-	On destination PC: When the video transmission finishes, click ‘q’ to exit ffmpeg
-	On destination PC: run the python decoder script :
```
python decoder.py <recorded_output.mp4>
```
-	If all is good your file is written into destination PC
-	You can checksum file on both Source and Destination PC with the command:
```
certutil -hashfile inputfile.zip MD5
```
and verify that the hash matches.

## Advantages:
-	Circumvent Bitlocker (file content is read on Source PC)
-	No network whatsoever needed (recommended: close VPN and disconnect WiFi/cable before transferring files)
-	DLP usually concentrates on suspicious network and email activities, but so far don't suspect that a HDMI second display to be the data leakage sink.
-	Permanent screen recording needs a ton of hard disk space. If you suspect that screen of source PC is recorded, you can exhaust it with playing legitimate videos for hours and hours before actually sending the real data.

## Cautions:
- This software is provided for educational purposes only. Use at your own risk. The author is not responsible for any misuse or damage caused by this software.
-	Make sure some kind of permanent screen capture software is not running on your source PC
-	Make sure VPN and WiFi or any kind of IP network is disabled on Source PC
-	The tool is very fragile for now, make sure no overlays are displayed in VLC in source PC
-	If you got a big file size, possible causes are:
Mismatch on screen resolution (did you capture with 1080p where the display is only configured for 720p?)

Did overlay appeared at some point? If so, the whole process should be restarted

Did you properly exit ffmpeg by using ‘q’ and not Ctrl-C ?

-	Numpy memoryarrayerror: you are encoding a file with a size larger than free RAM divided by 8 on Source PC. Split it into additional chucks
-	Still having problem? debug the output frames by enabling commented out outputs to see what’s the problem.

## Limitations/enhancements :
Currently, the encoder and decoder uses a 720p at 5fps with 10px borders so it's (1280 - 2 * 10) * (720 - 2 * 10) = 882 000 px

882 000 px corresponds to 882 000 bits which is 110KB, with 5 FPS the transmission bandwidth is ~ 550KB/s or 4.4Mbps

This calculus doesn't take into consideration encoding, decoding, stop, resume and repeat if failure durations.

Surely this can be enhanced but for my use case it's enough to send 1 or 2 GB of data with HDMI in a reasonable amount of time.

Frame size and Frame rate can be enhanced but needs further testing to make sure transmission remains stable.

So far, not supporting distortions (overlay from VLC for example) or a lag in source video player
Don't support synchronized file streaming. The file transmission is unfortunately send in a serialized way and steps must be executed in the specified order. (Encode video, then play/capture video, then decode video)
