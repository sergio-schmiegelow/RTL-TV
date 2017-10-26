# RTL-TV

## What is it?
The purpose of this project is create a simple TV transmitter and receiver using SDR (Software Defined Radio).

There is a special version of the receiver for RTL-SDR dongles.

## Encoding format
The video encoding format is proprietary as follow:
 * Each frame contains a full image (there is no line sync)
 * The frame format is:
   * Header:
     * A sync sequence (24 bit “gold” code, to be easily detected by cross correlation);
     * A maximum pixel value level reference;
     * A minimum pixel value level reference.
   * The image pixel values serialized.

![alt text](https://raw.githubusercontent.com/sergio-schmiegelow/RTL-TV/master/frame_diagram.png "Encoding diagram")

The frames are upsampled and modulated in AM.

The frequencies and sample rates are currently hard coded.

## Files description
  * **radio_video.py**:  class for encode, decode, modulate and demodulate the frames.

  * **tx.py**  encodes frames from the webcam, modulates, and output the IQ samples (complex64) to stdout.

  * **rx.py**: receives the IQ samples (complex64) from stdin, demodulates, decodes and show the frames on the screen.
    * Interactive commands:
      * **p** : Pause video
      * **q** : Quit

  * **rtl_rx.py**: receives the IQ samples from a RTL-SDR dongle, demodulates, decodes and show the frames on the screen.

  * **unload_rtl_driver.sh**: unload the RTL-SDR driver to make it possible to access the dongle on Python (using the rtlsdr lib)

## Examples
### Simple loopback
```
python tx.py | python rx.py
```
### Receive from RTL-SDR dongle
```
python rtl_rx.py
```
### Send IQ samples to a gnuradio script
```
mkfifo <pipe file>
<run gnuradio script reading IQ samples from pipe file>
python tx.py|<pipe_file>
```
