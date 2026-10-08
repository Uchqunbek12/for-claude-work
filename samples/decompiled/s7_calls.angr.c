// Manba: samples/bin/s7_calls.elf, funksiya(lar): rotl32, rot_hash
// Dekompilyator: angr (avtomatik yaratilgan psevdokod)
unsigned int rotl32(unsigned int a0, unsigned int a1)
{
    unsigned int v0;  // [bp-0x20]
    unsigned int v1;  // [bp-0x10]
    unsigned int v2;  // [bp-0xc]

    v0 = a1;
    v0 &= 31;
    v1 = a0 << ((char)v0 & 31);
    v2 = a0 >> ((char)-(v0) & 31);
    return v1 | v2;
}

unsigned int rot_hash(char *a0, unsigned int a1)
{
    unsigned int v0;  // [bp-0x14]
    unsigned int v1;  // [bp-0x10]
    unsigned int v2;  // [bp-0xc]

    v0 = 0;
    v1 = 0;
    v2 = 177;
    while (1)
    {
        switch (v2)
        {
        case 201:
            return v0;
        case 177:
            v0 = 305419896;
            v1 = 0;
            v2 = 14;
            break;
        case 14:
            v2 = (v1 < a1 ? 0x77 : 201);
            break;
        case 119:
            if ((a1 & 3) * (a1 & 3) == 2)
                v0 *= 31;
            v0 = rotl32(a0[v1] ^ v0, 5) + 1831565813;
            v1 += 1;
            v2 = 14;
            break;
        default:
            v2 = 177;
            break;
        }
    }
}

