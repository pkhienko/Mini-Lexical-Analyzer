# แนวทางการออกแบบและเนื้อหาสำหรับรายงาน

เอกสารนี้เป็นคำอธิบาย implementation สำหรับนำไปเรียบเรียงรายงาน สมาชิกควรเติมรายชื่อ ภาพผลการรันจริง และคำอธิบายด้วยความเข้าใจของตนเอง

## วัตถุประสงค์และลำดับการทำงาน

ฝึกใช้ Regular Expression และ SLY เพื่อแยกข้อความเป็น token ของภาษาจำลอง สร้าง symbol table และตรวจ lexical error

`ไฟล์ UTF-8 → SLY Lexer → token ตามลำดับ → ตรวจ symbol table → แสดงผล`

`main()` อ่านไฟล์แล้วเรียก `analyze(source)` ซึ่งสร้าง symbol table ใหม่และวนอ่าน token จาก `MiniLexer.tokenize()` ทีละตัว จากนั้น `format_token(token, symbol_table)` ตรวจชื่อซ้ำและคืนข้อความให้ `analyze()` พิมพ์ออกหน้าจอ เมื่อจบการวิเคราะห์ `analyze()` คืน symbol table เพื่อให้ตรวจสอบได้

แยกหน้าที่เป็น `MiniLexer` สำหรับ Regex, `format_token` สำหรับข้อความ output และ `analyze` สำหรับลูปการทำงาน จึงไม่ต้องใช้ class `Analyzer` หรือ `yield` ในส่วนแสดงผล แต่ SLY ยังส่ง token ให้ลูปทีละตัวตามปกติ

เมื่อ SLY พบอักขระหรือรูปแบบที่ผิด จะยก `LexicalError` ทันที ตัว CLI รับ exception แสดงข้อความและจบด้วย status 1 ตัว lexer จึงไม่มีขั้นตอนข้าม error แล้วประมวลผลต่อ

## Regular Expression

| ประเภท | รูปแบบ | Accepted | Rejected / ข้อจำกัด |
| --- | --- | --- | --- |
| Identifier | `[a-zA-Z][a-zA-Z0-9]*` | `A`, `id1`, `student123` | `1score`, `_score`, `student_name` |
| Integer | `[0-9]+` | `0`, `12345` | `1.2` ไม่ใช่ integer เดียว; `-10` เป็นสอง token |
| String | `"[^"\n\r]*"` | `""`, `"Hello World"` | quote ไม่ปิด, ขึ้นบรรทัดใหม่ภายใน string |
| Line comment | `//[^\n]*` | `// text` | ไม่ครอบคลุมบรรทัดถัดไป |
| Block comment | `/\*[\s\S]*?\*/` | `/**/`, comment หลายบรรทัด | ปิดที่ `*/` แรก |
| Unclosed comment | `/\*` | จับตัวเปิดที่กฎ block comment ปกติจับไม่ได้ | ยก error ทันที ไม่ส่งออก token |
| Invalid identifier | `[0-9]+[a-zA-Z_][a-zA-Z0-9_]*` | จับรูปแบบที่ต้องปฏิเสธ เช่น `1score` | เป็น error rule ไม่ใช่ token ที่ยอมรับ |
| Operators | รูปแบบ literal ที่ escape ตามความจำเป็น | `>=`, `++`, `+`, `/` ฯลฯ | ไม่รวม `!=`, `%`, `!` |
| Symbols | `\(`, `\)`, `;` | `(`, `)`, `;` | ไม่รวม `{`, `}` |

Keywords ตรวจชื่อเต็มใน set หลัง SLY จับ ID ด้วย Regex เพื่อไม่จับ keyword เป็น prefix ของ identifier เช่น `iffy` ต้องเป็น ID หนึ่งตัว ส่วน `if` เป็น KEYWORD การจับ comment อยู่ก่อน division และ operator สองตัวอักษรอยู่ก่อน operator ตัวเดียว

ชื่อ token ประกาศเป็น string และใช้ decorator `token_rule` ที่ประกาศไว้อย่างชัดเจนเพื่อแนบ pattern ให้ SLY อ่าน จึงไม่ต้องอาศัยชื่อ token และ `_` ที่ SLY สร้างให้ใน class namespace และตัวตรวจโค้ดไม่พบชื่อที่ยังไม่ได้ประกาศ การจับ token ยังคงทำโดย SLY และ Regex

Block comment แยกเป็นสองกฎ กฎแรกใช้ `[\s\S]` จับอักขระทุกชนิดรวมถึงขึ้นบรรทัดใหม่ และ `*?` จับจนถึงตัวปิด `*/` แรก เมื่อจับสำเร็จจะข้าม comment และนับบรรทัด หากกฎแรกจับไม่ได้ กฎ `/\*` ที่ตามมาจะรายงาน unterminated comment ก่อนถึงกฎ operator `/` และ `*` กรณี `/*/` จึงถูกปฏิเสธ กฎนี้ไม่รองรับ nested comments

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
