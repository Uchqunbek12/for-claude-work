/* s8_sort (obfuskatsiyalangan): ichma-ich tsikllar BITTA holatlar mashinasiga tekislangan.
 * Bu flattening'ning qiyinroq ko'rinishi: tashqi va ichki tsikl, shart va almashtirish —
 * hammasi bir xil darajadagi case'lar. */
void bubble_sort(int *a, unsigned int n)
{
    unsigned int i = 0u, j = 0u, s = 0x101u;
    int t = 0;

    while (1) {
        switch (s) {
        case 0x101u:                               /* kirish: n < 2 bo'lsa chiqish */
            s = (n < 2u) ? 0x999u : 0x202u;
            break;
        case 0x202u:                               /* tashqi tsikl boshlanishi */
            i = 0u;
            s = 0x303u;
            break;
        case 0x303u:                               /* tashqi tsikl sharti */
            s = (i + 1u < n) ? 0x404u : 0x999u;
            break;
        case 0x404u:                               /* ichki tsikl boshlanishi */
            j = 0u;
            s = 0x505u;
            break;
        case 0x505u:                               /* ichki tsikl sharti */
            s = (j + 1u < n - i) ? 0x606u : 0x909u;
            break;
        case 0x606u:                               /* taqqoslash */
            s = (a[j] > a[j + 1]) ? 0x707u : 0x808u;
            break;
        case 0x707u:                               /* almashtirish */
            t = a[j];
            a[j] = a[j + 1];
            a[j + 1] = t;
            s = 0x808u;
            break;
        case 0x808u:                               /* j++ */
            j = (j ^ 1u) + 2u * (j & 1u);
            s = 0x505u;
            break;
        case 0x909u:                               /* i++ */
            i = i + 1u;
            s = 0x303u;
            break;
        case 0x999u:
            return;
        default:
            s = 0x101u;
            break;
        }
    }
}
