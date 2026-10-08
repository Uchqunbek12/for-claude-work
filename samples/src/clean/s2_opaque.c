/* s2_opaque (toza versiya): x ni [lo, hi] oralig'iga cheklash. */
int clamp(int x, int lo, int hi)
{
    if (x < lo)
        return lo;
    if (x > hi)
        return hi;
    return x;
}
