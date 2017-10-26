#play video from RTL-SDR received IQ samples
import cv2
import radio_video
from rtlsdr import RtlSdr
import math
#-----------------------------------------------------------
def firstPot2Bigger(x):
    '''Returns the first power of 2 greater than x'''
    return math.pow(2, math.ceil((math.log(x,2))))
#-----------------------------------------------------------
def gainChange(x):
    '''Gain slider callback'''
    global sdr
    print "ganho mudou para", x
    sdr.gain = x
#-----------------------------------------------------------
rv = radio_video.radioVideo()
sdr = RtlSdr()

# configure device
sdr.sample_rate = 1e6  # Hz
sdr.center_freq = 900e6     # Hz
sdr.gain = 30

#create openCV window and gain slider
cv2.namedWindow('Video')
cv2.createTrackbar('Ganho','Video',10,40,gainChange)

#RTL-SDR samples must be read in power of 2 sizes
samplesToRead = firstPot2Bigger(rv.SAMPLES_PER_FRAME)
pause = False
while True:
    iq = sdr.read_samples(samplesToRead)
    demodulated = rv.demodulateAM(iq[-rv.SAMPLES_PER_FRAME:])
    frame = rv.decodeStream(demodulated)
    if not pause:
        cv2.imshow('Video', frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):
        pause = not pause
