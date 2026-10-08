/* s6_buffer (obfuskatsiyalangan): flattening + MBA + opaque predicate + o'lik kod.
 *   x ^ k        ->  (x | k) - (x & k)
 *   k * 5 + 1    ->  ((k << 2) ^ k) + 2 * ((k << 2) & k) + 1
 */
void xor_stream(unsigned char *buf, unsigned int len, unsigned char key)
{
    unsigned int i = 0u, st = 0x6Au, waste = 0u;
    unsigned int k = key;

    while (1) {
        switch (st) {
        case 0x6Au:
            st = (i < len) ? 0x13u : 0x5Cu;
            break;
        case 0x13u:
            buf[i] = (unsigned char)((buf[i] | k) - (buf[i] & k));
            if (((i * i + i) & 1u) != 0u)          /* opaque: har doim yolg'on */
                waste = buf[i] * 3u;                /* o'lik kod */
            st = 0x27u;
            break;
        case 0x27u:
            k = (((k << 2) ^ k) + 2u * ((k << 2) & k) + 1u) & 0xFFu;
            waste ^= k;                              /* natijaga ta'sir qilmaydi */
            i = (i ^ 1u) + 2u * (i & 1u);            /* i + 1 */
            st = 0x6Au;
            break;
        case 0x5Cu:
            return;
        default:
            st = 0x6Au;
            break;
        }
    }
}
