// deobf-agent uchun Ghidra eksport skripti: funksiyalarning psevdokodini .c faylga saqlaydi.
//
// GUI'da ishlatish:
//   1. Window -> Script Manager -> "Manage Script Directories" orqali shu papkani qo'shing.
//   2. Kerakli funksiyaga kursorni qo'ying va skriptni ishga tushiring.
//      "Faqat joriy funksiya?" savoliga "Yes" — bitta funksiya, "No" — barcha funksiyalar.
//
// Headless (avtomatik) rejim:
//   analyzeHeadless <loyiha_papkasi> <loyiha_nomi> -import samples/bin/s3_flatten.elf \
//       -scriptPath scripts -postScript ghidra_export.java natija.ghidra.c [funksiya_nomi]
//
// ESLATMA: bu skript loyiha ishlab chiqilgan muhitda sinab ko'rilmagan (u yerda Ghidra yo'q edi).
//
//@category deobf-agent
//@menupath Tools.deobf-agent.Export pseudocode

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class ghidra_export extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        File out;
        String only = null;
        boolean onlyCurrent = false;
        if (args.length > 0) {
            out = new File(args[0]);
            if (args.length > 1) {
                only = args[1];
            }
        } else {
            out = askFile("Psevdokodni saqlash (.c)", "Saqlash");
            Function cur = getFunctionContaining(currentAddress);
            if (cur != null) {
                onlyCurrent = askYesNo("deobf-agent", "Faqat joriy funksiya (" + cur.getName() + ")?");
                if (onlyCurrent) {
                    only = cur.getName();
                }
            }
        }

        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        int count = 0;
        try (PrintWriter w = new PrintWriter(new FileWriter(out))) {
            FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
            while (it.hasNext() && !monitor.isCancelled()) {
                Function f = it.next();
                if (f.isExternal() || f.isThunk()) {
                    continue;
                }
                if (only != null && !f.getName().equals(only)) {
                    continue;
                }
                DecompileResults res = ifc.decompileFunction(f, 60, monitor);
                if (res == null || !res.decompileCompleted() || res.getDecompiledFunction() == null) {
                    printerr("Dekompilyatsiya bo'lmadi: " + f.getName());
                    continue;
                }
                w.println("// " + f.getName() + " @ " + f.getEntryPoint());
                w.println(res.getDecompiledFunction().getC());
                count++;
            }
        } finally {
            ifc.dispose();
        }
        println("deobf-agent: " + count + " ta funksiya saqlandi -> " + out.getAbsolutePath());
    }
}
