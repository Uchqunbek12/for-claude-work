// Manba: samples/bin/s3_flatten.elf, funksiya: gcd
// Dekompilyator: angr (avtomatik yaratilgan psevdokod)
unsigned int gcd(unsigned int a0, unsigned int a1)
{
    unsigned int v0;  // [bp-0x20]
    unsigned int v1;  // [bp-0x1c]
    unsigned int v2;  // [bp-0x10]
    unsigned int v3;  // [bp-0xc]

    v1 = a0;
    v0 = a1;
    v2 = 0;
    v3 = 15391;
    while (1)
    {
        switch (v3)
        {
        case 37282:
            v2 = v1 % v0;
            v3 = 11117;
            break;
        case 24071:
            return v1;
        case 11117:
            v1 = v0;
            v0 = v2;
            v3 = 15391;
            break;
        case 15391:
            v3 = (!v0 ? 24071 : 37282);
            break;
        default:
            v3 = 15391;
            break;
        }
    }
}

