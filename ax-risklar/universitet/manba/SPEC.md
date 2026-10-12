# SPEC: 1- va 2-amaliy ishlar — UNIVERSITET (OTM) varianti

Fan: "Axborot xavfsizligi risklarini boshqarishga kirish". Ilgari xuddi shu ishlar **tijorat banki** misolida bajarilgan
(namuna fayllar shu papkada: `BANK_amaliy1.js`, `BANK_amaliy2.js`, `BANK_draw.py`, `BANK_1-amaliy-ish.docx`,
`BANK_2-amaliy-ish.docx`). Endi **xuddi shunday tuzilish, format, hajm va uslubda** universitet misolida yangi variant
kerak. Hujjat talaba tomonidan qo'lda yozilganday ko'rinishi kerak (tabiiy o'zbek tili, lotin yozuvi).

Ishchi papka: `/tmp/claude-0/-home-user-for-claude-work/be47e248-da41-584b-8ba2-8bc019478672/scratchpad/work_otm`
(quyida `$W`). `lib.js` — umumiy yordamchi (format: A4, Times New Roman 14, 1,5 interval, 1,25 sm xat boshi,
eni bo'yicha tekislash, sahifa raqami pastda markazda). **lib.js ni o'zgartirmang.**

## Umumiy qoidalar
- Tuzilish bank variantidagi bilan bo'limma-bo'lim bir xil: sarlavha, Mavzu, Ishdan maqsad, Qisqacha nazariy
  ma'lumot(lar), Topshiriqning bajarilishi (qadamlar, jadvallar, rasmlar), Nazorat savollariga javoblar, Xulosa,
  Foydalanilgan adabiyotlar. Jadval/rasm soni va joylashuvi bank variantiga o'xshash.
- Nazariy qism va nazorat savollariga javoblar **bank variantidan so'zma-so'z ko'chirilmasin** — mazmun bir xil
  bo'lsin, lekin boshqacha so'zlar bilan qayta yozilsin va misollar universitetga moslashtirilsin (ikki talaba bir-biridan
  ko'chirganday ko'rinmasin).
- Til: o'zbek lotin, apostrof oddiy `'` (o', g', ma'lumot). Raqamlar: minglik ajratuvchi — bo'sh joy (`3 200`),
  kasr — vergul (`0,25`). Tire `–`.
- Haqiqiy universitet nomi ishlatilmaydi: tashkilot shartli ravishda **"B" universiteti** deb ataladi.
  Haqiqiy axborot tizimlarining nomlari (HEMIS va h.k.) ishlatilmasin — umumiy nomlar ishlatilsin.
- Hujjatda "bank", "ABS", "bankomat", "ransomware" (1-ishdan tashqari kontekstda), "A-Bank" so'zlari qolmasin.
- Barcha qiymatlar "taxminiy, o'quv maqsadida" ekanligi bir joyda aytilsin (bankdagi kabi).

## 1-amaliy ish: Risk modeli — "B" universiteti

Tashkilot tavsifi: davlat oliy ta'lim muassasasi, ~12 000 talaba, ~850 xodim (professor-o'qituvchilar va xodimlar),
6 ta fakultet, axborot-resurs markazi, test (imtihon) markazi, masofaviy ta'lim platformasi (LMS), rasmiy web-sayt va
qabul portali, kampus Wi-Fi tarmog'i, bitta server xonasi. AX bilan Axborot texnologiyalari (AT) markazi shug'ullanadi.

### 1-jadval. Aktivlar (AV, mln so'm)
| № | Aktiv | Turi | AV | Muhimligi (M/Y/F) |
|---|---|---|---|---|
| A1 | Talabalar va xodimlar ma'lumotlar bazasi (shaxsiy ma'lumotlar, baholar, kontrakt to'lovlari) | Axborot | 3 200 | Yuqori / Yuqori / O'rta |
| A2 | Masofaviy ta'lim platformasi (LMS) va elektron o'quv resurslari | Dasturiy (xizmat) | 1 400 | O'rta / O'rta / Yuqori |
| A3 | Rasmiy web-sayt va qabul portali | Dasturiy (xizmat) | 600 | Past / Yuqori / Yuqori |
| A4 | Test (imtihon) markazi: 150 ta kompyuter va test dasturi, savollar bazasi | Dasturiy-texnik | 1 350 | Yuqori / Yuqori / Yuqori |
| A5 | Xodimlarning ish kompyuterlari va korporativ pochta (400 ta) | Texnik / axborot | 2 400 | O'rta / O'rta / O'rta |
| A6 | Server xonasi va tarmoq uskunalari (Wi-Fi, kommutatorlar, MSE) | Texnik | 900 | Past / O'rta / Yuqori |
| | **Jami** | | **9 850** | |

### 2-jadval. Tahdid, zaiflik, EF, SLE (= AV × EF)
| Risk | Aktiv | Tahdid | Zaiflik | AV | EF | SLE |
|---|---|---|---|---|---|---|
| R1 | A1 | Ma'lumotlar bazasining sirqib chiqishi (SQL-inyeksiya) | Web-ilovada kiruvchi ma'lumotlar tekshirilmaydi, baza shifrlanmagan | 3 200 | 0,25 | 800 |
| R2 | A2 | DDoS hujumi (imtihon sessiyasi paytida) | Trafikni filtrlash yo'q, yuklamani taqsimlash (load balancer) yo'q | 1 400 | 0,08 | 112 |
| R3 | A3 | Saytning buzilishi (deface) va zararli kod joylashtirilishi | CMS va plaginlar yangilanmagan, admin panelga zaif parol | 600 | 0,30 | 180 |
| R4 | A4 | Imtihon savollarining sizib chiqishi / natijalarni soxtalashtirish (insayder) | Administrator huquqlari nazoratsiz, harakatlar jurnali yuritilmaydi | 1 350 | 0,20 | 270 |
| R5 | A5 | Fishing orqali xodim hisob yozuvlarining egallanishi | MFA yo'q, xodimlarning AX bo'yicha bilimi past | 2 400 | 0,05 | 120 |
| R6 | A6 | Elektr ta'minotidagi uzilish va kuchlanish sakrashi (uskunalar ishdan chiqishi) | UPS eskirgan, kuchlanish stabilizatori yo'q | 900 | 0,25 | 225 |
Hisoblash misoli R1: SLE = 3 200 × 0,25 = 800 mln so'm.
EF izohi misoli (2-qadam matnida): fishing orqali pochta egallanganda spam/zararli fayllar tarqalishi, kompyuterlarni
tozalash, ish vaqti yo'qotilishi hisobga olinib aktiv qiymatining ~5 % yo'qotiladi deb olindi.

### 3-jadval. ARO va asoslash
| R1 | Bazaning sirqib chiqishi | 0,25 | OTM saytlariga SQL-inyeksiya urinishlari tez-tez bo'ladi, muvaffaqiyatli holat ~4 yilda 1 marta |
| R2 | DDoS hujumi | 3 | O'tgan o'quv yilida imtihon sessiyalari paytida LMS 3 marta ishlamay qolgan |
| R3 | Saytning buzilishi | 1 | Sayt yiliga taxminan 1 marta buziladi yoki unda zararli kod aniqlanadi |
| R4 | Savollarning sizib chiqishi | 0,5 | 2 yilda 1 marta test savollari tarqalib ketgan holat qayd etilgan |
| R5 | Fishing | 5 | AT markazi ma'lumotiga ko'ra yiliga 5 tagacha xodim pochtasi buzilgan |
| R6 | Elektr uzilishi | 0,4 | So'nggi 5 yilda 2 marta uskunalar ishdan chiqqan |
(ARO manbalari: AT markazi mas'ul xodimi bilan suhbat, insidentlar jurnali, ochiq manbalar.)

### 4-jadval. ALE = SLE × ARO (ALE bo'yicha tartiblangan)
| R5 Fishing | 120 | 5 | 600 | 1 |
| R2 DDoS hujumi | 112 | 3 | 336 | 2 |
| R1 Bazaning sirqib chiqishi | 800 | 0,25 | 200 | 3 |
| R3 Saytning buzilishi | 180 | 1 | 180 | 4 |
| R4 Savollarning sizib chiqishi | 270 | 0,5 | 135 | 5 |
| R6 Elektr uzilishi | 225 | 0,4 | 90 | 6 |
| Jami | | | **1 541** | |

### 5-jadval. Risklar xaritasi (ehtimollik × ta'sir, 1–5)
R1: ehtimollik 2, ta'sir 5 → 10 (o'rta); R2: 4, 3 → 12 (yuqori); R3: 3, 3 → 9 (o'rta); R4: 2, 4 → 8 (o'rta);
R5: 5, 3 → 15 (yuqori); R6: 2, 2 → 4 (past). Shkala: 1–5 past (yashil), 6–10 o'rta (sariq), 12–25 yuqori (qizil).
Bank variantidagi `riskMatrix()` funksiyasini shu pozitsiyalar bilan qayta ishlating (kalit "ta'sir,ehtimollik"):
`{"5,2":"R1","3,4":"R2","3,3":"R3","4,2":"R4","3,5":"R5","2,2":"R6"}`.
Sharh: R1 ning ALE si 3-o'rinda bo'lsa ham ta'siri eng yuqori (5): shaxsga doir ma'lumotlar oshkor bo'lishi
qonuniy javobgarlikka olib keladi. R4 ning pul zarari kichik, lekin universitet obro'si va imtihonlarning adolatliligiga
ta'siri katta — bu pulda to'liq aks etmaydi.

### 6-jadval. Qarshi choralar, xarajat/foyda (Foyda = ALE oldin − ALE keyin − yillik narx)
| Risk | Chora | Yillik narxi | Yangi EF / ARO | ALE keyin | ALE oldin | Foyda |
|---|---|---|---|---|---|---|
| R1 | WAF, kodni tuzatish (parametrli so'rovlar), bazani shifrlash, kirish jurnali | 90 | 0,10 / 0,05 | 16 | 200 | 94 |
| R2 | Provayderning DDoS himoya xizmati, yuklamani taqsimlash (load balancer) | 110 | 0,03 / 2 | 84 | 336 | 142 |
| R3 | CMS va plaginlarni yangilash, admin panelga MFA, saytning kunlik zaxira nusxasi | 30 | 0,10 / 0,3 | 18 | 180 | 132 |
| R4 | Rolga asoslangan kirish, harakatlar jurnali (audit log), videokuzatuv, savollar bazasini shifrlash | 45 | 0,10 / 0,1 | 13,5 | 135 | 76,5 |
| R5 | Xodimlar uchun MFA, o'quv mashg'ulotlari, pochta filtri | 70 | 0,03 / 1,5 | 108 | 600 | 422 |
| R6 | UPS ni yangilash, kuchlanish stabilizatori | 25 | 0,03 / 0,4 | 10,8 | 90 | 54,2 |
| Jami | | **370** | | **250,3** | **1 541** | **920,7** |
Hisoblash misoli R5: keyin SLE = 2 400 × 0,03 = 72; ALE = 72 × 1,5 = 108; Foyda = 600 − 108 − 70 = 422.
Rad etilgan variant (bankdagi yong'in o'chirish tizimi o'rniga): R3 uchun avval sayt to'liq bulutli himoyalangan
hostingga + tijoriy WAF ga ko'chirish ko'rib chiqildi, narxi ~220 mln so'm/yil — yillik zarardan (180) ko'p, shuning uchun
maqsadga muvofiq emas; arzonroq chora tanlandi.
1.2-rasm: choralargacha va keyingi ALE ustunli diagrammasi (oldin: 200, 336, 180, 135, 600, 90; keyin: 16, 84, 18,
13,5, 108, 10,8; R1..R6 tartibida). Bank variantidagi `ale_chart()` uslubida.

### 7-jadval. Qarorlar
R1 Kamaytirish; R2 O'tkazish va kamaytirish (DDoS himoyasi provayderga shartnoma asosida); R3 Kamaytirish;
R4 Kamaytirish; R5 Kamaytirish; R6 Kamaytirish;
"–" Qochish: xodimlarning talabalar shaxsiy ma'lumotlarini tashqi bepul fayl almashish xizmatlari va messenjer
guruhlari orqali yuborishi butunlay taqiqlandi, o'rniga universitetning ichki elektron hujjat aylanishi tizimi;
"Qoldiq risk" Qabul qilish: 250,3 mln so'm/yil qoldiq risk rektorat tomonidan qabul qilinadi.
Yakuniy: yiliga 370 mln so'm sarflab, yillik kutilgan zarar 1 541 dan 250,3 mln so'mgacha (~84 %) kamayadi,
sof foyda yiliga 920,7 mln so'm.

Xulosa: universitet misolida 6 aktiv/6 risk; eng katta yillik zarar — fishing va DDoS; eng og'ir oqibatli —
ma'lumotlar bazasining sirqib chiqishi; choralar zararni ~84 % kamaytiradi; har doim eng qimmat himoya to'g'ri emas
(R3 misoli); miqdoriy va sifat tahlili birga.
Adabiyotlar: bank variantidagi ro'yxat (ISO/IEC 27005:2022, NIST SP 800-30 Rev.1, Harris & Maymi CISSP, uslubiy ko'rsatma).
1.1-rasm: `img/riskmodel_c.png` (asl fayldagi Risk modeli rasmi), bankdagidek.

## 2-amaliy ish: "Galstuk-babochka" va "Sabab-oqibat" — "B" universiteti

**Hodisa (ikkala usul uchun bitta):** fishing orqali dekanat xodimining axborot tizimidagi hisob yozuvi buzg'unchi
qo'liga o'tishi (hisob yozuvining egallanishi) va baholarning soxtalashtirilishi. Qisqa: "Xodim hisob yozuvining egallanishi".
Kirish paragrafida: nima uchun bu hodisa dolzarb (OTM larda baholar, kontrakt va shaxsiy ma'lumotlar bir tizimda,
xodimlar ko'p xat oladi, fishing eng keng tarqalgan hujum), hujum qanday kechadi.

### Galstuk-babochka
Sabablar va oldini olish to'siqlari (1-jadval):
1. Fishing xat orqali parolni soxta saytga kiritish — pochta filtri, SPF/DKIM/DMARC, xodimlarni o'qitish
2. Zaif va takroriy parollar (boshqa saytlarda ham shu parol) — parol siyosati, ikki bosqichli autentifikatsiya (MFA)
3. Umumiy kompyuterlarda tizimdan chiqmaslik, parolni brauzerda saqlash — sessiyaning avtomatik tugashi, parol saqlashni taqiqlash
4. Kompyuterga keylogger (zararli dastur) o'rnatilishi — antivirus/EDR, USB fleshkalarni cheklash
5. Telefon orqali ijtimoiy muhandislik ("AT markazidan qo'ng'iroq qilyapmiz") — parol hech qachon so'ralmasligi qoidasi, qo'ng'iroqni tekshirish tartibi
Oqibatlar va kamaytirish to'siqlari (2-jadval):
1. Baholar va davomat ma'lumotlarining soxtalashtirilishi — o'zgarishlar jurnali (audit log), ikki kishilik tasdiqlash, baholarni muntazam solishtirish
2. Talabalar shaxsiy ma'lumotlarining sirqib chiqishi — minimal huquqlar (rolga asoslangan kirish), ma'lumotlarni eksport qilishni cheklash
3. Egallangan pochtadan boshqa xodimlarga fishing xatlar tarqatilishi (hujumning kengayishi) — g'ayritabiiy faollikni aniqlash, hisobni tezkor bloklash
4. Universitet obro'siga putur, tekshiruvlar va jarimalar — insidentga javob rejasi, rasmiy bayonot, vakolatli organlarga xabar berish
8-qadam boshqaruv elementlari: AX siyosati (parol, pochta, ma'lumot almashish qoidalari); AT markazida AX bo'yicha
mas'ul xodim; har semestrda AX bo'yicha o'quv mashg'ulotlari va o'quv fishing; tizim jurnallarini har hafta ko'rib
chiqish; yiliga bir marta ichki audit.
Xulosa paragrafi (bankdagidek): yo'llarning ko'pi inson omili → o'qitish + MFA bir nechta yo'lni to'sadi; oqibatlar
tomonida eng muhim to'siq — o'zgarishlar jurnali, u bo'lmasa soxta baholar sezilmay qoladi.
2.1-rasm: galstuk-babochka diagrammasi (BANK_draw.py `bowtie()` uslubida, yangi matnlar bilan, qisqa yorliqlar).

### Sabab-oqibat
a) Kritik hodisa: "Xodim hisob yozuvi egallandi".
b) Baliq skeleti (2.2-rasm), 6 guruh × 3 band:
- Odamlar: AX bo'yicha bilim pastligi; fishing xatni ochish; parolni boshqalarga aytish
- Texnik vositalar: antivirus/EDR yo'qligi; eskirgan brauzer va OT; parolni brauzerda saqlash
- Tashkiliy jarayonlar: AX siyosati bajarilmasligi; jurnallar ko'rilmasligi; o'quv mashg'ulotlari yo'qligi
- Autentifikatsiya: zaif / takroriy parollar; MFA joriy qilinmagan; kirish urinishlari cheklanmagan
- Tashqi omillar: soxta (o'xshash) domenlar; ommaviy fishing kampaniyalari; sirqib chiqqan parollar bazalari
- Muhit: umumiy foydalanishdagi kompyuterlar; ochiq (parolsiz) Wi-Fi; tizimdan chiqmay ketish
Nosozliklar daraxti (yillik ehtimolliklar):
- Fishing orqali parol o'g'irlanishi = VA(xat filtrdan o'tdi 0,2; xodim soxta saytga parol kiritdi 0,25) = 0,05
- Parolni tanlab topish = VA(parol zaif yoki takroriy 0,3; kirish urinishlari cheklanmagan 0,1) = 0,03
- Keylogger 0,02
- P(hodisa) = 1 − (1 − 0,05)(1 − 0,03)(1 − 0,02) = 1 − 0,903 ≈ 0,097 (yiliga ~9,7 %)
c) Holatlar tartibi: 1) kirish tizimi g'ayritabiiy kirishni (yangi IP / qurilma) aniqlab bloklaydimi; 2) o'zgarishlar
jurnali soxtalashtirishni 24 soat ichida aniqlaydimi; 3) to'g'ri ma'lumotlar zaxira nusxadan tiklanadimi.
d) Hodisalar daraxti: B1 HA 0,5 / YO'Q 0,5; B2 HA 0,7 / YO'Q 0,3; B3 HA 0,9 / YO'Q 0,1.
2.3-rasm: to'liq sabab-oqibat diagrammasi (nosozlik daraxti + hodisalar daraxti) — BANK_draw.py `cause_consequence()`
uslubida, albom (landscape) varaqda, bankdagidek "SPLIT" usuli bilan (nazorat savollaridan oldin).
e) 3-jadval:
| S1 | Begona kirish bloklandi, zarar yo'q | 0,5 | 0,500 | 0,0485 |
| S2 | Soxtalashtirish tez aniqlandi, zaxiradan tiklandi | 0,5 × 0,7 × 0,9 | 0,315 | 0,0306 |
| S3 | Aniqlandi, lekin baholar qo'lda tiklanadi (bir necha kun) | 0,5 × 0,7 × 0,1 | 0,035 | 0,0034 |
| S4 | Kech aniqlandi, ma'lumotlar sirqib chiqqan, baholar tiklandi | 0,5 × 0,3 × 0,9 | 0,135 | 0,0131 |
| S5 | Halokatli: soxta baholar qayd daftarchasi/diplomga o'tib ketgan | 0,5 × 0,3 × 0,1 | 0,015 | 0,0015 |
| Jami | | | 1,000 | ≈ 0,097 |
Qo'shish misoli: "jiddiy va halokatli" (S4+S5) = 0,135 + 0,015 = 0,15; yillik 0,15 × 0,097 ≈ 0,015.
Choralar: MFA to'liq joriy qilinsa (B1 → 0,9) va jurnal avtomatik ogohlantirsa (B2 → 0,9): S5 = 0,1 × 0,1 × 0,1 = 0,001
(0,015 dan 15 barobar kam). Sabablar tomonida: pochta filtri (0,2 → 0,1) va kirish urinishlarini cheklash (0,1 → 0,02):
P = 1 − (1 − 0,025)(1 − 0,006)(1 − 0,02) ≈ 0,05 — taxminan 2 barobar kam. Taklif etilgan choralar ro'yxati (5–6 band).
Nazorat savollariga javoblar (8 ta, asl uslubiy ko'rsatmadagi savollar matni bankdagi kabi), Xulosa (bank xulosasi
tuzilishida, universitet raqamlari bilan), Adabiyotlar (IEC 31010:2019, ISO/IEC 27005:2022, NIST SP 800-30, uslubiy ko'rsatma).

## Chiqish fayllari
- `$W/out/1-amaliy-ish-universitet.docx`, `$W/out/2-amaliy-ish-universitet.docx`
- Rasmlar: `$W/img/` (ale.png, bowtie.png, fishbone.png, cca.png; riskmodel_c.png allaqachon bor)
- Skriptlar: `$W/amaliy1.js`, `$W/amaliy2.js`, `$W/draw_ale.py` (faqat 1.2-rasm), `$W/draw_diagrams.py` (2.1–2.3 rasmlar)
- Render tekshiruvi: `python /root/.claude/skills/synced/e4660807-06cf-443d-bcbc-9b4329a4c75f_11a3e22b-4bd4-4725-a42b-801cc12c2300/docx/scripts/office/soffice.py --headless --convert-to pdf --outdir $W/out <docx>`
  so'ng `pdftoppm -jpeg -r 70` va rasmlarni Read bilan ko'rib chiqish. Validatsiya:
  `python .../docx/scripts/office/validate.py <docx>`.
- matplotlib shrifti: "Liberation Serif". Diagrammalarda yozuvlar bir-birini, chiziqlarni va to'siq to'rtburchaklarini
  qoplamasin, matn ramkadan chiqmasin (bankdagi oxirgi versiyalarda bu muammolar tuzatilgan — o'sha o'lchamlardan foydalaning).
