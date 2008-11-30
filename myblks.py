#!/usr/bin/env python

from gnuradio import gr, blks2

class debugwav(gr.hier_block2):
    def __init__(self, name, options):
        gr.hier_block2.__init__( self, "debugger: " + name,
            gr.io_signature(1, 1, gr.sizeof_gr_complex), # input signature
            gr.io_signature(0, 0, 0*0), # output signature
        )

        fname = "debug_" + name + ".wav"

        self.c_to_iq = gr.complex_to_float()
        self.wavdump = gr.wavfile_sink(fname, 2, options.wav_sample_rate, 16)

        if options.verbose: print "writing a complex stream to file: %s" % fname

        self.connect( self, self.c_to_iq )
        self.connect( (self.c_to_iq, 0), (self.wavdump, 0))
        self.connect( (self.c_to_iq, 1), (self.wavdump, 1))
