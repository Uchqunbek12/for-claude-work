/* s1_mba (toza versiya): ikki sonni aralashtiruvchi oddiy funksiya. */
unsigned int mix(unsigned int a, unsigned int b)
{
    unsigned int s = a + b;
    unsigned int d = a - b;
    return (s ^ d) | (a & 0xFFu);
}
