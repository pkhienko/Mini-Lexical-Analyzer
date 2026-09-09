# แนวทางการออกแบบและเนื้อหาสำหรับรายงาน

เอกสารนี้เป็นคำอธิบาย implementation สำหรับนำไปเรียบเรียงรายงาน สมาชิกควรเติมรายชื่อ ภาพผลการรันจริง และคำอธิบายด้วยความเข้าใจของตนเอง

## วัตถุประสงค์และลำดับการทำงาน

ฝึกใช้ Regular Expression และ SLY เพื่อแยกข้อความเป็น token ของภาษาจำลอง สร้าง symbol table และตรวจ lexical error

`ไฟล์ UTF-8 → SLY Lexer → token ตามลำดับ → ตรวจ symbol table → แสดงผล`

เมื่อ SLY พบอักขระหรือรูปแบบที่ผิด จะยก `LexicalError` ทันที ตัว CLI รับ exception แสดงข้อความและจบด้วย status 1 ตัว lexer จึงไม่มีขั้นตอนข้าม error แล้วประมวลผลต่อ

## Regular Expression

| ประเภท | รูปแบบ | Accepted | Rejected / ข้อจำกัด |
| --- | --- | --- | --- |
| Identifier | `[a-zA-Z][a-zA-Z0-9]*` | `A`, `id1`, `student123` | `1score`, `_score`, `student_name` |
| Integer | `[0-9]+` | `0`, `12345` | `1.2` ไม่ใช่ integer เดียว; `-10` เป็นสอง token |
| String | `"[^"\n\r]*"` | `""`, `"Hello World"` | quote ไม่ปิด, ขึ้นบรรทัดใหม่ภายใน string |
| Line comment | `//[^\n]*` | `// text` | ไม่ครอบคลุมบรรทัดถัดไป |
| Block comment | `/\*(?:[^*]|\*(?!/))*(?:\*/|\Z)` | `/**/`, comment หลายบรรทัด | EOF โดยไม่มีตัวปิดต้องยก error |
| Invalid identifier | `[0-9]+[a-zA-Z_][a-zA-Z0-9_]*` | จับรูปแบบที่ต้องปฏิเสธ เช่น `1score` | เป็น error rule ไม่ใช่ token ที่ยอมรับ |
| Operators | รูปแบบ literal ที่ escape ตามความจำเป็น | `>=`, `++`, `+`, `/` ฯลฯ | ไม่รวม `!=`, `%`, `!` |
| Symbols | `\(`, `\)`, `;` | `(`, `)`, `;` | ไม่รวม `{`, `}` |

Keywords ใช้การ remap จาก ID ของ SLY เพื่อไม่จับ keyword เป็น prefix ของ identifier เช่น `iffy` ต้องเป็น ID หนึ่งตัว ส่วน `if` เป็น KEYWORD การจับ comment อยู่ก่อน division และ operator สองตัวอักษรอยู่ก่อน operator ตัวเดียว

Block comment regex จับถึง EOF ได้เพื่อรายงาน unterminated comment; method ตรวจว่ามี `*/` จริงหลังตัวเปิด โดย `/*/` ไม่ใช่ comment ที่สมบูรณ์ กฎนี้ไม่รองรับ nested comments

## Symbol table

ใช้ `set[str]` เก็บชื่อ identifier เมื่อพบชื่อใหม่จะเพิ่มลงใน set และแสดง `new identifier: NAME` ถ้าพบชื่อเดิมจะแสดง `identifier "NAME" already in symbol table` การค้นหาและเพิ่มมีต้นทุนเฉลี่ย O(1) ต่อชื่อ และใช้หน่วยความจำตามจำนวนชื่อที่ไม่ซ้ำ

Keyword และ token ประเภทอื่นไม่ถูกเพิ่มลงในตาราง ไม่มีข้อมูลชนิดตัวแปรหรือค่า เพราะโจทย์กำหนดให้เก็บเพียง identifier ที่พบ

## ความเชื่อมโยงกับ Regular Language และ Finite Automata

Regular Expression ของแต่ละ token อธิบาย regular language และสามารถสร้าง finite automaton เพื่อยอมรับ lexeme ทั้งคำได้ SLY ทำหน้าที่แบ่ง input ตามกฎเหล่านี้

DFA ของ identifier:

| State | ตัวอักษรอังกฤษ | ตัวเลข ASCII | อื่น ๆ |
| --- | --- | --- | --- |
| q0 (เริ่มต้น) | q1 | dead | dead |
| q1 (accept) | q1 | q1 | dead |
| dead | dead | dead | dead |

DFA ของ integer:

| State | ตัวเลข ASCII | อื่น ๆ |
| --- | --- | --- |
| q0 (เริ่มต้น) | q1 | dead |
| q1 (accept) | q1 | dead |
| dead | dead | dead |

ทั้งสอง DFA ไม่ยอมรับ empty string เพราะ q0 ไม่ใช่ accepting state ตารางนี้ใช้ตัดสิน lexeme ทั้งคำ ส่วน lexer ของ source code ต้องตัด token และจัดการ delimiter เพิ่มเติม ตัวอย่าง `A+1` จึงเป็น ID, PLUS, INTEGER และ invalid-identifier rule ป้องกัน `1score` ถูกแยกผิดเจตนาโจทย์

## ประเด็นการตีความโจทย์

- เอกสารยก `1score` เป็น identifier ที่ผิดรูปแบบ จึงกำหนดให้เป็น lexical error ทั้งคำ
- ตัวอย่าง error บางจุดใช้ `identifier: A` แต่หัวข้อรูปแบบผลลัพธ์กำหนด `new identifier: A` จึงใช้รูปแบบจากหัวข้อผลลัพธ์ให้สอดคล้องกับตัวอย่างเต็ม
- เพิ่มการตรวจ block comment ไม่ปิด เนื่องจากไม่ควรตีความส่วนเปิด comment เป็น operator `/` และ `*` แยกกัน
- การตรวจ syntax และการรันภาษาจำลองอยู่นอกขอบเขต lexer ตัวอย่างที่ token ถูกต้องแต่ syntax ไม่สมบูรณ์ยังแยก token ได้
