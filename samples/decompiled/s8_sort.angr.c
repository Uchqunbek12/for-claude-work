// Manba: samples/bin/s8_sort.elf, funksiya(lar): bubble_sort
// Dekompilyator: angr (avtomatik yaratilgan psevdokod)
void bubble_sort(int *a0, unsigned int a1)
{
    unsigned int v0;  // [bp-0x18]
    unsigned int v1;  // [bp-0x14]
    unsigned int v2;  // [bp-0x10]
    unsigned int v3;  // [bp-0xc]

    v0 = 0;
    v1 = 0;
    v2 = 0x101;
    v3 = 0;
    while (1)
    {
        switch (v2)
        {
        case 2457:
            return;
        case 2313:
            v0 += 1;
            v2 = 0x303;
            break;
        case 2056:
            v1 = (v1 & 1) * 2 + (v1 ^ 1);
            v2 = 0x505;
            break;
        case 1799:
            v3 = a0[v1];
            a0[v1] = a0[1 + v1];
            a0[1 + v1] = v3;
            v2 = 0x808;
            break;
        case 1542:
            v2 = (a0[v1] <= a0[1 + v1] ? 0x808 : 0x707);
            break;
        case 1285:
            v2 = (v1 + 1 < a1 - v0 ? 0x606 : 0x909);
            break;
        case 1028:
            v1 = 0;
            v2 = 0x505;
            break;
        case 771:
            v2 = (v0 + 1 < a1 ? 0x404 : 2457);
            break;
        case 257:
            v2 = (a1 <= 1 ? 2457 : 0x202);
            break;
        case 514:
            v0 = 0;
            v2 = 0x303;
            break;
        default:
            v2 = 0x101;
            break;
        }
    }
}

