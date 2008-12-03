#ifndef INCLUDED_CBC_BLOWFISH_VBB_H
#define INCLUDED_CBC_BLOWFISH_VBB_H

#include <gr_block.h>
#include <openssl/blowfish.h>

class cbc_blowfish_vbb;

/*
 * We use boost::shared_ptr's instead of raw pointers for all access
 * to gr_blocks (and many other data structures).  The shared_ptr gets
 * us transparent reference counting, which greatly simplifies storage
 * management issues.  This is especially helpful in our hybrid
 * C++ / Python system.
 *
 * See http://www.boost.org/libs/smart_ptr/smart_ptr.htm
 *
 * As a convention, the _sptr suffix indicates a boost::shared_ptr
 */
typedef boost::shared_ptr<cbc_blowfish_vbb> cbc_blowfish_vbb_sptr;

/*!
 * \brief Return a shared_ptr to a new instance of cbc_blowfish_vbb.
 *
 * To avoid accidental use of raw pointers, cbc_blowfish_vbb's
 * constructor is private.  cbc_make_blowfish_vbb is the public
 * interface for creating new instances.
 */
cbc_blowfish_vbb_sptr cbc_make_blowfish_vbb(const char *civ, const char *ckey, bool dir);

/*!
 * \brief square a stream of bytes.
 * \ingroup block
 */
class cbc_blowfish_vbb : public gr_block {
    private:
        // The friend declaration allows cbc_make_blowfish_vbb to
        // access the private constructor.

        friend cbc_blowfish_vbb_sptr cbc_make_blowfish_vbb(const char *civ, const char *ckey, bool dir);

        cbc_blowfish_vbb(const char *civ, const char *ckey, bool dir); // private constructor

        BF_KEY key;
        char ivec[9];
        int direction;

    public:
        ~cbc_blowfish_vbb(); // public destructor

        // Where all the action really happens

        int general_work (int noutput_items,
                gr_vector_int &ninput_items,
                gr_vector_const_void_star &input_items,
                gr_vector_void_star &output_items);
};

#endif
