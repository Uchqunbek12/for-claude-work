"""deobf-agent uchun IDA eksport skripti (IDAPython): Hex-Rays psevdokodini .c faylga saqlaydi.

Ishlatish (IDA Pro / IDA Home — IDAPython va Hex-Rays dekompilyatori bilan):
    File -> Script file... -> scripts/ida_export.py

IDA Free'da IDAPython mavjud bo'lmasligi mumkin. Unda psevdokodni qo'lda oling:
    F5 (psevdokod oynasi) -> Ctrl+A -> Ctrl+C -> faylga yoki Web UI'ga joylang.
Global ma'lumotlar (masalan, shifrlangan baytlar): baytlarni belgilab, Shift+E ->
"C unsigned char array" -> natijani psevdokod oxiriga qo'shing.

ESLATMA: bu skript loyiha ishlab chiqilgan muhitda sinab ko'rilmagan (u yerda IDA yo'q edi).
"""

import ida_funcs
import ida_hexrays
import ida_kernwin
import idautils
import idc


def main():
    if not ida_hexrays.init_hexrays_plugin():
        ida_kernwin.warning("Hex-Rays dekompilyatori mavjud emas.")
        return
    path = ida_kernwin.ask_file(1, "*.c", "Psevdokodni saqlash")
    if not path:
        return
    cur = ida_funcs.get_func(idc.get_screen_ea())
    only_current = cur is not None and ida_kernwin.ask_yn(
        ida_kernwin.ASKBTN_YES, "Faqat joriy funksiya (%s)?" % idc.get_func_name(cur.start_ea)) == ida_kernwin.ASKBTN_YES
    starts = [cur.start_ea] if only_current else list(idautils.Functions())
    count = 0
    with open(path, "w", encoding="utf-8") as out:
        for ea in starts:
            func = ida_funcs.get_func(ea)
            if func is None or func.flags & (ida_funcs.FUNC_LIB | ida_funcs.FUNC_THUNK):
                continue
            try:
                cfunc = ida_hexrays.decompile(ea)
            except ida_hexrays.DecompilationFailure as exc:
                print("Dekompilyatsiya bo'lmadi: %s (%s)" % (idc.get_func_name(ea), exc))
                continue
            if cfunc is None:
                continue
            out.write("// %s @ 0x%X\n%s\n\n" % (idc.get_func_name(ea), ea, str(cfunc)))
            count += 1
    print("deobf-agent: %d ta funksiya saqlandi -> %s" % (count, path))


main()
