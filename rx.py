#play video from stdib received IQ samples
import cv2
import radio_video
import numpy as np
import sys

#-----------------------------------------------------------
rv = radio_video.radioVideo()

#create openCV window
cv2.namedWindow('Video')

bytesToRead = rv.SAMPLES_PER_FRAME * np.dtype('complex64').itemsize
pause = False
while True:
    dataBytes = sys.stdin.read(bytesToRead)
    iq = np.frombuffer(dataBytes, dtype = 'complex64')
    demodulated = rv.demodulateAM(iq)
    frame = rv.decodeStream(demodulated)
    if not pause:
        cv2.imshow('Video', frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):
        pause = not pause
