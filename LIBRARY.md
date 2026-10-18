# Libraries of the ITM autocode translator (2148)

The translator keeps two unrelated libraries on external volumes:

- a **text library** of autocode program texts on the "постановочная"
  tape 30 (МЛ30), optionally read from tape 31 (МЛ31), driven by key `Л`
  and by `Б;` sections;
- a **module library** of translated programs on volume 067, driven by
  key `Р`.

Evidence marks as in [README.md](README.md): **[трасса]** — seen in an
instruction trace, **[опыт]** — seen in a test job's output or on the
volume afterwards, **[код]** — read from the code only. Addresses are
octal; `0NNN` cells are in the resident (`aitm0`), 06NNN in `aitm6`.

## Volumes and passport

dispak mounts every `ЛЕНТ NN(vol)` **read-only** unless the volume
number is followed by `-ЗП` (`vsinput.c`). The translator needs:

| Unit | Passport | Used for |
|---|---|---|
| 030 | `ЛЕНТ 30(vol-ЗП)` | text library: catalogue in zone 0, texts from zone 1 |
| 031 | `ЛЕНТ 31(vol)` | second text library, read only (`Л…Л`) |
| 067 | `ЛЕНТ 67(vol-ЗП)` | module library: catalogue in zone 0, modules from zone 1 |
| drum 020 | — | zone 017 caches the МЛ30 catalogue (`БАРАБ`) |

Without `-ЗП` the first write gives «ОШИБКА МД ЭВМ» (the `tape` job,
Э70 at 01773); with no volume at all — «ОШ.В ИНФ.СЛ.ЭКСТ» (the `keys`
job at 06014, the `bib` job) [опыт].

The Э70 information words [код, decoded with dispak `ddio`]:

| Word | Exchange |
|---|---|
| 01050 | read МЛ30 zone 0 → 010000 (catalogue) |
| 01051 | write МЛ30 zone 0 from 010000 |
| 01052 | template: read МЛ30 text zones (zone added in `ЧТМЛ`) |
| 01053 | read МЛ31 zone 0 → 010000 |
| 01055 | write МЛ31 zone 0 |
| 01056 | template: read МЛ31 text zones |
| 01057 | read drum 020 zone 017 → 010000 |
| 01060 | write drum 020 zone 017 from 010000 |
| 05747 | read 067 zone 0 → 026000 (module catalogue) |
| 05750 | write 067 zone 0 from 026000 |
| 05751 | template: write 067 module zones from 014000 (zone from 05741) |

`БАРАБ` reads through 01050; the first time it also copies the
catalogue to the drum (01060) and redirects 01050 to the drum (01057),
so the tape catalogue is read once per job [трасса]. A write of the
catalogue (`БИБЛ`, `ЗПМЛ`) goes through 01051 or 01055 to the tape.

## Text library (МЛ30/МЛ31)

### Key Л

The 1969 manual describes `Л XY,`: X — tape work, Y — punch the edited
text on cards, Y operators per card ("Л 35," — read from tape, apply
corrections, write back, punch 5 per card). In 2148 `КЛЛ` (f1a 05216)
parses a richer form into `РЕЖМЛ` (06600) and `ИМЯМЛ` (06601) [код]:

```
Л XY [options] ,          by number
Л name mode [options] ,   by name; mode is ЗАПИСЬ, ЧТЕНИЕ or ИЗМЕН.
                          (only the first letter is compared)
```

Spaces are skipped, so the name and the mode must be separated by a
non-letter: `ЛПЕЧ.ЗАПИСЬ,` (also `-`, `/`, `(`, `:`) writes entry ПЕЧ,
while `ЛПЕЧ ЗАПИСЬ,` is one name (its last letters end up in `ИМЯМЛ`)
and `Л ПЕЧ…` gives «ОШИБКА В ИМЕНИ» [опыт, jobs `sb1`, `sb2`].

`РЕЖМЛ` layout:

| Bits | Meaning | Set by |
|---|---|---|
| & 7 (0363) | Y: punch the edited text (`МЛКОП`, Э71 card images; only with key `П`, job `punch`) | digit Y, option `П n` |
| & 010 (0272) | write the text to МЛ30 | X = 1, 3; ЗАПИСЬ, ИЗМЕН. |
| & 020 (0276) | read the text from the library | X = 2, 3; ЧТЕНИЕ, ИЗМЕН. |
| & 040 (0305) | text already read / do not load it | option `Б`; set after `ЧТМЛ` |
| >> 6 | catalogue entry number when there is no name | option `З n` |
| >> 24 | a selector letter (see below) | any other option letter |

Option letters after the number or mode [код]: `Т` clears the selector;
`Б` sets 040; `П n` ORs n & 7; `З n` sets the entry number; any other
letter becomes the selector:

- `Л` — read from МЛ31 instead of МЛ30 (`КАТМЛ`); with the write bit
  the text is also written to МЛ31 at once (`ЗПМЛ`);
- `Р` — write to МЛ30 at the end of phase 1, before macro processing
  (`КОНФ1` calls `БИБЛ` with М13 = 0215);
- `М` — write after macro expansion (`БИБЛ` with М13 = 0207);
- none — write at the start of phase 2 (`БИБЛ2`, f2a, М13 = 0);
  this is what `Л10,` does [опыт].

`БИБЛ` writes only when the selector equals its М13, so the selector
picks *which* version of the text goes to the tape: as punched,
after corrections, or after macros.

### Catalogue (zone 0, read into 010000)

| Words | Contents |
|---|---|
| 020 + i | name of entry i (0 — no name) |
| 0716 | 010000 + index of the last entry; 0 — empty catalogue |
| 0717 | start zone when the catalogue is empty |
| 0720 + i | entry i: start zone in the low 12 bits, length/end packed above |

`ИЩКАТ` (aitm0) scans names 020… (`16(М6)` is decimal) up to the index
in 0716 for `ИМЯМЛ` [код]; after `sb2` the catalogue holds СЛОВА at
020 and ПЕЧ at 021, 0716 = 010001, 0720 = 1, 0721 = 0001000000000002
[опыт]. A test with a zeroed zone 0 gave, after `Л10,` without a name:
0716 = 010000, 0720 = 1, text in zone 1; message «А-П. ЗАПИСЬ МЛ30
000 …001» [опыт]. A never-written zone 0 reads as the 2525… fill
pattern, so on a fresh volume the "catalogue" is garbage (entry 0526
in the same test without zeroing) — a real tape must have been
initialised by some other means; the translator has no key for it
[опыт, код].

The 1969 manual describes a simpler tape: zone 0 holds service
information, its word 0720 is the number of text zones, and a tape
holds one program. In 2148 this became the catalogue above, with
names at 020 + i and descriptors at 0720 + i.

### Stored text

Zones from the start zone hold the program text exactly as the editor
keeps it: ITM code, 6 characters per word, with its terminator. The
`Л10,` test stored

```
В;Н;100,К;НАЧ:Э064ИС=,=Э074,ИС:ЗЧА=ЗЧБ,4Э070=10ЗЧ,А;А:ПРИВЕТ,Б: ВСЕМУ,Н;НАЧ,Е;!,Е;!_
```

in 14 words of zone 1 [опыт].

### Write path (`БИБЛ`, aitm0 01706/01710)

1. Return unless the write bit is set and the selector matches М13;
   from phase 1, also return if `D06666` (error in text) is set.
2. Catalogue via `БАРАБ`; message words `МЛ30`, `ЗАПИСЬ` or (when the
   read bit is also set) `ИЗМЕН.`.
3. By name: `ИЩКАТ`. Found with ИЗМЕН. — rewrite in place if the new
   text fits, else the old name is cleared and a new entry is appended.
   Not found — append after the last entry (0716 += 1; start zone =
   end of the previous entry).
4. `ВЫГР` writes the text pages with Э70 by 0631, zone by zone, and
   the catalogue goes back through 01051.
5. `ПЕЧМЛ2` prints « А-П. ЗАПИСЬ МЛ30 name NNN zone-word».

Steps 3–4 are [код] except the appends of entries 0 and 1 (`sb1`,
`sb2`) [опыт]. `Л10,` on a text with error 06 (undefined name) wrote
nothing, so the error check is not limited to phase 1 [опыт].

### Read path (`КАТМЛ`/`ЧТМЛ`, f1a)

Called from the key parser (`КЛЛ`) and at the end of keys (`КЛКОН`).
If the read bit is set: read the МЛ31 catalogue (selector `Л`) or the
МЛ30 one (`БАРАБ`); find `ИМЯМЛ` with `ИЩКАТ`, or take entry `РЕЖМЛ >> 6`
and its name; print « А-П. ЧТЕНИЕ МЛ30 name …»; unless 040 is set,
read the zones by Э70 into the editor's pages and set 040. A missing
name prints « А-П. ОШИБКА» via `ПЕЧМЛ` [код].

Not confirmed: `Л20,` on the tape written above ended with ОШИБКА 22,
and `Л20,В;Е;` looped at address 010 before reaching any library code
[опыт]. The intended deck shape for reading (what follows `Л20,` when
the text comes from tape) is still unknown.

### Key `Ф` — blocks to МЛ31 (f1a `КЛФ`, `ФСПИС`)

`Фn1,ИМЯ1,n2,ИМЯ2,…!` saves blocks of the program text to the МЛ31
library (tape 31), each under its name [код, опыт, job `flist`]:

- `КЛФ` (05027) stores the pairs at 012600 (the number doubled, then
  the name) up to `!`; `ПРФ` holds the end of the list.
- At the end of phase 1 `КОНФ1` calls `ФСПИС` (05700). It records the
  position of every `В;` in the text at 012400 (2 words each; block n
  is the n-th `В;`) and puts each name from the key into the entry of
  its number.
- For every named entry (05725) the text from that `В;` to the paired
  `Е;` (nesting counted by `ПЛЮС7`/`МИН7`) is copied with a closing `!`;
  `РЕЖМЛ` := 010 (write), `ИМЯМЛ` := the name, and `ЗПМЛ` (05663)
  writes it through the МЛ31 words (01053, 01055). `РЕЖМЛ`/`ИМЯМЛ` of
  the `Л` key are restored afterwards.

`flist` (`Ф1,БЛОК!`, `ЛЕНТ 31(2222-ЗП)`, zeroed volume) printed
« А-П. ЗАПИСЬ МЛ31 БЛОК 000 0000000000000001»; the catalogue has БЛОК
at 020 (0716 = 010000, 0720 = 1) and zone 1 holds
`В;Н;100,К;НАЧ:Э064ИС=,=Э074,…,Н;НАЧ,Е;!`. With only tape 30 ordered the
write stops at Э70 01053 with «ОШ.В ИНФ.СЛ.ЭКСТ»; with a block number
that does not exist (`keys`: `Ф12,ПЕЧ!`) nothing is written [опыт].

МЛ30 and МЛ31 are only the unit numbers the job assigns: the writing
job orders the volume as `ЛЕНТ 31(vol-ЗП)`, the job that assembles from
it orders the same volume as `ЛЕНТ 30(vol)`. `fsb` (`В;Б;БЛОК,Е;` on the
`flist` volume, read-only) prints « А-П. СБОРКА МЛ30 БЛОК» and
«ПРИВЕТ ВСЕМУ» [опыт].

### `Б;` sections — assembly from the library (f1a `РАЗДБ`)

`Б;ИМЯ,ИМЯ2,…` names texts to be taken from the МЛ30 library
("СБОРКА") and inserted in place of the section. No key is needed; the
section only lists names [опыт, jobs `sb2`–`sb5`].

- At the start of phase 1 (`РАЗДВ1` → `НАЧ12`) `РАЗДБ` scans the whole
  text up to `!` and records every name with its text position in the
  table at 012000 (pairs name, position) [код].
- If there are any: message words switch to « СБОРКА МЛ30 »,
  `ИМЯМЛ`/`РЕЖМЛ` are saved in 04007/0636 and restored at the end, and
  the catalogue is read (`БАРАБ`). For each catalogue entry `ИЩ12`
  looks for its name in the table; when found, `ЧТМЛ` reads the text
  and « А-П. СБОРКА МЛ30 name NNN zone-word» is printed. After every
  insertion the catalogue is scanned again from the start [код,
  опыт].
- The inserted text loses its own outer `В;`…`Е;`, so its labels
  belong to the enclosing block: `sb2` wrote ПЕЧ as
  `В;Н;200,К;ИС:ЗЧ210=ЗЧ211,4Э070=10ЗЧ,Н;210,А;Т1:ПРИВЕТ,Т2: ВСЕМУ,Е;!`
  — the text of СЛОВА spliced in, and stored with the splice. So a
  library text written with `Б;` sections already contains its parts
  [опыт].
- A name listed twice (`sb4`, `Б;ПЕЧ,ПЕЧ,`) is reported once but its
  text is inserted twice, so its labels are defined twice (error 25).
  Inserted names are kept from 012201 on, with their descriptors from
  012301 (pointer in 012200, `16(М3)` and `'120'(М3)` off it) [опыт,
  код].
- A name not in the catalogue (`sb5`), or any `Б;` with an empty
  catalogue (0716 = 0), prints «ОШИБКА А-П.», the section is dropped,
  and the job ends with error 00 [опыт].

The `bib` job (no tape) ends with «ОШ.В ИНФ.СЛ.ЭКСТ»; on a never-written
tape (2525… catalogue) `Б;` does not finish within 60 s [опыт].
Unreached: 05604–05606, the step to the next page when an inserted
text spans more than one page — a 60-line text still fits, and a
120-line text breaks the write itself (errors 02, 11 until killed).

### Errors and messages

- «ОШИБКА В ИМЕНИ» (`ОШИМЯ`, 06670) — from `ОШИБ` when a read mode is
  set; the job continues at 0340. With a malformed `Ф` key it repeats
  forever [опыт].
- Message texts at `ТМЛ` (06650): « МЛ31 », « МЛ30 », «ЗАПИСЬ»,
  «ЧТЕНИЕ», «ИЗМЕН.», «СБОРКА», «ОШИБКА», « А-П. ».

## Module library (volume 067)

Tests `lib1`…`lib6` (below) build a library on one volume, job after
job; `tools/vol.py` decodes the volume (`traces/libN.lib`). Everything
in this section not marked otherwise is [опыт] from these tests.

### Key Р

`КЛР` (f1a 05052) sets 06502 := `С70000` (non-zero), which makes `ФИНАЛ` call `ВЫВМ`
instead of starting the program. Then it reads option letters:

| Letter | Cell | Meaning |
|---|---|---|
| `W` | 06476 := 0 | print the module in octal (Э64 05734) |
| `А` | 06474 := 0 | store the module in the library (`КАТ26`); without it `ВЫВМ` goes straight to `ЗАВЕР` |
| `Н` | 06504 := 0 | new catalogue: do not read the old one |
| `Г` | 06503 := 0 | append an export table to the module |
| `К` | 06505 := 0 | print the catalogue after storing |

After the letters: `!` ends the key, `,` starts a list, `(` goes
straight into the list. List items are a name or a number followed by
a delimiter [трасса for `!`, `+`, `(`; код for the rest]:

| Delimiter | Effect |
|---|---|
| `!` | the name becomes the module name (06501); end |
| `+` | the name is appended to the list at 010005 + 06470 (06470 counts) |
| `(` | the name becomes the module name (06501), and `КОНЗАД` := 0. A second `(` overwrites 06501, and that name is not listed: `ГЛАВ(ПЕРВ+ВТОР(ТРЕТ+ЧЕТВ))` gives main `ВТОР`, list `ПЕРВ ТРЕТ ЧЕТВ 0 0`, no error [трасса] |
| `)` | the name goes to the list, and the next slot is set to 0, which ends the list [трасса] |
| `:` | the name goes to 010003 |
| `-` | the name goes to 010004 |
| `,` | the name goes to 010000 |
| `/` | a control word `0020000000000000` goes to the list, then the name: `ВТОР/ТРЕТ` gives `0020000000000000 ВТОР ТРЕТ` [трасса] |
| `.` | only after the letter `А` or `Л`, which is not a module name: the control word `0020000000000001` (`А.`) or `0020000000000004` (`Л.`) goes to the list; any other name is error 23 [трасса for `А.`, `Л.`; код for the error] |
| other | error 23 |

The key `РК,ГЛАВ(ПЕРВ+ВТОР/ТРЕТ+А.ЧЕТВ+Л.ПЯТ)!` gives the list
`ПЕРВ 0020000000000000 ВТОР ТРЕТ 0020000000000001 ЧЕТВ 0020000000000004
ПЯТ 0` at 010005–010015 [трасса, f1a 05122/05136/05142]. The control
words are the only way to give the loader structure inside the list,
since the parentheses do not nest; they look like overlay marks (see
"Linking loader: expected behaviour"). `А` stands for абзац (one sector,
0400 words) and `Л` for лист (02000 words, four абзацы), so the low part
of the control word is the boundary in абзацы: 1 for `А.`, 4 for `Л.`,
and 0 for `/`. The translator itself is overlaid on абзац boundaries:
ФАЗ1Б/ФАЗ2Б share 06000–06377, ФАЗ2В (05000–05777) overlays the upper
half of ФАЗ2А, and the phases are read by the sector exchanges at aitm6
06760–06763. `tools/itmload.py` reads the words as overlay segments
([AITM-object.md](AITM-object.md), section 7).

Numbers go to 010001/010002 (an address range; defaults 010 and 070000)
[код]. The working forms are `РАК,ИМЯ!` (store) and
`РАК,ГЛАВ(ПЕРВ+ВТОР)!` (store, then link and run, see below); `|` and
`ГЛАВ!(…)` give errors 23 and 22.

### Catalogue (zone 0)

Pairs of words (name, descriptor). The name is ITM text right-justified
(`00ПЕРВ`); a zero name ends the list, and its second word is the first
free zone; name −1 (all ones) marks a freed entry. The descriptor is
written by `КОНВЫВ`:

| Bits | Contents |
|---|---|
| 48 | flag (05743), always 1 |
| 33–47 | image length in words (05737) |
| 21–32 | 05740 = 05455: size of the `Р` area (section `Э;`, below); 014 for `Р=10`, `Р=4` in `ext1` [опыт] |
| 1–10 | first zone (05741) |

For example `4000300000000001` is a 6-word module in zone 1, and
`4105400000000003` a 02130-word module from zone 3. The
key `К` printout shows (name, length << 12 | 05740), e.g. `000 00ПЕРВ
00000060000`. A store without a name (`РАНГКW!`, `keys` with 067
mounted) makes an entry with name 0, which reads as the end of the
list, so a name is required.

### Module layout

The format, and how entry and external names are recorded, is described
in detail in [AITM-object.md](AITM-object.md).

`ВЫВМ` builds the module at 014000 and `КОНВЫВ` writes it to
consecutive zones starting from the first zone (05736 zones):

| Words | Contents |
|---|---|
| 0 | image length (05737) << 33 \| literal count (05453) << 22 \| reference-record count (05452) << 10 |
| 1 | export-table length (0173) << 36 |
| 2 … | image of addresses 010 up to the location counter (from virtual 060010) |
| then | relocation scale: ⌈length/8⌉ words from 01000 |
| then | literals (023000): one word per external name, the name as ITM text right-justified [опыт] |
| then | reference records (virtual 010000), one word each [опыт] |
| then | export table (key `Г`): pairs (name, kind << 45 \| address) [опыт] |

The scale has one 3-bit field per half-word: field `3·(2·i + h)` from
bit 48 for word 010 + i, half h (0 = left). Value 1 marks an address
relative to the module (it must be relocated); 0 — absolute.

`ОТМЕТ` (f2a 05577) builds the scale during translation in virtual
memory from 01000, through `ЧТВ1`/`ЗПВ1`. It is called for command
halves (`СБКОМ`) and constant words (`КОНСТ`), and it does nothing
unless key `Р` is on (06502 ≠ 0), the address kind 05451 is non-zero,
and 0166 = 0. For address 05572 and half 05573 it computes
k = 2·(05572 − 010) + 05573, takes scale word 01000 + k/16 and puts the
kind into the field at 3·(k mod 16) by XOR. If the field is already set,
`ПРМОД` first checks that the two kinds are compatible (error 0611
otherwise). The field holds the kind itself, not a flag:

| Kind | Source | Meaning |
|---|---|---|
| 0 | — | absolute |
| 1 | `'142'` | address in the program, relocate (`СЧИС`) |
| 2 | `ЭКСТР` 05377 | offset in the `Р` area (`СЧР2`) |
| 3 | `МОДИФ` | minus an address in the program (`СЧ-ИС` gives 07766) |
| 4 | `МОДИФ` | minus an offset in the `Р` area (`СЧ-Р2` gives 07770) |
| 5 | 05567, `ЛИТПУЛ` | the address field is a literal number: the external name itself (`СЧВН`) |
| 6 | 01547, `ЛИТПУЛ` | the address field is a reference-record number: external name + offset (`СЧВН(5)`) |

All kinds are [опыт] (`ext1`). `МОДИФ` turns kinds 1 and 2 into 3 and
4 for a negative term, and `ПРМОД` adds the kinds of the terms of an
expression: `Т1-ИС` is 0 (absolute), `Т1+ИС` stays 1, `Р2-Т1` is error
61 [опыт]. `ВЫВМ` copies ⌈length/8⌉ scale words after the image. For
`К;Н2:СЧА=ЗЧБ,ПБН2=,Ч;А:1,Б:2,` the scale word is `1110000000000000`:
both halves of `СЧА=ЗЧБ` and `ПБН2` are relative.

With `Г`, the table is the outermost scope: every label of the outer
block, including `Э;` names, and every global label (`*ИМЯ:`) of a
nested block. `ПРОХ2` (f2a 04341) enters the `*` names into the outer
table before the pass, so they come first. A plain label of a nested
block is not exported (`В;С;ЕДИН:…,В;С;ВНУТР:1,Е;С;ДВА:2,Е;` exports
`ЕДИН` and `ДВА`; with `*ВНУТР:` also `ВНУТР`). The same `*` makes the
label visible in the outer block: `СЧВНУТР` there is error 06 without
it. `В;*ВНУТР,` gives errors 20 and 55. An outer-block label cannot be
kept private. Without `Г` the table is empty [опыт].

The export table for `ПЕРВ` in `lib1` is `НАЧ 1000000000000010`,
`ИС …012`, `А …014`, `Б …015`. It is not counted in the descriptor
length.

The module covers 010 up to the *final* location counter, wherever the
program was placed [опыт, ПРИВЕТ ВСЕМУ with `Н;` before the code]:

| Placement | Image | Zones |
|---|---|---|
| none (010) | 010–015, 6 words | 1 |
| `Н;20,` | 010–025, 016 | 1 |
| `Н;100,` | 010–0105, 076 | 1 |
| `Н;1000,` | 010–01005, 0776 | 1 |
| `Н;2000,` | 010–02005, 01776 | 2 |
| `Н;100,` code `Н;100,` | 010–077, 070 — the code is lost | 1 |
| `Н;100,` code `Н;20,` data | 010–021, 012 — the code is lost | 1 |
| `Н;5,` | errors 61, «ОШИБКА В ИМЕНИ», 53; nothing stored | — |
| `Н;1000,К;НАЧ:…,Н;100,К;ИС:…,А;…,Н;1000,` (or `Н;НАЧ,`) | 010–0777, 0770 — `НАЧ` at 01000–01001 is lost | 1 |

The last case is a correct program by the manual: a final `Н;` after
which no words are generated sets the start address (section 3.3),
and a normal run prints «ПРИВЕТ ВСЕМУ». But `ВЫВМ` takes the image
length from the location counter (05737 := M7 − 8), and `РАЗДН` sets M7
to the operand of every `Н;`, including the final one. No high-water
mark is kept, and the start address is not recorded in the module.
After `Н;` the section word must be repeated (`Н;100,К;…`, as in the
manual's example); otherwise `ИС:ЗЧА=ЗЧБ,` is read as an `Н;`
definition (`ИС` := address `ЗЧА`), giving errors 06 and 52.

Addresses below the program are not cleared. Word 010 is 0, and the
rest is a snapshot of the translator's own memory at the same
addresses: the resident (zone 0406) with about 66 cells in their
run-time state (0151–0204, 0611–…), and zone 0407 above 02000. These
words have scale code 0 (absolute). Exports and relocatable addresses
hold absolute addresses (`НАЧ` = 0100 for `Н;100,`), so a loader would
add the difference between the load address and 010. A library program
should therefore start at 010 and must not reset the counter at the end
(`Н;НАЧ,`).

### Section `Э;`: external names and the `Р` area

Literals and reference records come from section `Э;`. A label there
goes to `ЭКСТР` (f2a 05344), which looks at what follows the `:`
[опыт, `ext1`, `ext2`]:

| Item | Effect |
|---|---|
| `ВК:ИС+1,` or `ВК:П=ИС,` | equivalence: `ВК` := the address, with its kind. The address must be defined above, else error 07 |
| `ВН:Н=ВНЕШ,` | external name: the literal `ВНЕШ` is appended to 023000 (no check for duplicates), `ВН` gets kind 5 and the literal number. `Н=5` is error 61 |
| `Р1:Р=10,` | `Р1` := the current offset in the `Р` area (05455), kind 2; the area grows by 10 (octal) |
| `Р1:Р=2000=10,` | the same; the first number sets the start of the area, but only without key `Р` |

Without key `Р` the section is accepted and the program runs (`ext2`).
A use of an external name may come before its `Э;` item.

Under key `Р` an external name is used in two ways:

- `СЧВН`: kind 5, the address field holds the literal number;
- `СЧВН(5)`: `ЛИТПУЛ` writes a reference record `literal << 30 |
  offset` and the address field holds the record's number, kind 6. The
  parentheses hold a constant: `(5)` is 5, `(Л)` is 0311 (the letter's
  code), `(ИС)` is the text of `ИС`, not the label. Each use makes a new
  record, even an identical one.

`ВН+1`, `Р1+1` and `ВН-1` give error 13, because `АДР2` (f2a 05034)
rejects `+`/`-` after a name whose address (06700) is 0. `Р2+1` is
accepted (`Р2` = 010). In `СЧ1+ВН` the 1 is lost: the resident sets the
address of a kind-5 name to 0 (05343).

`ЗПКОМ` (from `ЛОГСЛ`, f2b) writes a reference record for each field of
an `Л;` word whose address kind is not 0: `kind << 45 | field
descriptor (07272) | value << 15 | word address`. In `ext1`,
`Л1:ДВН(5)/30=КТ1/0` at 021 gives:

- `6723000000100021`: field `Д` at `/30` (bits 42–45 width − 1 = 016,
  bits 36–41 top bit 046), kind 6, reference record 1;
- `1545400001400021`: field `К` at `/0` (013, 013), kind 1, `Т1` = 014.

The field descriptor is decoded in [AITM-object.md](AITM-object.md),
section 4.4.

The word itself holds the absolute values (`0000000100000014`), and its
scale is 0. Labels (kind 1), `Р` names (kind 2) and external names
(kind 5) all produce records. Without an `Л;` word or an external
name, no literals or records are written.

Exports of `Э;` names keep their kind: `ВН 5000000000000000`, `Р2
2000000000000010`.

A minus before an external name (`СЧ-ВН`) sets flag 04000 in the
literal number (05513–05514, when 05457 ≠ 0) [опыт, `ext3`]. Not
reached: the literal-table overflow (f2a 05507, error 61).

### Store path (`КАТ26` → `КОНВЫВ`)

`КАТ26` reads the catalogue (05747) into 026000 unless `Н`. An empty
first entry gets free zone 1. Then it makes two passes:

1. Pass M3 = 0 looks for the module's name. An entry fits if its zone +
   the module's zone count does not exceed the next entry's zone (or the
   free zone). If it fits, the module overwrites it in place. Otherwise
   the name becomes −1 and the search goes on.
2. Pass M3 = 1 (`КОНВЫВ` 06000) looks for a freed (−1) entry that fits
   by the same rule and reuses it.
3. If neither pass finds a place, the module is appended at the free
   zone (06001), and the end mark moves past it.

`КОНВЫВ` fills in the name and descriptor, writes the catalogue (05750),
prints it with `К` (Э64 06033) and writes the module zones (05741/05751
in a loop). Then it jumps to `ЗАВЕР` (aitm6 06517).

| Test | Key | Catalogue after (name: zone, length) |
|---|---|---|
| `lib1` | `РАНГКW,ПЕРВ!` | ПЕРВ: 1, 6 (+ export table); free 2 |
| `lib2` | `РАК,ВТОР!` | + ВТОР: 2, 4; free 3 — append |
| `lib3` | `РАК,ВТОР!`, 02130 words | (−1): 2, 4; ВТОР: 3, 02130; free 5 — old entry freed, appended in 2 zones |
| `lib4` | `РАК,ТРЕТ!` | ТРЕТ: 2, 4 — the freed entry is reused |
| `lib5` | `РАК,ПЕРВ!`, 4 words | ПЕРВ: 1, 4 — rewritten in place |
| `lib6` | `РАК,ГЛАВ(ПЕРВ+ВТОР)!` | + ГЛАВ: 5, 6; then «ЗАПРЕЩ.КОМАНДА» |

### Linking (`ЗАВЕР`)

If `КОНЗАД` ≠ 0 (no `(` in the key), `ЗАВЕР` ends the job (Э74).
Otherwise it sets M13 := 06470 (the length of the `+` list at 010005),
reads drum 21 zone 014 (= 2148 zone 0414) to address 0 (Э70 06764) and
jumps to 011. On 2148, sectors 0414.0–2 are zeros, so `lib6` runs
through zeros into the `z14` data and stops at 01507 (`06 002 3002`,
«ЗАПРЕЩ.КОМАНДА») [трасса lib6]. The linking loader that should read
the listed modules from 067 is missing. Nothing else in the translator
reads 067: its only information words are 05747, 05750 and 05751. The
Makefile drops `lib6`'s 0414 coverage, which is not code.

### Linking loader: expected behaviour

A host-side implementation of these steps, with the conventions it
chooses, is `tools/itmload.py` ([AITM-object.md](AITM-object.md),
section 7).

What the missing program in drum 21 zone 014 receives from the
translator, and what it must do. [вывод] marks what follows from the
formats above but has not been checked.

**How it is reached.**

1. Key `Р` with a `(` group, e.g. `РАК,ГЛАВ(ПЕРВ+ВТОР)!`: `(` makes
   `ГЛАВ` the module name and sets `КОНЗАД` := 0; each `+` name (and the
   one before `)`) goes to 010005 + `06470`, and `06470` counts them
   (`lib6`: 010005 = `ПЕРВ`, 010006 = `ВТОР`, `06470` = 2) [трасса].
2. At the closing `!` (f1a 05164–05167), if the list is not empty,
   `06470` += 6 (`D01547`), so it becomes the length of the block from
   010000 (010 in `lib6`). The block is handed to the resident exchange
   routine (`ПВ 12(М1)`, word `06470 << 15 | D05051`) [трасса].
3. At the end of translation `ВЫВМ` builds the module at 014000. With
   `А`, `КОНВЫВ` stores it on 067 and jumps to `ЗАВЕР` + 011 (06517)
   [трасса lib6]. Without `А`, `ВЫВМ` jumps to `ЗАВЕР` (06506), which
   first puts a header at 013776 (module name 06501) and 013777
   ((05737 << 12 | 05740) << 20) and writes out the last page, then
   reaches 06517 too [код; the jump is traced in `rnoa`, which has no
   `(`].
4. 06517: `КОНЗАД` ≠ 0 — Э74. Otherwise М13 := `06470`, `Э70 D06764`
   (`0014000000210014`: physical read of drum 021 zone 014 into page 0,
   addresses 0–01777) and `ПБ 011`. In `lib6`, М13 = 010 at the jump,
   and the accumulator still holds the information word [трасса].

The older build (0400–0404) also reads drum 21 zone 014 to link, so
that zone was the loader's fixed slot in both builds [код].

**The program.** One zone (1024 words), at 0–01777, entry 011. It
replaces the resident (zone 0406), so it must do its own exchanges
[код]. It is entered by `ПБ`, as the alternative to Э74, so it is the
last step of the job: it does what the parameter words say and ends
the job itself. М1 is no return link: it is 06515 without `А` and 05722
with `А` [трасса z14p, z14pn].

**Inputs.**

| Where | Contents | Status |
|---|---|---|
| М13 | 6 + the number of `+` names: length of the block from 010000 | [трасса] |
| 010000 | name after `,` in the key | purpose unknown |
| 010001, 010002 | address range as ITM text, defaults `+00010` and `+70000` (octal 010 and 070000); a number in the key replaces them | [трасса] for the defaults |
| 010003 | name after `:` | purpose unknown |
| 010004 | name after `-` | purpose unknown |
| 010005 … 010000 + М13 − 1 | the `+` list: modules to link to the main one | [трасса] |
| 06501 | name of the main module (the one before `(`) | [трасса] |
| volume 067 | catalogue in zone 0, modules as described above | [опыт] |
| 014000 | the main module as built by `ВЫВМ`; header at 013776–013777 only without `А` | in core [трасса z14p, z14pn] |

**What is in core at 011** [трасса]. Jobs `z14p` (`lib6`) and `z14pn`
(`lib6n`: the same key without `А`) run on a copy of 2148 whose zone
0414 holds a probe (`tools/mkz14.py`, `VOL2148` in `tools/trace.sh`):
`счи М13`, `счи М1`, reads of 010000–010007 and 013776–014001, Э74.

- М13 = 010 in both.
- 013776–014001: with `А` — 0, 0, `0000600000000000`, 0 (module word 0,
  image 6; word 1 is 0 without `Г`); without `А` — `0000031362314223`
  (`ГЛАВ`), `0000300000000000` ((6 << 12 | 0) << 20), then the same
  module words. So the module at 014000 is still in core, and the
  header is there only without `А`.
- 010000–010007 do not hold the key block: they hold phase 2's name
  table, pairs (name, kind << 30 | value): `НАЧ` 010, `ИС` 012, `А` 014,
  `Б` 015, all kind 1. The block that phase 1 passed to the pager at
  the `!` (step 2) went to virtual memory at v035000, which is drum 020
  tract 016, sector 2. It is on the drum by phase 2, so the loader must
  read it back from there [трасса lib6; see [VM.md](VM.md)].

**Required functions** [вывод]:

1. Read the 067 catalogue (zone 0) and find the main module (06501;
   with `А` it has just been stored there) and every `+` name. Each
   entry gives the start zone (bits 1–10) and the image length (bits
   33–47). A missing name needs an error report of unknown form.
2. Read each module's zones. Word 0 gives the image length, literal and
   reference-record counts, word 1 the export-table length; the image
   follows from word 2.
3. Place the images one after another inside the range 010001–010002.
   The first one at 010 needs no relocation, since every module is
   translated for 010.
4. Relocate: for every half-word whose 3-bit scale field is 1, add
   (load address − 010) to its address field; 3 subtracts it. Kinds 2
   and 4 add or subtract the address of the module's `Р` area (size in
   descriptor bits 21–32), which the loader must allocate. Fields of 0
   are absolute.
5. Link: kind 5 replaces the literal number in the address field with
   the address of the external name; kind 6 takes reference record n
   (`literal << 30 | offset`) and puts the name's address + offset in
   the field. Names are resolved against the other modules' export
   tables (pairs name, kind << 45 | address, written with option `Г`).
6. Patch `Л;` words: each reference record with a field descriptor
   (`ЗПКОМ`) names a word, a field and the kind of the value already in
   that field; the field must be relocated or linked like a half-word
   [вывод].
7. Start the program. The module records no start address, so the
   entry must be a convention: the first image word, an exported name,
   or one of the names after `,`, `:` or `-`.

**Not specifiable yet.** (The two kinds of reference record are told
apart by bits 46–48: 0 for `literal << 30 | offset`, the kind for an
`Л;` field [опыт, AITM-object.md].)

- Where the `Р` area goes, and whether modules share it (a common
  block) or each gets its own.
- The meaning of the `,`, `:`, `-`, `/`, `.` items.
- How the start address is chosen, and what the 013776 header is for.
- Error reporting.

## Search of the volumes

`tools/libscan.py 2048 2148 2248` checks every zone for a module
catalogue (validated on `traces/lib6.vol`), a text catalogue (validated
on a tape written by `Л10,`), zones of ITM text, Э70 information words
for unit 067, and similarity to the 2148 translator zones. No library
of either kind is on these volumes [опыт]:

- **Catalogues:** none.
- **AITM builds:** the current one at 0406–0414 (2148 and 2248,
  identical); an older one at 0400–0404 (2148, 2248; again at 2248
  1007–1013). The older one's loader reads drum 21 zones 006–011 and
  014, the same zones as the current build, so it is a saved copy, not a
  separate system with its own linker. The 2048 build (055–060) has no
  information words for unit 067 at all.
- **More builds in 2148 0477–0537** (`besmtool search 2148 00.00.70`
  finds their listing header). The region is copied at 0707–0743, and
  its tail 0527–0537 again at 0744–0754:
  - build A: 0477 (sectors 1–3 like 0407: `f2b`, `f2c`; header «АВТОКОД
    МГЧ 000070», so the search misses it), 0500 (`f1a`), 0501 sectors
    0–1 (`f1b`, `aitm6`), 0502 (`f2a`);
  - build B: 0531 (resident), 0532 (= 0517, 0727, 0747; sector 0 holds
    only the word 7, then `f2b` and `f2c`), 0533, 0534 (half), 0535;
  - zones holding just the word 7 (0503, 0504, 0536, 0537) end each set.

  Both builds have key `Р`, with the 067 triplet at 05742 (A) and 05713
  (B) instead of 05747. Build B's store path is the same algorithm
  (export table, two passes, −1, append, catalogue print), but all of it
  fits in `f2a` 05640–05777 and then jumps to 06477 in `aitm6` (the
  current build's 06517, in `ЗАВЕР`). Its `f2b`
  therefore has no `КОНВЫВ`, and the listing header is at 06014 instead
  of 06061. Both `aitm6` copies read drum zone 014 for linking, like the
  current build.
- **2148/2248:0700** is a composite of four sectors: phase 2 at
  05744–06143 (header at 0115, triplet at 05750), an `aitm6` with the
  drum loader words, and two quarters of a resident (like 0406.2–3
  shifted by −7 and +4).
- **Zone 0414:** `z14`'s "tables" are a stale copy of 2148/2248 zone
  0316, words 0401–0673, which is another program. So 0414 is a work
  zone; no other copy of the linking loader has been found, but the
  non-AITM users of unit 067 listed in TODO.md are unexamined.
- **ITM text:** one zone of an ITM-autocode source with «ДЕШИФРАТОР
  РЕД» (2148 0527, 0737, 0744; 2248 0737, 0744, all identical); one zone
  of a program with `LOAD`/`UNLOAD` (2248:1145); and six zones in another
  notation (2248 2410–2415). These are scratch leftovers, not stored
  libraries: there is no catalogue, and each text starts mid-statement.
- **The «ДЕШИФРАТОР РЕД» program compiled:** 2148 0505–0510 (copies at
  2148 and 2248 0715–0720) is one image loaded at 030000–037777, zone
  0505 at 030000 and each next zone 02000 higher (local jumps fit no
  other base). It uses cells below 010000 and calls routines at
  06311–07314 outside the image (`R3.ПВВБС` = `пв 07314(М5)`), so it is
  a part of a larger system. It is a different revision of the 0527
  text, not its exact translation:
  - same: `Х:` at 036003 is `ИКИСО=RЕ.ПА,RЕ.СЧТАБС=СД/25/,ЛУЦ1=R4.У1,
    RЕ.СЧТАБС=СД/34/,ЛУЦ37=У0ЗАПР` (ИСО 0343, ТАБС 05534, Ц1 05043,
    RЕ = 016, R4 = 4, R3 = 5; shift counts are octal);
  - merged: `Р:`, `В:`, `Х:`, `Т:` (shifts 1, 3, 4, 010) become one
    routine at 035760 entered from 033060–033064 with М6 = 1, 3, 4, 010;
  - errors go through one routine 035662 with the message address in М6
    (`ЗАПР` at 035661 is `R7.ПА` «ЗАПР. СИМВОЛ», `ПБ 035662`) instead of
    the source's `Э20` stub per message; the messages at 036114–036165
    are shortened («В ТБИМ НЕ СЕГМ.» for «В ТБИМ НЕ СЕГМЕНТ», «СМ. КОЭФ.
    КРАТН.» for «КОЭФ. КРАТНОСТИ НЕ ПОСТ.») but come in the source's
    order.

Open questions are in [TODO.md](TODO.md).
