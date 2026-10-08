# deobf-agent — obfuskatsiyalangan kodni deobfuskatsiya qilish agenti

IDA (Hex-Rays), Ghidra yoki angr orqali olingan **obfuskatsiyalangan psevdokodni** LLM (Claude)
yordamida soddalashtiradigan, **C tilidagi ekvivalentini** yaratadigan va **har bir blokni o'zbek
tilida tushuntiradigan** vosita. Natija kompilyator va minglab avtomatik test bilan tekshiriladi.

```
psevdokod → parser → statik tahlil (bepul) → Claude → tekshiruv (gcc + differensial test) → hisobot
                                               ↑                 │
                                               └── xato bo'lsa ──┘  (o'z-o'zini tuzatish, maks. 3 marta)
```

## Imkoniyatlar
- **Kirish:** IDA Free'dan nusxalangan psevdokod, IDA/Ghidra eksport skriptlari, angr, oddiy `.c` fayl.
- **Statik tahlil (LLM'siz, bepul):** MBA ifodalar, opaque predicate, control-flow flattening,
  kodlangan satrlar va konstantalar, o'lik kod, mashhur algoritm konstantalari (FNV, CRC32, TEA, ...).
  Topilmalar tasodifiy test bilan **isbotlanadi**.
- **Avtomatik soddalashtirish:** MBA → oddiy ifoda, soxta shartlar va o'lik tarmoqlarni kesish,
  **flattening'ni yechish** (`while(1){switch}` → `while`/`if`).
- **LLM (Claude):** toza C kod, bloklar bo'yicha tushuntirish, mazmunli nomlar. Standart model —
  **Haiku 5.5** (arzon, ~$0.001/funksiya); `--model sonnet` / `opus` bilan bir zumda almashtiriladi.
- **Murakkab kod:** ko'rsatkich/bufer parametrlari, bir nechta funksiyali kirish (yordamchi funksiyalar
  avval tahlil qilinadi), aniqlanmagan tashqi funksiyalar, global o'zgaruvchilar ham qo'llab-quvvatlanadi.
- **Tekshiruv:** gcc kompilyatsiyasi + asl psevdokod bilan **differensial test** (2000 tasodifiy kirish).
- **Ikki tilda tushuntirish:** har bir izoh "mutaxassis uchun" (atamalar bilan) va **"dehqoncha"**
  (kompyuterni bilmaydigan odam uchun, hayotiy o'xshatishlar bilan) beriladi — Web UI'da bir tugma bilan
  almashtiriladi. Batafsil: [docs/05](docs/05_dehqoncha_tushuntirish.md).
- **Tejamkorlik:** prompt keshi, disk keshi (takroriy tahlil = $0), narx hisoblagich.
- **Interfeys:** CLI (`deobf`) va Web UI (`deobf web`); hisobot Markdown / HTML / JSON.
- **Internetga chiqarish:** `DEOBF_PUBLIC=1` bilan xavfsiz public rejim (kalit saqlanmaydi, cheklangan
  muhit); `Dockerfile` va `render.yaml` tayyor. Batafsil: [docs/04](docs/04_internetga_chiqarish.md).
- **Tillar:** tushuntirishlar o'zbek (standart), rus yoki ingliz tilida.

## Tez boshlash

**Windows (eng oson):** loyiha papkasidagi fayllarni tartib bilan ikki marta bosing:
`1_ornatish.bat` → `2_kalit_kiritish.bat` → `3_web_ishga_tushirish.bat`.
Muammo bo'lsa: `4_tekshirish.bat`.

**Terminal orqali:**
```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"

deobf check                                                     # diagnostika: kalit ishlayaptimi?
deobf analyze samples/decompiled/s3_flatten.angr.c --offline   # bepul
deobf analyze samples/decompiled/s3_flatten.angr.c              # Claude Haiku (standart)
deobf analyze samples/decompiled/s3_flatten.angr.c --model sonnet
deobf web                                                       # http://127.0.0.1:5000
deobf web --public                                              # internetga chiqariladigan demo rejimi
```
API kalit loyiha papkasidagi `.env` fayliga yoziladi: `ANTHROPIC_API_KEY=sk-ant-...`.
Batafsil: **[docs/02_foydalanish.md](docs/02_foydalanish.md)**.

## Natijalar (offline rejim, 8 ta namuna)
| Ko'rsatkich | Natija |
|---|---|
| Psevdokodga ekvivalentligi isbotlangan | **8/8** |
| Haqiqiy asl kodga ekvivalent | **6/8** (2 tasida dekompilyatorning o'zi xato qilgan) |
| Obfuskatsiya usullarini aniqlash | **100%** |
| Tsiklomatik murakkablik | **58 → 21** (−64%) |
| Qatorlar | **216 → 100** (−54%) |

To'liq jadval: [docs/baholash_offline.md](docs/baholash_offline.md).

## Loyiha tuzilmasi
```
deobf_agent/
  parser.py      psevdokodni funksiyalarga ajratish, uslubni aniqlash (IDA/Ghidra/angr/C)
  expr.py        C ifodalari kalkulyatori (tasodifiy test asosida isbotlash)
  detectors.py   obfuskatsiya detektorlari
  unflatten.py   flattening'ni avtomatik yechish (graf tahlili)
  offline.py     LLM'siz soddalashtirish
  explain.py     tushuntirish matnlari: mutaxassis nomlari + "dehqoncha" o'xshatishlar
  prompts.py     Claude uchun ko'rsatmalar
  schema.py      javob sxemasi (structured output)
  llm.py         Claude API: modellar, narx, kesh, xatolar
  verifier.py    kompilyatsiya + differensial test
  harness.py     differensial test generatori
  compiler.py    gcc bilan ishlash (IDA/Ghidra idiomlarini moslashtirish)
  sandbox.py     tashqi dasturlarni cheklangan muhitda ishga tushirish (public rejim uchun)
  agent.py       hammasini birlashtiruvchi agent sikli
  report.py      Markdown / HTML / JSON hisobot
  evaluate.py    namunalar bo'yicha baholash
  cli.py         buyruq qatori
  web/           Flask Web UI
samples/         8 ta test namunasi: toza va obfuskatsiyalangan manba, binar, psevdokod
scripts/         namunalarni yig'ish, angr/IDA/Ghidra eksport skriptlari
tests/           avtomatik testlar (pytest)
docs/            hujjatlar: mavzu, ish jurnali, yo'riqnoma, baholash, hisobot
Dockerfile, render.yaml, wsgi.py   internetga chiqarish (docs/04)
```

## Hujjatlar
- [00 — Mavzu tushuntirishi va reja](docs/00_mavzu_tushuntirish.md)
- [01 — Ish jurnali: har bir qadam nima uchun qilingan](docs/01_jurnal.md)
- [02 — Foydalanish yo'riqnomasi](docs/02_foydalanish.md)
- [03 — Amaliy qism hisoboti](docs/03_amaliy_qism_hisoboti.md)
- [04 — Internetga chiqarish (deploy)](docs/04_internetga_chiqarish.md)
- [05 — "Dehqoncha" tushuntirish rejimi](docs/05_dehqoncha_tushuntirish.md)
