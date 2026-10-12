const L = require("./lib");
const { h, img, caption, tcap, AlignmentType: A } = L;
// Minglik ajratuvchi bo'sh joyni bo'linmas qilib qo'yamiz ("1 541" qatorlar orasida uzilmasin)
const nb = (s) => String(s).replace(/(\d) (?=\d{3}(?!\d))/g, "$1\u00A0");
const p = (t, o) => L.p(nb(t), o);
const li = (t, o) => L.li(nb(t), o);
const table = (w, rows, o) => L.table(w, rows.map((r) => r.map((c) => (typeof c === "object" ? { ...c, t: nb(c.t) } : nb(c)))), o);
const fs = require("fs");
const IMG = __dirname + "/img/";
const title = fs.existsSync(__dirname + "/titul.json") ? JSON.parse(fs.readFileSync(__dirname + "/titul.json")) : null;
const C = A.CENTER;

const body = [];
const add = (...x) => body.push(...x.flat());

if (title) add(L.titlePage(title, "1-amaliy ish", "Risk modeli"));

add(
  h("1- amaliy ish", { before: 0 }),
  h("Mavzu: Risk modeli.", { before: 0 }),
  p("**Ishdan maqsad:** Axborot xavfsizligidagi risk tushunchasi bilan tanishish va risk modelini o'rganishdan iborat."),
  h("Qisqacha nazariy ma'lumotlar"),
  p("**Risk** deganda noaniqlikning qo'yilgan maqsadlarga ko'rsatadigan ta'siri tushuniladi. Axborot xavfsizligi (AX) sohasida esa **AX riski** – biror tahdid aktiv yoki aktivlar guruhidagi zaiflikdan foydalanib, tashkilotga zarar keltirishi ehtimolidir."),
  p("**Tahdid** – xavf manbasi zaiflikdan foydalangan holda tashkilot faoliyatiga salbiy ta'sir ko'rsatishi mumkinligi. **Zaiflik** esa himoya tizimidagi bo'shliq yoki kamchilik bo'lib, tahdidning amalga oshishiga yo'l ochib beradi. **AX tahdidi** deb axborotning maxfiyligi, yaxlitligi va foydalanuvchanligi buzilishiga sabab bo'lishi mumkin bo'lgan shart-sharoitlar va omillar yig'indisiga aytiladi."),
  p("Riskning darajasi uchta kattalik orqali aniqlanadi: aktivning tashkilot uchun qiymati, tahdid darajasi va zaiflik darajasi. Ular orasidagi bog'liqlik 1.1-rasmda ko'rsatilgan."),
  img(IMG + "riskmodel_c.png", 300),
  caption("1.1-rasm. Risk modeli"),
  p("**Axborot aktivi** deganda axborotni o'zida saqlaydigan yoki uni qayta ishlash, saqlash va uzatishda ishlatiladigan, tashkilot uchun qadrli bo'lgan moddiy yoki nomoddiy obyekt tushuniladi."),
  p("Risklar miqdoriy jihatdan tahlil qilinganda quyidagi ko'rsatkichlar ishlatiladi:", { keepNext: true }),
  li("- **AV** (Asset Value) – aktivning pul ko'rinishidagi qiymati, so'mda;"),
  li("- **EF** (Exposure Factor) – bitta hodisa yuz berganda aktiv qiymatidan yo'qotiladigan ulush (0 dan 1 gacha);"),
  li("- **SLE** (Single Loss Expectancy) – bitta hodisa keltiradigan kutilgan zarar: **SLE = AV × EF**;"),
  li("- **ARO** (Annualized Rate of Occurrence) – hodisaning bir yil davomida necha marta sodir bo'lishi;"),
  li("- **ALE** (Annualized Loss Expectancy) – bir yilda kutiladigan zarar: **ALE = SLE × ARO**."),
  p("Himoya chorasi iqtisodiy jihatdan o'zini oqlaydimi yoki yo'qmi, quyidagi formula bilan tekshiriladi: **Foyda = ALE(choragacha) – ALE(choradan keyin) – choraning yillik narxi**. Foyda musbat chiqsa, chorani joriy qilish o'rinli hisoblanadi."),

  h("Topshiriqning bajarilishi"),
  p("Amaliy ishni bajarish uchun tashkilot sifatida davlat oliy ta'lim muassasasi olindi (ishda u shartli ravishda **\"B\" universiteti** deb nomlanadi). Universitetda 12 mingga yaqin talaba tahsil oladi, 850 ga yaqin professor-o'qituvchi va xodim ishlaydi. Uning tarkibida 6 ta fakultet, axborot-resurs markazi va test (imtihon) markazi bor. Universitet masofaviy ta'lim platformasi (LMS), rasmiy web-sayt va qabul portali hamda kampus Wi-Fi tarmog'idan foydalanadi, serverlar esa bitta server xonasida joylashgan. Axborot xavfsizligi masalalari bilan Axborot texnologiyalari (AT) markazi shug'ullanadi. Ishda keltirilgan barcha qiymatlar taxminiy bo'lib, ochiq manbalardagi o'rtacha ko'rsatkichlar asosida o'quv maqsadida baholangan."),

  h("1-qadam: Aktivlarning qiymatini aniqlash", { italic: false }),
  p("Har bir aktivning qiymatini topishda uslubiy ko'rsatmada berilgan savollardan foydalanildi: aktivni xarid qilish yoki yaratish narxi, uni tiklash uchun ketadigan xarajat, aktiv olib keladigan foyda hamda aktiv buzilganda universitetga qo'llanishi mumkin bo'lgan jarimalar hisobga olindi. Masalan, talabalar va xodimlar bazasining qiymatiga faqat serverni va ma'lumotlarni tiklash narxi emas, balki shaxsga doir ma'lumotlar oshkor bo'lganda kelib chiqadigan jarimalar, tekshiruvlar va ma'lumotlarni qayta kiritishga ketadigan mehnat ham qo'shildi. Natijalar 1-jadvalga kiritildi."),
  tcap("1-jadval", "Universitetning asosiy axborot aktivlari"),
  table([560, 3595, 1800, 1500, 1900], [
    ["№", "Aktiv nomi", "Turi", "Qiymati (AV), mln so'm", "Muhimligi (M / Y / F)"],
    ["A1", "Talabalar va xodimlar ma'lumotlar bazasi (shaxsiy ma'lumotlar, baholar, kontrakt to'lovlari)", "Axborot", "3 200", "Yuqori / Yuqori / O'rta"],
    ["A2", "Masofaviy ta'lim platformasi (LMS) va elektron o'quv resurslari", "Dasturiy (xizmat)", "1 400", "O'rta / O'rta / Yuqori"],
    ["A3", "Rasmiy web-sayt va qabul portali", "Dasturiy (xizmat)", "600", "Past / Yuqori / Yuqori"],
    ["A4", "Test (imtihon) markazi: 150 ta kompyuter va test dasturi, savollar bazasi", "Dasturiy-texnik", "1 350", "Yuqori / Yuqori / Yuqori"],
    ["A5", "Xodimlarning ish kompyuterlari va korporativ pochta (400 ta)", "Texnik / axborot", "2 400", "O'rta / O'rta / O'rta"],
    ["A6", "Server xonasi va tarmoq uskunalari (Wi-Fi, kommutatorlar, MSE)", "Texnik", "900", "Past / O'rta / Yuqori"],
    [{ t: "Jami", bold: true, span: 3, align: A.RIGHT }, { t: "9 850", bold: true, align: C }, ""],
  ], { align: [C, A.LEFT, C, C, C] }),
  p("*Izoh: M – maxfiylik, Y – yaxlitlik, F – foydalanuvchanlik.*", { noIndent: true, run: { size: 24 } }),

  h("2-qadam: Tahdiddan mumkin bo'lgan yo'qotishlarni taxmin qilish"),
  p("Har bir aktiv uchun unga eng xos bo'lgan tahdid va shu tahdidga imkon beradigan zaiflik tanlandi. Keyin hodisa bir marta sodir bo'lganda aktiv qiymatining qancha ulushi yo'qotilishi (EF) baholandi. Bunda uskunalarning shikastlanishi, xodimlar ish vaqtining behuda ketishi, ma'lumotlarni tiklash xarajati va xizmat qancha vaqt ishlamay turishi e'tiborga olindi. Masalan, fishing orqali xodimning pochtasi egallansa, undan boshqalarga spam va zararli fayllar tarqatiladi, zararlangan kompyuterlarni tozalashga to'g'ri keladi va ish vaqti yo'qoladi; shuning uchun bunday hodisada aktiv qiymatining taxminan 5 foizi yo'qotiladi, deb hisoblandi."),
  tcap("2-jadval", "Tahdidlar, zaifliklar va bitta hodisadan kutilgan zarar (SLE)"),
  table([680, 800, 2500, 2475, 1050, 700, 1150], [
    ["Risk", "Aktiv", "Tahdid", "Zaiflik", "AV, mln so'm", "EF", "SLE, mln so'm"],
    ["R1", "A1", "Ma'lumotlar bazasining sirqib chiqishi (SQL-inyeksiya)", "Web-ilovada kiruvchi ma'lumotlar tekshirilmaydi, baza shifrlanmagan", "3 200", "0,25", "800"],
    ["R2", "A2", "DDoS hujumi (imtihon sessiyasi paytida)", "Trafikni filtrlash yo'q, yuklamani taqsimlash (load balancer) yo'q", "1 400", "0,08", "112"],
    ["R3", "A3", "Saytning buzilishi (deface) va zararli kod joylashtirilishi", "CMS va plaginlar yangilanmagan, admin panelga zaif parol", "600", "0,30", "180"],
    ["R4", "A4", "Imtihon savollarining sizib chiqishi / natijalarni soxtalashtirish (insayder)", "Administrator huquqlari nazoratsiz, harakatlar jurnali yuritilmaydi", "1 350", "0,20", "270"],
    ["R5", "A5", "Fishing orqali xodim hisob yozuvlarining egallanishi", "MFA yo'q, xodimlarning AX bo'yicha bilimi past", "2 400", "0,05", "120"],
    ["R6", "A6", "Elektr ta'minotidagi uzilish va kuchlanish sakrashi (uskunalar ishdan chiqishi)", "UPS eskirgan, kuchlanish stabilizatori yo'q", "900", "0,25", "225"],
  ], { align: [C, C, A.LEFT, A.LEFT, C, C, C] }),
  p("Hisoblashga misol (R1 uchun): SLE = AV × EF = 3 200 × 0,25 = 800 mln so'm.", { spacing: { before: 120 } }),

  h("3-qadam: Tahdidni tahlil qilish"),
  p("Tahdidlarning bir yildagi takrorlanish chastotasini (ARO) aniqlash maqsadida AT markazining mas'ul xodimi bilan suhbatlashildi, insidentlar jurnalidagi so'nggi yillar yozuvlari ko'rib chiqildi, shuningdek oliy ta'lim muassasalariga qarshi hujumlar haqida ochiq manbalardagi ma'lumotlar o'rganildi. Olingan qiymatlar 3-jadvalda berilgan."),
  tcap("3-jadval", "Tahdidlarning yillik sodir bo'lish chastotasi (ARO)"),
  table([700, 2600, 1000, 5055], [
    ["Risk", "Tahdid", "ARO", "Asoslash"],
    ["R1", "Bazaning sirqib chiqishi", "0,25", "OTM saytlariga SQL-inyeksiya urinishlari tez-tez bo'ladi, muvaffaqiyatli holat taxminan 4 yilda 1 marta kutiladi"],
    ["R2", "DDoS hujumi", "3", "O'tgan o'quv yilida imtihon sessiyalari paytida LMS 3 marta ishlamay qolgan"],
    ["R3", "Saytning buzilishi", "1", "Sayt yiliga taxminan 1 marta buziladi yoki unda zararli kod aniqlanadi"],
    ["R4", "Savollarning sizib chiqishi", "0,5", "2 yilda 1 marta test savollari tarqalib ketgan holat qayd etilgan"],
    ["R5", "Fishing", "5", "AT markazi ma'lumotiga ko'ra yiliga 5 tagacha xodimning pochtasi buzilgan"],
    ["R6", "Elektr uzilishi", "0,4", "So'nggi 5 yilda 2 marta uskunalar ishdan chiqqan"],
  ], { align: [C, A.LEFT, C, A.LEFT] }),

  h("4-qadam: Har bir tahdid uchun yillik zararni aniqlash"),
  p("Oldingi qadamlarda topilgan SLE va ARO qiymatlaridan foydalanib, har bir risk bo'yicha yillik kutilayotgan zarar ALE = SLE × ARO formulasi orqali hisoblandi. So'ngra risklar zarar miqdori kamayib borish tartibida joylashtirildi (4-jadval)."),
  tcap("4-jadval", "Yillik kutilayotgan zarar (ALE) hisobi"),
  table([800, 3000, 1350, 1000, 1700, 1505], [
    ["Risk", "Tahdid", "SLE, mln so'm", "ARO", "ALE, mln so'm/yil", "O'rni"],
    ["R5", "Fishing", "120", "5", "600", "1"],
    ["R2", "DDoS hujumi", "112", "3", "336", "2"],
    ["R1", "Bazaning sirqib chiqishi", "800", "0,25", "200", "3"],
    ["R3", "Saytning buzilishi", "180", "1", "180", "4"],
    ["R4", "Savollarning sizib chiqishi", "270", "0,5", "135", "5"],
    ["R6", "Elektr uzilishi", "225", "0,4", "90", "6"],
    [{ t: "Jami", bold: true, span: 4, align: A.RIGHT }, { t: "1 541", bold: true, align: C }, ""],
  ], { align: [C, A.LEFT, C, C, C, C] }),
  p("4-jadvaldan ko'rinadiki, yillik zararning eng kattasi tez-tez takrorlanadigan, ammo har safar nisbatan kam zarar keltiradigan hodisalarga – fishing va DDoS hujumlariga to'g'ri keladi. Ma'lumotlar bazasining sirqib chiqishi esa kamdan-kam sodir bo'ladi, lekin uning bir martalik zarari eng katta (800 mln so'm). Shu sababli miqdoriy hisob natijasini sifat tahlili bilan ham solishtirdik: har bir riskning ehtimolligi va ta'siri 1 dan 5 gacha bo'lgan shkala bo'yicha baholandi (5-jadval).", { spacing: { before: 120 } }),
  tcap("5-jadval", "Risklar xaritasi (sifat tahlili)"),
  riskMatrix(),
  p("*Izoh: R = ehtimollik × ta'sir; 1–5 – past (yashil), 6–10 – o'rta (sariq), 12–25 – yuqori (qizil).*", { noIndent: true, run: { size: 24 } }),
  p("Sifat tahliliga ko'ra R2 va R5 yuqori darajadagi, R1, R3 va R4 o'rta darajadagi, R6 esa past darajadagi risklar qatoriga kirdi. R1 yillik zarar bo'yicha uchinchi o'rinda bo'lsa-da, uning ta'siri eng yuqori – 5 ball: talabalar va xodimlarning shaxsiy ma'lumotlari oshkor bo'lishi universitet uchun qonuniy javobgarlikni keltirib chiqaradi. R4 ning pulda ifodalangan zarari uncha katta emas, biroq u universitet obro'siga va imtihonlarning adolatli o'tishiga jiddiy putur yetkazadi, bu esa pul ko'rinishida to'liq aks etmaydi.", { spacing: { before: 120 } }),
  p("Keyin har bir risk uchun qarshi choralar belgilandi va ularning xarajati foydasi bilan solishtirildi (6-jadval). Choralar joriy qilingandan keyingi EF va ARO qiymatlari mutaxassis bahosiga tayanib olindi."),
  tcap("6-jadval", "Qarshi choralar bo'yicha xarajat / foyda tahlili"),
  table([680, 2900, 1100, 1350, 1100, 1100, 1125], [
    ["Risk", "Qarshi chora", "Yillik narxi, mln so'm", "Yangi EF / ARO", "ALE keyin, mln so'm", "ALE oldin, mln so'm", "Foyda, mln so'm"],
    ["R1", "WAF, kodni tuzatish (parametrli so'rovlar), bazani shifrlash, kirish jurnali", "90", "0,10 / 0,05", "16", "200", "94"],
    ["R2", "Provayderning DDoS himoya xizmati, yuklamani taqsimlash (load balancer)", "110", "0,03 / 2", "84", "336", "142"],
    ["R3", "CMS va plaginlarni yangilash, admin panelga MFA, saytning kunlik zaxira nusxasi", "30", "0,10 / 0,3", "18", "180", "132"],
    ["R4", "Rolga asoslangan kirish, harakatlar jurnali (audit log), videokuzatuv, savollar bazasini shifrlash", "45", "0,10 / 0,1", "13,5", "135", "76,5"],
    ["R5", "Xodimlar uchun MFA, o'quv mashg'ulotlari, pochta filtri", "70", "0,03 / 1,5", "108", "600", "422"],
    ["R6", "UPS ni yangilash, kuchlanish stabilizatori", "25", "0,03 / 0,4", "10,8", "90", "54,2"],
    [{ t: "Jami", bold: true, span: 2, align: A.RIGHT }, { t: "370", bold: true, align: C }, "", { t: "250,3", bold: true, align: C }, { t: "1 541", bold: true, align: C }, { t: "920,7", bold: true, align: C }],
  ], { align: [C, A.LEFT, C, C, C, C, C], size: 22 }),
  p("Hisoblashga misol (R5 uchun): choralardan keyin SLE = 2 400 × 0,03 = 72 mln so'm, ALE = 72 × 1,5 = 108 mln so'm. Foyda = 600 – 108 – 70 = 422 mln so'm. Foyda musbat bo'lgani uchun bu chorani joriy qilish iqtisodiy jihatdan o'zini oqlaydi.", { spacing: { before: 120 } }),
  p("R3 uchun dastlab saytni to'liq bulutli himoyalangan hostingga ko'chirish va tijoriy WAF xizmatini sotib olish varianti ham ko'rib chiqildi. Biroq bu variantning yillik narxi taxminan 220 mln so'mni tashkil etadi va yillik kutilayotgan zarardan (180 mln so'm) ham ko'p. Demak, u maqsadga muvofiq emas, shuning uchun arzonroq chora – CMS ni yangilash, MFA va zaxira nusxa tanlandi. Choralar joriy qilinishidan oldingi va keyingi ALE qiymatlari 1.2-rasmda solishtirilgan."),
  img(IMG + "ale.png", 560),
  caption("1.2-rasm. Choralar joriy qilinishidan oldin va keyin yillik kutilayotgan zarar"),

  h("5-qadam: Riskni kamaytirish, o'tkazish, oldini olish yoki qabul qilish"),
  p("O'tkazilgan tahlil natijalariga tayanib, har bir risk bo'yicha quyidagi qarorlar qabul qilindi (7-jadval)."),
  tcap("7-jadval", "Risklarga ishlov berish bo'yicha qarorlar"),
  table([1100, 2100, 6155], [
    ["Risk", "Qaror", "Izoh"],
    ["R1", "Kamaytirish", "Web-ilova WAF orqasiga olinadi, dastur kodi parametrli so'rovlarga o'tkaziladi, bazadagi shaxsiy ma'lumotlar shifrlanadi, bazaga kirishlar jurnalda qayd etiladi"],
    ["R2", "O'tkazish va kamaytirish", "DDoS himoyasi provayder bilan tuzilgan shartnoma asosida unga o'tkaziladi, LMS serverlari oldiga yuklamani taqsimlash qurilmasi qo'yiladi"],
    ["R3", "Kamaytirish", "CMS va plaginlar muntazam yangilanadi, admin panelga ikki bosqichli autentifikatsiya qo'yiladi, sayt har kuni zaxiralanadi"],
    ["R4", "Kamaytirish", "Test markazida rolga asoslangan kirish joriy qilinadi, administrator harakatlari jurnalga yoziladi, videokuzatuv o'rnatiladi, savollar bazasi shifrlanadi"],
    ["R5", "Kamaytirish", "Barcha xodimlar uchun MFA, har semestrda AX bo'yicha o'quv mashg'ulotlari, pochta filtri"],
    ["R6", "Kamaytirish", "Eskirgan UPS lar almashtiriladi, server xonasiga kuchlanish stabilizatori o'rnatiladi"],
    ["–", "Qochish", "Xodimlarga talabalarning shaxsiy ma'lumotlarini tashqi bepul fayl almashish xizmatlari va messenjer guruhlari orqali yuborish butunlay taqiqlandi, buning o'rniga universitetning ichki elektron hujjat aylanishi tizimi ishlatiladi"],
    ["Qoldiq risk", "Qabul qilish", "Choralardan keyin qoladigan 250,3 mln so'm/yil miqdoridagi qoldiq risk rektorat tomonidan qabul qilinadi"],
  ], { align: [C, C, A.LEFT] }),
  p("Natijada universitet yiliga 370 mln so'm sarflab, yillik kutilayotgan zararni 1 541 mln so'mdan 250,3 mln so'mgacha, ya'ni taxminan 84 foizga kamaytiradi. Barcha choralarning umumiy sof foydasi yiliga 920,7 mln so'mga teng bo'ladi.", { spacing: { before: 120 } }),

  h("Nazorat savollariga javoblar"),
  p("**1. Risk, tahdid va zaiflik tushunchalariga ta'rif bering.**", { keepNext: true }),
  p("Risk – noaniqlikning maqsadlarga ta'siri. AX da risk deganda tahdidning biror zaiflikdan foydalanib aktivga zarar yetkazish ehtimoli va bu zararning kattaligi birgalikda tushuniladi. Tahdid – axborotning maxfiyligi, yaxlitligi yoki foydalanuvchanligiga zarar yetkazishi mumkin bo'lgan hodisa yoki harakat (masalan, DDoS hujumi, fishing, elektr uzilishi). Zaiflik – himoyadagi kamchilik bo'lib, tahdid aynan u orqali amalga oshadi (masalan, yangilanmagan CMS, MFA yo'qligi). Agar zaiflik bartaraf etilsa, tahdid ro'yobga chiqa olmaydi, shuning uchun risk aktiv qiymati, tahdid va zaiflikning birgalikdagi natijasi hisoblanadi."),
  p("**2. Axborot aktivi nima va u qanday obyektlarni o'z ichiga oladi?**", { keepNext: true }),
  p("Axborot aktivi – tashkilot uchun qadrli bo'lgan, axborotni saqlaydigan yoki uni qayta ishlash, saqlash va uzatishga xizmat qiladigan moddiy yoki nomoddiy obyekt. Aktivlar qatoriga ma'lumotlar bazalari va hujjatlar, dasturiy ta'minot va axborot tizimlari, serverlar, kompyuterlar va tarmoq uskunalari, tashqi xizmatlar (internet, elektr ta'minoti), xodimlar va ularning bilimi, shuningdek tashkilotning obro'si kabi nomoddiy boyliklar kiradi. Ushbu ishda universitetning talabalar va xodimlar bazasi, LMS platformasi, web-sayt va qabul portali, test markazi, xodimlarning kompyuterlari hamda server xonasi va tarmoq uskunalari aktiv sifatida ko'rildi."),
  p("**3. Risklarni tahlil qilishning maqsadini tushuntirib bering.**", { keepNext: true }),
  p("Risk tahlilining maqsadi – qaysi aktivlar qimmatli ekanini aniqlash, ularga qanday tahdidlar va zaifliklar xavf solishini topish, tahdidlarning ehtimoli va tashkilot faoliyatiga ta'sirini baholash va shu asosda kutilayotgan zarar bilan himoya xarajatlari orasida iqtisodiy muvozanat topish. Tahlil cheklangan byudjetni eng xavfli yo'nalishlarga sarflashga yordam beradi: himoya chorasining yillik narxi u kamaytiradigan zarardan oshib ketmasligi lozim. Masalan, bizning ishimizda saytni qimmat bulutli hostingga ko'chirish yillik zarardan qimmatga tushgani uchun undan voz kechildi va arzonroq chora tanlandi."),
  p("**4. Risklarni tahlil qilishning qanday bosqichlari bor?**", { keepNext: true }),
  p("Risk tahlili besh bosqichda olib boriladi: 1) aktivlarni aniqlash va ularning qiymatini baholash; 2) har bir tahdid bo'yicha ehtimoliy yo'qotishlarni baholab, SLE ni hisoblash; 3) tahdidlarni tahlil qilib, ularning yillik chastotasini (ARO) topish; 4) har bir tahdid uchun yillik zararni (ALE) hisoblash, qarshi choralarni tanlash va xarajat/foyda tahlilini o'tkazish; 5) har bir risk yuzasidan qaror qabul qilish – riskni kamaytirish, boshqa tomonga o'tkazish, undan qochish yoki uni qabul qilish."),

  h("Xulosa"),
  p("Mazkur amaliy ishda axborot xavfsizligidagi risk tushunchasi va risk modeli o'rganib chiqildi. \"B\" universiteti misolida oltita asosiy axborot aktivi va ularning har biriga tegishli oltita risk aniqlanib, ular uchun SLE, ARO va ALE ko'rsatkichlari hisoblandi. Tahlil natijasida eng katta yillik zararni fishing va DDoS hujumlari keltirishi, eng og'ir oqibatli risk esa talabalar va xodimlar ma'lumotlar bazasining sirqib chiqishi ekani aniqlandi."),
  p("Tanlangan qarshi choralar yillik kutilayotgan zararni taxminan 84 foizga kamaytiradi va ularga sarflanadigan mablag' to'liq o'zini qoplaydi. Ish davomida eng qimmat himoya har doim ham eng to'g'ri yechim bo'lavermasligi ham ko'rindi: R3 misolida arzonroq chora ancha foydali chiqdi. Miqdoriy va sifat tahlilini birga qo'llash esa pul bilan o'lchab bo'lmaydigan oqibatlarni, masalan, universitet obro'si va imtihonlarning adolatliligini ham hisobga olish imkonini berdi."),

  h("Foydalanilgan adabiyotlar"),
  li("1. ISO/IEC 27005:2022. Information security, cybersecurity and privacy protection – Guidance on managing information security risks."),
  li("2. NIST SP 800-30 Rev. 1. Guide for Conducting Risk Assessments. – NIST, 2012."),
  li("3. Harris S., Maymi F. CISSP All-in-One Exam Guide. – McGraw-Hill."),
  li("4. \"Axborot xavfsizligi risklarini boshqarishga kirish\" fani bo'yicha amaliy mashg'ulotlar uchun uslubiy ko'rsatma."),
);

// Risklar xaritasi: kalit "ta'sir,ehtimollik"
function riskMatrix() {
  const pos = { "5,2": "R1", "3,4": "R2", "3,3": "R3", "4,2": "R4", "3,5": "R5", "2,2": "R6" };
  const col = (s) => (s >= 12 ? "F4B183" : s >= 6 ? "FFE699" : "C6E0B4");
  const rows = [[{ t: "Ta'sir \\ Ehtimollik", head: true }, "1 – juda kam", "2 – kam", "3 – o'rta", "4 – yuqori", "5 – juda yuqori"]];
  const imp = ["5 – halokatli", "4 – jiddiy", "3 – o'rta", "2 – kichik", "1 – juda kichik"];
  for (let i = 5; i >= 1; i--) {
    const r = [{ t: imp[5 - i], head: true }];
    for (let j = 1; j <= 5; j++) {
      const s = i * j;
      const lab = pos[`${i},${j}`];
      r.push({ t: lab ? `${lab} (${s})` : String(s), fill: col(s), bold: !!lab, align: C });
    }
    rows.push(r);
  }
  return table([1955, 1480, 1480, 1480, 1480, 1480], rows);
}

L.save(L.makeDoc(body), process.argv[2] || __dirname + "/../1-amaliy-ish-universitet.docx").then(() => console.log("ok"));
