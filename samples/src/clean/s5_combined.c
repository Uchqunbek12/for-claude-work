/* s5_combined (toza versiya): FNV-1a uslubidagi nazorat yig'indisi (checksum). */
unsigned int checksum(unsigned int x, unsigned int n)
{
    unsigned int h = 2166136261u;
    unsigned int i;

    n = n % 8u + 1u;
    for (i = 0; i < n; i++) {
        h ^= (x >> (8u * (i % 4u))) & 0xFFu;
        h *= 16777619u;
    }
    return h;
}
