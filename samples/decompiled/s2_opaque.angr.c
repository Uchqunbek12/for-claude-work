// Manba: samples/bin/s2_opaque.elf, funksiya: clamp
// Dekompilyator: angr (avtomatik yaratilgan psevdokod)
int clamp(unsigned int a0, unsigned int a1, unsigned int a2)
{
    unsigned int v0;  // [bp-0x14]
    unsigned int v1;  // [bp-0x10]
    unsigned int v2;  // [bp-0xc]

    v1 = a0;
    v2 = a2;
    v0 = a0;
    if (v1 * (v1 + 1) & 1)
    {
        v0 = a1 * 7 - a2;
    }
    else if ((int)a0 < (int)a1)
    {
        v0 = a1;
    }
    if ((v2 & 3) * (v2 & 3) == 2)
    {
        v0 ^= 0x5a5a;
        return v0 + 13;
    }
    if (!((v1 & 1) * ((v1 & 1) + 1)) && (int)a0 >= (int)a1 && (int)a0 > (int)a2)
        v0 = a2;
    return v0;
}

