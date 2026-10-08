// Manba: samples/bin/s4_strings.elf, funksiya: greet_char
// Dekompilyator: angr (avtomatik yaratilgan psevdokod)
extern char ENC;

long long greet_char(unsigned int a0)
{
    unsigned int i;  // [bp-0x40]
    unsigned int v1;  // [bp-0x3c]
    uint224_t v3;  // [bp-0x38]

    v1 = 27;
    for (i = 0; i < v1; i += 1)
    {
        *((char *)&v3 + i) = *(&(&ENC)[i]) ^ 92;
    }
    *((char *)&v3 + v1) = 0;
    return *((char *)&v3 + (a0 % v1 & 0xffffffff));
}

// --- Global ma'lumotlar (binar fayldan olingan) ---
// ENC @ 0x402010 (27 bayt): 14 39 30 30 33 70 7C 0E 39 2A 39 2E 2F 39 7C 19 32 3B 35 32 39 39 2E 35 32 3B 7D

