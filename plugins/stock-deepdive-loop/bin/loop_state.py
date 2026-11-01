#!/usr/bin/env python3
"""
loop_state.py — บันทึกและตรวจสถานะของวงวิจัยหุ้น เพื่อให้รันซ้ำแล้วทำต่อจากที่ค้างได้

เก็บที่ knowledge-base/_drafts/loop-<TICKER>/state.json
หลักการ: **ไม่เชื่อ state อย่างเดียว** — ขั้นจะถือว่าเสร็จก็ต่อเมื่อมีบันทึกว่าเสร็จ
และไฟล์ผลลัพธ์ของขั้นนั้นอยู่บนดิสก์จริง (กันกรณี agent บอกว่าเขียนแล้วแต่ไม่มีไฟล์)

ตัวอย่าง:
    python loop_state.py status CPALL
    python loop_state.py start  CPALL L3
    python loop_state.py done   CPALL L3 --seconds 540
    python loop_state.py next   CPALL
    python loop_state.py reset  CPALL L5        # ล้างสถานะตั้งแต่ L5 เป็นต้นไป (ไม่ลบไฟล์)

ใช้เฉพาะไลบรารีมาตรฐาน เขียนไฟล์แบบ atomic (.tmp แล้ว replace)
"""
import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        if (_s.encoding or "").lower().replace("-", "") != "utf8":
            _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

STEPS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"]


def outputs(step, t, kb, paper):
    """รายการ glob ที่ต้องมีอย่างน้อยหนึ่งไฟล์ต่อรายการ ขั้นถึงจะถือว่ามีผลลัพธ์จริง"""
    d = kb / "_drafts" / f"loop-{t}"
    return {
        "L0": [str(d / "state.json")],
        "L1": [str(d / "idea-card.md")],
        "L2": [],  # เอกสารอยู่ใน ทุกบริษัท\ ซึ่งสคริปต์นี้ไม่รู้ที่อยู่ — collector รายงานเอง
        "L3": [str(kb / "notebooklm-qa" / f"{t}.md")],
        "L4": [str(paper / f"{t}-FACTS.md"), str(paper / f"{t}-SPINE.md")],
        "L5": [str(paper / "_parts" / "*.html")],
        "L6": [str(paper / "_gate" / "checker-*.md"), str(paper / "_gate" / "critic-*.md"),
               str(paper / "_gate" / "redteam-*.md"), str(paper / "_gate" / "omission-*.md")],
        "L7": [str(paper / f"{t}-loop-*.html")],
        "L8": [str(kb / "atoms" / f"{t}-*.md")],
    }[step]


def find_root():
    """รากโปรเจกต์ = โฟลเดอร์แรก (ไล่ขึ้นจาก cwd) ที่มีทั้ง CLAUDE.md และ knowledge-base/
    ทำให้เรียกสคริปต์จาก subfolder (เช่นขณะ cwd อยู่ใน knowledge-base) ก็ยังเจอไฟล์ถูกที่"""
    cur = Path.cwd().resolve()
    for d in [cur, *cur.parents]:
        if (d / "CLAUDE.md").is_file() and (d / "knowledge-base").is_dir():
            return d
    return cur


def state_path(kb, t):
    return kb / "_drafts" / f"loop-{t}" / "state.json"


def load(kb, t):
    p = state_path(kb, t)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            print(f"คำเตือน: อ่าน {p} ไม่ได้ เริ่มสถานะใหม่ (ไฟล์เดิมไม่ถูกลบ)", file=sys.stderr)
    return {"ticker": t, "steps": {}}


def save(kb, t, st):
    p = state_path(kb, t)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def missing(step, t, kb, paper):
    return [g for g in outputs(step, t, kb, paper) if not glob.glob(g)]


def effective(st, step, t, kb, paper):
    """done จริง = บันทึกว่าเสร็จ และไฟล์ผลลัพธ์ครบ"""
    rec = st["steps"].get(step, {})
    if rec.get("status") != "done":
        return "pending" if rec.get("status") != "running" else "running"
    return "done" if not missing(step, t, kb, paper) else "stale"


def main():
    ap = argparse.ArgumentParser(description="สถานะวงวิจัยหุ้น")
    ap.add_argument("cmd", choices=["status", "start", "done", "next", "reset"])
    ap.add_argument("ticker")
    ap.add_argument("step", nargs="?")
    ap.add_argument("--seconds", type=float, default=None)
    ap.add_argument("--kb", default=None, help="ค่าเริ่มต้น: <รากโปรเจกต์>/knowledge-base")
    ap.add_argument("--paper", default=None, help="ค่าเริ่มต้น: <รากโปรเจกต์>/paper")
    a = ap.parse_args()

    t = a.ticker.upper()
    root = find_root()
    kb = Path(a.kb) if a.kb else root / "knowledge-base"
    paper = Path(a.paper) if a.paper else root / "paper"
    st = load(kb, t)

    if a.cmd in ("start", "done", "reset") and a.step not in STEPS:
        ap.error(f"ต้องระบุขั้นหนึ่งใน {', '.join(STEPS)}")

    if a.cmd == "start":
        st["steps"][a.step] = {"status": "running", "started": time.time()}
        save(kb, t, st)
        print(f"{t} {a.step}: เริ่ม")
    elif a.cmd == "done":
        rec = st["steps"].get(a.step, {})
        rec["status"] = "done"
        rec["finished"] = time.time()
        if a.seconds is not None:
            rec["seconds"] = a.seconds
        elif "started" in rec:
            rec["seconds"] = round(rec["finished"] - rec["started"], 1)
        st["steps"][a.step] = rec
        save(kb, t, st)
        miss = missing(a.step, t, kb, paper)
        if miss:
            print(f"คำเตือน: {a.step} บันทึกว่าเสร็จ แต่ยังไม่พบไฟล์ผลลัพธ์: {', '.join(miss)}")
            sys.exit(3)
        print(f"{t} {a.step}: เสร็จ ({rec.get('seconds', '?')} วินาที)")
    elif a.cmd == "reset":
        for s in STEPS[STEPS.index(a.step):]:
            st["steps"].pop(s, None)
        save(kb, t, st)
        print(f"{t}: ล้างสถานะตั้งแต่ {a.step} (ไฟล์ไม่ถูกลบ)")
    elif a.cmd == "status":
        for s in STEPS:
            e = effective(st, s, t, kb, paper)
            sec = st["steps"].get(s, {}).get("seconds")
            extra = f"  {sec} วินาที" if sec else ""
            if e == "stale":
                extra += "  ⚠️ บันทึกว่าเสร็จแต่ไฟล์ผลลัพธ์หาย — ต้องทำใหม่"
            print(f"{s}: {e}{extra}")
    elif a.cmd == "next":
        for s in STEPS:
            if effective(st, s, t, kb, paper) != "done":
                print(s)
                return
        print("ALL_DONE")


if __name__ == "__main__":
    main()
