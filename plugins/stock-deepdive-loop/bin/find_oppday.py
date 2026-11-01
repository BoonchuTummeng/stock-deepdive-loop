#!/usr/bin/env python3
"""
find_oppday.py — หาคลิป Opportunity Day (Oppday) ของหุ้นไทยจากช่อง YouTube ทางการ "SET Thailand"

อ่านหน้าผลค้นหาสาธารณะของ YouTube (เหมือนเปิดเบราว์เซอร์ค้นเอง) แล้วกรองเฉพาะ
- ช่อง = SET Thailand
- ชื่อคลิปขึ้นต้นด้วย "<TICKER>:" และมีคำว่า Oppday
เรียงจากงวดล่าสุดไปเก่า ไม่โหลดวิดีโอ ไม่ถอดเสียง ไม่ใช้บัญชีใด ๆ — ได้แค่รายการ URL
ส่วนการนำคลิปเข้า NotebookLM ทำด้วย `nlm source add <notebook> --youtube <URL>`

⚠️ หน้า YouTube เปลี่ยนโครงได้โดยไม่แจ้ง — ถ้าหาไม่เจอ/โครงเปลี่ยน สคริปต์ออกด้วยรหัส 2
   และต้องให้ผู้ใช้เปิดหาเองที่ช่อง SET Thailand (อย่าเดา URL)

ตัวอย่าง:
    python find_oppday.py CPALL
    python find_oppday.py CPALL --limit 4 --json
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

for _s in (sys.stdout, sys.stderr):
    try:
        if (_s.encoding or "").lower().replace("-", "") != "utf8":
            _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CHANNEL = "SET Thailand"
PERIOD = re.compile(r"\b(Q[1-4]|YE|9M|6M|3M)\s*/\s*(\d{4})", re.I)
ORDER = {"Q1": 1, "3M": 1, "Q2": 2, "6M": 2, "Q3": 3, "9M": 3, "Q4": 4, "YE": 4}


def fetch(query: str) -> str:
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "th-TH,th;q=0.9,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def parse(html: str):
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    if not m:
        return None
    data = json.loads(m.group(1))
    out = []

    def walk(o):
        if isinstance(o, dict):
            v = o.get("videoRenderer")
            if v and v.get("videoId"):
                title = "".join(r.get("text", "") for r in v.get("title", {}).get("runs", []))
                chan = "".join(r.get("text", "") for r in v.get("ownerText", {}).get("runs", []))
                out.append({"id": v["videoId"], "channel": chan, "title": title,
                            "when": (v.get("publishedTimeText") or {}).get("simpleText", "")})
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    walk(data)
    return out


def main():
    ap = argparse.ArgumentParser(description="หาคลิป Oppday ของหุ้นไทยจากช่อง SET Thailand")
    ap.add_argument("ticker")
    ap.add_argument("--limit", type=int, default=2, help="จำนวนงวดล่าสุดที่ต้องการ (ค่าเริ่มต้น 2)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    t = a.ticker.upper()

    seen, rows = set(), []
    for q in (f"{t} Earnings Call OPPDAY SET Thailand", f"{t} Oppday บมจ."):
        try:
            res = parse(fetch(q))
        except Exception as e:
            print(f"ดึงหน้าค้นหาไม่ได้: {e}", file=sys.stderr)
            sys.exit(2)
        if res is None:
            print("โครงหน้า YouTube เปลี่ยน อ่านผลค้นหาไม่ได้ — ให้ผู้ใช้เปิดช่อง SET Thailand หาคลิปเอง", file=sys.stderr)
            sys.exit(2)
        for r in res:
            if r["id"] in seen:
                continue
            if CHANNEL.lower() not in r["channel"].lower():
                continue
            if not r["title"].upper().startswith(t + ":") or "oppday" not in r["title"].lower():
                continue
            pm = PERIOD.search(r["title"])
            if not pm:
                continue
            seen.add(r["id"])
            q_, y = pm.group(1).upper(), int(pm.group(2))
            r["period"] = f"{pm.group(1).upper()}/{y}"
            r["url"] = "https://www.youtube.com/watch?v=" + r["id"]
            r["_key"] = (y, ORDER.get(q_, 0))
            rows.append(r)
        if len(rows) >= a.limit:
            break

    rows.sort(key=lambda r: r["_key"], reverse=True)
    rows = rows[:a.limit]
    for r in rows:
        r.pop("_key", None)
    if not rows:
        print(f"ไม่พบคลิป Oppday ของ {t} ในช่อง {CHANNEL} — หุ้นอาจไม่ได้จัด Oppday หรือหน้าค้นหาไม่ส่งผลมา "
              "(ห้ามเดา URL ให้ผู้ใช้หาเอง)", file=sys.stderr)
        sys.exit(1)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f'{r["period"]}\t{r["url"]}\t{r["when"]}\t{r["title"]}')


if __name__ == "__main__":
    main()
