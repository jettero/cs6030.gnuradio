
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <cbc_blowfish_vbb.h>
#include <gr_io_signature.h>

#define item_size  ( sizeof(char) )
#define block_size 8

cbc_blowfish_vbb_sptr cbc_make_blowfish_vbb(const char *civ, const char *ckey, bool dir) {
    return cbc_blowfish_vbb_sptr (new cbc_blowfish_vbb(civ, ckey, dir));
}

cbc_blowfish_vbb::cbc_blowfish_vbb(const char *civ, const char *ckey, bool dir) : gr_block("blowfish_vbb",
	      gr_make_io_signature( 1,1, item_size*block_size ),
	      gr_make_io_signature( 1,1, item_size*block_size )) {

    BF_set_key(&key, strlen(ckey), (const unsigned char *) ckey);
    strncpy(ivec, civ, 8);
    direction = dir ? BF_ENCRYPT : BF_DECRYPT;
}

cbc_blowfish_vbb::~cbc_blowfish_vbb() {
}

int cbc_blowfish_vbb::general_work (int noutput_items,
			       gr_vector_int &ninput_items,
			       gr_vector_const_void_star &input_items,
			       gr_vector_void_star &output_items) {

    const unsigned char *in = (const unsigned char *) input_items[0];
    unsigned char *out = (char unsigned *) output_items[0];

    BF_cbc_encrypt(in, out, block_size, &key, (char unsigned *) ivec, direction);

    // debug // for (int i=0; i<block_size; i++)
    // debug //     printf("in[%02d] = %03d; out[%02d] = %03d\n", i, in[i], i, out[i]);

        /* 
        ** BF_cbc_encrypt(const unsigned char *in, unsigned char *out,
        **                   long length, BF_KEY *schedule, unsigned char *ivec, int enc);
        **
        ** BF_cbc_encrypt() is the Cipher Block Chaining function for Blowfish. It
        ** encrypts or decrypts the 64 bits chunks of in using the key schedule,
        ** putting the result in out. enc decides if encryption (BF_ENCRYPT) or
        ** decryption (BF_DECRYPT) shall be performed. ivec must point at an 8 byte
        ** long initialization vector. 
        */

    // Tell runtime system how many input items we consumed on
    // each input stream.
    consume_each(noutput_items);

    // Tell runtime system how many output items we produced.
    return noutput_items;
}
