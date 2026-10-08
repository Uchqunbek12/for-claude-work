/* s2_opaque (obfuskatsiyalangan): opaque predicate (shaffof bo'lmagan shart) usuli.
 *  - u*(u+1) har doim juft  -> shart har doim ROST;
 *  - kvadratning 4 ga bo'linishdagi qoldig'i hech qachon 2 bo'lmaydi -> shart har doim YOLG'ON.
 * Yolg'on tarmoqlardagi kod hech qachon bajarilmaydi (o'lik kod).
 */
int clamp(int x, int lo, int hi)
{
    unsigned int u = (unsigned int)x;
    unsigned int w = (unsigned int)hi;
    int r = x;

    if (((u * (u + 1u)) & 1u) == 0u) {
        if (x < lo)
            r = lo;
    } else {
        r = lo * 7 - hi;          /* o'lik kod */
    }
    if ((w * w) % 4u == 2u) {
        r = r ^ 0x5A5A;           /* o'lik kod */
        return r + 13;
    }
    if (((u * u + u) % 2u) == 0u && x >= lo && x > hi)
        r = hi;
    return r;
}
