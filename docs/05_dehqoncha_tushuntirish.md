# 05. "Dehqoncha" tushuntirish rejimi

Vositaning har bir tushuntirishi **ikki tilda** beriladi:

* **Mutaxassis uchun** — "MBA ifoda", "opaque predicate", "control-flow flattening" kabi atamalar bilan.
  Teskari muhandislik biladigan odam uchun.
* **Oddiy tilda (dehqoncha)** — kompyuterni umuman bilmaydigan odam ham tushunadigan, hayotiy
  o'xshatishlar (bozor, oshxona, dala, qulflangan xat) bilan.

Bu bo'lim shu ikkinchi rejimni tushuntiradi: nega kerak, qanday ishlaydi va qayerda ko'rinadi.

---

## 1. Nega kerak?

Loyiha himoyasi yoki namoyishida har xil odam bo'ladi: ba'zi birlari dasturlashni biladi, ba'zilari yo'q.
Agar tushuntirish faqat atamalar bilan bo'lsa, ikkinchi guruh hech narsa tushunmaydi. Shuning uchun har
bir topilma va butun funksiya uchun **o'xshatishli, atamasiz** izoh ham tayyorlanadi. Maqsad:
"obfuskatsiya" so'zini birinchi marta eshitgan odam ham vosita nima qilganini tushunsin.

## 2. Qayerda ko'rinadi?

* **Web UI** — natija tepasida **"Mutaxassis uchun / Oddiy tilda"** almashtirgichi bor. Bosilganda butun
  sahifa (funksiya xulosasi va har bir blok izohi) tanlangan tilga o'tadi. Bu faqat ko'rinish —
  serverga qayta so'rov yuborilmaydi (`_report.html` dagi kichik skript `view-simple` klassini almashtiradi).
* **Markdown va HTML hisobot** — har bir funksiyada "Oddiy tilda (dehqoncha)" bo'limi va har bir blokda
  *Oddiy tilda:* izohi bo'ladi (`report.py`).
* **Sxema** — `DeobfResult.simple_summary` (butun funksiya) va `Block.simple` (har bir blok) maydonlari
  (`schema.py`). Ular natijaning ajralmas qismi, shuning uchun offline ham, Claude ham ularni to'ldiradi.

## 3. Offline va Claude farqi

* **Offline rejim** tayyor matnlardan foydalanadi (`explain.py`): har bir chalkashtirish usuli uchun bitta
  turg'un o'xshatish yozib qo'yilgan (pastdagi jadval). Bu internetsiz, bepul va **har doim bir xil** —
  ishonchli, lekin umumlashgan.
* **Claude rejimi** xuddi shu uslubda, lekin aynan shu funksiyaga moslab yozadi (`prompts.py` dagi
  qoidalar Claude'ga o'xshatishlardan foydalanishni va atama ishlatmaslikni buyuradi). Bu jonliroq, lekin
  pullik.

Ikkala holatda ham o'xshatishlar **bir xil obrazlar oilasidan** olingan (bozor, oshxona/retsept, dala,
xat/qulf), shunda hikoya bir butun bo'lib tuyuladi.

## 4. Har bir usul uchun o'xshatish

| Usul (mutaxassis tili) | Oddiy nomi | O'xshatish |
|---|---|---|
| MBA ifoda | aylanma hisob | «5» o'rniga «20 ning choragi, ustiga 3, keyin 3 ni ayir» |
| Soxta shart (opaque predicate) | javobi doim bir xil savol | «quyosh sharqdan chiqsa, chapga yur» |
| Boshqaruv oqimini tekislash | aralashtirilgan retsept | qadamlar raqamli kartochkalarga yozilib aralashtirilgan |
| Kodlangan satr | qulflangan yozuv | so'zlar bitta kalit bilan yopiladigan/ochiladigan xat kabi |
| Yashirilgan konstanta | yashirilgan son | «50» o'rniga «120 dan 70 ni ayir» |
| O'lik / keraksiz kod | ortiqcha ish | to'g'ralgan-u qozonga solinmagan sabzi |
| Mashhur algoritm konstantasi | tanish «imzo» son | palovni zira-sabzidan tanigandek |

To'liq matnlar: `deobf_agent/explain.py` (`SIMPLE_UZ`).

---

## 5. To'liq matn: bu loyiha nima qiladi (butunlay oddiy tilda)

> Quyida kompyuterni umuman bilmaydigan odam uchun yozilgan to'liq matn. Uni himoyada yoki
> namoyishda kirish so'zi sifatida ishlatish mumkin.



Bu sahifa kompyuterni umuman bilmaydigan odam uchun yozilgan. Hamma narsani oshxona, bozor va dala misolida tushuntiramiz.

### 1. Dastur nima?

Kompyuter juda itoatkor, lekin o'zi o'ylamaydigan oshpazga o'xshaydi. Unga nima deyilsa, shuni qiladi: na ortiq, na kam. **Dastur** shu oshpaz uchun yozilgan retsept: «avval buni qil, keyin buni; agar suv qaynasa, guruchni sol». Dasturning bitta ishni bajaradigan bo'lagi **funksiya** deyiladi. U retseptdagi bitta taomga o'xshaydi.

### 2. Kompilyator — tarjimon

Dasturchi retseptni odam o'qiy oladigan tilda yozadi (bizda bu **C tili**). Kompyuterning «miyasi» esa faqat 0 va 1 lardan iborat raqamlar tilini tushunadi. **Kompilyator** tarjimon vazifasini bajaradi: odam tilidagi retseptni raqamlar tiliga o'giradi. Tarjima paytida dasturchining izohlari va narsalarning nomlari («tuz», «guruch») yo'qoladi, faqat raqamlar qoladi.

Xaridorga odatda faqat tarjima qilingan nusxa beriladi. Bu tayyor palovni berib, retseptini bermaganga o'xshaydi: ta'mini ko'rasiz, lekin qanday pishirilganini o'zingiz topishingiz kerak.

### 3. IDA nima qiladi?

Tayyor ovqatdan retseptni qayta tiklash **teskari muhandislik** deyiladi. Bu, masalan, antivirus mutaxassisiga kerak: zararli dastur (kompyuter «kasalligi») nima qilishini bilish uchun. Xuddi o'g'ri qanday kirganini izlaridan aniqlaydigan tergovchidek.

**IDA** va **Ghidra** — shunday tergovchilar ishlatadigan dasturlar. Ular raqamlar tilini qaytadan odam tiliga yaqinlashtiradi. Lekin ular chiqargan matn chala retsept bo'ladi, uni **psevdokod** deyishadi. Nomlar yo'qolgani uchun undagi hamma narsa «1-idish», «2-idish» kabi ataladi.

### 4. Nega kod «chalkash» bo'ladi?

Ba'zi odamlar retseptni ataylab chigallashtiradi. Buni **obfuskatsiya**, ya'ni chalkashtirish deyishadi. Ovqatning ta'mi o'zgarmaydi — dastur avvalgidek ishlaydi. Faqat retseptni o'qish juda qiyinlashadi.

Kim qiladi? Dastur egalari — o'z mehnatini o'g'irlatmaslik uchun. Yomon niyatli odamlar ham — o'z virusini antivirusdan yashirish uchun.

Asosiy hiylalar:

- **Aylanma hisob** — «5» o'rniga «20 ning choragi, ustiga 3, keyin 3 ni ayir».
- **Javobi doim bir xil savol** — «quyosh sharqdan chiqsa, chapga yur».
- **Aralashtirilgan retsept** — qadamlar raqamli kartochkalarga yozilib, aralashtirib tashlangan.
- **Qulflangan yozuv** — so'zlar qulflangan xat kabi yopiq saqlanadi.
- **Yashirilgan son** — «50» o'rniga «120 dan 70 ni ayir».
- **Ortiqcha ish** — to'g'ralgan, lekin qozonga solinmagan sabzi.

Vosita yana bir narsani qidiradi — **tanish «imzo» sonni**. Bu hiyla emas, aksincha, yordamchi iz: mashhur hisoblash usullarining o'ziga xos sonlari bor. Shunday son uchrasa, funksiya nima qilishini taxmin qilish osonlashadi.

### 5. Bizning vosita nima qiladi?

**deobf-agent** chigalni yechuvchi yordamchi. U shunday ishlaydi:

1. Siz IDA'dan olingan chala retseptni berasiz.
2. Vosita uni funksiyalarga, ya'ni alohida taomlarga ajratadi.
3. Har bir taomni ko'zdan kechirib, yuqoridagi hiylalarni qidiradi. Bu qism internetsiz va bepul ishlaydi.
4. Keyin ikki yo'ldan biri tanlanadi:
   - **bepul yo'l (offline)** — vosita faqat o'zi aniq bila oladigan hiylalarni tozalaydi, nomlarni esa o'zgartirmaydi;
   - **Claude yo'li** — retsept aqlli yordamchiga yuboriladi. U butun retseptni tushunib, narsalarga ma'noli nom beradi va har bir bo'lakni tushuntiradi.
5. Yangi retsept tekshiriladi (pastda batafsil).
6. Oxirida hisobot chiqadi: bir tomonda eski chalkash retsept, ikkinchi tomonda yangi toza retsept va har bir bo'lakka izoh.

### 6. Nega o'zini o'zi tekshiradi?

Dono usta «yetti o'lchab, bir kes» deydi. Vosita ham yangi retseptga ko'r-ko'rona ishonmaydi.

- Avval tarjimon (**gcc** degan kompilyator) yangi retseptni o'qib ko'radi: unda xato yo'qmi?
- So'ng eng muhim sinov boshlanadi. Eski chalkash retsept va yangi toza retsept bo'yicha bir xil masalliqlar bilan **2000 marta** ovqat pishiriladi. Masalliqlar har safar tasodifiy tanlanadi, ta'mlar esa har safar solishtiriladi.
- Bitta marta ham ta'm farq qilsa, yangi retsept noto'g'ri. U Claude'ga «mana shu yerda xato, tuzat» deb qaytariladi. Claude jami 3 martagacha urinib ko'radi.

2000 ta sinov juda kuchli dalil, lekin yuz foiz kafolat emas. Ba'zi funksiyalarni esa avtomatik sinab bo'lmaydi. Bunday paytda hisobot buni ochiq aytadi.

### 7. Claude nima?

**Claude** sun'iy intellekt, ya'ni millionlab kitob, maqola va dasturni «o'qib» o'rgangan aqlli dastur. Uni ko'p retsept ko'rgan tajribali oshpazga o'xshatish mumkin. U chala retseptga qarab: «bu palov, mana bu yer — guruchni damlash qismi» deya oladi.

Lekin Claude ba'zan ishonch bilan xato gapiradi. Shuning uchun yuqoridagi sinovlar bor.

Claude bilan ishlash pullik, ammo arzon: eng arzon turi bilan bitta funksiya taxminan dollarning mingdan bir ulushi turadi. Bir xil retseptni ikkinchi marta so'rasangiz, javob xotiradan olinadi va bepul bo'ladi.

### 8. Natijalar nimani anglatadi?

Hisobotda quyidagi yozuvlardan birini ko'rasiz:

| Yozuv | Ma'nosi |
|---|---|
| **Tasdiqlandi** | Tarjimon yangi retseptni o'qidi va 2000 sinovda ham ta'm bir xil chiqdi. Eng yaxshi natija. |
| **Kompilyatsiya bo'ldi, solishtirilmadi** | Tarjimon retseptni o'qidi, lekin ta'mini avtomatik sinab bo'lmadi. Ehtiyot bo'ling. |
| **Asl koddan farq qiladi** | Ta'm farq qildi. Bu natijaga ishonmang. |
| **Kompilyatsiya xatosi** | Tarjimon yangi retseptni o'qiy olmadi. |
| **Tekshirilmadi** | Kompyuterda tarjimon (gcc) o'rnatilmagan. |

Boshqa ko'rsatkichlar:

- **Ishonch** (past / o'rta / yuqori) — natijani yaratgan tomonning o'z bahosi. Sinov natijasi undan muhimroq.
- **Qatorlar: 32 → 11** — retsept 32 qatordan 11 qatorga qisqardi.
- **Tsiklomatik murakkablik: 9 → 2** — retseptdagi yo'l ayrilishlarini sanaydi: har bir «agar ... bo'lsa» va har bir takrorlanadigan ish. Son qancha kichik bo'lsa, retseptni tushunish shuncha oson.
- **Narx** va **vaqt** — ish qancha pul va necha soniya olgani.

### Qisqasi

Vosita chalkash retseptni oladi, undagi hiylalarni topadi va olib tashlaydi. Keyin, imkoni bo'lsa, yangi retseptni 2000 marta sinab ko'radi va har bir qadamni oddiy tilda tushuntiradi.

Bitta chegara bor: juda kuchli himoyalar (masalan, dasturni o'zining maxsus yashirin tiliga o'girib yuboradiganlari) bu loyiha doirasidan tashqarida.