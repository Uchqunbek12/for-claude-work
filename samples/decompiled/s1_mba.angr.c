// Manba: samples/bin/s1_mba.elf, funksiya: mix
// Dekompilyator: angr (avtomatik yaratilgan psevdokod)
unsigned int mix(unsigned int a0, unsigned int a1)
{
    unsigned int v0;  // [bp-0x18]
    unsigned int v1;  // [bp-0x14]
    unsigned int v2;  // [bp-0x10]
    unsigned int v3;  // [bp-0xc]

    v0 = (a0 & a1) * 2 + (a0 ^ a1);
    v1 = (a0 ^ a1) - (~(a0) & a1) * 2;
    v2 = v0 ^ v1;
    v3 = a0 & 0xff;
    return v2 | v3;
}

