#!/usr/bin/env python3
"""
oppday_subs.py — ดึงคำบรรยายอัตโนมัติ (ASR) ของคลิป Oppday จาก YouTube เป็นไฟล์ข้อความอ่านง่าย

ใช้คู่กับ find_oppday.py (ได้ URL มาแล้วส่งต่อให้สคริปต์นี้)
ดึงเฉพาะ "คำบรรยาย" ไม่โหลดวิดีโอหรือเสียง — ใช้ yt-dlp (ไลบรารีภายนอก ติดตั้งเอง: python -m pip install -U yt-dlp)

เหตุที่ต้องใช้ yt-dlp: ลิงก์คำบรรยายที่หน้า YouTube ให้มาเรียกตรงได้ผลว่างเปล่า (YouTube ตรวจโทเคนฝั่งเบราว์เซอร์)
yt-dlp ตามการเปลี่ยนแปลงของ YouTube ให้ — ถ้าดึงไม่ได้ให้ลอง `python -m pip install -U yt-dlp` ก่อน

⚠️ ผลคือ "เสียงถอดอัตโนมัติ (ASR)" — ตัวเลขห้ามใช้ตรง ต้องเทียบงบ ชื่อคนอาจเพี้ยน หัวไฟล์จึงมีคำเตือนเสมอ
สคริปต์ไม่เขียนทับไฟล์ที่มีอยู่ (ชื่อซ้ำจะหยุด)

ตัวอย่าง:
    python oppday_subs.py https://www.youtube.com/watch?v=wYCz3EB5CsA --out ./CPALL_Oppday_Q2-2026.txt --label "CPALL Oppday Q2/2026"

รหัสออก: 0 สำเร็จ · 1 ไม่มีคำบรรยาย/ข้อความสั้นผิดปกติ · 2 ใช้ yt-dlp ไม่ได้/ดึงไม่ได้ · 3 ไฟล์ปลายทางมีอยู่แล้ว
"""
import argparse
import datetime
import os
import re
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        if (_s.encoding or "").lower().replace("-", "") != "utf8":
            _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MIN_CHARS = 2000
STAMP_EVERY = 300  # วินาที — ใส่เวลากำกับทุก ~5 นาที เพื่อย้อนกลับไปฟังช่วงนั้นได้

TS = re.compile(r"(\d+):(\d\d):(\d\d)\.(\d+)\s+-->\s+")
TAG = re.compile(r"<[^>]+>")


def vtt_to_text(vtt: str):
    """แปลง VTT ของ auto-caption (มีบรรทัดซ้ำแบบเลื่อนทีละคำ) เป็นข้อความต่อเนื่อง + เวลากำกับ"""
    out, last, next_stamp = [], "", 0
    cur_t = 0
    for raw in vtt.splitlines():
        m = TS.match(raw)
        if m:
            h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
            cur_t = h * 3600 + mi * 60 + s
            continue
        if not raw.strip() or raw.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        line = TAG.sub("", raw).strip()
        if not line or line == last:
            continue
        # auto-caption มักทวนบรรทัดก่อนหน้าเป็นส่วนต้นของบรรทัดใหม่ — เก็บเฉพาะส่วนที่เพิ่ม
        if last and line.startswith(last):
            addition = line[len(last):].strip()
            last = line
            if not addition:
                continue
            line = addition
        else:
            last = line
        if cur_t >= next_stamp:
            out.append(f"\n[{cur_t // 3600:02d}:{cur_t % 3600 // 60:02d}:{cur_t % 60:02d}]")
            next_stamp = cur_t + STAMP_EVERY
        out.append(line)
    return " ".join(out).replace(" \n", "\n").replace("\n ", "\n").strip()


def main():
    ap = argparse.ArgumentParser(description="ดึงคำบรรยายอัตโนมัติของคลิป Oppday เป็นไฟล์ข้อความ")
    ap.add_argument("url")
    ap.add_argument("--out", required=True, help="ไฟล์ข้อความปลายทาง (ต้องยังไม่มีอยู่)")
    ap.add_argument("--lang", default="th")
    ap.add_argument("--label", default="", help="ชื่อกำกับในหัวไฟล์ เช่น 'CPALL Oppday Q2/2026'")
    a = ap.parse_args()

    out = Path(a.out)
    if out.exists():
        print(f"ไม่เขียนทับ: {out} มีอยู่แล้ว", file=sys.stderr)
        sys.exit(3)

    try:
        import yt_dlp  # noqa: F401
        from yt_dlp import YoutubeDL
    except Exception:
        print("ไม่พบ yt-dlp — ติดตั้งด้วย: python -m pip install -U yt-dlp (แล้วรันใหม่) "
              "หรือใช้วิธีมือ: เปิดคลิป → 'แสดงข้อความถอดเสียง' → คัดลอก", file=sys.stderr)
        sys.exit(2)

    with tempfile.TemporaryDirectory() as td:
        opts = {"skip_download": True, "writeautomaticsub": True, "writesubtitles": True,
                "subtitleslangs": [a.lang], "subtitlesformat": "vtt",
                "outtmpl": os.path.join(td, "%(id)s"), "quiet": True, "no_warnings": True}
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(a.url, download=True)
        except Exception as e:
            print(f"ดึงคำบรรยายไม่ได้: {str(e)[:300]}\n"
                  "ลอง: python -m pip install -U yt-dlp  แล้วรันใหม่ · ไม่ได้ผล = ใช้วิธีมือ", file=sys.stderr)
            sys.exit(2)
        files = sorted(Path(td).glob("*.vtt"))
        if not files:
            print(f"คลิปนี้ไม่มีคำบรรยายภาษา {a.lang}", file=sys.stderr)
            sys.exit(1)
        text = vtt_to_text(files[0].read_text(encoding="utf-8", errors="replace"))

    if len(text) < MIN_CHARS:
        print(f"ข้อความสั้นผิดปกติ ({len(text)} ตัวอักษร) — ไม่บันทึก ห้ามใช้", file=sys.stderr)
        sys.exit(1)

    title = (info or {}).get("title", "")
    chan = (info or {}).get("channel") or (info or {}).get("uploader", "")
    vid_date = (info or {}).get("upload_date", "")
    header = (
        f"# {a.label or title}\n\n"
        f"- คลิป: {title}\n- ช่อง: {chan}\n- URL: {a.url}\n"
        f"- วันที่คลิป: {vid_date}\n- วันที่เก็บ: {datetime.date.today().isoformat()}\n"
        f"- ที่มา: คำบรรยายอัตโนมัติของ YouTube ({a.lang}) ผ่าน yt-dlp\n\n"
        "> ⚠️ **เสียงถอดอัตโนมัติ (ASR)** — คำพูดผู้บริหารเป็น**คำอ้าง** · **ห้ามใช้ตัวเลขตรง ๆ ต้องเทียบงบ** · "
        "ชื่อบุคคลอาจเพี้ยน · ศัพท์เทคนิค/ชื่อบริษัทอาจถอดผิด · เวลา [HH:MM:SS] ไว้ย้อนฟังต้นฉบับ\n\n---\n\n"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(header + text + "\n", encoding="utf-8")
    os.replace(tmp, out)
    print(f"บันทึก {out} ({len(text):,} ตัวอักษร)")


if __name__ == "__main__":
    main()
