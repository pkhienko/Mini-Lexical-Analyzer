# Mini Lexical Analyzer

โปรเจกต์วิชา Programming Languages Concepts and Paradigms ตามโจทย์ TermReport1-2569 ใช้ Python และ SLY เพื่ออ่าน source code จากไฟล์ `.txt` แยก token แสดงผลตามลำดับ และเก็บ identifier ใน symbol table

## ติดตั้งและรัน (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py inputs/valid_basic.txt
```

ไฟล์ input ใช้ UTF-8 และรองรับ UTF-8 BOM โปรแกรมไม่ต้อง activate virtual environment หากเรียก Python ตามตัวอย่าง

```text
new identifier: A
operator: +
new identifier: B
operator: -
operator: *
keyword: if
keyword: then
new identifier: id1
new identifier: id2
identifier "id1" already in symbol table
string: "Hello World"
```

ทดสอบ error:

```powershell
.\.venv\Scripts\python.exe main.py inputs/invalid_lexical.txt
```

```text
new identifier: A
Lexical error: unexpected character @
```

โปรแกรมหยุดที่ `@` และไม่อ่าน `B` ต่อ รหัสจบโปรแกรมคือ 0 เมื่อสำเร็จ, 1 เมื่อมี lexical error และ 2 เมื่ออ่านไฟล์ไม่ได้หรือใช้ CLI ไม่ถูกต้อง

## ส่วนประกอบ

| ไฟล์ | หน้าที่ |
| --- | --- |
| `lexer.py` | SLY rules, LexicalError, symbol table และรูปแบบ output |
| `main.py` | รับ path ของไฟล์ อ่าน UTF-8 และจัดการการจบโปรแกรม |
| `inputs/` | ตัวอย่างถูกต้อง 3 ไฟล์และมี error 4 ไฟล์ |
| `tests/test_lexer.py` | ตรวจ token, symbol table, error และ CLI |
| `docs/design.md` | อธิบายการออกแบบและ finite automata สำหรับใช้เตรียมรายงาน |

## ทดสอบ

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ชุดทดสอบใช้ standard library `unittest` รวมการเทียบ output ของตัวอย่างในโจทย์, operator ที่อยู่ติดกัน, case-sensitive keywords, comments หลายบรรทัด, strings, จำนวนลบ, identifier ผิดรูปแบบ, การหยุดเมื่อ error, การล้าง symbol table ระหว่าง input และการรัน CLI กับไฟล์ตัวอย่างทั้งหมด

## ขอบเขตการทำงาน

- Keywords ได้แก่ `if then else endif while do endwhile print newline read` ต้องเป็นตัวพิมพ์เล็ก โดย `If` และ `READ` เป็น identifier
- Identifier ใช้ตัวอักษรอังกฤษขึ้นต้น ตามด้วยตัวอักษรอังกฤษหรือตัวเลข และแยกตัวพิมพ์เล็ก/ใหญ่
- `1score` ถูกปฏิเสธเป็น invalid identifier ตามตัวอย่างในโจทย์ ส่วน `student_name` จะรายงาน error ที่ `_` หลังแสดง token `student`
- Integer เป็นเลข ASCII ไม่ติดลบ; `-10` แยกเป็น operator `-` และ integer `10` ส่วน `1.2` ผิดที่ `.`
- String อยู่ใน double quotes บรรทัดเดียว เก็บเครื่องหมาย quote ไว้ใน output รองรับข้อความภาษาไทยภายใน string และ string ว่าง
- ไม่มีการแปล escape sequence: backslash ภายใน string เป็นอักขระธรรมดา ไม่ทำให้ quote ถัดไปกลายเป็น escaped quote ตามกฎ regex ที่โจทย์แนะนำ
- Comments รองรับ `//` และ `/* ... */`; block comment ปิดที่ `*/` แรก ไม่รองรับ nested comments และตรวจ error เมื่อยังไม่ปิดก่อนจบไฟล์
- Whitespace ถูกข้าม ส่วนคำ `newline` เป็น keyword แยกจากอักขระขึ้นบรรทัดใหม่
- Symbol table ใช้ `set` เก็บเฉพาะ identifier และเริ่มใหม่สำหรับแต่ละ input
- งานนี้ตรวจ lexical structure เท่านั้น จึงไม่ตรวจวงเล็บสมดุล ลำดับไวยากรณ์ ตัวแปรประกาศหรือยัง หรือคำนวณค่าโปรแกรม

## งานสำหรับการส่ง

มี source code, inputs และเอกสารการออกแบบเริ่มต้นแล้ว ยังต้องจัดทำรายงานฉบับส่งพร้อมชื่อสมาชิก ภาพผลการรัน และวิดีโอที่สมาชิกทุกคนมีส่วนร่วมตามโจทย์ จากนั้นผู้จัดทำส่งลิงก์ Google Drive และ YouTube Unlisted ตามที่อาจารย์กำหนด

อ้างอิง: เอกสารโจทย์ `TermReport1-2569.pdf`; เอกสาร SLY https://sly.readthedocs.io/en/latest/sly.html
