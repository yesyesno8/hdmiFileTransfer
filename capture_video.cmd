taskkill /IM obs64.exe
set /p id=<count.txt
timeout /T 1 /nobreak &&  ffmpeg -f dshow -video_size 1280x720 -framerate 30 -i video="USB Video" output%id%.mp4
set /a id+=1
>count.txt echo %id%