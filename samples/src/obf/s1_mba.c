/* s1_mba (obfuskatsiyalangan): MBA (Mixed Boolean-Arithmetic) usuli.
 * Har bir oddiy amal ekvivalent, lekin murakkab ifoda bilan almashtirilgan:
 *   a + b  ->  (a ^ b) + 2*(a & b)
 *   a - b  ->  (a ^ b) - 2*(~a & b)
 *   x ^ y  ->  (x | y) - (x & y)
 *   x | y  ->  (x ^ y) + (x & y)
 */
unsigned int mix(unsigned int a, unsigned int b)
{
    unsigned int s = (a ^ b) + 2u * (a & b);
    unsigned int d = (a ^ b) - 2u * (~a & b);
    unsigned int x = (s | d) - (s & d);
    unsigned int m = a & 0xFFu;
    return (x ^ m) + (x & m);
}
