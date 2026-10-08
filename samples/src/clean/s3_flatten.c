/* s3_flatten (toza versiya): Yevklid algoritmi - EKUB (eng katta umumiy bo'luvchi). */
unsigned int gcd(unsigned int a, unsigned int b)
{
    while (b != 0u) {
        unsigned int t = a % b;
        a = b;
        b = t;
    }
    return a;
}
