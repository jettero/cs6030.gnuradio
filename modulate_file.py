#!/usr/bin/env python

import os, struct

from optparse import OptionParser
from gnuradio import gr, blks2, audio

from gnuradio.gr import firdes

verbose      = True
pkt_overhead = 4

class my_top_block(gr.top_block):
    def __init__(self, outputfile, options):
        gr.top_block.__init__(self)

        if options.dsp:
            self.dst = audio.sink( options.dsp_sample_rate )
        else:
            self.dst = gr.wavfile_sink(outputfile, 2, options.wav_sample_rate, 16)

        self.c_to_iq = gr.complex_to_float()
        self.connect( (self.c_to_iq, 0), (self.dst, 0))
        self.connect( (self.c_to_iq, 1), (self.dst, 1))

        # settings for the modulator: /usr/local/lib/python2.5/site-packages/gnuradio/blks2impl/gmsk.py

        self.modulator = blks2.gmsk_mod(samples_per_symbol=options.samples_per_symbol)
        self.pkt_queue = blks2.mod_pkts( modulator=self.modulator )

        if options.carrier_frequency == 0:
            self.mixer = self.pkt_queue
        else:
            self.mixer   = gr.multiply_vcc(1)
            self.carrier = gr.sig_source_c( options.carrier_sample_rate, gr.GR_SIN_WAVE, options.carrier_frequency, 1.0 )
            self.lowpass = gr.fir_filter_ccf(1, firdes.low_pass(1, 48000, 48000/(2*options.samples_per_symbol), 500, firdes.WIN_HAMMING, 6.76))
            self.connect(self.pkt_queue, self.lowpass, (self.mixer, 0) )
            self.connect(self.carrier,   (self.mixer, 1) )

        self.amp = gr.multiply_const_cc(1); self.amp.set_k(options.amp_amplitude)
        self.connect(self.mixer, self.amp, self.c_to_iq)

        if options.debug_wavs:
            from myblks import debugwav
            self._dpassw = debugwav("tx_passband", options)
            self._dprefw = debugwav("tx_prefband", options)
            self._dbasew = debugwav("tx_baseband", options)
            self.connect(self.amp, self._dpassw)
            self.connect(self.lowpass, self._dbasew)
            self.connect(self.pkt_queue, self._dprefw)

        if options.debug_files:
            self._dpassf = gr.file_sink(gr.sizeof_gr_complex*1, "debug_tx_passband.d_c")
            self._dpreff = gr.file_sink(gr.sizeof_gr_complex*1, "debug_tx_prefband.d_c")
            self._dbasef = gr.file_sink(gr.sizeof_gr_complex*1, "debug_tx_baseband.d_c")
            self.connect(self.amp, self._dpassf)
            self.connect(self.pkt_queue, self._dpreff)
            self.connect(self.lowpass, self._dbasef)

    def send_pkt(self, msg=""):
        self.pkt_queue.send_pkt(msg)

    def eof(self):
        self.send_pkt()
        self.pkt_queue.send_pkt(eof=True)

def make_packet(data, pktno, correct_size):
    header = struct.pack('!HH', pktno, len(data))
    packet = header + data

    if len(packet) < correct_size:
        packet += '\x00' * (correct_size - len(packet))

    if len(packet) != correct_size:
        raise RuntimeError, "INTERNAL ERROR: packet size(%d!=%d) is incorrect" % (len(packet), correct_size)

    return packet

def main(inputfile, outputfile, options):
    tb = my_top_block(outputfile, options)
    tb.start()

    carrier = make_packet("\xff" * (options.size - pkt_overhead), 0, options.size)

    for i in range(3):
        tb.send_pkt(carrier)

    file_header = "filename=%s; size=%d;" % (os.path.basename(inputfile), os.path.getsize(inputfile))

    if len(file_header) > options.size - pkt_overhead:
        raise SystemExit, "ERROR: packet size must be big enough to include file header (%d bytes in this case)" \
            % len(file_header) + pkt_overhead

    if verbose: print "pkt(1) -- %s" % file_header
    packet = make_packet(file_header, 1, options.size)
    for i in range(options.redundant_copies):
        tb.send_pkt(packet) # we send redundant_copies as a crappy kind of FEC

    pktno = 2
    f = open(inputfile)

    while True:
        data = f.read(options.size - pkt_overhead)
        if data:
            packet = make_packet(data, pktno, options.size)
            if verbose: print "pkt(%d)" % pktno
            for i in range(options.redundant_copies):
                tb.send_pkt(packet) # we send redundant_copies as a crappy kind of FEC
            pktno += 1

        else: break

    for i in range(3):
        tb.send_pkt(carrier)

    tb.eof()
    tb.wait()

if __name__ == '__main__':
    usage="%prog: [options] inputfile [outputfile|--dsp]"
    parser = OptionParser(conflict_handler="resolve")

    parser.add_option("-q", "--quiet", action="store_false", dest="verbose", default=False, help="quiet? [default: False]")
    parser.add_option("-v", "--verbose", action="store_true", default=True, help="verbose? [default: %default]")
    parser.add_option("-w", "--wav-sample-rate", type="int", default=48000, help="wav-file sample rate [default: %default Hz]") 
    parser.add_option("-z", "--carrier-sample-rate", type="int", default=48000, help="carrier sample rate [default: %default Hz]") 
    parser.add_option("-c", "--carrier-frequency",   type="int", default=7001, help="carrier wave frequency [default: %default Hz]") 
    parser.add_option("-a", "--amp-amplitude", type="float", default=0.1, help="amplitude on the amplifier [default=%default]")
    parser.add_option("-s", "--size", type="int", default=400, help="set packet size [default=%default Bytes]")
    parser.add_option("-f", "--redundant-copies", type="int", default=2, help="number of copies of each data packet to send (-f 1 for no-copies, -f 0 prevents sending any data) [default=%default]")
    parser.add_option("-z", "--samples-per-symbol", type="int", default=4, help="samples per symbol [default=%default]")

    parser.add_option("-d", "--dsp", action="store_true", default=False, help="use soundcard instead of wav file [default: False]")
    parser.add_option("-r", "--dsp-sample-rate", type="int", default=48000, help="soundcard sample rate [default: %default Hz]") 

    parser.add_option("", "--debug-wavs", action="store_true", default=False, help="dump received passband and baseband signals to wav files [default: False]")
    parser.add_option("", "--debug-files", action="store_true", default=False, help="dump received passband and baseband signals to binary files [default: False]")

    (options, args) = parser.parse_args()

    outputfile = "n/a"
    if options.dsp:
        if len(args) != 1:
            parser.print_help()
            raise SystemExit, "ERROR: one argument required"
    else:
        if len(args) != 2:
            parser.print_help()
            raise SystemExit, "ERROR: two arguments required"
        outputfile = args[1]

    inputfile = args[0]
    verbose   = options.verbose

    if not os.path.exists(inputfile):
        parser.print_help()
        raise SystemExit, "ERROR: input file must exist"

    try:
        main(inputfile, outputfile, options)

    except KeyboardInterrupt:
        pass
