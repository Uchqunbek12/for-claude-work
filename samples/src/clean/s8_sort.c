/* s8_sort (toza versiya): pufakchali saralash (bubble sort) — ichma-ich ikki tsikl. */
void bubble_sort(int *a, unsigned int n)
{
    unsigned int i, j;

    if (n < 2u)
        return;
    for (i = 0; i + 1u < n; i++)
        for (j = 0; j + 1u < n - i; j++)
            if (a[j] > a[j + 1]) {
                int t = a[j];
                a[j] = a[j + 1];
                a[j + 1] = t;
            }
}
