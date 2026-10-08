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
