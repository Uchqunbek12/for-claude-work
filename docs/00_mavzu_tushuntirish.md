# 00. Mavzuni tushuntirish: nimadan boshlaymiz, nimaga erishamiz

> **Mavzu (№10):** Obfuskatsiyalangan kodni deobfuskatsiya qilish agenti. IDA Pro yoki
> Ghidra orqali olingan obfuskatsiyalangan kodni LLM yordamida soddalashtiradigan,
> C tilidagi ekvivalentini yaratadigan va har bir blokni inson tushunadigan tilda
> tushuntiradigan vosita ishlab chiqish.

---

## 1. Asosiy tushunchalar (oddiy tilda)

### 1.1. Dastur qanday paydo bo'ladi
Dasturchi **C tilida** kod yozadi (`main.c`). **Kompilyator** (masalan `gcc`) uni
**mashina kodiga** (protsessor tushunadigan 0 va 1 lar) aylantiradi va `program.exe`
hosil bo'ladi. Shu jarayonda o'zgaruvchi nomlari, izohlar, kod tuzilmasi **yo'qoladi**.
Foydalanuvchiga faqat `.exe` beriladi, manba kodi berilmaydi.

```
  main.c  ──(gcc kompilyator)──►  program.exe   (manba kodi yo'q!)
```

### 1.2. Reverse engineering (teskari muhandislik)
Bu `.exe` fayldan dastur **nima qilishini** qayta tiklash. Kim uchun kerak:
- antivirus mutaxassislari (zararli dastur nima qiladi?);
- xavfsizlik tadqiqotchilari (dasturda zaiflik bormi?);
- eski dasturni manba kodisiz qo'llab-quvvatlash.

### 1.3. IDA va Ghidra nima qiladi
- **Disassembler** — mashina kodini assembler buyruqlariga aylantiradi (`mov eax, 5`).
- **Dekompilyator** — undan ham yuqoriroq: C tiliga *o'xshash* **psevdokod** chiqaradi
  (IDA'da `F5` tugmasi, Ghidra'da "Decompile" oynasi).

Lekin psevdokodda asl nomlar yo'q, shuning uchun u shunday ko'rinadi:

```c
// IDA uslubi                         // Ghidra uslubi
__int64 __fastcall sub_401136(int a1) undefined8 FUN_00401136(int param_1)
{                                     {
  int v2; // [rsp+10h]                  int local_c;
  ...                                   ...
```

### 1.4. Obfuskatsiya nima
**Obfuskatsiya** — kodni **ataylab chalkashtirish**: dastur ishlashi o'zgarmaydi, lekin
uni o'qish va tushunish juda qiyinlashadi. Kim ishlatadi:
- dasturiy ta'minot ishlab chiqaruvchilari (litsenziya tekshiruvini buzishdan himoya);
- **zararli dastur mualliflari** (antivirus va tahlilchidan yashirinish uchun).

Asosiy usullar (loyihada barchasini aniqlaymiz):

| Usul | Mohiyati | Kichik misol |
|---|---|---|
| **MBA** (Mixed Boolean-Arithmetic) | Oddiy amalni murakkab mantiqiy+arifmetik ifodaga almashtirish | `x + y` → `(x ^ y) + 2*(x & y)` |
| **Opaque predicate** (shaffof bo'lmagan shart) | Har doim bir xil natija beradigan, lekin murakkab ko'rinadigan shart | `if ((x*(x+1)) % 2 == 0)` — har doim rost |
| **Control-flow flattening** (boshqaruv oqimini tekislash) | Kod bloklarini `while(1) { switch(state) {...} }` ichiga tashlash, tartibni yashirish | quyida |
| **String encryption** (satrlarni shifrlash) | Matnlar XOR bilan shifrlanib, ishlash paytida ochiladi | `"password"` → `{0x3a,0x2b,...} ^ 0x4f` |
| **Dead / junk code** (o'lik / keraksiz kod) | Hech qachon bajarilmaydigan yoki natijaga ta'sir qilmaydigan kod | `v5 = v3 * 7; v5 ^= v5;` |

Control-flow flattening misoli:

```c
// ASL KOD                         // OBFUSKATSIYADAN KEYIN
if (a > 0) b = 1;                  int s = 0x1A2B;
else       b = 2;                  while (1) switch (s) {
return b;                            case 0x1A2B: s = (a > 0) ? 0x77 : 0x99; break;
                                     case 0x77:   b = 1; s = 0x55; break;
                                     case 0x99:   b = 2; s = 0x55; break;
                                     case 0x55:   return b;
                                   }
```

### 1.5. Deobfuskatsiya va LLM
**Deobfuskatsiya** — teskari jarayon: chalkash koddan toza, tushunarli kodni tiklash.
Qo'lda qilish soatlab vaqt oladi. **LLM** (katta til modeli, bizda — **Claude**)
millionlab kod namunalarida o'qitilgan, shuning uchun u chalkash kodni "o'qib"
soddalashtira oladi va **inson tilida tushuntira oladi**.

⚠️ Lekin LLM ba'zan **xato qiladi** ("gallyutsinatsiya" — ishonch bilan noto'g'ri javob).
Shuning uchun bizning vosita LLM javobini **ko'r-ko'rona qabul qilmaydi** — uni
kompilyator va testlar bilan **tekshiradi**. Aynan shu narsa uni oddiy "chatbot"dan
**agent**ga aylantiradi: agent natijani tekshiradi, xato bo'lsa o'zi tuzatadi.

---

## 2. Bizning vosita qanday ishlaydi (umumiy sxema)

```
 ┌──────────────┐   1. Kirish: IDA Free (F5 → nusxa) / Ghidra eksporti / .c fayl
 │ Psevdokod    │
 └──────┬───────┘
        ▼
 ┌──────────────┐   2. Parser: funksiyalarga ajratadi, IDA yoki Ghidra uslubini aniqlaydi
 │ Parser       │
 └──────┬───────┘
        ▼
 ┌──────────────┐   3. Statik tahlil (LLM'siz, BEPUL): MBA, opaque predicate,
 │ Detektorlar  │      flattening, XOR-satrlar, o'lik kodni topadi → "maslahatlar"
 └──────┬───────┘
        ▼
 ┌──────────────┐   4. Claude (default: Haiku 5.5 — arzon; --model sonnet/opus):
 │ LLM agent    │      soddalashtirilgan C kod + har blokka o'zbekcha izoh
 └──────┬───────┘
        ▼
 ┌──────────────┐   5. Tekshiruv: gcc bilan kompilyatsiya, ifodalar ekvivalentligini
 │ Verifier     │      tasodifiy sonlar bilan sinash. Xato bo'lsa → 4-qadamga qaytadi
 └──────┬───────┘      (o'z-o'zini tuzatish sikli, maks. N marta)
        ▼
 ┌──────────────┐   6. Natija: Markdown/HTML/JSON hisobot, CLI yoki Web sahifada
 │ Hisobot      │
 └──────────────┘
```

---

## 3. Qayerdan boshlaymiz → qayerga yetamiz

**Boshlang'ich nuqta (hozir):** bo'sh repozitoriy; sizda IDA Free bor; Claude API
ishlatishga qaror qildik (arzon bo'lishi uchun default — Haiku 5.5).

**Yakuniy nuqta (amaliy qism oxirida):** ishlaydigan, sinovdan o'tgan, hujjatlashtirilgan
vosita va uni himoyada namoyish qilish uchun hamma narsa.

### Bosqichlar (darajalar)

| № | Bosqich | Natija (nimaga ega bo'lamiz) |
|---|---|---|
| 1 | Loyiha asosi + test namunalari | 5 ta obfuskatsiyalangan C dastur, ularning asl (toza) versiyasi, binar fayllari va dekompilyatsiya natijasi |
| 2 | Kirish parseri | IDA va Ghidra psevdokodini funksiyalarga ajratuvchi modul |
| 3 | Statik tahlil | 5 xil obfuskatsiya usulini LLM'siz aniqlovchi detektorlar |
| 4 | LLM agent | Claude bilan ishlash: tuzilgan (JSON) javob, kesh, narx hisoblagich, model tanlash |
| 5 | Tekshiruv sikli | gcc kompilyatsiya + ekvivalentlik testi + xatoni LLM'ga qaytarib tuzattirish |
| 6 | Interfeys | CLI (`deobf analyze fayl.c`) va Web UI (brauzerda) |
| 7 | Testlar va baholash | avtomatik testlar (pytest) + metrikalar jadvali (kod qancha soddalashdi, kompilyatsiya bo'ldimi, ekvivalentmi) |
| 8 | Amaliy qism hisoboti | nima qilindi, nima uchun, qanday natija — hisobot |
| — | *Keyin:* Nazariy qism | alohida, amaliy qism tugagach |

### Yakunda sizda bo'ladigan narsalar
1. **`deobf-agent` dasturi** (Python) — CLI va Web UI bilan.
2. **3 xil kirish manbasi**: IDA Free'dan nusxalangan matn, Ghidra eksport skripti, oddiy `.c` fayl.
3. **Bepul offline rejim** — API kalitsiz ham statik tahlil va namoyish ishlaydi.
4. **Model tanlash bir zumda**: `--model haiku` (arzon, default) / `sonnet` / `opus`; Web UI'da ro'yxatdan tanlanadi.
5. **Narx hisoblagich** — har tahlil necha token va necha dollar turganini ko'rsatadi; **kesh** — bir xil kodni qayta tahlil qilish $0.
6. **Test namunalari** va **avtomatik testlar**.
7. **Hujjatlar o'zbek tilida**: har qadam nima uchun qilingani (jurnal), foydalanish yo'riqnomasi (IDA Free va Ghidra bilan qadam-baqadam), amaliy qism hisoboti.

### Narx haqida (talaba uchun)
1 ta funksiya tahlili taxminan: **Haiku 5.5 ≈ $0.0013**, Sonnet 5.5 ≈ $0.026, Opus 5.5 ≈ $0.052.
Ya'ni $5 kredit bilan Haiku'da **minglab** funksiyani tahlil qilish mumkin.
API kalitni <https://console.anthropic.com> saytidan olasiz (buni foydalanish yo'riqnomasida batafsil yozaman).

### Chegaralar (halol aytib o'tamiz)
- Juda kuchli himoyalar (VMProtect/Themida kabi virtual mashinaga asoslangan obfuskatsiya) bu loyiha doirasidan tashqarida.
- LLM 100% to'g'ri ishlashiga kafolat yo'q — shuning uchun tekshiruv moduli bor va natijada "ishonch darajasi" ko'rsatiladi.

---

## 4. Qaysi vositalarni ishlatamiz va nima uchun

| Vosita | Nima uchun |
|---|---|
| **Python 3** | O'rganish oson, AI va tahlil kutubxonalari ko'p, Claude'ning rasmiy kutubxonasi bor |
| **anthropic** (Python SDK) | Claude API bilan ishlashning rasmiy yo'li |
| **Flask** | Eng oddiy Python veb-freymvork — Web UI uchun |
| **gcc** | C kodni kompilyatsiya qilish: namunalar yaratish va LLM natijasini tekshirish |
| **angr** | Bepul Python dekompilyatori. Ishlab chiqish muhitida (bulutli server) Ghidra'ni yuklab bo'lmadi, shuning uchun test namunalarining *haqiqiy* dekompilyatsiya natijasini angr bilan olamiz. Sizning kompyuteringizda esa IDA Free/Ghidra ishlatasiz |
| **pytest** | Avtomatik testlar — kod buzilmaganini tekshirish |
| **git / GitHub** | Barcha o'zgarishlar tarixini saqlash |
