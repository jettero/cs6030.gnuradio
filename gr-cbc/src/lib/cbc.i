%feature("autodoc", "1");		// generate python docstrings

%include "exception.i"
%import "gnuradio.i"			// the common stuff

%{
#include "gnuradio_swig_bug_workaround.h"	// mandatory bug fix
#include "cbc_blowfish_vbb.h"
#include <stdexcept>
#include <openssl/blowfish.h>
%}

// ----------------------------------------------------------------

/*
 * First arg is the package prefix.
 * Second arg is the name of the class minus the prefix.
 *
 * This does some behind-the-scenes magic so we can
 * access cbc_blowfish_vbb from python as cbc.blowfish_vbb
 */
GR_SWIG_BLOCK_MAGIC(cbc,blowfish_vbb);

cbc_blowfish_vbb_sptr cbc_make_blowfish_vbb(const char *civ, const char *ckey, bool dir);

class cbc_blowfish_vbb : public gr_block {
    private:
        cbc_blowfish_vbb(const char *civ, const char *ckey, bool dir);
};
