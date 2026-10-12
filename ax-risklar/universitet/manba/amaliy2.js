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
  p("**Ishdan maqsad:** axborot xavfsizligi risklarini \"Galstuk-Babochka\" va \"Sabab-oqibat\" usullari yordamida baholash ko'nikmasini hosil qilish."),

  h("Qisqacha nazariy ma'lumot"),
  p("**\"Galstuk-babochka\"** usuli xavfli hodisaga olib keluvchi sabablarni va undan kelib chiqadigan oqibatlarni bitta sxemada ko'rsatib, ularni birgalikda tahlil qilishga imkon beradi. Sxemaning o'rtasiga hodisa qo'yiladi: chap tomonda sabablar va ularni to'xtatuvchi oldini olish to'siqlari, o'ng tomonda esa oqibatlar va zararni kamaytiruvchi to'siqlar joylashadi. Tayyor sxema babochka-galstukni eslatgani uchun usul shunday nomlangan."),
  p("**\"Sabab-oqibat\"** tahlili nosozliklar daraxti va hodisalar daraxti tahlilini o'zida birlashtiradi. Uning markazida kritik hodisa turadi. Hodisaga olib kelgan sabablar \"VA\" hamda \"YOKI\" mantiqiy elementlari yordamida, hodisadan keyingi rivojlanish esa \"himoya vositasi ishladimi?\" degan savolga javob beruvchi \"HA / YO'Q\" bloklari yordamida quriladi. Bloklarga ehtimolliklar berilsa, har bir oqibat ehtimolini son bilan hisoblash mumkin."),

  h("Topshiriqning bajarilishi"),
  p("Ikkala usul bo'yicha tahlil uchun \"B\" universitetidagi bitta hodisa olindi – **fishing orqali dekanat xodimining axborot tizimidagi hisob yozuvi buzg'unchi qo'liga o'tishi va baholarning soxtalashtirilishi**. Oliy ta'lim muassasalarida baholar, davomat, kontrakt to'lovlari va talabalarning shaxsiy ma'lumotlari odatda bitta tizimda yuritiladi, xodimlar esa kuniga o'nlab xat oladi va ular orasidan soxtasini ajratish oson emas. Shu bois fishing OTMlarda eng keng tarqalgan hujum turi hisoblanadi. Hujum odatda shunday kechadi: xodimga AT markazi nomidan xat keladi, undagi havola tizimning kirish sahifasiga o'xshash soxta saytga olib boradi, xodim login va parolini kiritadi va hujumchi shu zahoti uning nomidan tizimga kira oladi."),

  h("1. \"Galstuk-babochka\" usuli bo'yicha tahlil"),
  p("Ish uslubiy ko'rsatmadagi qadamlar ketma-ketligida bajarildi."),
  p("**1-qadam. Xavfli hodisani aniqlash.** Diagramma markaziga \"Xodim hisob yozuvining egallanishi\" hodisasi qo'yildi. Bunda begona shaxsning dekanat xodimi login-paroli bilan talabalar o'zlashtirishini hisobga oluvchi tizimga kirib, ma'lumotlarni ko'rish va o'zgartirish imkoniga ega bo'lishi nazarda tutiladi."),
  p("**2-qadam. Hodisa sabablari ro'yxatini tuzish.** AT markazining AX bo'yicha mas'ul xodimi bilan suhbat, insidentlar jurnali va ochiq manbalardagi shunga o'xshash holatlar asosida hodisaning beshta asosiy sababi ajratildi (1-jadval)."),
  p("**3-qadam. Hodisagacha rivojlanish mexanizmi.** Avval hujumchi xodimning parolini qo'lga kiritadi – fishing xat, keylogger, sirqib chiqqan parollar bazasi yoki telefon orqali aldash yo'li bilan. Tizimda MFA bo'lmagani uchun parolning o'zi yetarli. Tizimga kirgach, u ayrim talabalarning baholarini o'zgartiradi, ro'yxatlarni yuklab oladi va xodim pochtasidan hamkasblariga yangi fishing xatlar jo'natadi."),
  p("**4–5-qadamlar. Diagrammaning chap qismi va oldini olish to'siqlari.** Har bir sabab hodisa bilan chiziq orqali bog'landi, chiziq ustiga esa shu yo'lni yopuvchi himoya chorasi (to'siq) qo'yildi."),
  tcap("1-jadval", "Hodisa sabablari va oldini olish to'siqlari"),
  table([600, 3800, 4955], [
    ["№", "Sabab", "Oldini olish to'sig'i (chora)"],
    ["1", "Fishing xat orqali parolni soxta saytga kiritish", "Pochta filtri, SPF/DKIM/DMARC yozuvlari, xodimlarni o'qitish"],
    ["2", "Zaif va takroriy parollar (boshqa saytlarda ham shu parol ishlatiladi)", "Parol siyosati, ikki bosqichli autentifikatsiya (MFA)"],
    ["3", "Umumiy kompyuterlarda tizimdan chiqmaslik, parolni brauzerda saqlash", "Sessiyaning avtomatik tugashi, brauzerda parol saqlashni taqiqlash"],
    ["4", "Kompyuterga keylogger (zararli dastur) o'rnatilishi", "Antivirus / EDR, USB fleshkalardan foydalanishni cheklash"],
    ["5", "Telefon orqali ijtimoiy muhandislik (\"AT markazidan qo'ng'iroq qilyapmiz\")", "Parol hech qachon so'ralmasligi qoidasi, qo'ng'iroqni tekshirish tartibi"],
  ], { align: [C, A.LEFT, A.LEFT] }),
  p("**6–7-qadamlar. Oqibatlar va ularni kamaytirish to'siqlari.** Endi o'ng qismga hodisaning to'rtta asosiy oqibati joylashtirildi va har biriga zararni kamaytiruvchi to'siq tanlandi (2-jadval).", { spacing: { before: 120 } }),
  tcap("2-jadval", "Hodisa oqibatlari va ularni kamaytirish choralari"),
  table([600, 3800, 4955], [
    ["№", "Oqibat", "Oqibatni kamaytirish to'sig'i (chora)"],
    ["1", "Baholar va davomat ma'lumotlarining soxtalashtirilishi", "O'zgarishlar jurnali (audit log), ikki kishilik tasdiqlash, baholarni muntazam solishtirish"],
    ["2", "Talabalar shaxsiy ma'lumotlarining sirqib chiqishi", "Minimal huquqlar (rolga asoslangan kirish), ma'lumotlarni eksport qilishni cheklash"],
    ["3", "Egallangan pochtadan boshqa xodimlarga fishing xatlar tarqatilishi (hujumning kengayishi)", "G'ayritabiiy faollikni aniqlash, hisob yozuvini tezkor bloklash"],
    ["4", "Universitet obro'siga putur yetishi, tekshiruvlar va jarimalar", "Insidentga javob rejasi, rasmiy bayonot, vakolatli organlarga xabar berish"],
  ], { align: [C, A.LEFT, A.LEFT] }),
  p("To'liq \"Galstuk-babochka\" diagrammasi 2.1-rasmda ko'rsatilgan.", { spacing: { before: 120 } }),
  img(IMG + "bowtie.png", 620),
  caption("2.1-rasm. Xodim hisob yozuvining egallanishi uchun \"Galstuk-babochka\" diagrammasi"),
  p("**8-qadam. Boshqaruv bilan bog'liq yordamchi elementlar.** To'siqlar doim ishlab turishi uchun quyidagi boshqaruv elementlari belgilandi:"),
  li("- universitetning AX siyosati (parol, pochta va ma'lumot almashish qoidalari);"),
  li("- AT markazida AX bo'yicha mas'ul xodim tayinlanishi;"),
  li("- har semestrda AX bo'yicha o'quv mashg'ulotlari va o'quv fishing;"),
  li("- axborot tizimi jurnallarini har hafta ko'rib chiqish;"),
  li("- yiliga bir marta ichki audit o'tkazish."),
  p("Diagrammadan ko'rinib turibdiki, beshta sababdan to'rttasi (fishing, zaif parollar, tizimdan chiqmaslik, telefon orqali aldash) inson omiliga bog'liq. Shu sababli xodimlarni o'qitish va MFA bir yo'la bir nechta yo'lni yopadi: parol o'g'irlansa ham MFA hujumchini tizimga kiritmaydi. Oqibatlar tomonida esa asosiy to'siq – o'zgarishlar jurnali, u bo'lmasa soxta baholar sezilmay qoladi."),

  h("2. \"Sabab-oqibat\" usuli bo'yicha tahlil"),
  p("Tahlil uslubiy ko'rsatmada keltirilgan a)–e) bosqichlar bo'yicha olib borildi."),
  p("**a) Kritik hodisani aniqlash.** Kritik hodisa sifatida \"Xodim hisob yozuvi egallandi\" hodisasi olindi. U nosozliklar daraxtining yuqori hodisasi va hodisalar daraxtining boshlang'ich nuqtasi hisoblanadi."),
  p("**b) Hodisa sabablarini aniqlash.** Avval sabablar \"baliq skeleti\" ko'rinishidagi sxemada oltita guruhga ajratildi: odamlar, texnik vositalar, tashkiliy jarayonlar, autentifikatsiya, tashqi omillar va muhit (2.2-rasm)."),
  img(IMG + "fishbone.png", 620),
  caption("2.2-rasm. Hisob yozuvi egallanishi sabablarining sabab-oqibat sxemasi"),
  p("Keyin asosiy sabablar uchun nosozliklar daraxti qurildi. Yillik ehtimolliklar AT markazi ma'lumotlari va ochiq manbalar asosida berildi (taxminiy, o'quv maqsadida). Fishing orqali parol o'g'irlanishi uchun ikki shart birga bajarilishi kerak (\"VA\"): xat filtrdan o'tadi (0,2) va xodim soxta saytga parol kiritadi (0,25):"),
  p("P(fishing) = 0,2 × 0,25 = 0,05.", { align: C, noIndent: true }),
  p("Parolni tanlab topish uchun parol zaif yoki takroriy bo'lishi (0,3) va kirish urinishlari soni cheklanmagan bo'lishi (0,1) kerak:"),
  p("P(parolni topish) = 0,3 × 0,1 = 0,03.", { align: C, noIndent: true }),
  p("Keylogger ehtimoli 0,02 ga teng. Uch yo'ldan istalgani hodisaga olib keladi (\"YOKI\"):"),
  p("P(hodisa) = 1 – (1 – 0,05)(1 – 0,03)(1 – 0,02) = 1 – 0,903 ≈ 0,097.", { align: C, noIndent: true }),
  p("Demak, hodisaning yillik ehtimoli taxminan 9,7 % ga teng."),
  p("**c) Holatlarni ko'rib chiqish tartibi.** Himoya choralari ketma-ketligi: 1) notanish IP yoki qurilmadan kirish bloklanadimi; 2) jurnal soxtalashtirishni 24 soat ichida aniqlaydimi; 3) ma'lumotlar zaxira nusxadan tiklanadimi."),
  p("**d) Oqibatlarning paydo bo'lish yo'llari.** Har bir holat \"HA / YO'Q\" bloki bilan tasvirlanib, beshta oqibat (S1–S5) olindi (2.3-rasm)."),
  p("**e) Oqibatlar ehtimolini hisoblash.** Bloklar mustaqil deb olindi: oqibatning shartli ehtimoli yo'ldagi ehtimolliklar ko'paytmasiga, yillik ehtimolligi esa uning 0,097 ga ko'paytmasiga teng (3-jadval)."),
  tcap("3-jadval", "Oqibatlarning ehtimolliklari"),
  table([950, 3600, 1900, 1450, 1455], [
    ["Oqibat", "Tavsifi", "Yo'l bo'yicha hisob", "Shartli ehtimollik", "Yillik ehtimollik"],
    ["S1", "Begona kirish bloklandi, zarar yo'q", "0,5", "0,500", "0,0485"],
    ["S2", "Soxtalashtirish tez aniqlandi, zaxiradan tiklandi", "0,5 × 0,7 × 0,9", "0,315", "0,0306"],
    ["S3", "Aniqlandi, lekin baholar qo'lda tiklanadi (bir necha kun)", "0,5 × 0,7 × 0,1", "0,035", "0,0034"],
    ["S4", "Kech aniqlandi, ma'lumotlar sirqib chiqqan, baholar tiklandi", "0,5 × 0,3 × 0,9", "0,135", "0,0131"],
    ["S5", "Halokatli: soxta baholar qayd daftarchasi / diplomga o'tib ketgan", "0,5 × 0,3 × 0,1", "0,015", "0,0015"],
    [{ t: "Jami", bold: true, span: 3, align: A.RIGHT }, { t: "1,000", bold: true, align: C }, { t: "≈ 0,097", bold: true, align: C }],
  ], { align: [C, A.LEFT, C, C, C] }),
  p("Bir turdagi oqibatlarning ehtimolliklarini qo'shish mumkin. Masalan, ma'lumotlarning sirqib chiqishi yoki soxta baholarning hujjatlarga o'tib ketishi bilan bog'liq \"jiddiy va halokatli\" oqibatlar (S4 va S5) ehtimoli 0,135 + 0,015 = 0,15 ga, yillik ehtimolligi esa 0,15 × 0,097 ≈ 0,015 ga teng.", { spacing: { before: 120 } }),
  p("**Oldini olish va oqibatlarni kamaytirish choralari.** Diagramma qaysi to'siqni kuchaytirish foydaliroq ekanini ko'rsatadi. MFA to'liq joriy qilinsa (bloklash ehtimoli 0,9 gacha) va jurnal shubhali o'zgarishlar haqida avtomatik ogohlantirsa (aniqlash ehtimoli 0,9 gacha), halokatli oqibat ehtimoli 0,5 × 0,3 × 0,1 = 0,015 dan 0,1 × 0,1 × 0,1 = 0,001 gacha, ya'ni 15 barobar kamayadi. Sabablar tomonida pochta filtrini kuchaytirish (0,2 → 0,1) va kirish urinishlarini cheklash (0,1 → 0,02) kritik hodisa ehtimolini 1 – (1 – 0,025)(1 – 0,006)(1 – 0,02) ≈ 0,05 gacha, ya'ni taxminan 2 barobar pasaytiradi. Shu asosda quyidagi choralar taklif qilindi:"),
  li("- barcha xodimlar (avvalo dekanat xodimlari) uchun MFA ni joriy qilish;"),
  li("- pochta filtrini kuchaytirish, SPF/DKIM/DMARC ni sozlash;"),
  li("- kirish urinishlarini cheklash, yangi qurilmadan kirishda ogohlantirish;"),
  li("- baholar o'zgarishini jurnalga yozish va avtomatik ogohlantirish;"),
  li("- bazaning kunlik zaxira nusxasi va undan tiklashni sinab ko'rish;"),
  li("- har semestrda AX bo'yicha o'qitish va o'quv fishing o'tkazish."),

  "SPLIT",
  h("Nazorat savollariga javoblar", { before: 0 }),
  q("**1. \"Galstuk-babochka\" tahlili tushunchasiga ta'rif bering.**"),
  p("\"Galstuk-babochka\" tahlili – xavfli hodisani markazga qo'yib, unga olib keladigan sabablarni va undan kelib chiqadigan oqibatlarni bitta sxemada birlashtiradigan grafik usul. Sxemaning chap qismida sabablar va hodisani to'xtatib qoluvchi to'siqlar, o'ng qismida oqibatlar va ularning ta'sirini kamaytiruvchi to'siqlar chiziladi. Usulning asosiy vazifasi hodisa qaysi yo'llar bilan yuzaga kelishi mumkinligini va har bir yo'lda qanday himoya choralari mavjudligini ko'rsatib berishdan iborat."),
  q("**2. \"Galstuk-babochka\" tahlilida ko'rsatilgan omillarni tushuntiring.**"),
  p("Diagrammada quyidagilar aks etadi: markazda turgan xavfli hodisa; xavf manbalari va hodisani keltirib chiqaruvchi sabablar; sabab bilan hodisa orasiga qo'yiladigan oldini olish (profilaktik) to'siqlari; hodisaning oqibatlari; hodisa ro'y bergandan keyin zararni cheklovchi (tiklovchi) to'siqlar; hamda to'siqlarning ishlashini ta'minlovchi boshqaruv elementlari – siyosat va qoidalar, mas'ul xodim, o'qitish, audit va monitoring. Ushbu ishda universitet misolida beshta sabab va to'rtta oqibat ko'rib chiqildi, har biriga kamida bitta to'siq belgilandi."),
  q("**3. Ushbu usul qaysi sohalarda qo'llaniladi?**"),
  p("Usul hodisaning mumkin bo'lgan sabab va oqibatlari doirasini ko'rsatish orqali risklarni o'rganish kerak bo'lganda, to'liq nosozliklar daraxtini tuzish ortiqcha murakkab bo'lganda, har bir yo'l uchun alohida to'siq va boshqaruv choralarini belgilash talab qilinganda hamda hodisaga olib boruvchi yo'llarni bir-biridan aniq ajratish mumkin bo'lganda qo'llaniladi. Amalda u axborot xavfsizligi, ishlab chiqarish va mehnat xavfsizligi, energetika, neft-gaz, aviatsiya, sog'liqni saqlash sohalarida, shuningdek, ushbu ishdagi kabi ta'lim muassasalarida ham ishlatiladi."),
  q("**4. Usulning afzallik va kamchiliklarini tushuntirib bering.**"),
  p("Afzalliklari: sxema ko'rgazmali va mutaxassis bo'lmagan xodimlar uchun ham tushunarli (masalan, uni dekanat xodimlariga tushuntirish oson); asosiy e'tibor oldini olish va zararni kamaytirish choralariga hamda ularning yetarliligiga qaratiladi; foydali (ijobiy) hodisalarni tahlil qilishda ham qo'llash mumkin; maxsus dasturlar va yuqori malaka talab qilinmaydi. Kamchiliklari: bir nechta sabab bir vaqtda ta'sir qilgan holatlarni ko'rsatib bo'lmaydi; murakkab jarayonlar haddan tashqari soddalashib ketishi mumkin; ehtimolliklarni miqdoriy hisoblash imkoniyati cheklangan."),
  q("**5. \"Sabab-oqibat\" tahlili tushunchasiga ta'rif bering.**"),
  p("\"Sabab-oqibat\" tahlili – nosozliklar daraxti (sabablar) va hodisalar daraxti (oqibatlar) tahlilini birlashtirgan usul. Tahlil markazida kritik hodisa turadi: undan bir tomonga sabablar \"VA\", \"YOKI\" mantiqiy elementlari orqali, ikkinchi tomonga esa himoya vositalarining ishlagan yoki ishlamaganiga qarab \"HA/YO'Q\" bloklari orqali oqibatlar quriladi. Natijada tizim qanday buzilishi mumkinligi va har bir oqibatning ehtimoli aniqlanadi."),
  q("**6. \"Sabab-oqibat\" tahlilida ko'rsatilgan omillarni tushuntiring.**"),
  p("Diagramma tarkibiga kritik hodisa; uning sabablari, ularni bog'lovchi \"VA\", \"YOKI\" elementlari va quyi hodisalarning ehtimolliklari; kritik hodisadan keyin vaqt bo'yicha ketma-ket ishga tushadigan himoya vositalari (shart bloklari); har bir blokning \"HA\" va \"YO'Q\" chiqishlari va ularning ehtimolliklari; yakuniy oqibatlar va ularning ehtimolliklari kiradi. Bizning misolda shart bloklari g'ayritabiiy kirishni bloklash, o'zgarishlar jurnali orqali aniqlash va zaxira nusxadan tiklashdan iborat."),
  q("**7. Ushbu usulni amalga oshirish tartibi qanday?**"),
  p("a) kritik hodisa tanlanadi; b) uning sabablari uchun nosozliklar daraxti quriladi va tekshiriladi; c) holatlarni ko'rib chiqish tartibi belgilanadi – odatda himoya vositalari ishga tushadigan vaqt ketma-ketligida; d) har bir holatning \"HA/YO'Q\" natijasiga qarab oqibatlarga olib boruvchi yo'llar chiziladi; e) har bir shart blokiga ehtimollik beriladi va oqibat ehtimoli yo'ldagi ehtimolliklar ko'paytmasi sifatida topiladi. Bir xil oqibatga olib keluvchi yo'llarning ehtimolliklari qo'shiladi, bloklar bir-biriga bog'liq bo'lsa, bu bog'liqlik hisobdan oldin aniqlanishi kerak."),
  q("**8. Usulning afzallik va kamchiliklarini tushuntirib bering.**"),
  p("Afzalliklari: tizim har tomonlama ko'rinadi, sabablar ham, oqibatlar ham bitta sxemada joylashadi; vaqt bo'yicha ketma-ketlik va kechikishlarni hisobga olish mumkin (masalan, jurnal soxtalashtirishni 24 soat ichida aniqlaydimi); har bir oqibatning ehtimoli son bilan baholanadi va qaysi to'siqni kuchaytirish samaraliroq ekani ko'rinadi. Kamchiliklari: sxemani tuzish nosozliklar yoki hodisalar daraxtining o'zini tuzishdan murakkabroq; bloklar o'rtasidagi bog'liqliklarni hisobga olish qiyin; ishonchli ehtimollik qiymatlarini topish uchun ko'p statistik ma'lumot kerak, OTMlarda esa insidentlar statistikasi ko'pincha to'liq yuritilmaydi."),

  h("Xulosa"),
  p("Mazkur amaliy mashg'ulotda axborot xavfsizligi risklari \"Galstuk-babochka\" va \"Sabab-oqibat\" usullari yordamida tahlil qilindi. \"B\" universiteti misolida fishing orqali dekanat xodimi hisob yozuvining egallanishi hodisasi ko'rib chiqilib, uning beshta asosiy sababi va to'rtta oqibati aniqlandi, har biri uchun oldini olish va zararni kamaytirish to'siqlari tanlandi."),
  p("\"Galstuk-babochka\" diagrammasi hodisani yaxlit va ko'rgazmali tasvirladi hamda sabablarning aksariyati inson omiliga bog'liq ekanini ko'rsatdi. \"Sabab-oqibat\" tahlili esa bu manzaraga raqamlar qo'shdi: hodisaning yillik ehtimoli taxminan 9,7 % ekanligi, MFA va jurnal asosidagi avtomatik ogohlantirish joriy etilsa, halokatli oqibat ehtimoli 15 barobar kamayishi hisoblab chiqildi. Ikki usulni birga qo'llash cheklangan mablag'ni avvalo qaysi himoya choralariga yo'naltirish kerakligini asoslashga yordam beradi."),

  h("Foydalanilgan adabiyotlar"),
  li("1. IEC 31010:2019. Risk management – Risk assessment techniques."),
  li("2. ISO/IEC 27005:2022. Information security, cybersecurity and privacy protection – Guidance on managing information security risks."),
  li("3. NIST SP 800-30 Rev. 1. Guide for Conducting Risk Assessments. – NIST, 2012."),
  li("4. \"Axborot xavfsizligi risklarini boshqarishga kirish\" fani bo'yicha amaliy mashg'ulotlar uchun uslubiy ko'rsatma."),
);

const k = body.indexOf("SPLIT");
const parts = [
  { children: body.slice(0, k) },
  { landscape: true, children: [img(IMG + "cca.png", 930), caption("2.3-rasm. Xodim hisob yozuvi egallanishining sabab-oqibat diagrammasi")] },
  { children: body.slice(k + 1) },
];
L.save(L.makeDoc(parts), process.argv[2] || __dirname + "/../2-amaliy-ish-universitet.docx").then(() => console.log("ok"));
