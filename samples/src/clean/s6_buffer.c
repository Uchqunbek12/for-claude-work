/* s6_buffer (toza versiya): bufer ustida aylanma XOR (oddiy oqimli kodlash).
 * Har bir baytga kalit XOR qilinadi, kalit esa har qadamda o'zgaradi. */
void xor_stream(unsigned char *buf, unsigned int len, unsigned char key)
{
    unsigned int i;

    for (i = 0; i < len; i++) {
        buf[i] ^= key;
        key = (unsigned char)(key * 5u + 1u);
    }
}
