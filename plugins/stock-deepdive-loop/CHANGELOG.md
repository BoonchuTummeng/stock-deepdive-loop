# Changelog

## 0.1.0 — ร่างแรก (ยังไม่เผยแพร่)
- วงวิจัย L0–L8: อ่านคลังเดิม → การ์ดไอเดีย → เก็บเอกสาร → คำถาม 4 ชั้น → FACTS+SPINE → เขียนเป็นคลื่น → ด่านตรวจ 4–6 ด่านขนาน → เย็บ HTML → เข้าคลัง
- 4 คำสั่ง: `loop` · `questions` · `gate` · `vault`
- 11 agents: idea · collector · factcheck · writer · vault + ด่านตรวจ critic · checker · redteam · omission (ตกหล่น) · contrarian (แย้ง) · premortem (ชันสูตร)
- ด่านตรวจ: ทุกโหมด 4 ด่าน (critic · checker · redteam · omission) · โหมดเต็มเพิ่ม contrarian + premortem
- แจ้งผู้ใช้ให้ `nlm login` เมื่อเรียก NotebookLM ไม่ได้ (ไม่ข้ามเงียบ ๆ)
- เทปประชุมนักลงทุน (Oppday) หุ้นไทย ดึงอัตโนมัติ: `bin/find_oppday.py` (หาคลิปจากช่อง SET Thailand) → `bin/oppday_subs.py` (ดึงคำบรรยายอัตโนมัติผ่าน yt-dlp เป็น .txt มีเวลากำกับ + หัวเตือน ASR) → อัปเข้า notebook · ทางสำรอง `nlm source add --youtube` / คัดลอกมือ
- ดึงอัตโนมัติไม่ได้ → แจ้งผู้ใช้ให้ไปเอามาลง `raw\` (Obsidian Web Clipper/โหลดเอง) แล้วพิมพ์ "ต่อ" — collector คัดแยกเข้าโฟลเดอร์หุ้นเอง (ย้าย ไม่ก๊อป · กำกวมถาม)
- `bin/check_quotes.py`: ตรวจ Quote ของ atom กับเอกสารต้นฉบับแบบกำหนดแน่นอน (ไม่ใช้ AI) หลัง L8 ทุกครั้ง — ปิดช่องที่ atom ไม่ผ่านด่านใด
- แก้ `extract.py`: `--no-overwrite` (ไม่ทับ .txt เดิมในคลัง) · `--manifest-dir` (ไม่วาง MANIFEST.md ในชั้นบนของคลัง) · ข้ามโฟลเดอร์ขึ้นต้น `_` — พบจากการทดสอบเคส E ว่าเวอร์ชันเดิมเขียนทับ .txt 17 ไฟล์และวาง MANIFEST.md ลงคลังตอนรันเคส A
- ไลบรารีภายนอกตัวเดียว (ไม่บังคับ): yt-dlp สำหรับขั้นเทป Oppday
- bin: ก๊อปจาก stock-deepdive-lite 1.0.0 (fetch_th · fetch_us · extract · build_paper · check_numbers) + `loop_state.py` (สถานะวง ทำต่อจากที่ค้าง)
- รองรับ Claude Code และ Codex ด้วยเนื้อชุดเดียว (`AGENTS.md` + `ROOT.md`)
