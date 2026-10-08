/* s3_flatten (obfuskatsiyalangan): control-flow flattening (boshqaruv oqimini tekislash).
 * Barcha bloklar bitta while(1) + switch ichiga joylangan; keyingi blok
 * "state" o'zgaruvchisi orqali tanlanadi, shuning uchun asl tsikl ko'rinmaydi.
 */
unsigned int gcd(unsigned int a, unsigned int b)
{
    unsigned int t = 0u;
    unsigned int state = 0x3C1Fu;

    while (1) {
        switch (state) {
        case 0x3C1Fu:                     /* tsikl sharti */
            state = (b != 0u) ? 0x91A2u : 0x5E07u;
            break;
        case 0x91A2u:                     /* t = a % b */
            t = a % b;
            state = 0x2B6Du;
            break;
        case 0x2B6Du:                     /* a = b; b = t */
            a = b;
            b = t;
            state = 0x3C1Fu;
            break;
        case 0x5E07u:                     /* chiqish */
            return a;
        default:
            state = 0x3C1Fu;
            break;
        }
    }
}
