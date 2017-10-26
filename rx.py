#play video from stdib received IQ samples
import cv2
import radio_video
import numpy as np

#-----------------------------------------------------------
rv = radio_video.radioVideo()
sdr = RtlSdr()

#create openCV window and gain slider
cv2.namedWindow('Video')
cv2.createTrackbar('Ganho','Video',10,40,gainChange)

samplesToRead = firstPot2Bigger(rv.SAMPLES_PER_FRAME)
bytesToRead = samplesToRead * np.dtype('complex64').itemsize
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
