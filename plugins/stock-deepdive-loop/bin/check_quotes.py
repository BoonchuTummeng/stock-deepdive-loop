#!/usr/bin/env python3
"""
check_quotes.py — ตรวจว่า Quote ใน atom ตรงกับเอกสารต้นฉบับที่อ้างจริงไหม

atom เขียนที่ขั้น L8 ซึ่งอยู่หลังด่านตรวจทั้งหมด จึงไม่มีใครตรวจ — สคริปต์นี้ปิดช่องนั้น
ทำงานแบบกำหนดแน่นอน (ไม่ใช้ AI) เหมือน check_numbers.py:
  1. อ่านทุก atom ของหุ้น (knowledge-base/atoms/<TICKER>-*.md)
  2. ดึง source_file (อาจมีหลายไฟล์) และบรรทัด **Quote:**
  3. เทียบ Quote กับ "ไฟล์ .txt ที่อ้าง" โดยไม่สนช่องว่าง/การขึ้นบรรทัด/เครื่องหมายคำพูด
     (ตัดคำอธิบายในวงเล็บเหลี่ยมท้าย Quote และแยกท่อนที่คั่นด้วย … หรือ ... ตรวจทีละท่อน)

ผลต่อ atom:
  OK         Quote ทุกท่อนอยู่ในไฟล์ที่อ้าง
  WRONG-FILE Quote อยู่ในไฟล์อื่นของหุ้นนี้ ไม่ใช่ที่อ้าง  (แก้ source_file)
  NOT-FOUND  Quote ไม่พบในไฟล์ใดเลย  (ประกอบ/ย่อ/แก้ถ้อยคำ → แก้ให้ตรงหรือเลิกใช้ Quote)
  NO-QUOTE   ไม่มี Quote และไม่ได้อ้างเป็น "ตาราง: …"
  NO-SOURCE  หา .txt ของไฟล์ที่อ้างไม่เจอ (เปิดตรวจไม่ได้ — ไม่ถือว่าผ่าน)

รหัสออก: 0 ผ่านทุก atom · 1 มี atom ที่ไม่ผ่าน · 2 หาโฟลเดอร์/ไฟล์ไม่เจอ

ตัวอย่าง:
    python check_quotes.py CPALL
    python check_quotes.py CPALL --lib "C:\\ทุกบริษัท" --atoms knowledge-base/atoms
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        if (_s.encoding or "").lower().replace("-", "") != "utf8":
            _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MIN_FRAGMENT = 12  # ท่อนสั้นกว่านี้ (หลังตัดช่องว่าง) ไม่ใช้ตัดสิน
DROP = re.compile(r"[\s\u200b\u00a0\"'“”‘’`]+")
SRC_EXT = re.compile(r"[\w\-.]+\.(?:txt|pdf|docx|xlsx|htm|html)", re.I)


def norm(s: str) -> str:
    return DROP.sub("", unicodedata.normalize("NFC", s))


def find_root() -> Path:
    cur = Path.cwd().resolve()
    for d in [cur, *cur.parents]:
        if (d / "CLAUDE.md").is_file() and (d / "knowledge-base").is_dir():
            return d
    return cur


def find_lib(root: Path, ticker: str):
    """หารากคลังเอกสารจากบรรทัด 'ราก: <path>\\<TICKER>' ใน CLAUDE.md ของโปรเจกต์"""
    cm = root / "CLAUDE.md"
    if cm.is_file():
        for line in cm.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"\s*ราก\s*[:：]\s*(.+?)[\\/]<TICKER>", line)
            if m:
                return Path(m.group(1).strip().strip("`"))
    return None


def frontmatter(text: str) -> dict:
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    return dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M)) if m else {}


def quote_of(text: str):
    m = re.search(r"\*\*Quote:\*\*\s*(.+?)(?:\n\s*\n|\n\*\*|\Z)", text, re.S)
    return m.group(1).strip() if m else None


def fragments(q: str):
    q = re.sub(r"\s*\[[^\]]*\]\s*$", "", q.strip())          # คำอธิบายท้าย Quote
    parts = re.split(r"\s*(?:…|\.{3,})\s*", q)
    return [p for p in parts if len(norm(p)) >= MIN_FRAGMENT]


def main():
    ap = argparse.ArgumentParser(description="ตรวจ Quote ของ atom กับเอกสารต้นฉบับ")
    ap.add_argument("ticker")
    ap.add_argument("--atoms", default=None, help="โฟลเดอร์ atoms (ค่าเริ่มต้น <รากโปรเจกต์>/knowledge-base/atoms)")
    ap.add_argument("--lib", default=None, help="รากคลังเอกสาร (ค่าเริ่มต้น: อ่านจาก CLAUDE.md)")
    a = ap.parse_args()
    t = a.ticker.upper()

    root = find_root()
    atoms_dir = Path(a.atoms) if a.atoms else root / "knowledge-base" / "atoms"
    lib = Path(a.lib) if a.lib else find_lib(root, t)
    if lib is None:
        print("หารากคลังเอกสารไม่เจอ — ระบุด้วย --lib", file=sys.stderr)
        sys.exit(2)
    tdir = lib / t
    if not tdir.is_dir() or not atoms_dir.is_dir():
        print(f"ไม่พบโฟลเดอร์: {tdir if not tdir.is_dir() else atoms_dir}", file=sys.stderr)
        sys.exit(2)

    cache = {}

    def text_of(path: Path):
        if path not in cache:
            cache[path] = norm(path.read_text(encoding="utf-8", errors="replace")) if path.is_file() else None
        return cache[path]

    def txt_for(name: str):
        p = tdir / name
        cand = p if p.suffix.lower() == ".txt" else p.with_suffix(".txt")
        return cand if cand.is_file() else None

    all_txt = sorted(tdir.glob("*.txt"))
    bad = 0
    rows, fails = [], []
    files = sorted(atoms_dir.glob(f"{t}-*.md"))
    if not files:
        print(f"ไม่พบ atom ของ {t} ใน {atoms_dir}", file=sys.stderr)
        sys.exit(2)

    for f in files:
        body = f.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(body)
        names = SRC_EXT.findall(fm.get("source_file", ""))
        cited = [p for p in (txt_for(n) for n in names) if p]
        q = quote_of(body)
        status, note = "OK", ""
        if q is None or not q.strip():
            if re.search(r"ตาราง\s*[:：]", body):
                status, note = "OK", "อ้างเป็นตาราง ไม่มี Quote"
            else:
                status = "NO-QUOTE"
        elif not cited:
            status, note = "NO-SOURCE", f"หา .txt ของ {names or 'source_file ว่าง'} ไม่เจอ"
        else:
            frs = fragments(q)
            if not frs:
                status, note = "NO-QUOTE", "Quote สั้นเกินกว่าจะตรวจ"
            else:
                miss_cited, miss_all = [], []
                for fr in frs:
                    n = norm(fr)
                    if any(n in (text_of(p) or "") for p in cited):
                        continue
                    miss_cited.append(fr)
                    if not any(n in (text_of(p) or "") for p in all_txt):
                        miss_all.append(fr)
                if miss_all:
                    status, note = "NOT-FOUND", "ไม่พบ: " + miss_all[0][:90].replace("\n", " ")
                elif miss_cited:
                    status, note = "WRONG-FILE", "Quote อยู่ในไฟล์อื่น ไม่ใช่ " + ", ".join(p.name for p in cited)[:80]
        line = f"{f.name}\t{status}\t{note}"
        rows.append(line)
        if status != "OK":
            bad += 1
            fails.append(line)

    # ไม่ผ่านขึ้นก่อน และสรุปเป็นบรรทัดสุดท้ายเสมอ — กันการอ่านผลแค่บางส่วนแล้วสรุปว่า "ผ่านทุกตัว"
    if fails:
        print(f"== ไม่ผ่าน {bad} atom ==")
        print("\n".join(fails))
        print()
    print("== ทุก atom ==")
    print("\n".join(rows))
    verdict = "ผ่านทุก atom" if not bad else f"ไม่ผ่าน {bad} atom (ห้ามรายงานว่า L8 เสร็จ)"
    print(f"\nสรุป: {len(files) - bad}/{len(files)} atom ผ่าน — {verdict}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
