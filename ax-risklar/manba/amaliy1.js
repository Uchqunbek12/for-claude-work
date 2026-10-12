const L = require("./lib");
const { p, h, li, img, caption, tcap, table, AlignmentType: A } = L;
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
  p("**Ishdan maqsad:** Axborot xavfsizligida risk tushunchasini aniqlash va risk modelini o'rganib chiqishdan iborat."),
  h("Qisqacha nazariy ma'lumotlar"),
  p("**Risk** – bu noaniqlikning maqsadlarga ta'siri. Axborot xavfsizligi (AX) nuqtai nazaridan esa **AX riski** deganda tahdid aktiv yoki aktivlar guruhining zaifligidan foydalanib, tashkilotga zarar yetkazishi ehtimoli tushuniladi."),
  p("**Tahdid** – xavf manbasining zaiflikdan foydalanib, biznesga salbiy ta'sir ko'rsatish ehtimoli. **Zaiflik** – himoya tizimidagi kamchilik bo'lib, aynan u tahdidning ro'yobga chiqishiga imkon beradi. **AX tahdidi** – axborotning maxfiyligi, yaxlitligi va foydalanuvchanligini buzishga olib kelishi mumkin bo'lgan shartlar va omillar majmui."),
  p("Risk darajasi uchta kattalikka bog'liq: aktivning biznes uchun qiymati, tahdid darajasi va zaiflik darajasi. Bu bog'liqlik 1.1-rasmda keltirilgan."),
  img(IMG + "riskmodel_c.png", 300),
  caption("1.1-rasm. Risk modeli"),
  p("**Axborot aktivi** – axborotni o'z ichiga olgan yoki uni qayta ishlash, saqlash, uzatish uchun xizmat qiladigan hamda tashkilot uchun ahamiyatga ega bo'lgan moddiy yoki nomoddiy obyekt."),
  p("Risklarni miqdoriy tahlil qilishda quyidagi ko'rsatkichlardan foydalaniladi:"),
  li("- **AV** (Asset Value) – aktivning qiymati, so'mda;"),
  li("- **EF** (Exposure Factor) – bitta hodisa sodir bo'lganda aktiv qiymatining necha foizi yo'qotilishi (0 dan 1 gacha);"),
  li("- **SLE** (Single Loss Expectancy) – bitta hodisadan kutilayotgan zarar: **SLE = AV × EF**;"),
  li("- **ARO** (Annualized Rate of Occurrence) – hodisaning bir yilda sodir bo'lish chastotasi;"),
  li("- **ALE** (Annualized Loss Expectancy) – yillik kutilayotgan zarar: **ALE = SLE × ARO**."),
  p("Himoya chorasining iqtisodiy foydasi quyidagicha baholanadi: **Foyda = ALE(choragacha) – ALE(choradan keyin) – choraning yillik narxi**. Agar foyda musbat bo'lsa, chorani joriy etish maqsadga muvofiq hisoblanadi."),

  h("Topshiriqning bajarilishi"),
  p("Topshiriqni bajarish uchun tashkilot sifatida tijorat bankining viloyat filiali tanlandi (ishda shartli ravishda **\"A-Bank\" filiali** deb ataladi). Filialda 120 nafar xodim ishlaydi, 3 ta bank xizmatlari ofisi va 20 ta bankomat mavjud, 45 mingga yaqin jismoniy va yuridik shaxslarga xizmat ko'rsatiladi. Filial avtomatlashtirilgan bank tizimi (ABS), internet-banking va mobil ilova orqali ishlaydi. Quyida keltirilgan barcha qiymatlar taxminiy bo'lib, ochiq manbalardagi o'rtacha ko'rsatkichlar va o'quv maqsadida qilingan baholashlar asosida olingan."),

  h("1-qadam: Aktivlarning qiymatini aniqlash", { italic: false }),
  p("Aktivlar qiymatini aniqlashda uslubiy ko'rsatmada keltirilgan savollarga javob berildi: aktivni sotib olish yoki ishlab chiqish narxi, uni qayta tiklash xarajati, aktiv keltiradigan foyda, shuningdek aktiv buzilganda bankka qo'llaniladigan jarimalar hisobga olindi. Masalan, mijozlar bazasi uchun nafaqat serverdagi ma'lumotni tiklash narxi, balki shaxsga doir ma'lumotlar oshkor bo'lgandagi jarimalar va mijozlarning ketib qolishi natijasidagi yo'qotishlar ham qo'shildi. Natijalar 1-jadvalda keltirilgan."),
  tcap("1-jadval", "Bank filialining asosiy axborot aktivlari"),
  table([500, 3555, 1900, 1500, 1900], [
    ["№", "Aktiv nomi", "Turi", "Qiymati (AV), mln so'm", "Muhimligi (M / Y / F)"],
    ["A1", "Mijozlar ma'lumotlar bazasi (shaxsiy va moliyaviy ma'lumotlar)", "Axborot", "4 500", "Yuqori / Yuqori / O'rta"],
    ["A2", "Avtomatlashtirilgan bank tizimi (ABS) serveri", "Dasturiy-texnik", "2 800", "Yuqori / Yuqori / Yuqori"],
    ["A3", "Internet-banking va mobil ilova", "Dasturiy (xizmat)", "1 900", "O'rta / Yuqori / Yuqori"],
    ["A4", "Bankomatlar tarmog'i (20 dona)", "Texnik", "1 200", "O'rta / Yuqori / Yuqori"],
    ["A5", "Xodimlarning ish stansiyalari va korporativ pochta (120 ta)", "Texnik / axborot", "960", "O'rta / O'rta / O'rta"],
    ["A6", "Tarmoq uskunalari va server xonasi (router, MSE, kommutatorlar)", "Texnik", "650", "Past / O'rta / Yuqori"],
    [{ t: "Jami", bold: true, span: 3, align: A.RIGHT }, { t: "12 010", bold: true, align: C }, ""],
  ], { align: [C, A.LEFT, C, C, C] }),
  p("*Izoh: M – maxfiylik, Y – yaxlitlik, F – foydalanuvchanlik.*", { noIndent: true, run: { size: 24 } }),

  h("2-qadam: Tahdiddan mumkin bo'lgan yo'qotishlarni taxmin qilish"),
  p("Har bir aktiv uchun unga xos bo'lgan asosiy tahdid va zaiflik aniqlandi. So'ngra bitta hodisa sodir bo'lganda aktiv qiymatining qancha qismi yo'qotilishi (EF) baholandi. EF ni aniqlashda jismoniy zarar, ish unumdorligining yo'qotilishi, ma'lumotlarni tiklash xarajatlari va xizmatlarning to'xtab qolish vaqti hisobga olindi. Masalan, ransomware hujumida ABS serveri shifrlanib qolsa, zaxira nusxadan tiklash, 1–2 kunlik bekor turish va qo'shimcha mutaxassislar xizmati uchun aktiv qiymatining taxminan 40 foizi yo'qotiladi, deb olindi."),
  tcap("2-jadval", "Tahdidlar, zaifliklar va bitta hodisadan kutilgan zarar (SLE)"),
  table([620, 720, 2400, 2865, 950, 700, 1100], [
    ["Risk", "Aktiv", "Tahdid", "Zaiflik", "AV, mln so'm", "EF", "SLE, mln so'm"],
    ["R1", "A2", "Ransomware (shifrlovchi zararli dastur)", "Yangilanmagan OT, RDP porti ochiq, tarmoq segmentatsiyasi yo'q", "2 800", "0,40", "1 120"],
    ["R2", "A1", "Mijozlar bazasining sirqib chiqishi (SQL-inyeksiya, insayder)", "Web-ilovada kiruvchi ma'lumotlar tekshirilmaydi, DLP yo'q", "4 500", "0,30", "1 350"],
    ["R3", "A5", "Fishing orqali xodim hisob yozuvining egallanishi", "Xodimlarning AX bo'yicha bilimi past, MFA joriy qilinmagan", "960", "0,15", "144"],
    ["R4", "A3", "DDoS hujumi", "Trafikni filtrlash xizmati yo'q, bitta provayder", "1 900", "0,10", "190"],
    ["R5", "A4", "Bankomatlarda skimming", "Antiskimming qurilmalari o'rnatilmagan", "1 200", "0,05", "60"],
    ["R6", "A6", "Server xonasida yong'in", "Avtomatik yong'in o'chirish tizimi yo'q", "650", "0,60", "390"],
  ], { align: [C, C, A.LEFT, A.LEFT, C, C, C] }),
  p("Hisoblashga misol (R1 uchun): SLE = AV × EF = 2 800 × 0,40 = 1 120 mln so'm.", { spacing: { before: 120 } }),

  h("3-qadam: Tahdidni tahlil qilish"),
  p("Har bir tahdidning yillik chastotasini (ARO) aniqlash uchun filialning AX bo'yicha mas'ul xodimi bilan suhbat o'tkazildi, o'tgan yillardagi insidentlar jurnali ko'rib chiqildi hamda bank sohasidagi hujumlar bo'yicha ochiq hisobotlardagi statistik ma'lumotlar o'rganildi. Natijalar 3-jadvalda keltirilgan."),
  tcap("3-jadval", "Tahdidlarning yillik sodir bo'lish chastotasi (ARO)"),
  table([700, 2600, 1100, 4955], [
    ["Risk", "Tahdid", "ARO", "Asoslash"],
    ["R1", "Ransomware", "0,5", "Bank sohasida bunday hujumlar ko'paygan; filialda 2 yilda 1 marta jiddiy holat kutiladi"],
    ["R2", "Bazaning sirqib chiqishi", "0,2", "Kamdan-kam bo'ladi, taxminan 5 yilda 1 marta"],
    ["R3", "Fishing", "4", "Insidentlar jurnaliga ko'ra yiliga 4 tagacha muvaffaqiyatli fishing holati qayd etilgan"],
    ["R4", "DDoS hujumi", "3", "O'tgan yili internet-banking 3 marta qisqa muddatga ishlamay qolgan"],
    ["R5", "Skimming", "2", "Viloyat bo'yicha yiliga 1–3 ta holat qayd etiladi"],
    ["R6", "Yong'in", "0,05", "Juda kam uchraydi, taxminan 20 yilda 1 marta"],
  ], { align: [C, A.LEFT, C, A.LEFT] }),

  h("4-qadam: Har bir tahdid uchun yillik zararni aniqlash"),
  p("Dastlabki uch qadamda to'plangan ma'lumotlar asosida har bir risk uchun yillik kutilayotgan zarar ALE = SLE × ARO formulasi bo'yicha hisoblandi va risklar zarar miqdoriga qarab tartiblandi (4-jadval)."),
  tcap("4-jadval", "Yillik kutilayotgan zarar (ALE) hisobi"),
  table([800, 2900, 1400, 1000, 1700, 1555], [
    ["Risk", "Tahdid", "SLE, mln so'm", "ARO", "ALE, mln so'm/yil", "O'rni"],
    ["R3", "Fishing", "144", "4", "576", "1"],
    ["R4", "DDoS hujumi", "190", "3", "570", "2"],
    ["R1", "Ransomware", "1 120", "0,5", "560", "3"],
    ["R2", "Bazaning sirqib chiqishi", "1 350", "0,2", "270", "4"],
    ["R5", "Skimming", "60", "2", "120", "5"],
    ["R6", "Yong'in", "390", "0,05", "19,5", "6"],
    [{ t: "Jami", bold: true, span: 4, align: A.RIGHT }, { t: "2 115,5", bold: true, align: C }, ""],
  ], { align: [C, A.LEFT, C, C, C, C] }),
  p("Jadvaldan ko'rinib turibdiki, eng katta yillik zararni tez-tez takrorlanadigan, lekin bir martalik zarari nisbatan kichik bo'lgan tahdidlar (fishing va DDoS) keltiradi. Ransomware va bazaning sirqib chiqishi esa kam sodir bo'lsa-da, bir martalik zarari juda katta. Shu sababli miqdoriy natijani sifat tahlili bilan ham tekshirib ko'rdik: har bir risk uchun ehtimollik va ta'sir 1 dan 5 gacha bo'lgan shkalada baholandi (5-jadval).", { spacing: { before: 120 } }),
  tcap("5-jadval", "Risklar xaritasi (sifat tahlili)"),
  riskMatrix(),
  p("*Izoh: R = ehtimollik × ta'sir; 1–5 – past (yashil), 6–10 – o'rta (sariq), 12–25 – yuqori (qizil).*", { noIndent: true, run: { size: 24 } }),
  p("Sifat tahlili natijasiga ko'ra R1, R3 va R4 yuqori darajadagi, R2 va R5 o'rta darajadagi, R6 esa past darajadagi risk hisoblanadi. R2 ning yillik zarari kichikroq chiqqan bo'lsa ham, uning ta'siri eng yuqori (5 ball), shuning uchun u e'tibordan chetda qolmasligi kerak.", { spacing: { before: 120 } }),
  p("Keyingi bosqichda har bir risk uchun qarshi choralar tanlandi va ular bo'yicha xarajat/foyda tahlili o'tkazildi (6-jadval). Choralar joriy etilgandan keyingi EF va ARO qiymatlari mutaxassis bahosi asosida olindi."),
  tcap("6-jadval", "Qarshi choralar bo'yicha xarajat / foyda tahlili"),
  table([620, 3000, 1100, 1200, 1100, 1100, 1235], [
    ["Risk", "Qarshi chora", "Yillik narxi, mln so'm", "Yangi EF / ARO", "ALE keyin, mln so'm", "ALE oldin, mln so'm", "Foyda, mln so'm"],
    ["R1", "EDR tizimi, patch-menejment, offline zaxira nusxa (3-2-1 qoidasi)", "180", "0,10 / 0,1", "28", "560", "352"],
    ["R2", "WAF, DLP tizimi, bazani shifrlash", "150", "0,10 / 0,1", "45", "270", "75"],
    ["R3", "Xodimlarni o'qitish, MFA, pochta filtri", "60", "0,10 / 1", "96", "576", "420"],
    ["R4", "Provayderning DDoS himoya xizmati, ikkinchi kanal", "120", "0,02 / 3", "114", "570", "336"],
    ["R5", "Antiskimming qurilmalari, videokuzatuv", "40", "0,05 / 0,5", "30", "120", "50"],
    ["R6", "Mulkni sug'urtalash (zararning 90 % qoplanadi)", "8", "0,06* / 0,05", "1,95", "19,5", "9,55"],
    [{ t: "Jami", bold: true, span: 2, align: A.RIGHT }, { t: "558", bold: true, align: C }, "", { t: "314,95", bold: true, align: C }, { t: "2 115,5", bold: true, align: C }, { t: "1 242,55", bold: true, align: C }],
  ], { align: [C, A.LEFT, C, C, C, C, C], size: 22 }),
  p("* Sug'urtadan keyin bankning o'zi qoplaydigan qism.", { noIndent: true, run: { size: 24, italics: true } }),
  p("Hisoblashga misol (R1 uchun): choradan keyin SLE = 2 800 × 0,10 = 280 mln so'm, ALE = 280 × 0,1 = 28 mln so'm. Foyda = 560 – 28 – 180 = 352 mln so'm. Foyda musbat, demak chorani joriy etish iqtisodiy jihatdan o'zini oqlaydi.", { spacing: { before: 120 } }),
  p("R6 uchun avval avtomatik gaz bilan yong'in o'chirish tizimi ko'rib chiqildi. Uning yillik narxi (amortizatsiya va xizmat ko'rsatish bilan) taxminan 70 mln so'm bo'lib, yillik kutilayotgan zarardan (19,5 mln so'm) bir necha barobar ko'p. Shuning uchun bu chora iqtisodiy jihatdan maqsadga muvofiq emas va uning o'rniga sug'urta tanlandi. Choralar qo'llanishidan oldingi va keyingi ALE qiymatlari 1.2-rasmda taqqoslangan."),
  img(IMG + "ale.png", 560),
  caption("1.2-rasm. Choralar joriy etilishidan oldin va keyin yillik kutilayotgan zarar"),

  h("5-qadam: Riskni kamaytirish, o'tkazish, oldini olish yoki qabul qilish"),
  p("Yuqoridagi tahlil natijalariga ko'ra har bir risk bo'yicha quyidagi qarorlar qabul qilindi (7-jadval)."),
  tcap("7-jadval", "Risklarga ishlov berish bo'yicha qarorlar"),
  table([1100, 2100, 6155], [
    ["Risk", "Qaror", "Izoh"],
    ["R1", "Kamaytirish", "EDR o'rnatiladi, yangilanishlar har oy o'rnatiladi, RDP faqat VPN orqali ishlaydi, zaxira nusxalar tarmoqdan ajratilgan holda saqlanadi"],
    ["R2", "Kamaytirish", "Web-ilova WAF orqali himoyalanadi, bazadagi shaxsga doir ma'lumotlar shifrlanadi, DLP joriy qilinadi"],
    ["R3", "Kamaytirish", "Har chorakda o'quv fishing-mashg'ulotlari, barcha xodimlar uchun ikki bosqichli autentifikatsiya"],
    ["R4", "O'tkazish va kamaytirish", "DDoS himoyasi provayderga shartnoma asosida o'tkaziladi, zaxira aloqa kanali ulanadi"],
    ["R5", "Kamaytirish", "Bankomatlarga antiskimming qurilmalari o'rnatiladi"],
    ["R6", "O'tkazish", "Server xonasi uskunalari sug'urtalanadi"],
    ["–", "Qochish", "Filialdagi internetga ochiq eski FTP-server orqali hujjat almashishdan butunlay voz kechildi, uning o'rniga himoyalangan elektron hujjat aylanishi tizimi ishlatiladi"],
    ["Qoldiq risk", "Qabul qilish", "Choralardan keyin qolgan 314,95 mln so'm/yil miqdoridagi qoldiq risk filial rahbariyati tomonidan qabul qilinadi"],
  ], { align: [C, C, A.LEFT] }),
  p("Shunday qilib, yiliga 558 mln so'm xarajat qilish orqali bankning yillik kutilayotgan zarari 2 115,5 mln so'mdan 314,95 mln so'mgacha, ya'ni taxminan 85 foizga kamayadi. Choralarning umumiy sof foydasi yiliga 1 242,55 mln so'mni tashkil etadi.", { spacing: { before: 120 } }),

  h("Nazorat savollariga javoblar"),
  p("**1. Risk, tahdid va zaiflik tushunchalariga ta'rif bering.**", { keepNext: true }),
  p("Risk – noaniqlikning maqsadlarga ta'siri; AX da esa tahdidning zaiflikdan foydalanib aktivga zarar yetkazish ehtimoli va shu zarar miqdorining birikmasi. Tahdid – axborotning maxfiyligi, yaxlitligi yoki foydalanuvchanligini buzishi mumkin bo'lgan potensial hodisa yoki harakat (masalan, xaker hujumi, yong'in). Zaiflik – himoya tizimidagi kamchilik bo'lib, tahdid aynan shu kamchilik orqali amalga oshadi (masalan, yangilanmagan dastur, zaif parol). Zaiflik bo'lmasa, tahdid zarar yetkaza olmaydi, shuning uchun risk tahdid, zaiflik va aktiv qiymatiga birgalikda bog'liq."),
  p("**2. Axborot aktivi nima va u qanday obyektlarni o'z ichiga oladi?**", { keepNext: true }),
  p("Axborot aktivi – tashkilot uchun qiymatga ega bo'lgan, axborotni o'z ichiga olgan yoki uni qayta ishlash, saqlash va uzatish uchun xizmat qiladigan moddiy yoki nomoddiy obyekt. Unga ma'lumotlar bazalari va hujjatlar, dasturiy ta'minot, serverlar va kompyuterlar, tarmoq uskunalari, xizmatlar (internet, elektr ta'minoti), xodimlar va ularning bilimlari hamda tashkilotning obro'si kabi nomoddiy aktivlar kiradi. Bizning ishimizda mijozlar bazasi, ABS serveri, internet-banking, bankomatlar, ish stansiyalari va tarmoq uskunalari aktiv sifatida olindi."),
  p("**3. Risklarni tahlil qilishning maqsadini tushuntirib bering.**", { keepNext: true }),
  p("Risklarni tahlil qilishning maqsadi – aktivlar va ularning qiymatini aniqlash, tahdid va zaifliklarni topish, tahdidlarning ehtimoli va biznesga ta'sirini baholash hamda zarar bilan himoya choralari xarajati o'rtasida iqtisodiy muvozanatni ta'minlash. Boshqacha aytganda, tahlil cheklangan mablag'ni eng xavfli joylarga yo'naltirishga yordam beradi: himoya chorasining yillik narxi u oldini oladigan zarardan oshmasligi kerak. Masalan, bizning ishimizda server xonasi uchun qimmat yong'in o'chirish tizimi o'rniga sug'urta tanlandi."),
  p("**4. Risklarni tahlil qilishning qanday bosqichlari bor?**", { keepNext: true }),
  p("Risk tahlili beshta bosqichdan iborat: 1) aktivlar va ularning qiymatini aniqlash; 2) har bir tahdid bo'yicha mumkin bo'lgan yo'qotishlarni baholash va SLE ni hisoblash; 3) tahdidlarni tahlil qilish va ularning yillik chastotasini (ARO) aniqlash; 4) har bir tahdid uchun yillik zararni (ALE) hisoblash, qarshi choralarni tanlash va ular bo'yicha xarajat/foyda tahlilini o'tkazish; 5) har bir risk bo'yicha qaror qabul qilish – uni kamaytirish, o'tkazish, undan qochish yoki qabul qilish."),

  h("Xulosa"),
  p("Ushbu amaliy ishda axborot xavfsizligidagi risk tushunchasi va risk modeli o'rganildi. Tijorat banki filiali misolida oltita asosiy axborot aktivi va ularga xos oltita risk aniqlandi, har biri uchun SLE, ARO va ALE ko'rsatkichlari hisoblandi. Tahlil shuni ko'rsatdiki, eng katta yillik zararni fishing, DDoS va ransomware hujumlari keltiradi, mijozlar bazasining sirqib chiqishi esa kam ehtimolli bo'lsa-da, eng og'ir oqibatli risk hisoblanadi."),
  p("Tanlangan qarshi choralar yillik kutilayotgan zararni taxminan 85 foizga kamaytiradi va ularga sarflangan mablag' to'liq o'zini oqlaydi. Shuningdek, ish davomida har doim ham eng kuchli himoya vositasi eng to'g'ri tanlov emasligini – ba'zi hollarda riskni sug'urta orqali o'tkazish yoki uni qabul qilish iqtisodiy jihatdan foydaliroq ekanini ko'rdik. Miqdoriy va sifat tahlillarini birgalikda qo'llash risklarni to'g'riroq baholash imkonini berdi."),

  h("Foydalanilgan adabiyotlar"),
  li("1. ISO/IEC 27005:2022. Information security, cybersecurity and privacy protection – Guidance on managing information security risks."),
  li("2. NIST SP 800-30 Rev. 1. Guide for Conducting Risk Assessments. – NIST, 2012."),
  li("3. Harris S., Maymi F. CISSP All-in-One Exam Guide. – McGraw-Hill."),
  li("4. \"Axborot xavfsizligi risklarini boshqarishga kirish\" fani bo'yicha amaliy mashg'ulotlar uchun uslubiy ko'rsatma."),
);

function riskMatrix() {
  const pos = { "5,3": "R1", "5,2": "R2", "3,5": "R3", "3,4": "R4", "2,3": "R5", "4,1": "R6" };
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

L.save(L.makeDoc(body), process.argv[2] || __dirname + "/../1-amaliy-ish.docx").then(() => console.log("ok"));
