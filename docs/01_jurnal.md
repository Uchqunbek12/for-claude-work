# 01. Ish jurnali: har bir qadam nima uchun shunday qilindi

Bu fayl loyiha davomida yozib boriladi. Har bir bosqichda quyidagilar qayd etiladi:
**nima qilindi → nima uchun → qaysi vosita ishlatildi → natija → kuzatuvlar**.
Yakuniy hisobot va himoya uchun asosiy manba shu fayl bo'ladi.

---

## 1-bosqich. Loyiha asosi va test namunalari

### 1.1. Loyiha tuzilmasi
**Nima qilindi:** Python loyihasi yaratildi.

```
for-claude-work/
├── deobf_agent/            ← asosiy dastur (Python paketi)
│   ├── data/re_types.h     ← IDA/Ghidra turlari uchun C sarlavha fayli
│   ├── compiler.py         ← gcc bilan ishlash
│   └── harness.py          ← differensial test (ikki funksiyani solishtirish)
├── samples/                ← test namunalari
│   ├── src/clean/          ← asl (toza) C kodlar — "to'g'ri javob"
│   ├── src/obf/            ← obfuskatsiyalangan C kodlar
│   ├── bin/                ← kompilyatsiya qilingan binar fayllar (.elf)
│   ├── decompiled/         ← binar fayllardan olingan psevdokod
│   └── manifest.json       ← namunalar ro'yxati (funksiya nomi, turlari, usullar)
├── scripts/                ← yordamchi skriptlar
├── tests/                  ← avtomatik testlar
└── docs/                   ← hujjatlar (shu fayl ham)
```

**Nima uchun Python:** o'rganish oson, Claude'ning rasmiy kutubxonasi (`anthropic`) bor,
matn bilan ishlash (psevdokodni tahlil qilish) qulay.

**Fayllar:**
- `requirements.txt` — kerakli kutubxonalar ro'yxati (`pip install -r requirements.txt` bilan o'rnatiladi).
- `pyproject.toml` — loyiha "pasporti": nomi, versiyasi, bog'liqliklari va `deobf` buyrug'i.
- `.gitignore` — git'ga yuklanmasligi kerak bo'lgan fayllar (kesh, vaqtinchalik fayllar, `.env` dagi API kalit).

### 1.2. Test namunalari (5 ta)
**Nima qilindi:** 5 ta kichik, zararsiz C funksiya yozildi. Har birining ikki versiyasi bor:
toza (asl) va obfuskatsiyalangan.

| Namuna | Funksiya | Nima qiladi | Obfuskatsiya usuli |
|---|---|---|---|
| `s1_mba` | `mix(a, b)` | ikki sonni aralashtiradi | MBA ifodalar |
| `s2_opaque` | `clamp(x, lo, hi)` | sonni oraliqqa cheklaydi | opaque predicate + o'lik kod |
| `s3_flatten` | `gcd(a, b)` | EKUB (Yevklid algoritmi) | control-flow flattening |
| `s4_strings` | `greet_char(idx)` | matndan belgi qaytaradi | XOR bilan kodlangan satr |
| `s5_combined` | `checksum(x, n)` | FNV-1a nazorat yig'indisi | hammasi aralash + kodlangan konstantalar |

**Nima uchun o'zimiz yozdik:** agentni baholash uchun **"to'g'ri javob"** kerak. Toza
versiya — aynan shu to'g'ri javob. Agent obfuskatsiyalangan koddan qanchalik toza versiyaga
yaqin natija chiqarganini o'lchay olamiz. Tayyor dasturlarda bunday imkoniyat yo'q.

**Nima uchun funksiyalar butun sonli:** bunday funksiyalarni avtomatik test qilish oson
(tasodifiy sonlar berib, natijani solishtiramiz).

### 1.3. `re_types.h` — dekompilyator turlari
**Muammo:** IDA psevdokodi `_DWORD`, `__int64`, `__fastcall`, `LODWORD(x)` kabi nomlarni,
Ghidra esa `undefined4`, `uint`, `CONCAT44(...)` kabi nomlarni ishlatadi. Bu standart
C emas, shuning uchun gcc ularni tushunmaydi.

**Yechim:** `deobf_agent/data/re_types.h` faylida bu nomlarning barchasini standart C
turlariga bog'ladik. Endi psevdokodni ham, LLM yozgan kodni ham kompilyatsiya qila olamiz.

### 1.4. Differensial test (`harness.py`)
**G'oya:** ikki funksiya bir xil ishlashini qanday bilamiz? Ikkalasini **bir xil** tasodifiy
kirish qiymatlari bilan minglab marta chaqiramiz va natijalarini solishtiramiz.
Kirish qiymatlarining bir qismi ataylab "chegaraviy" sonlar bo'ladi (0, 1, -1, 0x7FFFFFFF,
0x80000000, ...), chunki xatolar ko'pincha shu qiymatlarda yuzaga chiqadi.

**Texnik nuqta:** ikkala funksiyaning nomi bir xil (masalan, `mix`). Ular bitta dasturda
yashashi uchun gcc'ning `-D` parametri bilan har biriga yashirincha boshqa nom beramiz:
`-Dmix=deobf_fn_original` va `-Dmix=deobf_fn_candidate`.

**Bu matematik isbot emas**, lekin 2000–20000 ta testdan o'tish — kuchli dalil.

### 1.5. Namunalarni tekshirish va kompilyatsiya (`scripts/build_samples.py`)
**Nima qilindi:** skript har bir namunaning toza va obfuskatsiyalangan versiyasini
20 000 ta test bilan solishtiradi, so'ng obfuskatsiyalangan versiyani `samples/bin/*.elf`
binar fayliga kompilyatsiya qiladi (`-O0` — optimizatsiyasiz, aks holda gcc
obfuskatsiyaning bir qismini o'zi "tozalab" yuborardi).

**🔎 Kuzatuv №1 — vosita mening xatoimni topdi.** Birinchi urinishda `s2_opaque` uchun
**3353/20000** testda farq chiqdi. Sabab: toza versiyada `x < lo` bo'lsa funksiya darhol
`lo` ni qaytaradi, men yozgan obfuskatsiyalangan versiyada esa `lo > hi` holatida kod keyingi
tekshiruvga o'tib ketardi. Shart tuzatildi (`x >= lo && x > hi`) va endi 5/5 namuna ekvivalent.
Bu differensial testning amaliy foydasini yaxshi ko'rsatadi.

### 1.6. Haqiqiy dekompilyatsiya (`scripts/decompile_angr.py`)
**Muammo:** loyiha ishlab chiqilayotgan bulutli serverda GitHub bloklangan, shuning uchun
Ghidra'ni yuklab bo'lmadi. IDA esa faqat sizning kompyuteringizda bor.

**Yechim:** **angr** — Python'da yozilgan bepul dekompilyator (Kaliforniya universiteti,
Santa Barbara, tomonidan ishlab chiqilgan). U ham IDA/Ghidra kabi binar fayldan C psevdokod
chiqaradi. `samples/decompiled/*.angr.c` fayllari shu yo'l bilan olindi. Bular qo'lda
yozilgan emas, balki **haqiqiy dekompilyator natijasi**.

> Siz o'z kompyuteringizda `samples/bin/*.elf` fayllarini IDA Free'da ochib, `F5` bosib,
> xuddi shunday psevdokodni IDA uslubida olishingiz mumkin.

**Global ma'lumotlar:** `s4_strings` da shifrlangan baytlar kodda emas, binar faylning
ma'lumotlar bo'limida turadi (`extern char ENC`). Skript bunday ma'lumotlarni binar fayldan
o'qib, psevdokod oxiriga izoh sifatida qo'shadi. IDA'da buning o'xshashi: baytlarni belgilab,
`Shift+E` (Export data) bosish.

**🔎 Kuzatuv №2 — dekompilyator soddalashtirishni qisman o'zi qiladi.** angr `s1_mba` dagi
`(s | d) - (s & d)` ni `v0 ^ v1` ga, `s5_combined` dagi kodlangan konstantani `2166136261` ga
o'zi aylantirdi. Lekin flattening (`while(1){switch...}`), opaque predicate va o'lik kod
joyida qoldi. Aynan shu qolgan qismni LLM agenti soddalashtirishi kerak.

**🔎 Kuzatuv №3 — dekompilyator ham xato qiladi!** angr psevdokodini toza manba bilan
solishtirganimizda `s2_opaque` da farq chiqdi. angr `(u*u + u) % 2 == 0` shartini
`!((v1 & 1) * ((v1 & 1) + 1))` ga "soddalashtirgan", lekin oxiridagi `% 2` ni tushirib
qoldirgan. Natijada toq sonlarda shart noto'g'ri bo'lib qoladi. **Xulosa:** dekompilyator
natijasiga ham 100% ishonib bo'lmaydi. Bu namuna ataylab shundayligicha qoldirildi va
baholashda alohida ko'rib chiqiladi.

Qolgan natijalar: `s1`, `s3`, `s5` psevdokodi asl kod bilan ekvivalent. `s4` uchun angr
`uint224_t` (28 baytlik bufer) degan nostandart tur ishlatgan, shuning uchun `compiler.py` ga
bunday turlarni avtomatik e'lon qilish qo'shildi.

### 1-bosqich natijasi
- ✅ Loyiha tuzilmasi
- ✅ 5 ta namuna (toza + obfuskatsiyalangan), ekvivalentligi 20 000 test bilan tasdiqlangan
- ✅ 5 ta binar fayl va ularning haqiqiy dekompilyatsiya natijasi
- ✅ gcc bilan ishlash moduli va differensial test moduli

---

## 2-bosqich. Kirish parseri (`deobf_agent/parser.py`)

### 2.1. Vazifa
Foydalanuvchi vositaga matn beradi: IDA'dan nusxalangan psevdokod, Ghidra eksporti yoki
oddiy `.c` fayl. Parser bu matndan quyidagilarni ajratib oladi:
1. **Uslub** — matn qaysi vositadan kelgan (`ida`, `ghidra`, `angr` yoki `c`);
2. **Funksiyalar** — har birining nomi, qaytish turi, parametrlari, tanasi, qator raqamlari;
3. **Chaqiruvlar** — funksiya qaysi boshqa funksiyalarni chaqiradi (masalan, `sub_401000`);
4. **Global ma'lumotlar** — shifrlangan baytlar kabi ma'lumot massivlari.

### 2.2. Nima uchun tayyor C parser ishlatmadik
Python'da `pycparser` kabi to'liq C parserlar bor, lekin ular faqat **standart** C ni
tushunadi. Psevdokodda esa `__fastcall`, `int a1@<eax>`, `LODWORD(v4) = 5` kabi
nostandart yozuvlar bo'ladi va qat'iy parser ularda xato berib to'xtaydi. Shuning uchun
soddaroq, lekin **chidamli** usulni tanladik:
- avval izohlar (`// ...`, `/* ... */`) va satrlar (`"..."`) ichini bo'sh joy bilan
  almashtiramiz, shunda ular ichidagi `{` `}` belgilar hisobni buzmaydi;
- keyin figurali qavslarni sanab, har bir yuqori darajadagi `{ ... }` blokni topamiz;
- blokdan oldingi matn `nom(...)` ko'rinishida bo'lsa, demak bu funksiya.
  `struct S { ... };` yoki `massiv[] = { ... };` kabi bloklar e'tiborga olinmaydi.

### 2.3. Uslubni aniqlash — "ball tizimi"
Har bir vosita o'ziga xos nomlar ishlatadi. Matnda qaysi uslubning belgilari ko'p
uchrasa, o'sha uslub tanlanadi:

| Vosita | Tipik belgilar |
|---|---|
| IDA (Hex-Rays) | `sub_401136`, `v4`, `a1`, `_DWORD`, `__fastcall`, `LODWORD(...)`, `// [rsp+1Ch]` |
| Ghidra | `FUN_00101149`, `param_1`, `local_10`, `iVar1`, `undefined4`, `DAT_...`, `CONCAT44(...)` |
| angr | `// [bp-0x18]` |
| oddiy C | yuqoridagilarning hech biri yo'q |

**🔎 Kuzatuv:** birinchi versiyada angr natijasi "IDA" deb aniqlandi. Sabab: IDA'ning
`// [rsp+..]` naqshi angr'ning `// [bp-0x18]` izohiga ham mos kelib qolgan edi. Naqsh
aniqlashtirildi va endi 5/5 namuna `angr` deb to'g'ri aniqlanadi.

### 2.4. Global ma'lumotlar formati
Parser ikki formatni taniydi:
```c
// ENC @ 0x402010 (27 bayt): 14 39 30 30 ...           ← bizning angr skriptimiz formati
unsigned char byte_4020[27] = { 0x14, 0x39, ... };     ← IDA: Shift+E → "C array" eksporti
```

### 2.5. Testlar (`tests/`)
**pytest** — Python'da avtomatik testlar yozish uchun eng mashhur vosita. `test_` bilan
boshlanuvchi har bir funksiya alohida test hisoblanadi. `python -m pytest` buyrug'i
hammasini ishga tushiradi va qaysi biri o'tganini yoki yiqilganini ko'rsatadi.

| Fayl | Nimani tekshiradi |
|---|---|
| `tests/test_parser.py` | IDA, Ghidra, angr va oddiy C uslubidagi matnni to'g'ri ajratish |
| `tests/test_harness.py` | differensial test: ekvivalent va noekvivalent kodni farqlash; 5 ta namunaning ekvivalentligi |

Natija: **9/9 test o'tdi.**

### 2-bosqich natijasi
- ✅ 4 xil uslubni taniydigan parser
- ✅ funksiya signaturasi va parametrlarini ajratish (IDA'ning `@<eax>` kabi yozuvlari bilan ham)
- ✅ global ma'lumotlarni o'qish
- ✅ avtomatik testlar

---

## 3-bosqich. Statik tahlil — LLM'siz, bepul detektorlar

### 3.1. Nima uchun LLM'dan oldin statik tahlil
1. **Pul tejash:** oddiy holatlarni (masalan, `(a&b)*2 + (a^b)` = `a+b`) dastur o'zi
   topadi, LLM'ga murojaat qilish shart emas.
2. **LLM xatolarini kamaytirish:** LLM'ga "bu shart har doim yolg'on, 3000 test bilan
   isbotlangan" degan aniq dalillarni beramiz, u taxmin qilib o'tirmaydi.
3. **Offline rejim:** API kalitsiz ham vosita foydali natija beradi.

### 3.2. Asosiy g'oya: ifoda kalkulyatori (`deobf_agent/expr.py`)
C tilidagi ifodani Python ichida hisoblaydigan kichik interpretator yozildi:
- **tokenizer** matnni bo'laklarga ajratadi: `(a ^ b) + 2u` → `(`, `a`, `^`, `b`, `)`, `+`, `2u`;
- **Pratt parser** bo'laklardan daraxt (AST) quradi va amallar ustuvorligini hisobga oladi
  (`*` amali `+` dan oldin bajariladi va h.k.);
- **hisoblash** C qoidalarini takrorlaydi: 32 bitda "aylanib ketish" (`0xFFFFFFFF + 1 = 0`),
  ishorali va ishorasiz taqqoslash farqi (`(int)x < 0` va `x < 0`), `(unsigned char)` kabi
  tur o'zgartirishlar.

Bu kalkulyator ustiga ikki "tasodifiy test" usuli qurildi:
- `is_constant(ifoda)` — ifodani 3000 ta tasodifiy qiymat bilan hisoblaydi. Natija doim bir
  xil chiqsa, ifoda aslida **konstanta**. Opaque predicate'lar shu yo'l bilan topiladi;
- `equivalent(a, b)` — ikki ifoda barcha testlarda bir xil natija beradimi? MBA
  soddalashtirish shunga tayanadi.

### 3.3. Detektorlar (`deobf_agent/detectors.py`)

| Detektor | Qanday ishlaydi |
|---|---|
| **MBA** | Ifodada ham arifmetik (`+ - *`), ham bit (`& \| ^ ~`) amallari bo'lsa, oddiy nomzodlarni (`x`, `~x`, `x+y`, `x^y`, `x+1`, ...) birma-bir sinab, tasodifiy testda **teng** chiqqanini taklif qiladi. Bu "sintez orqali soddalashtirish" deyiladi |
| **Yashirin konstantalar** | Faqat sonlardan iborat ifodani (`0x7A1C3E55 ^ 0xFB00A390`) hisoblab, bitta songa aylantiradi |
| **Opaque predicate** | `if`/`while` shartlari va `a ? b : c` dagi shartlarni `is_constant` bilan tekshiradi |
| **O'lik kod** | Qiymat beriladigan, lekin hech qayerda **o'qilmaydigan** o'zgaruvchilarni topadi (`junk ^= h` kabi faqat o'ziga ishlatilganlar ham hisobga olinadi) |
| **Flattening** | `while(1)` ichidagi `switch(state)` ni topadi, har bir `case` dan keyingi holatni ajratib, **holatlar xaritasini** tiklaydi. IDA/Ghidra'dagi `if`-zanjiri ko'rinishini ham taniydi |
| **Kodlangan satrlar** | Global ma'lumot yoki stekdagi baytlarni koddagi `^ KALIT` qiymatlari bilan ochib ko'radi. Kalit topilmasa, 255 ta kalitning hammasini sinab, eng "matnga o'xshash" natijani tanlaydi |
| **Mashhur konstantalar** | FNV, CRC32, TEA, MD5, SHA kabi algoritmlarning "sehrli" sonlarini taniydi. Bu funksiya nima qilishini tushunishga katta yordam beradi |

`s3_flatten` uchun tiklangan holatlar xaritasi (angr psevdokodidan):
```
Holat o'zgaruvchisi: v3; boshlang'ich holat: 15391
  holat 15391 -> 24071 [agar !v0] | 37282 [agar v0]
  holat 24071 -> return (chiqish)
  holat 37282 -> 11117
  holat 11117 -> 15391
```
Bu xaritadan ko'rinadiki, 15391 → 37282 → 11117 → 15391 halqasi aslida **`while (v0 != 0)` tsikli**,
24071 esa tsikldan chiqish.

### 3.4. Topilgan va tuzatilgan muammolar
| Muammo | Tuzatish |
|---|---|
| `unsigned int s = (a^b) + ...` — e'lon bilan birga qiymat berish tahlil qilinmagan | gapni "e'lon + qiymat" shaklida ajratish qo'shildi |
| `^ 0x5Cu` dagi `u` qo'shimchasi sabab kalit tanilmagan, natijada tanlash usuli noto'g'ri kalit (0x5F) bilan ma'nosiz matn chiqargan | regex tuzatildi, tanlash usuli endi "tabiiy tilga o'xshashlik" (e, t, a, o, bo'sh joy ulushi) bo'yicha baholaydi |
| Taqqoslash ifodalari (`... != 0`) MBA deb ham belgilangan | taqqoslash/mantiqiy ifodalar MBA detektoridan chiqarildi, ular opaque predicate detektorining ishi |
| Shartlarda "MBA bo'lishi mumkin" degan noaniq ogohlantirishlar shovqin bergan | noaniq ogohlantirish faqat >=2 arifmetik va >=2 bit amali bo'lgan holatda chiqariladi |

**🔎 Kuzatuv:** `s5_combined` ning angr psevdokodida ham `s2` dagi angr xatosi takrorlangan:
`((i*i + i) & 1) != 0` (har doim yolg'on) sharti `(v2 & 1) * ((v2 & 1) + 1)` ga aylangan va toq
sonlarda rostga chiqadi. Lekin bu shart ostida faqat **keraksiz** `v3` o'zgaruvchisi o'zgaradi,
shuning uchun funksiya natijasi buzilmaydi (differensial test ham shuni tasdiqlagan).

### 3.5. Metrikalar (`deobf_agent/metrics.py`)
Deobfuskatsiya natijasini **raqamlar bilan** baholash uchun:
- **qatorlar soni**;
- **tsiklomatik murakkablik (CC)**: 1 + tarmoqlanishlar soni (`if`, `while`, `case`, `&&`, ...).
  Bu dasturiy injiniringda keng tarqalgan o'lchov (McCabe, 1976).

| Namuna | toza (qator / CC) | obfuskatsiyalangan | angr psevdokodi |
|---|---|---|---|
| s1_mba | 4 / 1 | 6 / 1 | 10 / 1 |
| s2_opaque | 6 / 3 | 15 / 7 | 17 / 7 |
| s3_flatten | 6 / 2 | 22 / 7 | 28 / 7 |
| s4_strings | 4 / 1 | 9 / 2 | 10 / 2 |
| s5_combined | 8 / 2 | 32 / 9 | 42 / 9 |

Agentning maqsadi — psevdokod ustunidagi raqamlarni "toza" ustundagi qiymatlarga yaqinlashtirish.

### 3.6. Testlar
`tests/test_detectors.py` qo'shildi: MBA, opaque predicate, flattening, satrlar, o'lik kod,
metrikalar. Muhim test — **toza kodda soxta topilma (false positive) yo'qligi**.
Natija: **17/17 test o'tdi.**

### 3-bosqich natijasi
- ✅ C ifoda kalkulyatori va tasodifiy test asosidagi isbotlash
- ✅ 7 ta detektor: barcha 5 namunada barcha obfuskatsiya usullari topildi
- ✅ flattening uchun holatlar xaritasini tiklash
- ✅ murakkablik metrikalari

---

## 4-bosqich. LLM agent (Claude) va offline rejim

### 4.1. Virtual muhit (`.venv`)
Kutubxonalarni tizim Python'iga o'rnatmoqchi bo'lganimizda paketlar ziddiyati chiqdi
(`blinker` paketini tizim boshqaruvchisi o'rnatgan ekan). Yechim — **virtual muhit**:
```bash
python -m venv .venv                 # loyiha uchun alohida Python muhiti
.venv/bin/pip install -e ".[dev]"    # loyiha va uning kutubxonalarini o'rnatish
```
Virtual muhit loyiha kutubxonalarini boshqa dasturlardan ajratadi. Bu Python'dagi standart amaliyot.

### 4.2. Claude API bilan ishlashning asosiy tushunchalari
| Tushuncha | Ma'nosi | Loyihada |
|---|---|---|
| **Token** | Model o'qiydigan/yozadigan matn bo'lagi (~3–4 harf) | Narx tokenlar soniga qarab hisoblanadi |
| **Model** | Haiku (arzon) → Sonnet → Opus (eng kuchli) | Default `haiku`, `--model sonnet/opus` bilan bir zumda almashtiriladi |
| **Effort** | Modelning "o'ylash" chuqurligi | `low/medium/high`, default `medium` |
| **Structured output** | Javob aniq sxema bo'yicha keladi | `schema.py` dagi `DeobfResult` |
| **Prompt caching** | O'zgarmas qism serverda keshlanadi, keyingi so'rovda ~10x arzon | Tuzatish so'rovlarida avvalgi suhbat keshdan o'qiladi |
| **Disk kesh** | Bir xil so'rov qayta yuborilmaydi | `.deobf_cache/` papkasi, takroriy tahlil = **$0** |

### 4.3. Javob sxemasi (`deobf_agent/schema.py`)
Erkin matn o'rniga Claude quyidagi tuzilmani qaytaradi (pydantic modeli):
- `c_code` — kompilyatsiya qilinadigan toza C funksiya (**nomi va parametrlari aslidagidek**,
  aks holda differensial testni o'tkazib bo'lmaydi);
- `blocks` — har bir blok uchun: psevdokoddagi qatorlar → soddalashtirilgan kod → **o'zbekcha tushuntirish**;
- `renames` — `v3 → state`, `a1 → divisor` kabi qayta nomlashlar va sababi;
- `summary`, `techniques`, `confidence`, `notes`.

**Nima uchun:** dastur javobni ishonchli o'qiy oladi (kod qayerda, izoh qayerda); Web UI va hisobot
uni chiroyli ko'rsatadi; offline rejim ham aynan shu tuzilmani qaytaradi.

### 4.4. Prompt (`deobf_agent/prompts.py`)
- **Tizim ko'rsatmasi (system prompt)** — o'zgarmas: Claude'ning roli, obfuskatsiya usullari va
  kod uchun qat'iy qoidalar (nom va parametrlarni saqlash, ma'lumotlarni `static` qilish,
  ishonchsiz joyda asl mantiqni saqlab, `notes` ga yozish).
- **Foydalanuvchi xabari** — o'zgaruvchan: raqamlangan psevdokod, global ma'lumotlar baytlari,
  **statik tahlil faktlari** (`VERIFIED` belgisi bilan — "bu tasodifiy test bilan isbotlangan, ishon"),
  holatlar xaritasi, tushuntirish tili.

**Nima uchun ko'rsatmalar ingliz tilida:** modellar ingliz tilidagi ko'rsatmalarga eng aniq amal
qiladi va ingliz matni kamroq token egallaydi, ya'ni arzonroq. Tushuntirishlar esa tanlangan tilda
(`uz`, `ru`, `en`) yoziladi.

### 4.5. Claude moduli (`deobf_agent/llm.py`)
- `resolve_model("haiku")` → `claude-haiku-5-5` (aliaslar: `haiku`, `sonnet`, `opus`; `DEOBF_MODEL`
  muhit o'zgaruvchisi bilan ham tanlanadi);
- `ClaudeSession.ask()` — so'rov yuboradi. Suhbat tarixi **faqat oxiriga qo'shiladi**, shunda tuzatish
  so'rovlarida oldingi qism prompt keshidan o'qiladi;
- **xatolar** foydalanuvchiga tushunarli o'zbekcha xabarga aylantiriladi: noto'g'ri kalit, limit,
  internet yo'qligi, model rad etishi (`refusal`), javob kesilishi (`max_tokens`);
- **narx hisoblagich**: har so'rovdan keyin token soni va $ narxi yig'iladi;
- **API kalit** `.env` faylida saqlanadi (`ANTHROPIC_API_KEY=...`). `.env` esa `.gitignore` da, shuning uchun
  kalit GitHub'ga tushib qolmaydi.

Taxminiy narxlar (1 million token uchun, $):

| Model | Kirish | Chiqish |
|---|---|---|
| Haiku 5.5 (default) | 0.10 | 0.50 |
| Sonnet 5.5 | 2.00 | 10.00 |
| Opus 5.5 | 4.00 | 20.00 |

### 4.6. Offline rejim (`deobf_agent/offline.py`)
API kalitsiz ishlaydi va xuddi shu `DeobfResult` ni qaytaradi:
1. isbotlangan MBA soddalashtirishlari va konstantalarni kodga qo'llaydi;
2. soxta shartlarni `0`/`1` ga almashtiradi, so'ng **o'lik tarmoqlarni kesadi**
   (`if (0) {...} else X` → `X`);
3. keraksiz o'zgaruvchilarni (e'lon va qiymat berishlarni) olib tashlaydi;
4. flattening xaritasi va dekodlangan satrlarni kod boshida izoh qilib yozadi.

Natijalar (angr psevdokodi → offline natija, barchasi differensial testdan o'tdi):

| Namuna | Ekvivalent | CC | Qatorlar |
|---|---|---|---|
| s1_mba | ✅ | 1 → 1 | 10 → 10 (MBA → `a0 + a1`, `a0 - a1`) |
| s2_opaque | ✅ | 7 → 5 | 17 → 12 |
| s3_flatten | ✅ | 7 → 7 | 28 → 28 (faqat xarita izohi) |
| s4_strings | ✅ | 2 → 2 | satr dekodlandi |
| s5_combined | ✅ | 9 → 8 | 42 → 37 |

**Xulosa:** offline rejim ifodalar darajasida yaxshi ishlaydi, lekin **boshqaruv oqimini (flattening)
qayta qurish va mazmunli nomlar berish** uchun "tushunish" kerak. Bu LLM rejimining vazifasi.

### 4.7. Global ma'lumotlarni testga ulash
`s4` ning psevdokodi `extern char ENC;` ga murojaat qiladi, baytlar esa binar faylda. Differensial
testga **qo'shimcha fayl** qo'shildi: `unsigned char ENC[27] = {0x14, ...};`. Bog'lovchi (linker)
`ENC` nomini shu massivga ulaydi. Natijada `s4` psevdokodi ham to'liq sinovdan o'tdi va asl kod bilan ekvivalent chiqdi.

### 4.8. Testlar — soxta mijoz (fake client)
Bu muhitda Claude API kaliti yo'q. Shuning uchun haqiqiy mijoz o'rniga **soxta mijoz** (`tests/fakes.py`)
yozildi. U oldindan berilgan javoblarni qaytaradi va yuborilgan so'rovlarni eslab qoladi. Shu yo'l bilan
tekshiriladi: so'rov to'g'ri tuzilganmi (model, effort, kesh), narx to'g'ri hisoblanadimi, suhbat tarixi
faqat oxiriga qo'shiladimi, disk kesh ishlaydimi (2-so'rov API'ga bormaydi), rad etish va kesilish
to'g'ri qayta ishlanadimi.
Natija: **22/22 test o'tdi.**

> ⚠️ Haqiqiy Claude javobi bilan sinov API kaliti bor kompyuterda o'tkaziladi (yo'riqnomada yoziladi).

---

## 5-bosqich. Tekshiruv va o'z-o'zini tuzatish sikli (agent)

### 5.1. Nima uchun bu "agent"
Oddiy chatbot javobni bir marta beradi va unga ishonish-ishonmaslik foydalanuvchining zimmasida qoladi.
Bizning vosita esa **natijani o'zi tekshiradi** va muammo bo'lsa, aniq xato ma'lumoti bilan
modeldan tuzatishni so'raydi:

```
 psevdokod → parser → statik tahlil → Claude → tekshiruv ──✅──→ hisobot
                                         ↑          │
                                         └──── ❌ ──┘  (xato matni bilan, maks. 3 marta)
```

### 5.2. Tekshiruv (`deobf_agent/verifier.py`)
| Qadam | Nima tekshiriladi | Xato bo'lsa Claude'ga nima yuboriladi |
|---|---|---|
| 1. Sintaksis | `gcc -fsyntax-only` | gcc xato xabarlari |
| 2. Shakl | funksiya nomi va parametrlar soni aslidagidekmi | "nomni/parametrlarni saqla: (...)" |
| 3. Xatti-harakat | asl psevdokod va yangi kod 2000 tasodifiy kirishda bir xilmi | farq chiqqan kirish qiymatlari va ikkala natija |

Natija holatlari: **verified** ✅ (ekvivalentligi isbotlangan), **compiled** 🟡 (kompilyatsiya bo'ldi,
lekin avtomatik solishtirib bo'lmadi, masalan funksiya ko'rsatkich qabul qiladi), **mismatch** ❌,
**compile_error** ❌, **no_compiler** ⚪.

### 5.3. Agent (`deobf_agent/agent.py`)
- Har bir urinish natijasi saqlanadi va **eng yaxshisi** tanlanadi (verified > compiled > mismatch > compile_error).
- Urinishlar tugasa ham natija yaxshi bo'lmasa, vosita buni **ochiq aytadi** — "muvaffaqiyat" deb yolg'on ko'rsatmaydi.
- Claude bilan muammo bo'lsa (kalit yo'q, limit, rad etish), vosita to'xtab qolmaydi:
  natijani **offline rejimdan** oladi va xatoni hisobotda ko'rsatadi.
- Offline rejim ham tekshiruvdan o'tadi. Agar "agressiv" variant (tarmoqlarni kesish) testdan o'tmasa,
  ehtiyotkor variantga (faqat ifodalarni soddalashtirish) qaytiladi.

### 5.4. Testlar (soxta mijoz bilan ssenariylar)
| Ssenariy | Kutilgan xatti-harakat | Natija |
|---|---|---|
| Claude 1-urinishda `a + b` o'rniga `a \| b` yozadi | differensial test farqni topadi → misollar Claude'ga yuboriladi → 2-urinish ✅ | ✅ |
| Claude sintaksis xatoli kod beradi | gcc xatolari Claude'ga yuboriladi → 2-urinish ✅ | ✅ |
| Claude ikki marta ham xato qiladi | natija "mismatch" deb ochiq ko'rsatiladi | ✅ |
| Claude rad etadi | offline natija + xato matni | ✅ |
| Offline rejim, 5 ta namuna | hammasi "verified" | ✅ |

Natija: **28/28 test o'tdi.**
