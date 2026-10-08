/* s4_strings (obfuskatsiyalangan): string encoding (satrni kodlash).
 * Matn dasturda ochiq ko'rinishda saqlanmaydi: har bir bayt 0x5C kaliti bilan
 * XOR qilingan va faqat ishlash paytida dekodlanadi.
 */
static const unsigned char ENC[] = { 0x14, 0x39, 0x30, 0x30, 0x33, 0x70, 0x7C, 0x0E, 0x39, 0x2A, 0x39, 0x2E, 0x2F, 0x39, 0x7C, 0x19, 0x32, 0x3B, 0x35, 0x32, 0x39, 0x39, 0x2E, 0x35, 0x32, 0x3B, 0x7D };

int greet_char(unsigned int idx)
{
    char buf[sizeof(ENC) + 1];
    unsigned int i;
    unsigned int len = sizeof(ENC);

    for (i = 0; i < len; i++)
        buf[i] = (char)(ENC[i] ^ 0x5Cu);
    buf[len] = 0;
    return (int)(unsigned char)buf[idx % len];
}
