// Builds docs/Proje_Dokumantasyonu.docx from the project's markdown docs.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, LevelFormat, ExternalHyperlink, PageBreak,
  TableOfContents, Footer, Header, PageNumber, BorderStyle,
} = require("docx");

const ROOT = "C:/Projects/master/pertubation-prediction";
const CONTENT_W = 9638; // A4 (11906) - 2 x 1134 margins
const FONT = "Calibri";
const ACCENT = "1F4E79";

// ---------- inline markdown -> runs ----------
function inline(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|<https?:\/\/[^>]+>|https?:\/\/[^\s)|,]+)/g;
  let last = 0, m;
  const push = (t, o = {}) => t && out.push(new TextRun({ text: t, font: FONT, ...base, ...o }));
  while ((m = re.exec(text))) {
    push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(...inline(tok.slice(2, -2), { ...base, bold: true }));
    else if (tok.startsWith("`")) push(tok.slice(1, -1), { font: "Consolas", size: (base.size || 22) - 2, color: "7A2E2E" });
    else if (tok.startsWith("[")) {
      const [, t, u] = tok.match(/\[([^\]]+)\]\(([^)]+)\)/);
      const url = u.startsWith("http") ? u : null;
      if (url) out.push(link(t, url, base)); else push(t, { font: "Consolas", size: (base.size || 22) - 2 });
    } else if (tok.startsWith("<")) out.push(link(tok.slice(1, -1), tok.slice(1, -1), base));
    else if (tok.startsWith("http")) out.push(link(tok, tok, base));
    else push(tok.slice(1, -1), { italics: true });
    last = m.index + tok.length;
  }
  push(text.slice(last));
  return out;
}
function link(t, url, base) {
  return new ExternalHyperlink({ link: url, children: [new TextRun({ text: t, style: "Hyperlink", font: FONT, ...base })] });
}

// ---------- table ----------
function table(rows) {
  const cells = rows.map(r => r.replace(/^\||\|$/g, "").split("|").map(c => c.trim()));
  const n = cells[0].length;
  const len = Array(n).fill(0);
  cells.forEach(r => r.forEach((c, i) => { len[i] = Math.max(len[i], Math.min(c.length, 60)); }));
  const raw = len.map(l => Math.max(l, 8));
  const tot = raw.reduce((a, b) => a + b, 0);
  const widths = raw.map(l => Math.floor(CONTENT_W * l / tot));
  widths[n - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: cells.map((r, ri) => new TableRow({
      tableHeader: ri === 0,
      children: r.map((c, ci) => new TableCell({
        width: { size: widths[ci], type: WidthType.DXA },
        borders,
        shading: ri === 0 ? { type: ShadingType.CLEAR, fill: ACCENT, color: "auto" }
          : ri % 2 === 0 ? { type: ShadingType.CLEAR, fill: "F2F6FA", color: "auto" } : undefined,
        margins: { top: 60, bottom: 60, left: 90, right: 90 },
        children: [new Paragraph({
          spacing: { before: 0, after: 0 },
          children: inline(c, ri === 0 ? { size: 18, bold: true, color: "FFFFFF" } : { size: 18 }),
        })],
      })),
    })),
  });
}

// ---------- block markdown -> docx elements ----------
function convert(md, { title, dropFirstH1 = true, headingShift = 0 } = {}) {
  const lines = md.replace(/\r/g, "").split("\n");
  const out = [];
  if (title) out.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun(title)] }));
  let i = 0, para = [];
  const flush = () => {
    if (para.length) out.push(new Paragraph({ spacing: { after: 120 }, children: inline(para.join(" ")) }));
    para = [];
  };
  const H = [HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3, HeadingLevel.HEADING_4];
  while (i < lines.length) {
    const l = lines[i];
    const hm = l.match(/^(#{1,4})\s+(.*)$/);
    if (hm) {
      flush();
      const lvl = hm[1].length;
      if (lvl === 1 && dropFirstH1) { i++; continue; }
      out.push(new Paragraph({ heading: H[Math.min(lvl - 1 + headingShift, 3)], children: inline(hm[2]) }));
      i++; continue;
    }
    if (l.startsWith("```")) {
      flush(); i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        out.push(new Paragraph({
          shading: { type: ShadingType.CLEAR, fill: "F3F3F3", color: "auto" },
          spacing: { before: 0, after: 0 },
          children: [new TextRun({ text: lines[i] || " ", font: "Consolas", size: 18 })],
        }));
        i++;
      }
      out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
      i++; continue;
    }
    if (l.startsWith("|")) {
      flush();
      const rows = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        if (!/^\|\s*:?-{2,}/.test(lines[i])) rows.push(lines[i]);
        i++;
      }
      out.push(table(rows));
      out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
      continue;
    }
    const bm = l.match(/^(\s*)[-*]\s+(.*)$/);
    const nm = l.match(/^(\s*)\d+\.\s+(.*)$/);
    if (bm || nm) {
      flush();
      const m = bm || nm;
      const level = Math.min(Math.floor(m[1].length / 2), 2);
      out.push(new Paragraph({
        numbering: { reference: bm ? "bullets" : "numbers", level },
        spacing: { after: 60 },
        children: inline(m[2]),
      }));
      i++; continue;
    }
    if (/^---+\s*$/.test(l)) {
      flush();
      out.push(new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "BFBFBF", space: 1 } }, children: [] }));
      i++; continue;
    }
    if (!l.trim()) { flush(); i++; continue; }
    para.push(l.trim());
    i++;
  }
  flush();
  return out;
}

const read = f => fs.readFileSync(path.join(ROOT, f), "utf8");

// README: drop the file-index table section (the document itself replaces it)
let readme = read("README.md");
readme = readme.replace(/^[\s\S]*?(?=## Kurulum)/, "");
readme = readme.replace(/^## /gm, "## ");

const cover = [
  new Paragraph({ spacing: { before: 3000 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: "Bitirme Projesi Dokümantasyonu", font: FONT, size: 28, color: "595959" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
    children: [new TextRun({ text: "Donör-Farkında, Çok Modaliteli Tek Hücre Perturbation Cevabı Tahmini", font: FONT, size: 44, bold: true, color: ACCENT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1200 },
    children: [new TextRun({ text: "Literatür taraması, veri setleri, araştırma planı ve pertbench benchmark paketi", font: FONT, size: 24, italics: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "Hasan Berk Berber, Emre Atay Tümer, Alperen Çantay, Bengisu Atlı", font: FONT, size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "Danışman: Hilal Kazan", font: FONT, size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "Bilgisayar Mühendisliği", font: FONT, size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "29 Eylül 2026 · Taslak v0.1", font: FONT, size: 22, color: "7F7F7F" })] }),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "İçindekiler", font: FONT, size: 36, bold: true, color: ACCENT })] }),
  new TableOfContents("İçindekiler", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ spacing: { before: 200 }, children: [new TextRun({
    text: "Not: İçindekiler tablosu Word'de açılışta güncellenmezse tabloya sağ tıklayıp \"Alanı Güncelleştir\" seçin.",
    font: FONT, size: 18, italics: true, color: "7F7F7F" })] }),
];

const body = [
  ...cover,
  ...convert(read("docs/01_literatur_taramasi.md"), { title: "1. Literatür Taraması" }),
  ...convert(read("docs/02_veri_setleri.md"), { title: "2. Veri Setleri" }),
  ...convert(read("docs/03_arastirma_plani.md"), { title: "3. Araştırma Planı" }),
  ...convert(readme, { title: "4. Teknik Dokümantasyon: pertbench" }),
  ...convert(read("docs/04_hocaya_email_taslagi.md"), { title: "Ek A. Danışmana Yanıt Taslağı" }),
];

const doc = new Document({
  creator: "Hasan Berk Berber, Emre Atay Tümer, Alperen Çantay, Bengisu Atlı",
  title: "Donör-Farkında Çok Modaliteli Perturbation Tahmini",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, color: ACCENT, font: FONT }, paragraph: { spacing: { before: 240, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: ACCENT, font: FONT }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: "404040", font: FONT }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [0, 1, 2].map(l => ({
        level: l, format: LevelFormat.BULLET, text: ["•", "◦", "▪"][l], alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720 + 360 * l, hanging: 360 } } } })) },
      { reference: "numbers", levels: [0, 1, 2].map(l => ({
        level: l, format: LevelFormat.DECIMAL, text: `%${l + 1}.`, alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720 + 360 * l, hanging: 360 } } } })) },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Perturbation Prediction · Bitirme Projesi", size: 16, color: "7F7F7F", font: FONT })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "7F7F7F", font: FONT })] })] }) },
    children: body,
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(ROOT, "docs", "Proje_Dokumantasyonu.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out, buf.length, "bytes");
});
