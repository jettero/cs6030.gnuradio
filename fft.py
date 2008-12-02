#!/usr/bin/env python

import os, wx

from gnuradio import gr, audio
from gnuradio.eng_option import eng_option
from gnuradio.wxgui import stdgui2, fftsink2
from optparse import OptionParser

import os

sample_rate=48000

class app_top_block(stdgui2.std_top_block):
    def __init__(self, frame, panel, vbox, argv):
        stdgui2.std_top_block.__init__(self, frame, panel, vbox, argv)

        self.frame = frame
        self.panel = panel
        
        parser = OptionParser(option_class=eng_option)
        parser.add_option("", "--fft-size",      type="int",       default=512,  help="[default=%default]");
        parser.add_option("", "--fft-rate",      type="int",       default=30,    help="[default=%default]");
        parser.add_option("", "--ref-scale",     type="eng_float", default=1.0,   help="[default=%default]");
        parser.add_option("", "--ref-level",     type="int",       default=20,    help="[default=%default]");
        parser.add_option("", "--y-divs",        type="int",       default=12,    help="[default=%default]");
        parser.add_option("", "--y-per-div",     type="int",       default=10,    help="[default=%default]");
        parser.add_option("", "--baseband-freq", type="eng_float", default=0,     help="[default=%default]")
        parser.add_option("", "--input-file",    type="string",    default=None,  help="[default=%default]")

        (options, args) = parser.parse_args()

        if len(args) != 0:
            parser.print_help()
            raise SystemExit, 1

        using_wav=False
        if options.input_file and os.path.exists(options.input_file):
            self.wav = gr.wavfile_source( options.input_file, True )
            using_wav=True
        else:
            self.wav = audio.source(sample_rate, "", True)

      	self.f2c   = gr.float_to_complex()
        self.scope = fftsink2.fft_sink_c(panel, fft_size=options.fft_size,
                sample_rate=sample_rate, fft_rate=options.fft_rate, ref_scale=options.ref_scale,
                ref_level=options.ref_level, y_divs=options.y_divs, average=True,
                baseband_freq=options.baseband_freq, y_per_div=options.y_per_div)

      	self.connect((self.wav, 0), (self.f2c, 0))
      	self.connect((self.wav, 1), (self.f2c, 1))

        if using_wav:
            self.throttle = gr.throttle(gr.sizeof_gr_complex, sample_rate)
            self.connect(self.f2c, self.throttle, self.scope)
        else:
            self.connect((self.f2c, 0), (self.scope, 0))

        vbox.Add(self.scope.win, 10, wx.EXPAND)

def main ():
    app = stdgui2.stdapp(app_top_block, "FFT Wav Player", nstatus=1)
    app.MainLoop()

if __name__ == '__main__':
    main ()
