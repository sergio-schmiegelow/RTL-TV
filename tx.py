#Output the IQ samples to sdtout
import radio_video
import numpy as np
import time
import sys

rv = radio_video.radioVideo()
while True:
    encoded = rv.encodeFrame()
    modulated = rv.modulateAM(encoded, 100e3, 1e6)
    sys.stdout.write(modulated.astype('complex64'))
