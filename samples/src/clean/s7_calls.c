/* s7_calls (toza versiya): ikki funksiya — yordamchi aylantirish va uni chaqiruvchi xesh. */
unsigned int rotl32(unsigned int x, unsigned int r)
{
    r &= 31u;
    return (x << r) | (x >> ((32u - r) & 31u));
}

unsigned int rot_hash(const unsigned char *data, unsigned int len)
{
    unsigned int h = 0x12345678u;
    unsigned int i;

    for (i = 0; i < len; i++)
        h = rotl32(h ^ data[i], 5u) + 0x6D2B79F5u;
    return h;
}
