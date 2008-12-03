#!/usr/bin/env python

from gnuradio import gr, gr_unittest
import cbc

class qa_cbc(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block ()

    def tearDown(self):
        self.tb = None

    def test_001_blowfish_vbb(self):
        global encrypted_data, src_data

        src_data = tuple(ord(x) for x in "12345678");
        expected_result = tuple(int(x, 16) for x in "a4 2e 1a 10 fa b3 7e a0".split())

        src1 = gr.vector_source_b(src_data)
        src2 = gr.stream_to_vector(gr.sizeof_char*1, 8)

        cbcb = cbc.blowfish_vbb("MY*IV000", "my key", True)

        dst1 = gr.vector_to_stream(gr.sizeof_char*1, 8)
        dst2 = gr.vector_sink_b()

        self.tb.connect(src1, src2, cbcb)
        self.tb.connect(cbcb, dst1, dst2)

        self.tb.run()
        encrypted_data = dst2.data()

        self.assertEqual(expected_result, encrypted_data)

    def test_005_blowfish_vbb(self):
        global encrypted_data, src_data

        src1 = gr.vector_source_b(encrypted_data)
        src2 = gr.stream_to_vector(gr.sizeof_char*1, 8)

        cbcb = cbc.blowfish_vbb("MY*IV000", "my key", False)

        dst1 = gr.vector_to_stream(gr.sizeof_char*1, 8)
        dst2 = gr.vector_sink_b()

        self.tb.connect(src1, src2, cbcb)
        self.tb.connect(cbcb, dst1, dst2)

        self.tb.run()
        result_data = dst2.data()

        self.assertEqual(src_data, result_data)

if __name__ == '__main__':
    gr_unittest.main ()
