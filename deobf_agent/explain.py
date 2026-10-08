"""Tushuntirish matnlari: mutaxassis uchun nomlar va "dehqoncha" (juda sodda) izohlar.

Vosita har bir topilmani ikki tilda tushuntiradi:
  * mutaxassis tili — "MBA ifoda", "opaque predicate" va h.k. (TECH_NAMES_UZ);
  * dehqoncha — kompyuterdan uzoq odam ham tushunadigan, hayotiy o'xshatishlar bilan (SIMPLE_UZ).
Offline rejim shu matnlardan foydalanadi; LLM rejimida Claude xuddi shu uslubda o'zi yozadi.
"""

from __future__ import annotations

TECH_NAMES_UZ = {
    "mba": "MBA ifoda",
    "opaque_predicate": "Soxta shart (opaque predicate)",
    "control_flow_flattening": "Boshqaruv oqimini tekislash (flattening)",
    "encoded_strings": "Kodlangan satr",
    "encoded_constants": "Yashirilgan konstanta",
    "dead_code": "O'lik / keraksiz kod",
    "known_constants": "Mashhur algoritm konstantasi",
}

# Dehqoncha nomlar
SIMPLE_TITLES = {
    "mba": "aylanma hisob",
    "opaque_predicate": "javobi doim bir xil savol",
    "control_flow_flattening": "aralashtirilgan retsept",
    "encoded_strings": "qulflangan yozuv",
    "encoded_constants": "yashirilgan son",
    "dead_code": "ortiqcha ish",
    "known_constants": "tanish «imzo» son",
}

# Har bir usul uchun: hayotiy o'xshatish + vosita nima qildi (bir xil "hikoya" obrazlari: bozor, retsept, xat).
SIMPLE_UZ = {
    "mba": (
        "Bozorda sotuvchi «olma besh ming so'm» deyish o'rniga: «yigirma mingning to'rtdan biri, ustiga uch ming qo'sh, keyin uch mingni ayir» deydi. Narx baribir besh ming so'm, faqat uni tushunish uchun bosh qotirish kerak. Dasturda ham oddiy qo'shish yoki ayirish ataylab uzun hisobga aylantiriladi: unda oddiy qo'shish-ayirish bilan kompyuterning sonni 0 va 1 lar qatori sifatida o'zgartiradigan maxsus amallari aralashtirib yuboriladi. Dastur bu uzun hisobni minglab tasodifiy sonlar bilan sinab ko'rdi va har safar qisqa hisob bilan bir xil javob chiqqach, uzun yozuv o'rniga qisqasini qo'ydi (masalan, «ikki sonni qo'sh»). Qisqa shaklini topa olmasa, hech narsani o'zgartirmaydi, faqat «bu yer chigal» deb belgilab qo'yadi."
    ),
    "opaque_predicate": (
        "Dala yo'lidagi ayrilishga «Agar quyosh sharqdan chiqsa, chapga yur» deb yozib qo'yilgan. Quyosh har doim sharqdan chiqadi, demak hamma doim chapga yuradi, o'ng yo'l esa hech qachon kerak bo'lmaydi. Dasturda ham shart murakkab ko'rinadi, lekin javobi oldindan ma'lum: masalan, ketma-ket kelgan ikki sonning ko'paytmasi (3 × 4 = 12) har doim juft chiqadi. Dastur shartni 3000 xil tasodifiy son bilan tekshirib, javob har safar bir xil chiqishini ko'rdi va shartni «doim ha» yoki «doim yo'q» deb almashtirdi. So'ng hech qachon yurilmaydigan yo'lni (o'lik kodni) butunlay olib tashladi."
    ),
    "control_flow_flattening": (
        "Palov retsepti qadam-baqadam yozilmagan: har bir qadam alohida raqamli kartochkaga yozilib, kartochkalar aralashtirib tashlangan. Har kartochka oxirida «endi 77-kartochkani ol» yoki «suv qaynagan bo'lsa 12-ni, bo'lmasa 5-ni ol» degan yozuv bor, oshpaz esa har safar kerakli raqamni qidirib topadi. Palov baribir o'sha palov bo'lib chiqadi, lekin kartochkalarga qarab qaysi ish qachon qilinishini va qaysi ish takrorlanishini tushunish juda qiyin. Dastur barcha kartochkalarni o'qib, qaysi biri qaysi biriga yo'llashini xarita qilib chizdi; orqaga qaytaradigan yo'lni takrorlanadigan ish, ikkiga ajraladigan joyni «agar ... bo'lsa» deb tanib, retseptni yana tartibli ko'rinishga keltirdi. Tartibni to'liq tiklay olmasa, hech bo'lmaganda shu xaritani ko'rsatib beradi."
    ),
    "encoded_strings": (
        "Xatni begona o'qimasin deb, undagi har bir harf kalit yordamida boshqa belgiga almashtirib yoziladi. Xat egasi kalitni biladi va o'qishdan oldin belgilarni joyiga qaytaradi; bu qulfning qiziq tomoni — bitta kalitning o'zi bilan ham yopiladi, ham ochiladi. Dastur ichidagi so'zlar ham (masalan, «Parol noto'g'ri») shunday yopiq saqlanadi va faqat dastur ishlayotgan paytda ochiladi. Dastur kalitni avval kodning o'zidan qidirdi, topilmasa 255 ta mumkin bo'lgan kalitning hammasini birma-bir sinab, qaysi biri odam o'qiy oladigan matn berishini aniqladi (kalit shunday tanlab topilgan bo'lsa, buni ochiq aytadi). Ochilgan matnni hisobotga va tozalangan kod boshiga izoh qilib yozib qo'ydi."
    ),
    "encoded_constants": (
        "Do'kondor daftarga «qarz: 50 ming» deb yozish o'rniga «qarz: 120 mingdan 70 ming ayirilgani» deb yozib qo'yadi. Bu hisobda noma'lum narsa yo'q, faqat tayyor sonlar bor, shuning uchun javob har doim bir xil: 50 ming. Dasturda ham kerakli son to'g'ridan-to'g'ri yozilmaydi, bir necha sondan hisoblab chiqariladigan qilib yashiriladi. Dastur bu hisobni o'zi bajarib, uzun yozuv o'rniga tayyor javobni — bitta sonni qo'ydi. Bu yerda sinov ham kerak emas: hisobda noma'lum narsa yo'q, shuning uchun javob aniq."
    ),
    "dead_code": (
        "Oshpaz sabzi to'g'raydi-yu, uni qozonga solmay chetga tashlab qo'yadi. Palovning ta'mi o'zgarmaydi, faqat oshxonada ortiqcha ish ko'payadi, kuzatuvchi esa «bu sabzi qayerga ketdi?» deb boshini qotiradi. Dasturda ham hisoblanadi-yu hech qayerda ishlatilmaydigan qatorlar va hech qachon bajarilmaydigan bo'laklar ataylab qo'shiladi. Dastur har bir qiymat keyin qayerda ishlatilishini kuzatib chiqdi va hech qayerga «solinmaydigan» qutichalarni (o'zgaruvchilarni) hamda ularga tegishli qatorlarni olib tashladi. Keyin, imkoni bo'lsa, natija o'zgarmaganini sinov bilan tekshiradi."
    ),
    "known_constants": (
        "Qozonda zira, sariq sabzi va guruch ko'rsangiz, hali tatib ko'rmay turib «bu palov bo'lsa kerak» deysiz. Mashhur hisoblash usullarining ham shunday «imzo» sonlari bor, masalan 2166136261. Bu son kodda uchrasa, funksiya qaysi usulga o'xshashini taxmin qilish mumkin; bu chalkashtirish emas, aksincha, tahlilchiga yordam beradigan iz. Dastur koddagi sonlarni o'zi biladigan mashhur sonlar ro'yxati bilan solishtirdi va moslik topsa, «bu, ehtimol, falon usul» degan maslahat yozdi (masalan, FNV — uzun matndan qisqa «barmoq izi» son yasash usuli). Kodning o'zini esa o'zgartirmadi."
    ),
    "simplify": (
        "Bu qatordagi chigal hisob qisqaroq, lekin aynan bir xil javob beradigan ko'rinishga keltirildi. "
        "Dastur buni minglab tasodifiy sonlar bilan sinab ko'rdi."
    ),
    "unflatten": (
        "Aralashtirib tashlangan kartochkalar to'g'ri tartibga terildi: qayta-qayta bajariladigan ish "
        "«toki ... ekan, takrorla» ko'rinishiga, tanlov esa «agar ... bo'lsa» ko'rinishiga keltirildi."
    ),
}


def simple_explanation(key: str) -> str:
    return SIMPLE_UZ.get(key, "")


def simple_summary(techniques: list[str], unflattened: bool, simplified: bool) -> str:
    """Butun funksiya uchun dehqoncha xulosa (offline rejim)."""
    if not techniques:
        return ("Bu kodda ataylab chalkashtirish belgilari topilmadi — u shundoq ham oddiy yozilgan "
                "yoki chalkashtirish usuli vositaga notanish.")
    found = ", ".join(SIMPLE_TITLES.get(t, t) for t in techniques)
    done = []
    if simplified:
        done.append("chalkash hisoblarni soddalashtirdi")
    if unflattened:
        done.append("aralashtirilgan qadamlarni to'g'ri tartibga terdi")
    if "dead_code" in techniques:
        done.append("ortiqcha ishlarni olib tashladi")
    text = f"Bu kod ataylab chalkashtirilgan edi. Unda {found} bor edi."
    if done:
        text += " Vosita " + ", ".join(done) + "."
    return text + (" Keyin yangi kod eskisi bilan minglab tasodifiy sonlarda solishtiriladi: "
                   "ikkalasi bir xil javob bersa — soddalashtirish to'g'ri.")
