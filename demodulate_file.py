#!/usr/bin/env python

import os, struct, re, time

from optparse import OptionParser
from gnuradio import gr, blks2, audio

verbose      = True
pkt_overhead = 4

class my_top_block(gr.top_block):
    def __init__(self, inputfile, callback, options):
        gr.top_block.__init__(self)

        # settings for the demodulator: /usr/local/lib/python2.5/site-packages/gnuradio/blks2impl/gmsk.py
        # settings for the demodulator: /usr/local/lib/python2.5/site-packages/gnuradio/blks2impl/pkt.py

        if options.dsp:
            self.src = audio.source(options.dsp_sample_rate, "", True)
        else:
            self.src = gr.wavfile_source( inputfile, False )

        self.iq_to_c = gr.float_to_complex()
        if options.dsp and options.wait:
            samples = options.dsp_sample_rate * options.wait
            self._head0 = gr.head(gr.sizeof_float, samples)
            self._head1 = gr.head(gr.sizeof_float, samples)
            self.connect( (self.src, 0), self._head0, (self.iq_to_c, 0) )
            self.connect( (self.src, 1), self._head1, (self.iq_to_c, 1) )
            if verbose: print "installed %d second head filter on dsp (%d samples at %d sps)" % (options.wait, samples, options.dsp_sample_rate)
        else:
            self.connect( (self.src, 0), (self.iq_to_c, 0) )
            self.connect( (self.src, 1), (self.iq_to_c, 1) )

        if options.modulator == 'gmsk':
            if verbose: print "demodulating with GMSK"
            self.demodulator = blks2.gmsk_demod()

      # elif options.modulator == 'qam16':
      #     if verbose: print "demodulating with QAM16"
      #     self.demodulator = blks2.qam16_demod()

        else:
            raise SystemExit, "ERROR: modulation option '%s' invalid" % options.modulator

        self.pkt_queue = blks2.demod_pkts( demodulator=self.demodulator, callback=callback, threshold=options.threshold )

        if options.carrier_frequency == 0:
            self.mixer = self.iq_to_c
        else:
            self.carrier  = gr.sig_source_c( options.carrier_sample_rate, gr.GR_SIN_WAVE, - options.carrier_frequency, 1.0 )
            self.mixer    = gr.multiply_vcc(1)
            self.connect(self.iq_to_c, (self.mixer, 0) )
            self.connect(self.carrier, (self.mixer, 1) )

        self.amp = gr.multiply_const_cc(1); self.amp.set_k(options.amp_amplitude)
        self.connect(self.mixer, self.amp, self.pkt_queue)

        if options.debug_wavs:
            from myblks import debugwav
            self._dpass = debugwav("rx_passband", options)
            self._dbase = debugwav("rx_baseband", options)
            self.connect(self.iq_to_c, self._dpass)
            self.connect(self.mixer,   self._dbase)

        if options.debug_files:
            self._dpassf = gr.file_sink(gr.sizeof_gr_complex*1, "debug_rx_passband.d_c")
            self._dbasef = gr.file_sink(gr.sizeof_gr_complex*1, "debug_rx_baseband.d_c")
            self.connect(self.iq_to_c, self._dpassf)
            self.connect(self.mixer,   self._dbasef)

def rx(ok, payload):
    global infile, lpktno, filesz, f, header_re, crrno, ofilesz, ctime

    (pktno, size) = struct.unpack('!HH', payload[0:4])
    payload = payload[4:]

    if ok: # ok is the result of a crc32 check in pkt_utils
        if size > len(payload):
            print "WARNING: size of data part is bigger than data block (%d>%d)" % (size, len(payload))

        if pktno>0:
            if infile:
                if pktno == lpktno:
                    pass
                else:
                    if verbose: print "pktno: %d; remaining: %d; this-sz: %d;" % (pktno, filesz, size)
                    f.write(payload[0:size])
                    filesz -= size
                    lpktno = pktno
                    if filesz <= 0:
                        if filesz < 0:
                            print "WARNING: received more file than expected... difference: %d" % filesz
                        infile = False
                        f.close()
                        if verbose:
                            dt  = (time.time() - ctime)
                            bps = ofilesz / dt
                            print "file.close(); %d/%f = %f bps" % (ofilesz, dt, bps)
            else:
                m = header_re.match(payload)
                if m:
                    fname = "test_" + m.group(1)
                    infile = True
                    f = open(fname, "w")
                    ofilesz = filesz = int(m.group(2))
                    ctime = time.time()
                    lpktno = 1
                    if verbose: print "pktno: %d; fname: %s; fsize: %d; this-sz: %d;" % (pktno, fname, filesz, size)

                else:
                    if lpktno == pktno:
                        pass
                    else:
                        print "WARNING: received file chunk while not receiving a file pktno=%d; size=%d" % (pktno, size)
        else:
            global errno
            if verbose: print "-carrier packet (%d)-" % crrno
            crrno += 1

    else:
        if verbose:
            global errno
            print "-recv error (%d)-" % errno
            errno += 1


def main(inputfile, options):
    global infile, lpktno, filesz, f, header_re, errno, crrno
    header_re = re.compile("filename=(.+?); size=([0-9]+);")
    infile = False
    lpktno = 0
    errno = 0
    crrno = 0

    tb = my_top_block(inputfile, rx, options)
    tb.run()

if __name__ == '__main__':
    usage="%prog: [options] inputfile"
    parser = OptionParser(conflict_handler="resolve")

    parser.add_option("-q", "--quiet", action="store_false", dest="verbose", default=False, help="quiet? [default: False]")
    parser.add_option("-v", "--verbose", action="store_true", default=True, help="verbose? [default: %default]")
    parser.add_option("-w", "--wav-sample-rate", type="int", default=48000, help="wav-file sample rate [default: %default Hz]") 
    parser.add_option("",   "--carrier-sample-rate", type="int", default=48000, help="carrier sample rate [default: %default Hz]") 
    parser.add_option("-c", "--carrier-frequency",   type="int", default=7001, help="carrier wave frequency [default: %default Hz]") 
    parser.add_option("-s", "--size", type="int", default=400, help="set packet size [default=%default Bytes]")
    parser.add_option("-a", "--amp-amplitude", type="float", default=1.0, help="amplitude on the amplifier [default=%default]")
    parser.add_option("-t", "--threshold", type="int", default=12, help="detect frame header with up to threshold bits wrong [default=%default]")

    parser.add_option("-d", "--dsp", action="store_true", default=False, help="use soundcard instead of wav file [default: False]")
    parser.add_option("-r", "--dsp-sample-rate", type="int", default=48000, help="soundcard sample rate [default: %default Hz]") 
    parser.add_option("-w", "--wait", type="int", default=None, help="when on dsp, accept this many seconds worth of audio or give up and exit. [default=%default]")

    parser.add_option("", "--debug-wavs", action="store_true", default=False, help="dump received passband and converted baseband signals to wav files [default: False]")
    parser.add_option("", "--debug-files", action="store_true", default=False, help="dump received passband and baseband signals to binary files [default: False]")

    parser.add_option("-m", "--modulator", type="string", default='gmsk', help="modulator choices are currently limited to 'gmsk' or 'qam16' [default: %default]") 

    (options, args) = parser.parse_args()

    inputfile = None
    if not options.dsp:
        if len(args) != 1:
            parser.print_help()
            raise SystemExit, "ERROR: one argument required"

        inputfile = args[0]

        if not os.path.exists(inputfile):
            parser.print_help()
            raise SystemExit, "ERROR: input file must exist"

    verbose = options.verbose

    try:
        main(inputfile, options)

    except KeyboardInterrupt:
        pass
