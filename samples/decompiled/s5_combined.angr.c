// Manba: samples/bin/s5_combined.elf, funksiya: checksum
// Dekompilyator: angr (avtomatik yaratilgan psevdokod)
unsigned int checksum(unsigned int a0, unsigned int a1)
{
    unsigned int v0;  // [bp-0x30]
    unsigned int v1;  // [bp-0x1c]
    unsigned int v2;  // [bp-0x18]
    unsigned int v3;  // [bp-0x14]
    unsigned int v4;  // [bp-0x10]
    unsigned int v5;  // [bp-0xc]

    v0 = a1;
    v1 = 0;
    v2 = 0;
    v5 = 0;
    v3 = 0;
    v4 = 161;
    while (1)
    {
        switch (v4)
        {
        case 196:
            v5 = a0 >> ((char)v2 * 8 & 24 & 31) & 0xff;
            if ((v2 & 1) * ((v2 & 1) + 1))
                v3 = v5 * 4919;
            v1 ^= v5;
            v4 = 59;
            break;
        case 161:
            v1 = 2166136261;
            v0 = (v0 & 7) + 1;
            v2 = 0;
            v4 = 31;
            break;
        case 119:
            return v1;
        case 31:
            v4 = (v2 < v0 ? 196 : 0x77);
            break;
        case 59:
            v1 *= 16777619;
            v3 ^= v1;
            v2 = (v2 & 1) * 2 + (v2 ^ 1);
            v4 = 31;
            break;
        default:
            v4 = 161;
            break;
        }
    }
}

