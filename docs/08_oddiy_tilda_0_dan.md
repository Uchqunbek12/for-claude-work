# 08. Loyihani 0 dan, oddiy so'zlar bilan

> **Kim uchun.** Kompyuter va dasturlash haqida deyarli hech narsa bilmasangiz ham, loyihani tushunib, boshqaga ayta olishingiz uchun.
> **Qancha vaqt.** Taxminan 20 daqiqa. **Qanday o'qish.** Boshidan tartib bilan: har bo'lim oldingisiga tayanadi.
> Qiyin so'z **qalin** yoziladi va darhol izohlanadi. Hammasi tushunarli bo'lgach, chuqurroq ma'lumot kerak bo'lsa: `07_hammasi_0_dan_va_ustoz_savollari.md`.

## Mundarija

1. Bir minutda: loyiha nima?
2. Dastur nima va uni nega tushunish qiyin?
3. Ataylab chalkashtirishning 5 usuli
4. Bizning dastur nima qiladi (4 qadam)
5. Dasturning «aqli»: qoidalar va sun'iy intellekt
6. Eng muhim g'oya: tekshirish
7. «Agent» degani nima?
8. Bizning sayt va uni ishlatish
9. Nima qildik (hikoya)
10. Natijalar (uchta raqam)
11. Nima ishlamaydi (halol)
12. Oddiy savol-javob
13. Ustozga 3 daqiqalik gap
14. Mini lug'at
15. Qaysi hujjat nima uchun

---

## 1. Bir minutda: loyiha nima?

Tasavvur qiling, sizga **palov retsepti** berishdi. Lekin retsept ataylab chigal yozilgan:

* qadamlar **aralashtirib tashlangan** (avval «guruch solinadi», keyin «suv quyiladi», keyin yana «qozon olinadi»...);
* orasiga **keraksiz qadamlar** qo'shilgan («sabzini to'g'rang va uni tashlab yuboring»);
* oddiy «besh ta olma» o'rniga «yigirmatadan to'rtdan bir» deb yozilgan.

Siz bu retseptni tushunib, to'g'ri palov pishirishingiz kerak. Qo'lda buni qilish soatlab vaqt oladi.

**Bizning dastur shu ishni qiladigan yordamchi:**

1. keraksiz va chalkash joylarni **topadi**;
2. retseptni tartibga solib, oddiy qilib **qayta yozadi**;
3. **ikkala retseptni ham pishirib, ta'mini solishtiradi** (bu eng muhim qadam: yangi retsept haqiqatan eskisi bilan bir xil palov beradimi?);
4. har bir qadamni oddiy so'zlar bilan **tushuntiradi**.

Dasturlar dunyosida «retsept» — **dastur kodi**. Qolgan hammasi shu g'oyaning kompyuterdagi ko'rinishi.

---

## 2. Dastur nima va uni nega tushunish qiyin?

**Dastur** — kompyuterga yozilgan ko'rsatmalar to'plami, xuddi retsept kabi. Dasturchi uni odam o'qiy oladigan tilda yozadi (masalan, **C** tilida). Bu yozuv **kod** deyiladi.

Kompyuter odam tilini tushunmaydi, unga faqat 0 va 1 lar kerak. Shuning uchun maxsus dastur (**kompilyator**) kodni 0 va 1 larga aylantiradi. Hosil bo'lgan fayl (`.exe`) foydalanuvchiga beriladi. Dasturchi yozgan chiroyli kod esa berilmaydi.

```
   dasturchi yozgan kod  ──kompilyator──►  0 va 1 lar (.exe)   ← foydalanuvchiga shu beriladi
   (o'qiladi)                              (o'qib bo'lmaydi)
```

**Savol:** agar sizga begona `.exe` fayl tushib qolsa va uning ichida nima borligini bilishingiz kerak bo'lsa-chi? Masalan, bu virusmi? Shunda **teskari muhandislik** (reverse engineering) qilinadi: tayyor narsadan uning ichini tushunishga harakat. Buni antivirus mutaxassislari va xavfsizlik tadqiqotchilari qiladi.

Bunda ikkita mashhur dastur yordam beradi: **IDA** va **Ghidra**. Ular 0 va 1 larni **psevdokod** deb ataladigan narsaga aylantiradi. Psevdokod — «kodga o'xshash matn»: asl kodning o'zi emas, lekin o'qishga yaqin. Unda dasturchi qo'ygan chiroyli nomlar yo'q, faqat `v1`, `v2`, `a1` kabi bo'sh nomlar bor:

```c
v0 = a1;
v1 = 0;
v1 = v1 + v0;
```

Hali bir muammo: virus yozuvchilar psevdokodni ham **ataylab** tushunib bo'lmaydigan qilib yozadi. Bu **obfuskatsiya** deyiladi («ataylab chalkashtirish»). Dastur xuddi shunday ishlaydi, lekin o'qib tushunish juda qiyin. Chalkashtirishdan maqsad: tahlilchi charchasin va tushunolmasin.

**Bizning loyiha aynan shu psevdokodni oladi va tushunarli qiladi.** Bu «deobfuskatsiya» (chalkashlikni olib tashlash) deyiladi.

> Muhim farq. Biz **asl kodni qaytarmaymiz** (u 0 va 1 larga aylanganda yo'qolgan, qaytarib bo'lmaydi). Biz «shu psevdokod bilan **bir xil ishlaydigan**, lekin tushunarli kod» beramiz.

---

## 3. Ataylab chalkashtirishning 5 usuli

Dastur ularni taniydi. Har biri uchun hayotiy misol:

| # | Usul | Oddiy misol | Biz nima qilamiz |
|---|---|---|---|
| 1 | **Uzun yo'lli hisob** (MBA) | Sotuvchi «besh ming» demaydi, «yigirma mingning to'rtdan biri, ustiga uch ming qo'sh, uch mingni ayir» deydi. Narx baribir besh ming | Uzun hisobni qisqa shakliga almashtiramiz va ikkalasi bir xil ekanini sinab ko'ramiz |
| 2 | **Javobi doim bir xil savol** (soxta shart) | Yo'lda yozuv: «Quyosh sharqdan chiqsa, chapga yur». Quyosh doim sharqdan chiqadi, demak hamma doim chapga yuradi, «o'ng»ga yo'l hech qachon ochilmaydi | Bunday savolni va hech qachon bajarilmaydigan yo'lni olib tashlaymiz |
| 3 | **Aralashtirilgan retsept** | Retsept qadamlari alohida kartochkalarga yozilgan va aralashtirib tashlangan; har kartochkada «keyingi kartochka: 77» | Kartochkalarni to'g'ri tartibga teramiz va oddiy retsept qilib yozamiz |
| 4 | **Qulflangan yozuv** | Xatdagi har harf boshqa belgiga almashtirilgan; kalit bor odam o'qiy oladi | Kalitni topib, yashirilgan matnni ochamiz |
| 5 | **Ortiqcha ish** | Oshpaz sabzi to'g'raydi-yu, qozonga solmay tashlab qo'yadi | Natijaga ta'sir qilmaydigan ishni olib tashlaymiz |

---

## 4. Bizning dastur nima qiladi (4 qadam)

```
   chigal psevdokod ─► 1. TOPISH ─► 2. SODDALASHTIRISH ─► 3. TEKSHIRISH ─► 4. TUSHUNTIRISH ─► toza kod + izohlar
```

**Haqiqiy misol** (loyihadagi `s1_mba` namunasi). Kirishda shunday qator bor edi:

```c
v0 = (a0 & a1) * 2 + (a0 ^ a1);
```

1. **Topish.** Dastur ko'radi: bu «uzun yo'lli hisob» (1-usul).
2. **Soddalashtirish.** Dastur uni qisqa shaklga almashtiradi: `v0 = a0 + a1;`
3. **Tekshirish.** Ikkala shaklga bir xil sonlar beriladi (masalan, 5 va 3): birinchisi 8 beradi, ikkinchisi ham 8. Buni 2000 marta, har xil sonlar bilan takrorlaydi. Hammasida bir xil bo'lsa: «Tasdiqlandi».
4. **Tushuntirish.** Dastur yozadi: «Bu yerda oddiy qo'shish ataylab uzun yozilgan, xuddi bozorda narx aylanma hisoblangandek. Biz uni oddiy qo'shishga almashtirdik».

Natijada tahlilchi soatlar o'rniga daqiqalarda tushunadi.

---

## 5. Dasturning «aqli»: qoidalar va sun'iy intellekt

2-qadamda («soddalashtirish») kim ishlaydi? Ikki yo'l bor, ikkalasi ham dasturda:

### 5.1. Qoidalar (Offline rejim)

Oldindan yozib qo'yilgan «agar shunday bo'lsa, buni qil» qoidalari. Masalan: «agar `(a & b)*2 + (a ^ b)` ko'rsang, uni `a + b` ga almashtir».

* ✅ **Bepul**, tez, har safar bir xil natija.
* ❌ Faqat **oldindan biladigan** shakllarni tushunadi. Yangi usul chiqsa, ojiz.

### 5.2. Sun'iy intellekt (LLM): DeepSeek yoki Claude

**LLM** — odam kabi matnni o'qiydigan va yoza oladigan katta dastur. **DeepSeek** va **Claude** — ikki xil kompaniyaning LLM'lari. Biz ularga psevdokodni beramiz va «buni tushunarli qilib yoz» deymiz.

* ✅ Yangi, noma'lum usullarni ham tushunadi; o'zgaruvchilarga ma'noli nom beradi; chiroyli tushuntiradi.
* ❌ **Xato qilishi mumkin**, va xatoni ham ishonch bilan aytadi. Shuning uchun uning javobiga ko'r-ko'rona ishonmaymiz (6-bo'lim).
* ❌ Pullik.

### 5.3. API kalit nima? (pul haqida)

Sun'iy intellektdan foydalanish uchun dasturimiz DeepSeek'ning serveriga so'rov yuboradi. Server «sen kimsan, kimning hisobidan to'lanadi?» deb so'raydi. Javob — **API kalit**: uzun harf-raqamlar qatori (`sk-...`).

> Kalit **oldindan to'langan mobil raqamning PIN kodiga** o'xshaydi. Kimda kalit bo'lsa, shu hisobdan pul sarflay oladi. Shuning uchun kalitni **hech kimga bermaymiz, chatga yozmaymiz, kodga yozmaymiz**. U faqat Render saytining maxfiy sozlamalarida turadi.

**Narx qanday?** Matn **token** deb ataladigan bo'laklarga bo'linadi (bir token ≈ 3-4 harf). Pul bo'laklar soniga qarab olinadi. Bizning o'lchovimiz:

* **DeepSeek:** bitta funksiya ≈ **0.35 sent** (1 dollarga taxminan 280 ta funksiya);
* **Claude Sonnet:** bitta funksiya ≈ 3 sent (taxminan 10 baravar qimmat).

Shuning uchun endi asosiy model — DeepSeek. Dastur ikkalasini ham biladi: qaysi kalitingiz bo'lsa, o'shani ishlatadi.

---

## 6. Eng muhim g'oya: tekshirish

Sun'iy intellekt chiroyli, ishonchli ko'rinadigan, lekin **boshqacha ishlaydigan** kod yozishi mumkin. Agar tahlilchi noto'g'ri kodga tayansa, virus haqida noto'g'ri xulosa chiqaradi. Shuning uchun loyihaning yuragi sun'iy intellekt emas, **tekshirish**.

### «Ikki kalkulyator» misoli

Sizda ikkita kalkulyator bor: eskisi (chigal) va yangisi (soddalashtirilgan). Siz ikkalasiga **bir xil sonlarni** kiritasiz: 2000 marta, har safar boshqa sonlar. Har safar ikkalasi **bir xil javob** bersa, siz ishonasiz: «ular bir xil ishlaydi».

Dastur aynan shuni qiladi:

1. Yangi kodni kompilyator bilan 0 va 1 larga aylantiradi (kompilyatsiya bo'ladimi? xato bormi?).
2. Eski va yangi kodga 2000 ta sonlar to'plamini beradi (tasodifiy, chegaraviy 0, 1, eng katta son va h.k.).
3. Javoblarni solishtiradi. Bittasi farq qilsa: **«Farq bor»** deydi va xatoni qaytarib beradi.

### Muhim ogohlantirish: bu «isbot» emas

2000 ta sonda bir xil chiqsa, **ehtimol** kodlar bir xil. Lekin 2001-sonda farq chiqishi mumkin. Shuning uchun biz **«tasdiqlandi»** deymiz, **«isbotlandi»** demaymiz. To'liq isbot uchun murakkab matematik usul kerak (kelajakdagi ish).

### Bizning o'zimizning xatomiz (eng yaxshi dars)

Dastlab dasturimiz shunday xato qilgan: kodda `agar son 1337 bo'lsa...` degan **haqiqiy** shart bor edi. Dastur uni «soxta shart» deb **o'chirib tashladi** va «tasdiqlandi» dedi. Nega? Chunki tasodifiy 2000 ta sonning birortasi aynan 1337 chiqmaydi: test xatoni ko'rmadi!

Buni 5 ta mustaqil tekshiruvchi (dasturni **sindirishga urinadigan** alohida yordamchilar) topdi. Biz tuzatdik: endi test kodning ichidagi sonlarni (1337 kabi) alohida sinaydi. Jami 18 ta jiddiy xato topilib tuzatildi, har biri uchun «bu xato qaytib kelmasin» testi yozildi.

> **Saboq:** test faqat **nimani ko'ra olmasligini** bilgandagina ishonchli.

---

## 7. «Agent» degani nima?

Mavzu nomida «agent» so'zi bor. Agent — **o'zi harakat qilib, natijasini tekshirib, kerak bo'lsa qayta urinadigan** dastur. Bizniki shunday ishlaydi:

```
   1. LLM'ga so'rov yuboradi
   2. Javob oladi (toza kod)
   3. TEKSHIRADI (2 ta kalkulyator)
   4. Farq bormi? ──ha──► farqni LLM'ga qaytaradi, qayta so'raydi (3 martagacha)  ← "xatosidan o'rganish"
   5. Baribir bo'lmadimi? ──► qoidalar (offline) natijasini oladi                ← "zaxira reja"
```

**Haqiqiy voqea.** `s2_opaque` funksiyasida DeepSeek birinchi urinishda xato qildi: «bu odatdagi clamp funksiyasi» deb o'ylab, kodda bor juft/toq tekshiruvini tashlab yubordi. Tekshiruv buni ushladi, xatoni modelga qaytardi, ikkinchi urinishda model «o'ylash rejimi»da to'g'ri javob berdi. Mana shu — agentning ishi.

> Halol qo'shimcha: bizning agent **qat'iy** agent. Qadamlar tartibini sun'iy intellekt emas, biz belgilaganmiz. Bu ataylab: bunday ishonchliroq.

---

## 8. Bizning sayt va uni ishlatish

**Manzil:** https://deobfuskatsiya12.onrender.com

Sayt **Render** deb ataladigan bepul xizmatda turadi. Bepul reja 15 daqiqa ishlatilmasa «uxlab qoladi», birinchi ochilish 30–60 soniya olishi mumkin: kuting.

**Kim kira oladi?** Faqat **kirish kodini** bilgan odam. Kod Render'dagi `DEOBF_ACCESS_CODE` sozlamasida turadi (uni siz o'zgartira olasiz). Noto'g'ri kod ko'p terilsa, sayt vaqtincha to'xtatadi.

### Qadamma-qadam ishlatish

1. Saytni oching, **kirish kodini** kiriting.
2. «Namuna» ro'yxatidan **s5_combined** ni tanlang (yoki o'z psevdokodingizni joylang).
3. «Model» ro'yxatida **DeepSeek Flash** turadi (agar «Offline» tanlasangiz, hech qanday sun'iy intellektsiz, bepul ishlaydi).
4. **«Tahlil qilish»** tugmasini bosing. 10–40 soniya kuting.
5. Natijani o'qing:
   * **«Tasdiqlandi»**: tekshiruvdan o'tdi ✅;
   * chapda **asl** (chigal), o'ngda **soddalashtirilgan** kod;
   * pastda har bir blok uchun tushuntirish; **«Oddiy tilda»** tugmasi — matnni dehqoncha qilib beradi;
   * yuklab olish: Markdown, HTML, JSON.
6. Yuqoridagi **«Qorong'i fon»** tugmasi sahifa rangini almashtiradi (standart — oq fon).

### Kalit xavfsizmi?

* Kalit faqat Render'ning maxfiy sozlamasida (`DEEPSEEK_API_KEY`). Sahifada, kodda, GitHub'da yo'q.
* Kodsiz kirib bo'lmaydi, shuning uchun begona odam kalitingiz bilan pul sarflay olmaydi.
* Kunlik chegara bor: bir kunda $2 dan ortiq sarflanmaydi.
* Qo'shimcha: DeepSeek hisobi oldindan to'ldiriladi, balans tugasa so'rovlar o'zi to'xtaydi.

### Agar nimadir ishlamasa

| Ko'rsangiz | Nima qilish kerak |
|---|---|
| Sayt ochilmaydi yoki juda sekin | 1 daqiqa kuting, sahifani yangilang (u uxlab qolgan edi) |
| Ro'yxatda DeepSeek yo'q, faqat Claude | Render → servis → **Environment** → `DEEPSEEK_API_KEY` qo'shing (qiymati: DeepSeek kalitingiz) → **Save** |
| «Kalit noto'g'ri yoki bekor qilingan» | platform.deepseek.com da yangi kalit yarating va Render'dagi qiymatni almashtiring |
| «Hisobda mablag' tugagan (402)» | platform.deepseek.com da hisobni to'ldiring (shu orada «Offline» ishlaydi) |

---

## 9. Nima qildik (hikoya)

Ishni ketma-ket qadamlar bilan qildik. Har bir qadam oldingisiga tayanadi:

1. **Namunalar yasadik.** Toza kod yozdik → ataylab chalkashtirdik → kompilyatordan va dekompilyatordan o'tkazdik. Shunda «to'g'ri javob» (asl toza kod) bizda bor: natijani u bilan solishtirsak bo'ladi. Jami 8 ta namuna.
2. **O'qiydigan qism** (parser): psevdokodni funksiyalarga bo'ladi va IDA / Ghidra / angr uslubini aniqlaydi.
3. **Topuvchilar:** 5 xil chalkashtirishni topadi, ularni tasodifiy sonlar bilan sinab tasdiqlaydi.
4. **Sun'iy intellekt qatlami:** Claude, keyin DeepSeek bilan gaplashadi.
5. **Tekshiruv va agent:** 2 ta kalkulyator + xatoni qaytarib qayta urinish.
6. **Terminal va sayt:** buyruq qatori va brauzerdagi interfeys.
7. **Mustaqil tekshiruvchilar** 18 ta jiddiy xato topdi: tuzatdik (6-bo'limdagi voqea).
8. **Tushuntirish sifati:** har blok uchun ikki xil matn: mutaxassis uchun va «dehqoncha».
9. **Internetga chiqarish:** yopiq sayt (kirish kodi, kalit serverda, kunlik chegara).
10. **Claude kaliti almashtirilgach DeepSeek'ni qo'shdik.** Haqiqiy DeepSeek bilan 8 namuna sinaldi.

---

## 10. Natijalar (uchta raqam)

| Raqam | Nima degani |
|---|---|
| **8 / 8** | 8 ta namunaning hammasida (DeepSeek bilan) natija eski kod bilan bir xil ishlashi tasdiqlandi. Jami narx **$0.028**: taxminan 3 sent! |
| **58 → 21** | Kodning «murakkabligi» (nechta ayrilish, tsikl bor) 64% kamaydi: kod ancha oddiylashdi |
| **161 ta test** | Dasturning o'zini tekshiradigan 161 ta avtomatik test. Biror narsani buzsak, darhol ko'rinadi |

Qo'shimcha: boshqa 21 ta «IDA/Ghidra uslubidagi» kirishda (61 funksiya) noto'g'ri natija **0** ta bo'ldi.

---

## 11. Nima ishlamaydi (halol)

Ustoz so'rasa, yashirmasdan ayting:

* **Test isbot emas.** «Tasdiqlandi» = 2000 ta sinovda bir xil chiqdi. 100% kafolat emas.
* **Haqiqiy virus bilan sinalmagan.** Namunalarni o'zimiz yaratdik (shunda to'g'ri javobni bilamiz). Haqiqiy IDA va Ghidra dasturlari o'rnatilmagan: ularning uslubidagi matnlar bilan va angr dekompilyatori bilan sinadik.
* **Juda murakkab himoya** (VMProtect kabi: kod ichida o'zining mayda kompyuteri) bizning doiradan tashqarida.
* **Kod sun'iy intellekt serveriga yuboriladi** (DeepSeek yoki Claude'ga). Maxfiy kod uchun «Offline» rejim bor: hech narsa tashqariga chiqmaydi. DeepSeek ma'lumotni qayerda saqlashini ularning rasmiy maxfiylik siyosatidan o'zingiz o'qing.
* **4 xonali kirish kodi kuchsiz.** Cheklovlar bor, lekin ustozga ko'rsatgach kodni o'zgartirib qo'ying.

---

## 12. Oddiy savol-javob

Har javob qisqa. «Nega?» deb so'ralsa, 5–11-bo'limlarga qarang.

**1. Loyihangiz nima?**
Chigal, tushunib bo'lmaydigan dastur matnini oladigan, uni oddiy qilib yozib beradigan, har qadamini tushuntiradigan va natija eskisi bilan bir xil ishlashini o'zi tekshiradigan dastur.

**2. Obfuskatsiya nima?**
Dasturni ataylab chalkash qilib yozish. Dastur xuddi shunday ishlaydi, lekin o'qib tushunish qiyin. Virus yozuvchilar antivirusdan va tahlilchidan yashirinish uchun shunday qiladi.

**3. Bu nima uchun kerak?**
Tahlilchi bitta chigal funksiyani tushunishga soatlab vaqt sarflaydi. Dastur birinchi tushunishni bir necha soniyada qiladi.

**4. Asl kodni qaytaradimi?**
Yo'q. Asl kod 0 va 1 larga aylanganda yo'qolgan. Biz «shu matn bilan bir xil ishlaydigan, lekin tushunarli» kod beramiz.

**5. Sun'iy intellekt xato qilsa-chi?**
Shuning uchun tekshiruv bor: yangi kod eskisi bilan 2000 ta sonda solishtiriladi. Xato bo'lsa, xato sun'iy intellektga qaytariladi (3 martagacha). Baribir bo'lmasa, qoidalar natijasi olinadi. Tekshirilmagan natija «tasdiqlandi» deb ko'rsatilmaydi.

**6. Kodlar bir xil ekanini qanday bilasiz?**
Ikkalasiga bir xil 2000 ta son beramiz va javoblarni solishtiramiz. Hammasi bir xil bo'lsa — «tasdiqlandi». Bu kuchli dalil, lekin matematik isbot emas, shuning uchun «isbotlandi» demaymiz.

**7. Nega DeepSeek?**
Claude kaliti almashtirilgach DeepSeek'ga o'tdik. U taxminan 10 baravar arzon (bitta funksiya ≈ 0.35 sent), va 8 ta namunaning hammasi tekshiruvdan o'tdi. Dastur ikkalasini ham biladi.

**8. API kalit nima? Xavfsizmi?**
Xizmatdan foydalanish uchun «PIN kod». Kimda bo'lsa, shu hisobdan pul sarflaydi. Shuning uchun u faqat Render'ning maxfiy sozlamasida turadi; sahifada va GitHub'da yo'q; saytga faqat kod bilan kiriladi; kunlik chegara bor.

**9. «Agent» deganingiz nima?**
O'zi urinib, natijasini tekshirib, xato bo'lsa qayta urinadigan dastur. Bizniki: so'raydi → tekshiradi → xato bo'lsa xatoni qaytarib qayta so'raydi → bo'lmasa zaxira yo'lga o'tadi.

**10. Eng katta xatongiz nima edi?**
Dastur haqiqiy shartni (`agar son 1337 bo'lsa`) «soxta» deb o'chirib tashlagan, test esa buni ko'rmagan va «tasdiqlandi» degan. Mustaqil tekshiruvchilar topdi, tuzatdik, qaytib kelmasligi uchun test yozdik.

**11. Nimalarni qilolmadingiz?**
Haqiqiy virus va haqiqiy IDA/Ghidra bilan sinab ko'rmadik (namunalarni o'zimiz yasadik); matematik isbot yo'q; juda murakkab himoyalar (VMProtect) yechilmaydi.

**12. Buni kim yozdi?** *(halol javob tayyorlang)*
Loyiha sun'iy intellekt yordamchisi (Claude Code) bilan, mening rahbarligimda ishlab chiqildi: men mavzuni, talablarni va qarorlarni belgiladim, natijalarni sinab ko'rdim va saytni joyladim. Har bir qismni tushuntira olaman. Ustoz qoidalariga qarab shuni ochiq ayting.

**13. Keyingi qadam nima bo'lishi mumkin?**
Matematik isbot; haqiqiy obfuskatorlar va haqiqiy IDA/Ghidra bilan sinov; kattaroq dasturlar.

---

## 13. Ustozga 3 daqiqalik gap

> «Ba'zi dasturlar ataylab tushunib bo'lmaydigan qilib yozilgan: bunga obfuskatsiya deyiladi. Virus yozuvchilar shunday qiladi, tahlilchi esa bitta funksiyaga soatlab vaqt sarflaydi.
>
> Biz shunday dasturni tushunarli qiladigan agent yaratdik. U to'rt ish qiladi: avval chalkashlikni **topadi**; keyin uni **soddalashtiradi**, buni qoidalar bilan yoki sun'iy intellekt bilan (DeepSeek yoki Claude) qiladi; keyin natijani **tekshiradi**; oxirida har bir blokni o'zbek tilida, hatto kompyuterni bilmaydigan odamga ham tushunarli qilib **tushuntiradi**.
>
> Eng muhim qismi tekshirish. Sun'iy intellekt xato qilishi mumkin, shuning uchun uning javobiga ishonmaymiz. Yangi kodni eskisi bilan 2000 ta sonda solishtiramiz. Farq chiqsa, xatoni sun'iy intellektga qaytarib, qayta urintiramiz.
>
> Natijalar: 8 ta namunaning hammasi tekshiruvdan o'tdi, kod murakkabligi 64 foizga kamaydi, hammasi 3 sentga tushdi. Kodni mustaqil tekshiruvchilar bilan sindirdik: ular 18 ta jiddiy xato topdi, hammasini tuzatdik.
>
> Cheklovlar: test isbot emas, faqat kuchli dalil; namunalarni o'zimiz yasadik, haqiqiy virus bilan sinalmagan. Hammasi internetda ishlaydi: kod bilan kiriladi, kalit serverda maxfiy turadi.»

---

## 14. Mini lug'at

| So'z | Oddiy gap bilan |
|---|---|
| **Kod** | Dasturchi yozgan, odam o'qiy oladigan ko'rsatmalar (retsept) |
| **Kompilyator** | Kodni kompyuter tushunadigan 0 va 1 larga aylantiruvchi dastur |
| **Dekompilyator (IDA, Ghidra)** | 0 va 1 larni qaytib «kodga o'xshash matn»ga aylantiruvchi dastur |
| **Psevdokod** | Dekompilyator chiqargan, kodga o'xshash, lekin nomlari yo'q matn |
| **Obfuskatsiya** | Kodni ataylab chalkash qilib yozish |
| **Deobfuskatsiya** | Chalkashlikni olib tashlash (bizning loyiha shuni qiladi) |
| **Funksiya** | Bitta aniq ishni bajaradigan kod bo'lagi (retseptdagi bitta taom) |
| **LLM / sun'iy intellekt** | Matnni o'qib, odamdek yoza oladigan katta dastur (DeepSeek, Claude) |
| **API kalit** | Xizmatdan foydalanish va hisobdan to'lash uchun «PIN kod» |
| **Token** | Matnning bo'lagi (3-4 harf); narx shunga qarab hisoblanadi |
| **Tekshirish (differensial test)** | Eski va yangi kodga bir xil sonlar berib, javoblarni solishtirish |
| **Tasdiqlandi** | 2000 ta sinovda bir xil chiqdi (isbot emas, kuchli dalil) |
| **Agent** | Natijasini tekshirib, xato bo'lsa qayta uringan dastur |
| **Render** | Saytni internetga chiqarib beradigan xizmat |
| **Offline rejim** | Sun'iy intellektsiz, qoidalar bilan ishlash (bepul, hech narsa tashqariga chiqmaydi) |

---

## 15. Qaysi hujjat nima uchun

| Hujjat | Qachon o'qiysiz |
|---|---|
| **08 — shu hujjat** | **Birinchi bo'lib.** Hammasini 0 dan tushunish |
| `07_hammasi_0_dan_va_ustoz_savollari.md` | Chuqurroq: har bir funksiya qayerda, atamalar jadvali, **56 ta ustoz savoli** |
| `02_foydalanish.md` | Dasturni o'z kompyuteringizda ishga tushirish |
| `04_internetga_chiqarish.md` | Saytni Render'da sozlash, nosozliklar |
| `01_jurnal.md` | Har bosqichda nima va nega qilingani (ish jurnali) |
| `baholash_*.md` | O'lchov natijalari (offline, Claude, DeepSeek) |

**Eslab qolish uchun 6 ta gap:**

1. Loyiha chigal dastur matnini tushunarli qiladi.
2. Qadamlar: **topish → soddalashtirish → tekshirish → tushuntirish**.
3. Soddalashtirishni qoidalar (bepul) yoki sun'iy intellekt (DeepSeek/Claude) qiladi.
4. Eng muhimi **tekshirish**: eski va yangi kod 2000 ta sonda solishtiriladi.
5. «Tasdiqlandi» ≠ «isbotlandi»: bu kuchli dalil, kafolat emas.
6. Kalit — PIN kod: hech kimga bermaymiz, faqat Render'da turadi.
