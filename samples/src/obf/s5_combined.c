/* s5_combined (obfuskatsiyalangan): bir nechta usul birgalikda:
 * flattening + MBA + opaque predicate + o'lik kod + kodlangan konstantalar.
 */
unsigned int checksum(unsigned int x, unsigned int n)
{
    unsigned int h = 0u, i = 0u, k = 0u, junk = 0u;
    unsigned int st = 0xA1u;

    while (1) {
        switch (st) {
        case 0xA1u:
            h = 0x7A1C3E55u ^ 0xFB00A390u;          /* = 2166136261 (kodlangan) */
            n = (n & 7u) + 1u;                      /* n % 8 + 1 */
            i = 0u;
            st = 0x1Fu;
            break;
        case 0x1Fu:
            st = (i < n) ? 0xC4u : 0x77u;
            break;
        case 0xC4u:
            k = (x >> ((i & 3u) << 3)) & 0xFFu;     /* 8*(i%4) */
            if (((i * i + i) & 1u) != 0u)           /* opaque: har doim yolg'on */
                junk = k * 0x1337u;                 /* o'lik kod */
            h = (h | k) - (h & k);                  /* h ^ k (MBA) */
            st = 0x3Bu;
            break;
        case 0x3Bu:
            h = h * (0x01000000u + 0x193u);         /* 16777619 (kodlangan) */
            junk ^= h;                              /* natijaga ta'sir qilmaydi */
            i = (i ^ 1u) + 2u * (i & 1u);           /* i + 1 (MBA) */
            st = 0x1Fu;
            break;
        case 0x77u:
            return h;
        default:
            st = 0xA1u;
            break;
        }
    }
}
