// Umumiy yordamchi funksiyalar: asl amaliy ish fayllaridagi formatga moslangan
const fs = require("fs");
const sizeOf = (p) => {
  const b = fs.readFileSync(p);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; // PNG IHDR
};
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType,
  WidthType, BorderStyle, ShadingType, Footer, PageNumber, VerticalAlign, LevelFormat, PageBreak,
  TabStopType, PageOrientation,
} = require("docx");

const FONT = "Times New Roman";
const TEXT_W = 11906 - 1701 - 850; // 9355 DXA

// **qalin**, *kursiv* belgilarini TextRun larga ajratish
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), ...base, bold: true }));
    else out.push(new TextRun({ text: t.slice(1, -1), ...base, italics: true }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

const sp = { after: 0, line: 360, lineRule: "auto" };

// Oddiy matn abzasi: eni bo'yicha tekislangan, xat boshi 1,25 sm
const p = (text, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { ...sp, ...(o.spacing || {}) },
  indent: o.noIndent ? undefined : { firstLine: o.firstLine ?? 709 },
  keepNext: o.keepNext,
  children: runs(text, o.run || {}),
});

// Markazlashgan qalin sarlavha (asl fayldagidek, Heading stilisiz)
const h = (text, o = {}) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { ...sp, before: o.before ?? 120, after: o.after ?? 0 },
  keepNext: true,
  children: runs(text, { bold: true, italics: !!o.italic }),
});

// Ro'yxat bandi: "- matn" yoki "1. matn" ko'rinishida, xat boshi bilan
const li = (text, o = {}) => p(text, o);

const img = (path, widthPx) => {
  const s = sizeOf(path);
  const width = widthPx;
  const height = Math.round((s.h / s.w) * widthPx);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 0, line: 240, lineRule: "auto" },
    keepNext: true,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width, height } })],
  });
};

const caption = (text) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { ...sp, after: 120 },
  children: [new TextRun({ text, size: 24 })],
});

// Jadval nomi: o'ngda "1-jadval", keyin markazda nomi
const tcap = (num, title) => [
  new Paragraph({
    alignment: AlignmentType.RIGHT, spacing: { ...sp, before: 120 }, keepNext: true,
    children: [new TextRun({ text: num, italics: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { ...sp, after: 60 }, keepNext: true,
    children: [new TextRun({ text: title, bold: true })],
  }),
];

const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: border, bottom: border, left: border, right: border };

// rows: birinchi qator sarlavha. Katak: string yoki {t, fill, bold, align}
function table(widths, rows, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const fs_ = o.size || 24;
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    alignment: AlignmentType.CENTER,
    rows: rows.map((r, ri) => new TableRow({
      tableHeader: ri === 0,
      cantSplit: true,
      children: r.map((c, ci) => {
        const cell = typeof c === "object" ? c : { t: String(c) };
        const head = ri === 0 || cell.head;
        const lines = String(cell.t).split("\n");
        const align = cell.align || (head ? AlignmentType.CENTER : (o.align?.[ci] || AlignmentType.LEFT));
        return new TableCell({
          borders,
          width: { size: widths[ci], type: WidthType.DXA },
          columnSpan: cell.span,
          verticalAlign: VerticalAlign.CENTER,
          shading: (cell.fill || head) ? { fill: cell.fill || "F2F2F2", type: ShadingType.CLEAR, color: "auto" } : undefined,
          margins: { top: 30, bottom: 30, left: 80, right: 80 },
          children: lines.map((ln) => new Paragraph({
            alignment: align,
            spacing: { after: 0, line: 240, lineRule: "auto" },
            children: runs(ln, { size: fs_, bold: head || cell.bold }),
          })),
        });
      }),
    })),
  });
}

const blank = () => new Paragraph({ spacing: sp, children: [] });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

// Titul varag'i (ma'lumotlar keyin to'ldiriladi)
function titlePage(t, workTitle, topic) {
  const c = (text, o = {}) => new Paragraph({
    alignment: o.align || AlignmentType.CENTER,
    spacing: { after: 0, line: 360, lineRule: "auto", before: o.before || 0 },
    children: [new TextRun({ text, bold: !!o.bold, size: o.size || 28, allCaps: !!o.caps })],
  });
  const kv = (k, v, before = 0) => new Paragraph({
    spacing: { after: 0, line: 360, lineRule: "auto", before },
    indent: { left: 4536 },
    children: [new TextRun({ text: k, bold: true }), new TextRun({ text: v })],
  });
  const out = [];
  (t.ministry ? [t.ministry] : []).forEach((x) => out.push(c(x, { bold: true, caps: true })));
  out.push(c(t.university, { bold: true, caps: true }));
  if (t.faculty) out.push(c(t.faculty, { before: 240 }));
  if (t.department) out.push(c(t.department));
  out.push(c(`"${t.subject}" fanidan`, { before: 1800 }));
  out.push(c(workTitle.toUpperCase(), { bold: true, size: 36, before: 240 }));
  out.push(c(`Mavzu: ${topic}`, { bold: true, before: 240 }));
  out.push(kv("Bajardi: ", t.student, 2200));
  out.push(kv("Guruh: ", t.group));
  out.push(kv("Qabul qildi: ", t.teacher));
  out.push(c(`${t.city} – ${t.year}`, { before: 2000 }));
  out.push(pageBreak());
  return out;
}

// parts: oddiy children massivi yoki [{ children, landscape }] bo'limlar ro'yxati
function makeDoc(parts) {
  if (!parts[0] || !parts[0].children) parts = [{ children: parts }];
  const footer = () => new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 22 })],
    })],
  });
  return new Document({
    styles: {
      default: { document: { run: { font: FONT, size: 28, language: { value: "uz-Latn-UZ" } } } },
    },
    sections: parts.map((part) => ({
      properties: {
        page: part.landscape ? {
          size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE },
          margin: { top: 1134, right: 1134, bottom: 850, left: 1134, header: 709, footer: 567 },
        } : {
          size: { width: 11906, height: 16838 },
          margin: { top: 1134, right: 850, bottom: 1134, left: 1701, header: 709, footer: 709 },
        },
      },
      footers: { default: footer() },
      children: part.children,
    })),
  });
}

async function save(doc, path) {
  fs.writeFileSync(path, await Packer.toBuffer(doc));
}

module.exports = { p, h, li, img, caption, tcap, table, blank, pageBreak, titlePage, makeDoc, save, TEXT_W, AlignmentType };
