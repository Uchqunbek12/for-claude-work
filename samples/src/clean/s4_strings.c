/* s4_strings (toza versiya): matndan idx-belgini qaytaradi (idx matn uzunligiga qoldiqli). */
static const char MESSAGE[] = "Hello, Reverse Engineering!";

int greet_char(unsigned int idx)
{
    unsigned int len = sizeof(MESSAGE) - 1u;
    return (int)(unsigned char)MESSAGE[idx % len];
}
