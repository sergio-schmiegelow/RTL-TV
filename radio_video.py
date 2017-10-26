#Glossary
#Image: grayscale bitmap of resized webcam image
#Frame: sync pattern + level reference + image

#frame format:
# -sync pattern: sequence of bits (self.CODE) with values of 0.0 and 1.0
# -level reference:
#   -half image line long pixels with min pixel value
#   -half image line long pixels with max pixel value
# -image: pixels values normalized on range [0.0 : 1.0]

import cv2
import numpy as np
import scipy.signal as signal
import scipy.ndimage as ndi
import scipy.misc as misc
import math

#-------------------------------------------------------------------------
class radioVideo:
    def __init__(self):
        self.WIDTH = 200  #number of image columns to encode
        self.HEIGHT = 200 #number of image lines to encode
        self.PLAY_SHAPE = (480, 640) #image size to play on screen
        self.CODE = '001010110110010011100011' #sync code
        self.PIXELS_PER_IMAGE = self.HEIGHT * self.WIDTH #number of pixel on the encoded image
        self.PIXELS_PER_FRAME = (self.HEIGHT + 1) * self.WIDTH + len(self.CODE) #number of pixels per frame
        self.SAMPLES_PER_PIXEL = 2 #number of IQ samples per pixel
        self.SAMPLES_PER_FRAME = self.PIXELS_PER_FRAME * self.SAMPLES_PER_PIXEL #number of IQ samples per frame
        self.IMAGE_SHAPE = (self.HEIGHT, self.WIDTH)
        self.MAX_PIXEL_LEVEL = 255 #maximum grayscale pixel value from webcam
        self.createSync()
        self.createTxBuffer()
        self.videoCapture = None #openCV vide capture handle
        self.filterSize = 1 #size of FIR filter size on resampling
        self.freq = None #carrier frequency
        self.sampleRate = None #IQ sample rate
        cv2.namedWindow('Video') #openCV window
#-------------------------------------------------------------------------
    def createSync(self):
        '''Create buffer with sync pattern'''
        syncPixels = []
        syncPattern = []
        for chip in self.CODE:
            if chip == '1':
                syncPixels.append(self.MAX_PIXEL_LEVEL)
                syncPattern.append(1)
            else:
                syncPixels.append(0)
                syncPattern.append(-1)
        self.syncPixels = np.array(syncPixels) # 0/1 format for encoding
        self.syncPattern = np.array(syncPattern) # -1/1 format for sync correlation
        self.paddedSyncPattern = np.zeros(self.PIXELS_PER_FRAME)
        self.paddedSyncPattern[:len(self.syncPattern)] = self.syncPattern #sync padded with zeros to fit frame size
        self.conjFfttPaddedSyncPattern = np.conj(np.fft.fft(self.paddedSyncPattern)) #conjugated FFT of the padded sync pattern for correlation
#-------------------------------------------------------------------------
    def createTxBuffer(self):
        '''Create base tx buffer'''
        self.maxRefLocation = len(self.syncPixels) #location of the max level reference
        self.minRefLocation = self.maxRefLocation + self.WIDTH / 2 #location of the min level reference
        self.imageLocation = len(self.syncPixels) + self.WIDTH #location of the image
        self.txBuffer = np.zeros(self.PIXELS_PER_FRAME)
        self.txBuffer[:self.maxRefLocation] = self.syncPixels
        self.txBuffer[self.maxRefLocation : self.imageLocation] = np.concatenate((np.ones(self.WIDTH / 2 ) * self.MAX_PIXEL_LEVEL, np.zeros(self.WIDTH / 2)))
#-------------------------------------------------------------------------
    def encodeFrame(self):
        '''Encode a frame'''
        #start video capture if necessary
        if self.videoCapture == None:
            self.videoCapture = cv2.VideoCapture(-1)
        #capture frame
        ret, frame = self.videoCapture.read()
        #convert to grayscale and target size
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #resize frame to encoding size
        if gray.shape != self.IMAGE_SHAPE:
            gray = misc.imresize(gray, self.IMAGE_SHAPE, interp = 'nearest')
        #serialize pixels
        grayLinear = gray.reshape((self.PIXELS_PER_IMAGE))
        #insert pixels on TX buffer
        self.txBuffer[self.imageLocation : self.PIXELS_PER_FRAME] = grayLinear
        #resample to IQ rate
        resampled = np.repeat(self.txBuffer, self.SAMPLES_PER_PIXEL)
        #normalize to [0.0 : 1.0] range
        return (resampled / float(np.max(self.txBuffer))).astype('float32')
#-------------------------------------------------------------------------
    def decodeStream(self, data):
        '''Decode a frame from demodulated data'''
        #decimate to pixel rate
        data = signal.decimate(data, self.SAMPLES_PER_PIXEL, n = self.filterSize)
        #find the sync location by FFT cross correlation method
        fftData = np.fft.fft(data)
        syncLocation = np.argmax(np.real(np.fft.ifft(self.conjFfttPaddedSyncPattern * fftData)))
        #roll the data to put the sync on the beginning (yes, you probably will get two different imagems mixed, but for simplification it is acceptable)
        data = np.roll(data, -syncLocation)
        #get the reference levels
        maxRef = np.average(data[self.maxRefLocation : self.minRefLocation])
        minRef = np.average(data[self.minRefLocation : self.imageLocation])
        #extract the image pixels
        imageData = data[self.imageLocation : self.PIXELS_PER_FRAME]
        #recover the original levels using the reference levels
        grayLinear = (imageData - minRef) / (maxRef - minRef) * self.MAX_PIXEL_LEVEL
        #reshape the pixels to  a 2D image
        frame = grayLinear.reshape(self.IMAGE_SHAPE).astype('uint8')
        #resize the image to the play size
        resizedFrame = misc.imresize(frame, self.PLAY_SHAPE, interp = 'nearest')
        return resizedFrame
#-------------------------------------------------------------------------
    def modulateAM(self, encoded, freq, sampleRate):
        '''Modulate the frame in AM'''
        #Create the carrier if necessary
        if any((self.freq is None,
                self.freq != freq,
                self.sampleRate is None,
                self.sampleRate != sampleRate)):
            self.freq = freq
            self.sampleRate = sampleRate
            omega = (freq * 2 * math.pi) / sampleRate
            self.carrier = np.exp(np.array(range(len(encoded))) * omega * 1j)
        #modulate AM by multiplication
        return np.multiply(encoded, self.carrier)
#-------------------------------------------------------------------------
    def demodulateAM(self, modulated):
        '''Demodulate AM'''
        return np.absolute(modulated - np.mean(modulated))
