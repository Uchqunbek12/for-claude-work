/* s7_calls (obfuskatsiyalangan): yordamchida MBA, asosiy funksiyada flattening,
 * opaque predicate va kodlangan konstantalar.
 *   a | b  ->  (a ^ b) + (a & b)
 */
unsigned int rotl32(unsigned int x, unsigned int r)
{
    unsigned int a, b;

    r &= 31u;
    a = x << r;
    b = x >> ((32u - r) & 31u);
    return (a ^ b) + (a & b);
}

unsigned int rot_hash(const unsigned char *data, unsigned int len)
{
    unsigned int h = 0u, i = 0u, st = 0xB1u;

    while (1) {
        switch (st) {
        case 0xB1u:
            h = 0x4A1F2C3Du ^ 0x582B7A45u;          /* = 0x12345678 */
            i = 0u;
            st = 0x0Eu;
            break;
        case 0x0Eu:
            st = (i < len) ? 0x77u : 0xC9u;
            break;
        case 0x77u:
            if ((((len * len) % 4u) == 2u))         /* opaque: har doim yolg'on */
                h = h * 31u;                         /* o'lik tarmoq */
            h = rotl32((h | data[i]) - (h & data[i]), 5u) + (0x6D2B0000u + 0x79F5u);
            i = i + 1u;
            st = 0x0Eu;
            break;
        case 0xC9u:
            return h;
        default:
            st = 0xB1u;
            break;
        }
    }
}
