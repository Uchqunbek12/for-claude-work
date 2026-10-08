// Manba: samples/bin/s6_buffer.elf, funksiya(lar): xor_stream
// Dekompilyator: angr (avtomatik yaratilgan psevdokod)
void xor_stream(char *a0, unsigned int a1, char a2)
{
    unsigned int v0;  // [bp-0x18]
    unsigned int v1;  // [bp-0x14]
    unsigned int v2;  // [bp-0x10]
    unsigned int v3;  // [bp-0xc]

    v0 = 0;
    v1 = 106;
    v2 = 0;
    v3 = a2;
    while (1)
    {
        switch (v1)
        {
        case 106:
            v1 = (v0 < a1 ? 19 : 92);
            break;
        case 92:
            return;
        case 19:
            a0[v0] = a0[v0] ^ (char)v3;
            if ((v0 & 1) * ((v0 & 1) + 1))
                v2 = a0[v0] * 3;
            v1 = 39;
            break;
        case 39:
            v3 = (v3 * 4 ^ v3) + (v3 * 4 & v3) * 2 + 1 & 0xff;
            v2 ^= v3;
            v0 = (v0 & 1) * 2 + (v0 ^ 1);
            v1 = 106;
            break;
        default:
            v1 = 106;
            break;
        }
    }
}

