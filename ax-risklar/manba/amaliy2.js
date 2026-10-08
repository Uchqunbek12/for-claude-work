const L = require("./lib");
const { p, h, li, img, caption, tcap, table, AlignmentType: A } = L;
const fs = require("fs");
const IMG = __dirname + "/img/";
const title = fs.existsSync(__dirname + "/titul.json") ? JSON.parse(fs.readFileSync(__dirname + "/titul.json")) : null;
const C = A.CENTER;
const q = (t) => p(t, { keepNext: true });

const body = [];
const add = (...x) => body.push(...x.flat());

if (title) add(L.titlePage(title, "2-amaliy mashg'ulot", "Risklarni \"Galstuk-babochka\" va \"Sabab-oqibat\" usullari yordamida tahlili"));

add(
  h("2-Amaliy mashg'ulot.", { before: 0 }),
  h("Mavzu: Risklarni \"Galstuk-Babochka\" va \"Sabab-oqibat\" usullari yordamida tahlili", { before: 0 }),
  p("**Ishdan maqsad:** \"Galstuk-Babochka\" va \"Sabab-oqibat\" usullaridan foydalangan holda axborot xavfsizligidagi risklarni baholashni o'rganishdan iborat."),

  h("Qisqacha nazariy ma'lumot"),
  p("**\"Galstuk-babochka\"** usuli xavfli hodisaning sabablardan oqibatlargacha rivojlanish yo'llarini sxematik tasvirlash va tahlil qilish imkonini beradi. Diagramma markazida xavfli hodisa joylashadi, uning chap tomonida hodisaga olib keluvchi sabablar va ularni oldini oluvchi to'siqlar, o'ng tomonida esa hodisaning oqibatlari va ularni yumshatuvchi to'siqlar ko'rsatiladi. Diagramma shakli babochkaga (kapalak shaklidagi galstukka) o'xshagani uchun usul shunday nomlangan."),
  p("**\"Sabab-oqibat\"** tahlili nosozliklar daraxti va hodisalar daraxti tahlilining birikmasidan iborat. Tahlil kritik hodisadan boshlanadi: uning sabablari nosozliklar daraxti yordamida (\"VA\", \"YOKI\" mantiqiy elementlari orqali), oqibatlari esa himoya tizimlarining ishlashi yoki ishlamasligini ko'rsatuvchi \"HA / YO'Q\" bloklari yordamida ko'rib chiqiladi. Har bir shart blokiga ehtimollik berilsa, har bir oqibatning yuzaga kelish ehtimolini miqdoriy baholash mumkin bo'ladi."),

  h("Topshiriqning bajarilishi"),
  p("Ikkala usul bo'yicha tahlil uchun bitta xavfli hodisa – **tijorat banki filiali serverlariga ransomware (shifrlovchi zararli dastur) tushishi** tanlandi. Bu hodisa so'nggi yillarda moliya sohasida eng ko'p uchrayotgan va eng katta zarar keltirayotgan hujumlardan biri hisoblanadi. Ransomware tarmoqqa kirgach serverlardagi ma'lumotlarni shifrlab qo'yadi va ularni ochish uchun to'lov talab qiladi. Ko'p hollarda hujumchilar ma'lumotlarni oldindan o'g'irlab, ularni e'lon qilish bilan ham tahdid qiladi."),

  h("1. \"Galstuk-babochka\" usuli bo'yicha tahlil"),
  p("Tahlil uslubiy ko'rsatmada berilgan tartibda bajarildi."),
  p("**1-qadam. Xavfli hodisani aniqlash.** Diagramma markaziga \"Bank serverlariga ransomware tushishi\" hodisasi qo'yildi. Bunda hodisa deganda zararli dasturning tarmoq ichida ishga tushib, avtomatlashtirilgan bank tizimi (ABS) serverlaridagi ma'lumotlarni shifrlay boshlashi tushuniladi."),
  p("**2-qadam. Hodisa sabablari ro'yxatini tuzish.** Filialning AX bo'yicha mas'ul xodimi bilan suhbat va ochiq manbalardagi hujumlar tahlili asosida beshta asosiy sabab aniqlandi (1-jadval)."),
  p("**3-qadam. Hodisagacha rivojlanish mexanizmi.** Odatda hujum quyidagicha rivojlanadi: hujumchi fishing xat, ochiq RDP porti yoki zararlangan fleshka orqali bitta kompyuterga kiradi, so'ng zaif parollar va ortiqcha administrator huquqlaridan foydalanib tarmoq bo'ylab tarqaladi va oxirida serverlarni shifrlaydi."),
  p("**4–5-qadamlar. Diagrammaning chap tomoni va oldini olish to'siqlari.** Har bir sababdan hodisaga chiziq tortildi va har bir chiziqqa shu yo'lni to'suvchi himoya chorasi qo'yildi."),
  tcap("1-jadval", "Hodisa sabablari va oldini olish to'siqlari"),
  table([600, 3800, 4955], [
    ["№", "Sabab", "Oldini olish to'sig'i (chora)"],
    ["1", "Fishing xat orqali zararli ilovaning ochilishi", "Pochta filtri va sandbox, xodimlarni muntazam o'qitish, o'quv fishing-mashg'ulotlari"],
    ["2", "Operatsion tizim va dasturlarning yangilanmaganligi, RDP porti internetga ochiqligi", "Patch-menejment (yangilanishlarni oyiga kamida 1 marta o'rnatish), RDP ni faqat VPN orqali ishlatish"],
    ["3", "Zaif va takroriy parollar", "Parol siyosati (kamida 12 belgi), ikki bosqichli autentifikatsiya (MFA)"],
    ["4", "Zararlangan USB fleshkadan foydalanish", "USB portlarni cheklash, tashqi qurilmalarni avtomatik antivirus tekshiruvi"],
    ["5", "Litsenziyasiz yoki noma'lum dasturlarni o'rnatish", "Foydalanuvchilarning administrator huquqlarini olib tashlash, ruxsat etilgan dasturlar ro'yxati (whitelisting)"],
  ], { align: [C, A.LEFT, A.LEFT] }),
  p("**6–7-qadamlar. Oqibatlar va ularni kamaytirish to'siqlari.** Diagrammaning o'ng tomoniga hodisaning to'rtta asosiy oqibati joylashtirildi va har biriga oqibatni yumshatuvchi to'siq qo'yildi (2-jadval).", { spacing: { before: 120 } }),
  tcap("2-jadval", "Hodisa oqibatlari va ularni kamaytirish choralari"),
  table([600, 3800, 4955], [
    ["№", "Oqibat", "Oqibatni kamaytirish to'sig'i (chora)"],
    ["1", "ABS ning to'xtashi, mijozlarga xizmat ko'rsatishning uzilishi", "Zaxira (rezerv) server, biznes uzluksizligi rejasi (BCP)"],
    ["2", "Mijozlar va operatsiyalar ma'lumotlarining yo'qolishi", "\"3-2-1\" qoidasi bo'yicha zaxira nusxalar, ulardan biri tarmoqdan ajratilgan (offline) holda saqlanadi"],
    ["3", "Ma'lumotlarning sirqib chiqishi va tovlamachilik (double extortion)", "Bazalardagi shaxsga doir ma'lumotlarni shifrlash, DLP tizimi"],
    ["4", "Moliyaviy zarar, regulyator jarimalari, bank obro'sining tushishi", "Insidentga javob berish rejasi, kiber-sug'urta, mijozlar uchun tayyor PR-bayonot"],
  ], { align: [C, A.LEFT, A.LEFT] }),
  p("Tuzilgan \"Galstuk-babochka\" diagrammasi 2.1-rasmda keltirilgan.", { spacing: { before: 120 } }),
  img(IMG + "bowtie.png", 620),
  caption("2.1-rasm. Ransomware hodisasi uchun \"Galstuk-babochka\" diagrammasi"),
  p("**8-qadam. Boshqaruv bilan bog'liq yordamchi elementlar.** To'siqlar doimiy ishlab turishi uchun quyidagi boshqaruv elementlari belgilandi:"),
  li("- bankning AX siyosati va undagi zaxira nusxa olish, parol va dasturlarni o'rnatish bo'yicha qoidalar;"),
  li("- filialda AX bo'yicha mas'ul xodim tayinlanishi va uning vazifalari;"),
  li("- zaxira nusxalardan tiklashni har chorakda sinab ko'rish;"),
  li("- yiliga bir marta ichki AX auditi va zaifliklarni skanerlash;"),
  li("- xavfsizlik hodisalarini kuzatish (SIEM / SOC) va shubhali holatlar haqida darhol xabar berish tartibi."),
  p("Diagrammadan ko'rinib turibdiki, hodisaga olib keluvchi yo'llarning ko'pchiligi inson omili (fishing, parollar, fleshkalar) bilan bog'liq. Shu sababli xodimlarni o'qitish bir vaqtning o'zida bir nechta yo'lni to'sadi. Oqibatlar tomonida esa eng muhim to'siq – tarmoqdan ajratilgan zaxira nusxa, chunki u bo'lmasa ma'lumotlarni tiklashning boshqa yo'li deyarli qolmaydi."),

  h("2. \"Sabab-oqibat\" usuli bo'yicha tahlil"),
  p("Tahlil uslubiy ko'rsatmadagi a)–e) bandlar tartibida bajarildi."),
  p("**a) Kritik hodisani aniqlash.** Kritik hodisa sifatida yana \"Ransomware ishga tushdi\" hodisasi olindi. U nosozliklar daraxtining oxirgi (yuqori) hodisasi va hodisalar daraxtining boshlang'ich hodisasi hisoblanadi."),
  p("**b) Hodisa sabablarini aniqlash.** Avval sabablar guruhlarga ajratildi va \"baliq skeleti\" ko'rinishidagi sxema tuzildi (2.2-rasm). Sabablar oltita guruhga bo'lindi: odamlar, dasturiy ta'minot, jarayonlar, infratuzilma, tashqi omillar va kirish nazorati."),
  img(IMG + "fishbone.png", 620),
  caption("2.2-rasm. Ransomware hodisasi sabablarining sabab-oqibat sxemasi"),
  p("So'ngra asosiy sabablar uchun nosozliklar daraxti tuzildi va ularga yillik ehtimolliklar berildi. Fishing orqali hujum ikki shart bir vaqtda bajarilganda sodir bo'ladi (\"VA\" elementi): xat filtrdan o'tishi (0,1) va xodimning ilovani ochishi (0,3). Demak:"),
  p("P(fishing) = 0,1 × 0,3 = 0,03.", { align: C, noIndent: true }),
  p("RDP orqali hujum uchun port ochiq bo'lishi (0,2) va yangilanish o'rnatilmagan bo'lishi (0,25) kerak:"),
  p("P(RDP) = 0,2 × 0,25 = 0,05.", { align: C, noIndent: true }),
  p("Zararlangan fleshka ehtimoli 0,01 deb olindi. Bu uch yo'ldan istalgan biri hodisaga olib keladi (\"YOKI\" elementi), shuning uchun:"),
  p("P(hodisa) = 1 – (1 – 0,03)(1 – 0,05)(1 – 0,01) = 1 – 0,912 ≈ 0,088.", { align: C, noIndent: true }),
  p("Demak, hozirgi holatda filialda bir yil ichida ransomware ishga tushishi ehtimoli taxminan 8,8 % ni tashkil etadi."),
  p("**c) Holatlarni ko'rib chiqish tartibi.** Hodisadan keyin himoya vositalari vaqt bo'yicha quyidagi ketma-ketlikda ishga tushadi: 1) EDR/antivirus zararli dasturni aniqlab bloklaydimi; 2) tarmoq segmentatsiyasi uning boshqa segmentlarga tarqalishini to'xtatadimi; 3) offline zaxira nusxa yaroqli va undan tiklash mumkinmi."),
  p("**d) Oqibatlarning paydo bo'lish yo'llari.** Har bir shart \"HA / YO'Q\" bloki ko'rinishida tasvirlandi va beshta mumkin bo'lgan oqibat (S1–S5) hosil bo'ldi. To'liq sabab-oqibat diagrammasi (nosozliklar daraxti va hodisalar daraxti birgalikda) 2.3-rasmda keltirilgan."),
  p("**e) Oqibatlar ehtimolini hisoblash.** Shart bloklari bir-biridan mustaqil deb hisoblandi. Har bir oqibatning ehtimoli shu oqibatga olib boruvchi yo'ldagi ehtimolliklarni ko'paytirish orqali topildi. Yillik ehtimollik esa shu qiymatni kritik hodisa ehtimoliga (0,088) ko'paytirib hisoblandi (3-jadval)."),
  tcap("3-jadval", "Oqibatlarning ehtimolliklari"),
  table([950, 3005, 2400, 1500, 1500], [
    ["Oqibat", "Tavsifi", "Yo'l bo'yicha hisob", "Shartli ehtimollik", "Yillik ehtimollik"],
    ["S1", "Hujum EDR tomonidan to'xtatildi, zarar deyarli yo'q", "0,7", "0,700", "0,0616"],
    ["S2", "Bitta segment shifrlandi, zaxiradan tez tiklandi", "0,3 × 0,6 × 0,8", "0,144", "0,0127"],
    ["S3", "Bitta segment ma'lumotlari yo'qoldi", "0,3 × 0,6 × 0,2", "0,036", "0,0032"],
    ["S4", "Butun tarmoq shifrlandi, tiklash 2–3 kun", "0,3 × 0,4 × 0,8", "0,096", "0,0084"],
    ["S5", "Butun tarmoq shifrlandi, zaxira yo'q – halokatli oqibat", "0,3 × 0,4 × 0,2", "0,024", "0,0021"],
    [{ t: "Jami", bold: true, span: 3, align: A.RIGHT }, { t: "1,000", bold: true, align: C }, { t: "0,088", bold: true, align: C }],
  ], { align: [C, A.LEFT, C, C, C] }),
  p("Bir xil turdagi oqibatlarning ehtimolliklari qo'shiladi. Masalan, bankning bir necha kun ishlamay qolishiga olib keladigan \"jiddiy va halokatli\" oqibatlar (S4 va S5) ehtimoli: 0,096 + 0,024 = 0,12, yillik ehtimolligi esa 0,12 × 0,088 ≈ 0,011 ga teng.", { spacing: { before: 120 } }),
  p("**Oldini olish va oqibatlarni kamaytirish choralari.** Diagramma qaysi to'siqni kuchaytirish ko'proq foyda berishini ko'rsatadi. Agar EDR tizimi to'g'ri sozlansa (bloklash ehtimoli 0,9 gacha) va zaxira nusxalar muntazam tekshirilsa (yaroqlilik 0,95 gacha), halokatli oqibat ehtimoli 0,3 × 0,4 × 0,2 = 0,024 dan 0,1 × 0,4 × 0,05 = 0,002 gacha, ya'ni 12 barobar kamayadi. Sabablar tomonida esa RDP ni internetdan yopish (0,2 → 0,02) va pochta filtrini kuchaytirish (0,1 → 0,05) orqali kritik hodisa ehtimolini 1 – (1 – 0,015)(1 – 0,005)(1 – 0,01) ≈ 0,03 gacha, ya'ni qariyb 3 barobar tushirish mumkin. Shunday qilib, quyidagi choralar taklif etildi:"),
  li("- RDP ni internetdan yopish va yangilanishlarni o'z vaqtida o'rnatish;"),
  li("- barcha xodimlar uchun MFA va har chorakda AX bo'yicha o'quv mashg'ulotlari;"),
  li("- EDR tizimini joriy qilish va sozlash;"),
  li("- tarmoqni segmentlarga ajratish (ABS serverlari alohida segmentda);"),
  li("- zaxira nusxalarni offline saqlash va ulardan tiklashni muntazam sinab ko'rish;"),
  li("- insidentga javob berish rejasini ishlab chiqish va xodimlarni u bilan tanishtirish."),

  "SPLIT",
  h("Nazorat savollariga javoblar", { before: 0 }),
  q("**1. \"Galstuk-babochka\" tahlili tushunchasiga ta'rif bering.**"),
  p("\"Galstuk-babochka\" tahlili – xavfli hodisaning sabablardan oqibatlargacha rivojlanish yo'llarini bitta diagrammada ko'rsatuvchi grafik tahlil usuli. Diagrammaning markazida hodisa, chap tomonida sabablar va oldini olish to'siqlari, o'ng tomonida oqibatlar va ularni kamaytirish to'siqlari joylashadi. Usul hodisaga qarshi choralarni va uni keltirib chiqaradigan sabablarni aniq ko'rsatishga qaratilgan."),
  q("**2. \"Galstuk-babochka\" tahlilida ko'rsatilgan omillarni tushuntiring.**"),
  p("Tahlilda quyidagi omillar ko'rsatiladi: xavfli hodisa (markaziy element); xavf manbalari va hodisa sabablari; hodisaning oldini oluvchi to'siqlar (profilaktik nazorat); hodisa oqibatlari; oqibatlarni yumshatuvchi to'siqlar (tiklovchi nazorat); hamda diagramma ostida ko'rsatiladigan boshqaruv elementlari – siyosatlar, mas'ul shaxslar, audit va monitoring. Bizning ishimizda besh sabab, to'rt oqibat va har biri uchun to'siq aniqlandi."),
  q("**3. Ushbu usul qaysi sohalarda qo'llaniladi?**"),
  p("Usul quyidagi hollarda qo'llaniladi: mumkin bo'lgan sabab va oqibatlar diapazonini ko'rsatish asosida risklarni tadqiq qilishda; nosozliklar daraxti tahlilini o'tkazish murakkab bo'lganda; har bir rivojlanish yo'li uchun to'siqlar va boshqarish vositalarini ishlab chiqish kerak bo'lganda; hodisaga olib boruvchi mustaqil yo'llarni aniq ajratish mumkin bo'lganda. Amalda u axborot xavfsizligi, sanoat xavfsizligi, neft-gaz, aviatsiya va tibbiyot sohalarida keng ishlatiladi."),
  q("**4. Usulning afzallik va kamchiliklarini tushuntirib bering.**"),
  p("Afzalliklari: muammoni aniq va ko'rgazmali tasvirlaydi; hodisaning oldini olish va oqibatlarini kamaytirish choralari hamda ularning samaradorligini baholashga qaratilgan; foydali oqibatlar uchun ham qo'llanilishi mumkin; yuqori malakali mutaxassislarni talab qilmaydi. Kamchiliklari: bir vaqtda yuzaga keladigan sabablar birikmasini ko'rsatib bo'lmaydi; murakkab vaziyatlar haddan tashqari soddalashtirilishi mumkin; ehtimolliklarni miqdoriy hisoblash imkoni cheklangan."),
  q("**5. \"Sabab-oqibat\" tahlili tushunchasiga ta'rif bering.**"),
  p("\"Sabab-oqibat\" tahlili – nosozliklar daraxti va hodisalar daraxti tahlilining birikmasi. U kritik hodisadan boshlanib, bir tomondan hodisa sabablarini mantiqiy elementlar orqali, ikkinchi tomondan himoya tizimlarining ishlashi yoki ishlamasligini ko'rsatuvchi HA/YO'Q bloklari orqali uning oqibatlarini tahlil qiladi. Natijada tizim qanday qilib nosozlikka uchrashi mumkinligi va har bir oqibat ehtimoli aniqlanadi."),
  q("**6. \"Sabab-oqibat\" tahlilida ko'rsatilgan omillarni tushuntiring.**"),
  p("Diagrammada kritik (boshlang'ich) hodisa; uning sabablari va ularni bog'lovchi \"VA\", \"YOKI\" mantiqiy elementlari; hodisadan keyin vaqt ketma-ketligida ishga tushadigan himoya tizimlari (shart bloklari); har bir blokdagi \"HA\" va \"YO'Q\" chiqishlari va ularning ehtimolliklari; hamda yakuniy oqibatlar va ularning ehtimolliklari ko'rsatiladi. Bizning misolda shart bloklari EDR, tarmoq segmentatsiyasi va offline zaxira nusxadan iborat."),
  q("**7. Ushbu usulni amalga oshirish tartibi qanday?**"),
  p("a) kritik hodisa aniqlanadi; b) uning sabablarini topish uchun nosozliklar daraxti tuziladi va tekshiriladi; c) holatlarni ko'rib chiqish tartibi belgilanadi (odatda ular sodir bo'ladigan vaqt ketma-ketligida); d) har xil holatlarga qarab oqibatlarning paydo bo'lish yo'llari quriladi; e) har bir shart blokining chiqishlariga ehtimolliklar beriladi va har bir oqibat ehtimoli yo'ldagi ehtimolliklarni ko'paytirish orqali topiladi. Bir xil oqibatga olib keluvchi yo'llarning ehtimolliklari qo'shiladi, bloklar o'rtasida bog'liqlik bo'lsa, u hisobdan oldin aniqlanadi."),
  q("**8. Usulning afzallik va kamchiliklarini tushuntirib bering.**"),
  p("Afzalliklari: tizimning har tomonlama ko'rinishini beradi; sabablar va oqibatlarni bitta sxemada birlashtiradi; vaqt ketma-ketligi va kechikishlarni hisobga olish imkonini beradi; har bir oqibatning ehtimolini miqdoriy baholashga va qaysi to'siqni kuchaytirish foydaliroq ekanini aniqlashga yordam beradi. Kamchiliklari: sxemani tuzish nosozliklar daraxti yoki hodisalar daraxtining o'ziga qaraganda murakkabroq; bloklar o'rtasidagi bog'liqliklarni hisobga olish qiyin; ishonchli ehtimollik qiymatlarini topish ko'p ma'lumot talab qiladi."),

  h("Xulosa"),
  p("Ushbu amaliy mashg'ulotda axborot xavfsizligi risklarini \"Galstuk-babochka\" va \"Sabab-oqibat\" usullari yordamida tahlil qilish o'rganildi. Bank filiali serverlariga ransomware tushishi hodisasi misolida besh asosiy sabab va to'rt oqibat aniqlandi, har biri uchun oldini olish va oqibatlarni kamaytirish to'siqlari ishlab chiqildi."),
  p("\"Galstuk-babochka\" diagrammasi hodisaning umumiy manzarasini sodda va tushunarli ko'rsatdi hamda ko'p sabablar inson omiliga bog'liqligini ochib berdi. \"Sabab-oqibat\" tahlili esa bunga miqdoriy baho qo'shdi: hodisaning yillik ehtimoli taxminan 8,8 % ekanligi, halokatli oqibat ehtimoli esa EDR va zaxira nusxalarni kuchaytirish orqali 12 barobar kamaytirilishi mumkinligi hisoblab chiqildi. Ikkala usulni birgalikda qo'llash qaysi himoya choralariga birinchi navbatda mablag' ajratish kerakligini asoslab berishga imkon beradi."),

  h("Foydalanilgan adabiyotlar"),
  li("1. IEC 31010:2019. Risk management – Risk assessment techniques."),
  li("2. ISO/IEC 27005:2022. Information security, cybersecurity and privacy protection – Guidance on managing information security risks."),
  li("3. NIST SP 800-30 Rev. 1. Guide for Conducting Risk Assessments. – NIST, 2012."),
  li("4. \"Axborot xavfsizligi risklarini boshqarishga kirish\" fani bo'yicha amaliy mashg'ulotlar uchun uslubiy ko'rsatma."),
);

const k = body.indexOf("SPLIT");
const parts = [
  { children: body.slice(0, k) },
  { landscape: true, children: [img(IMG + "cca.png", 930), caption("2.3-rasm. Ransomware hodisasining sabab-oqibat diagrammasi")] },
  { children: body.slice(k + 1) },
];
L.save(L.makeDoc(parts), process.argv[2] || __dirname + "/../2-amaliy-ish.docx").then(() => console.log("ok"));
