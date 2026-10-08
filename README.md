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
- **Tekshiruv:** gcc kompilyatsiyasi + asl psevdokod bilan **differensial test** (2000 tasodifiy kirish).
- **Tejamkorlik:** prompt keshi, disk keshi (takroriy tahlil = $0), narx hisoblagich.
- **Interfeys:** CLI (`deobf`) va Web UI (`deobf web`); hisobot Markdown / HTML / JSON.
- **Tillar:** tushuntirishlar o'zbek (standart), rus yoki ingliz tilida.

## Tez boshlash
```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"

deobf analyze samples/decompiled/s3_flatten.angr.c --offline   # bepul
echo ANTHROPIC_API_KEY=sk-ant-... > .env
deobf analyze samples/decompiled/s3_flatten.angr.c              # Claude Haiku
deobf web                                                       # http://127.0.0.1:5000
```
Batafsil: **[docs/02_foydalanish.md](docs/02_foydalanish.md)**.

## Natijalar (offline rejim, 5 ta namuna)
| Ko'rsatkich | Natija |
|---|---|
| Psevdokodga ekvivalentligi isbotlangan | **5/5** |
| Haqiqiy asl kodga ekvivalent | **4/5** (5-chisida dekompilyatorning o'zi xato qilgan) |
| Obfuskatsiya usullarini aniqlash | **100%** |
| Tsiklomatik murakkablik | **26 → 12** (−54%) |
| Qatorlar | **106 → 60** (−43%) |

To'liq jadval: [docs/baholash_offline.md](docs/baholash_offline.md).

## Loyiha tuzilmasi
```
deobf_agent/
  parser.py      psevdokodni funksiyalarga ajratish, uslubni aniqlash (IDA/Ghidra/angr/C)
  expr.py        C ifodalari kalkulyatori (tasodifiy test asosida isbotlash)
  detectors.py   obfuskatsiya detektorlari
  unflatten.py   flattening'ni avtomatik yechish (graf tahlili)
  offline.py     LLM'siz soddalashtirish
  prompts.py     Claude uchun ko'rsatmalar
  schema.py      javob sxemasi (structured output)
  llm.py         Claude API: modellar, narx, kesh, xatolar
  verifier.py    kompilyatsiya + differensial test
  harness.py     differensial test generatori
  agent.py       hammasini birlashtiruvchi agent sikli
  report.py      Markdown / HTML / JSON hisobot
  evaluate.py    namunalar bo'yicha baholash
  cli.py         buyruq qatori
  web/           Flask Web UI
samples/         5 ta test namunasi: toza va obfuskatsiyalangan manba, binar, psevdokod
scripts/         namunalarni yig'ish, angr/IDA/Ghidra eksport skriptlari
tests/           avtomatik testlar (pytest)
docs/            hujjatlar: mavzu, ish jurnali, yo'riqnoma, baholash, hisobot
```

## Hujjatlar
- [00 — Mavzu tushuntirishi va reja](docs/00_mavzu_tushuntirish.md)
- [01 — Ish jurnali: har bir qadam nima uchun qilingan](docs/01_jurnal.md)
- [02 — Foydalanish yo'riqnomasi](docs/02_foydalanish.md)
- [03 — Amaliy qism hisoboti](docs/03_amaliy_qism_hisoboti.md)
