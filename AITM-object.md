# Relocatable module of the ITM autocode translator (2148)

With key `Р` the 2148 build of АИТМ does not run the translated program.
`ВЫВМ` (f2a 05645) builds a **module** at 014000, and `КОНВЫВ` writes it
to the module library on volume 067. This file describes the module
format, mainly how it records **entry names** (the export table) and
**external names** (literals and reference records). For the catalogue,
the store path and the missing linking loader, see
[LIBRARY.md](LIBRARY.md). The 2048 build has neither key `Р` nor section
`Э;`, so this applies to 2148 only.

Evidence marks as in [README.md](README.md): **[опыт]** — seen in a
module written by a test job, **[код]** — read from the code only.
Addresses are octal. Bits are numbered from 1 (lowest) to 48. A word is
written as 16 octal digits: the first digit holds bits 46–48, and each
following digit holds the next three bits down.

Sources of the evidence:

| Job | What it records |
|---|---|
| `jobs/ext1.b6` | first `Э;` test: two external names, the `Р` area, an equivalence, a `Л;` field |
| `jobs/ext3.b6` | external names: order, duplicate texts, a use before the declaration, minus, offsets, long commands, `Л;` fields |
| `jobs/ext4.b6` | entry names of kinds 0–5, `*` names of nested blocks, `С;`/`А;`/`Л;` labels, `Л;` field descriptors |
| `jobs/lib1.b6` … | catalogue chain (LIBRARY.md) |

`make traces/ext3.ev` writes the volume to `traces/ext3.vol` and decodes
it into `traces/ext3.lib` (`tools/vol.py`). To try a single fragment,
run `tools/modtry.sh 'Э;ВН:Н=ВНЕШ,К;НАЧ:СЧВН=,'`. It translates the
fragment with key `РАНГКW,МОД!` on an empty volume and prints the errors
and the decoded module. Results below that come from such a fragment
quote the fragment.

## 1. Where the information is kept

| Item | Module | Catalogue |
|---|---|---|
| name of the module | — | name word of the entry |
| image length | word 0 | descriptor bits 33–47 |
| size of the `Р` area | — | descriptor bits 21–32 |
| relocation of each half-word | scale | — |
| external names | literals | — |
| external name + offset, `Л;` fields | reference records | — |
| entry names | export table (key `Г`) | — |
| start address | — | — |

The module contains neither its own name nor the size of its `Р` area.
Both are only in the catalogue entry, so a module copied out of the
library loses them [опыт, `ext4`: `Р=4`, `Р=3` give descriptor field 7
and appear nowhere in the module].

## 2. Layout

The module is stored in consecutive zones from the first zone of its
catalogue entry:

| Words | Contents | Count |
|---|---|---|
| 0 | header | 1 |
| 1 | export header | 1 |
| 2 … | image of addresses 010 … 010 + L − 1 | L |
| then | relocation scale | ⌈L/8⌉ |
| then | literals | NL |
| then | reference records | NR |
| then | export table | NE (two words per name) |

**Word 0** [код: shifts in `ВЫВМ` 05701–05711; опыт: all tests]:

| Bits | Contents |
|---|---|
| 34–48 | L, the image length (05737 = location counter − 010) |
| 23–33 | NL, the number of literals (05453) |
| 11–22 | NR, the number of reference records (05452) |
| 1–10 | 0 |

**Word 1**: NE << 36, the export-table length in words (0173), bits
37–48. It is 0 without option `Г` [опыт].

`ext3` gives `0001200100032000 0016000000000000`: L = 012, NL = 4,
NR = 015, NE = 016 (7 names).

The image is the translator's virtual memory from 060010. Every address
in it assumes that the module starts at 010, so a loader adds
(load address − 010) where the scale says so (LIBRARY.md, "Module
layout").

## 3. Relocation scale

There is one 3-bit field per half-word. Word i of the image (address
010 + i) uses scale word ⌊i/8⌋. Its left half (h = 0) uses bits
48 − 6·(i mod 8) − 3h down to 46 − 6·(i mod 8) − 3h. The field holds the
*kind* of the address in that half (`ОТМЕТ`, f2a 05577):

| Kind | Address field holds | Example |
|---|---|---|
| 0 | an absolute value | `СЧ100`, any `С;`/`А;`/`Л;` word |
| 1 | an address in the module (relocate) | `СЧНАЧ` |
| 2 | an offset in the `Р` area | `СЧР2` |
| 3 | minus an address in the module | `СЧ-ИС` |
| 4 | minus an offset in the `Р` area | `СЧ-Р2` |
| 5 | a literal number: the external name itself | `СЧВН`, `ПБВН` |
| 6 | a reference-record number: external name + offset | `СЧВН(5)`, `1ПВВН(3)` |

In the tests only command halves get a kind other than 0. `ОТМЕТ` is
also called for constant words (`КОНСТ`), but `С;` does not accept
names (error 34), and `Л;` words always have scale 0. A `Л;` field
whose kind is not 0 gets a reference record instead (section 4.4)
[опыт].

## 4. External names

### 4.1 Declaration

An external name is declared in section `Э;` as `МЕТКА:Н=ИМЯ,`. `МЕТКА`
is the label the program uses, and `ИМЯ` is the name the loader must find
in another module (`ЭКСТР`, f2a 05344, branch 05405). `МЕТКА` gets kind
5, and `ИМЯ` is appended to the literal table at 023000 [опыт].

- **Literal word.** The name is stored as ITM text, one byte per
  letter, right-justified with zero bytes in front. `ВНЕШ` is
  `0000022341310324` (bytes 000 000 223 205 220 324), and `ПЕРВЫЙ`
  is `6331021544752732` (six bytes, no padding).
- **Name length.** A name is at most six letters, the same limit as
  for labels: `Н=ВТОРОЙИ`, `Н=ВТОРОЙИМЯ` and the label `ДЛИННАЯМ:` give
  error 41 [опыт, `tools/modtry.sh`].
- **Literal numbers.** Literals are numbered from 0 in the order of the
  `Э;` items. Every item makes a literal, including an unused one
  (`А4:Н=НЕИСП` in `ext3`).
- **Duplicates.** The texts are not merged: `А1:Н=ПЕРВ` and
  `А3:Н=ПЕРВ` make literals 0 and 2. A use refers to its *label's*
  literal, so `СЧА1=СЧА3` gives addresses 0 and 2 (`ext3` word 011).
- **Use before declaration.** A label used before its `Э;` item
  resolves correctly (`ext3` word 010, `К;НАЧ:СЧА2(1)=СЧА1(2),` before
  `Э;`).
- **Other forms are errors** [опыт, `tools/modtry.sh`]:
  - `Н=5`, `Н=ПЕРВ+5`, `Н=ПЕРВ(5)`, `Н=ПЕРВ=5` give error 61;
  - an equivalence to an external name, `Э2:П=ВН` or `Э2:П=ВН(3)`,
    gives error 61;
  - `ВН+1` and `ВН-1` in an address give error 13 (LIBRARY.md);
  - an external name in a `С;` constant (`С;А1,`) gives error 34.
- **`Н=` with a name that is already a label of the program.** The
  literal is then not the text. Fragment
  `К;НАЧ:СЧ=,Т:СЧ=,Э;А1:Н=Т,К;СЧА1=,` gives the literal
  `0000000000000201`; `Э;Р1:Р=4,А1:Н=Р1,` gives `0000000000106401`, and
  `Э;А2:Н=ВТОР,А1:Н=А2,` gives `0000000000114002` [опыт]. The mechanism
  [код]:
  - after reading the name, `ЭКСТР` finds 0630 ≠ 0 (the lexer's value
    for a known name);
  - it records the pair (0630, literal number) at virtual 06000 + 05454;
  - `ВЫВМ` (05671–05700) then stores 0630 over the literal.

  What 0630 holds in this case is not established. Uses of `А1` are not
  affected: they still carry the literal number.
- **Redefining an `Э;` label.** `Э;ВН:Н=ВНЕШ,К;СЧВН=,Э;ВН:Н=ДРУГ,К;СЧВН=,`
  gives no error 25. The two uses get literals 0 and 1, and the export
  table has two `ВН` entries, `0000000000000000` and `5000000000000000`
  [опыт].

### 4.2 Use in a command: kind 5

A plain use (`СЧВН`, `ПБВН`, `ПВВН`, `ПАВН`) puts the literal number into
the address field, and the scale field is 5. This works in both the
12-bit and the 15-bit address field. The index register stays in its
own field. In `ext3`, `ПБА1=ПВА2` is `0300000003100001` (literals 0
and 1, scale 55), and `1ПВА1(3)` is the half `07100007`: М1, ПВ (031),
record 7, scale 6 [опыт, `ext3` words 015–017].

A minus before the name (`СЧ-ВН`) sets **flag 04000** in the literal
number. In `ext3`, `СЧ-А1` gives address 04000 and `СЧ-А2` gives 04001,
both of kind 5 [опыт]. The flag is set from the sign of the term
(0634 → 05457 at f2a 04203–04205, OR with 05566 at 05513–05514). The
literal number must stay below 04000, i.e. 11 bits, otherwise error 61
(`ЛИТПУЛ` 05502, check at 05511, `сда 64+11`) [код]. This 11-bit number plus the flag
gives the 12 bits that fit a short address field.

### 4.3 Use with an offset: kind 6 and reference records

`ВН(n)` is the external name plus a constant offset. `ЛИТПУЛ` appends a
**reference record** to virtual 010000 and puts the record's number
into the address field, with scale kind 6. The record has this layout
[опыт, `ext1`, `ext3`]:

| Bits | Contents |
|---|---|
| 46–48 | 0 |
| 42 | the minus flag (04000 of the literal number) |
| 31–41 | literal number |
| 16–30 | 0 |
| 1–15 | the offset n, 15 bits, as written |

In `ext3`:

| Text | Record |
|---|---|
| `СЧА1(7)` | `0000000000000007` (literal 0, offset 7) |
| `СЧА2(1)` | `0000010000000001` (literal 1) |
| `СЧ-А2(3)` | `0040010000000003` (flag, literal 1, offset 3) |
| `СЧА1(-2)` | `0000000000077776` (offset in 15-bit two's complement) |
| `СЧА1(77777)` | `0000000000077777` |

Every use makes a new record, even an identical one: `СЧА1(7)=СЧА1(7)`
makes records 3 and 4. Records are numbered from 0 in the order they
are made. A use made before the `Э;` item gets its record when the item
is read, so in `ext3` `СЧА1(2)` (right half of word 010) is record 0 and
`СЧА2(1)` (left half) is record 1, in the order `А1`, `А2` are declared.
The offset is a constant: `(Л)` is the letter's code and `(ИС)` the text
of `ИС`, not the label (LIBRARY.md).

### 4.4 Records for `Л;` fields

A `Д` or `К` field of an `Л;` word whose value has a kind other than 0
also gets a reference record (`ЗПКОМ`, f2a 05542). The record names the
word and the field:

| Bits | Contents |
|---|---|
| 46–48 | kind of the value (1–6) |
| 42–45 | field width − 1: 016 for `Д` (15 bits), 013 for `К` (12 bits) |
| 36–41 | M + width − 1, the 0-based number of the field's top bit (M from `/M`) |
| 32–35 | 0 |
| 16–30 | the value as written into the field |
| 1–15 | the word's address |

Bits 32–45 come from the field description 07272, masked by 05541 =
`0777760000000000`. `ПОЛЕЛ` (f2b 06332) takes the width and the position from
the same word [код]. The two fields were checked against seven cases
[опыт, `ext4`, `ext1`]:

| Field | Bits 42–45 | Bits 36–41 | Record |
|---|---|---|---|
| `ДНАЧ/0` | 016 | 016 | `1707000001000016` |
| `ДНАЧ/1` | 016 | 017 | `1707400001000017` |
| `ДВН(5)/30` | 016 | 046 | `6723000000100021` (`ext1`) |
| `ДНАЧ/41` | 016 | 057 | `1727400001000020` |
| `КНАЧ/0` | 013 | 013 | `1545400001000021` |
| `КНАЧ/14` | 013 | 027 | `1553400001000022` |
| `КНАЧ/44` | 013 | 057 | `1567400001000023` |

Only `Д` and `К` fields hold addresses, so only these two widths occur.

The value depends on the kind:

| Kind | Value (bits 16–30) |
|---|---|
| 1–4 | the address (absolute for origin 010), as in the word |
| 5 | the literal number |
| 6 | the number of a kind-6 record, made just before this one |

In `ext3`:

| Text | Records |
|---|---|
| `Л1:ДА1/30=КА2/0` at 020 | `5723000000000020` (kind 5, literal 0); `5545400000100020` (kind 5, literal 1) |
| `Л2:ДА1(3)/30` at 021 | `0000000000000003` (record 013: literal 0 + 3); `6723000001300021` (kind 6, record 013) |

The `Л;` word itself holds the same values in its fields, with scale 0
(020 = `0000000000000001`, 021 = `0000001300000000`). A field of kind 0
makes no record.

**Telling the two record forms apart.** Bits 46–48 are 0 in a
name + offset record and hold the kind (never 0) in a field record
[опыт]. A loader can therefore read the record table in one pass.

## 5. Entry names: the export table

With option `Г` of key `Р`, `ВЫВМ` appends the table of the outermost
scope after the reference records. It has NE/2 pairs [опыт, `ext4`]:

| Word | Contents |
|---|---|
| 1st | the name: ITM text, right-justified, at most 6 letters |
| 2nd | kind << 45 \| value (15 bits) |

The kind is the same as in the scale (section 3). The value is
absolute for origin 010 [опыт, `ext4`]:

| Text | Entry | Kind |
|---|---|---|
| `НАЧ:` at 010 (`К;`) | `1000000000000010` | 1, label |
| `ДАН:` (`С;`), `ТЕКСТ:` (`А;`), `Л1:` (`Л;`) | `1000000000000014`, `…15`, `…16` | 1 |
| `ВК:П=НАЧ+1` | `1000000000000011` | 1, equivalence |
| `АБС:П=100` | `0000000000000100` | 0, absolute |
| `Р1:Р=4`, `Р2:Р=3` | `2000000000000000`, `2000000000000004` | 2, offset in the `Р` area |
| `М3:П=АБС-НАЧ` | `3000000000000070` | 3 (0100 − 010) |
| `М4:П=АБС-Р2` | `4000000000000074` | 4 (0100 − 4) |
| `МИН:П=НАЧ-АБС` | `1000000000077710` | 1 (010 − 0100, 15 bits) [fragment `К;НАЧ:СЧ=,Э;АБС:П=100,МИН:П=НАЧ-АБС,`] |
| `ВН:Н=ВНЕШ` | `5000000000000000` | 5, external |

An external name is exported with kind 5 and value 0, so the entry does
not say which literal it is. Two external names both give
`5000000000000000` (`ext1`, `ext3`), and a loader cannot resolve
anything through such an entry.

**Order.** First come the global names of nested blocks (`*ИМЯ:`,
entered by `ПРОХ2`, f2a 04341, before the pass), then the outer block's
names in the order they are defined, `Э;` items included. In `ext4`
the order is `ГЛ`, `ГЛ2`, `НАЧ`, then the `Э;` names, then
`ДАН` … `Л6`. `ГЛ2` comes from a block nested two levels deep. A plain
label of a nested block (`ЛОК`) is not exported. There is no way to
keep an outer-block label out of the table [опыт].

The export table is not counted in the catalogue's image length.
Without `Г` the table is empty and word 1 is 0.

## 6. What a loader does with it

The full list of expected loader steps is in LIBRARY.md ("Linking
loader: expected behaviour"). From the format above:

1. Read word 0, word 1, the image, the scale, NL literals, NR records,
   and NE words of exports.
2. For each half-word, look at its scale kind:
   - 1 or 3: add or subtract the load offset;
   - 2 or 4: add or subtract the address of the `Р` area, whose size
     is in the catalogue;
   - 5: the field holds literal k, plus 04000 for a minus; replace it
     by ± the address of the name in literal k;
   - 6: the field holds record r; take its literal and its offset and
     put ± address + offset.
3. For each record with a non-zero kind (bits 46–48), patch the field
   of the word at bits 1–15. The position and width come from bits
   36–45, and the value is treated like a half-word of that kind.
4. Resolve names against the other modules' export tables, using kinds
   0–4. Kind-5 entries carry nothing.

## 7. Loader: `tools/itmload.py`

The script replaces the lost loader of drum 21 zone 014. It is the
reference for the linking rules; a BEMSH loader for zone 0414 should
follow it.

```
tools/itmload.py 'РАК,ГЛАВ(ПЕРВ+ВТОР)!' LIB[/ZONE] [-o job.b6] [--seg N] [--common]
                 [--store ИМЯ OUT.vol] [--vol N]
```

- **Inputs.** The key `Р`: the main module is the name before `(`, and
  the list is the names separated by `+`. Letters before the comma are
  ignored, and `ИМЯ!` loads one module. `LIB` is a volume number (a file
  in `$BESM6_PATH`) or the path of a volume image (`traces/link2.vol`).
  `/ZONE` is the zone of the catalogue; the module zones in the
  descriptors count from it.
- **Output.** The memory map, the names and the resolved external
  references go to stdout. With `-o`, the script writes a dispak job
  that loads the main module and one segment (`--seg`, default 1), each
  module from its `В` card, and starts the program.

Conventions (not recorded in the module, chosen for the script):

| Question | Choice |
|---|---|
| placement | the main module at 010 (as translated), the others after it in the order of the list. A module with an entry `НАЗ` of kind 0 (`Э;НАЗ:П=4000,`) goes to that address instead (shift = НАЗ − 010; `НАЗ` = 1 puts the main module at 1). A segment then spans from its lowest module start to its highest end |
| `Р` areas | each module gets its own zeroed area after all the images, of the size in its catalogue descriptor; `--common` gives one area of the largest size to all |
| start | the main module's entry `НАЧ` (kind 1) if exported, else 010 |
| names | from the export tables of all loaded modules (kinds 0–4); a module needs option `Г` to be called. On a repeated name, the first one wins |
| kind 6 with a minus | `-ВН(3)` is −(address + 3) |
| overlays | see below |

**Overlays.** The key passes the loader control words between the names
(LIBRARY.md, "Key Р"). `ИМЯ/` gives `0020000000000000`, `А.` gives
`0020000000000001` and `Л.` gives `0020000000000004`. Brackets do not
nest. `А` is абзац (0400 words) and `Л` is лист (02000), so the low
part of the word is a boundary in абзацы. The script reads them as
follows [вывод: the translator only passes the words on]:

- `/` after a name ends a segment. `ГЛАВ(ПЕРВ+ВТОР/ТРЕТ)` is the root
  `ГЛАВ` plus two segments, `ПЕРВ+ВТОР` and `ТРЕТ`. Every segment
  starts at the end of the root, and the `Р` areas come after the
  longest segment. Without `/` the list is one segment, i.e. plain
  linking.
- `А.` or `Л.` before a name puts that module on an абзац or лист
  boundary. Translator phases are overlaid this way: ФАЗ2В at 05000
  over the upper half of ФАЗ2А, and ФАЗ1Б/ФАЗ2Б at 06000.
- Name lookup order: the referencing module's own segment, then the
  root, then the other segments.
  - A segment may not refer to another segment.
  - A reference from the root must have the same address in every
    segment that defines the name, otherwise it is an error
    (`ГЛАВ(ПЕЧ/Л.ПЕЧБ)`: `ПЕЧ` is at 014 and at 02000).
- The job holds only the root and the chosen segment. To switch
  segments at run time, the program must be stored with `--store`
  (below) and read the segments itself.

**Storing a linked program** (`--store ИМЯ OUT.vol`) [вывод: a format
chosen for the script, modelled on how the translator's own phases are
stored and read]. The program is linked as above, with three changes:
- the first module of each segment is put at least on an абзац
  boundary;
- the `Р` areas start on an абзац boundary;
- the root gets a **segment table** right after the main module. The
  table holds one Э70 word per sector of each segment, and each
  segment's run of words ends with 0.

The loader defines the names `СЕГ1`, `СЕГ2`, … as the addresses of
these runs. The program reads segment n itself: it declares
`Э;С2:Н=СЕГ2,` and loops `Э070` over the words up to the 0.

`ГЛАВ2` (`jobs/link4.b6`) does this:

```
К;НАЧ:12ПВПЧ=,1ПАС2=,
Ц:1Э070=,1СА1=1СЧ,
У1Ц=,12ПВПЧ=,=Э074,
```

The Э70 word reads one sector of unit 067 to its place [опыт;
decoded from dispak `ddio`]:

| Bits | Contents |
|---|---|
| 45–48 | 010: sector exchange |
| 37–43 | 010: read |
| 36 | 04000 of the left address: the sector is given by number (КУС) |
| 31–35 | лист of the memory address |
| 25–26 | абзац within the лист |
| 13–19 | 067: unit |
| 3–7 | zone (only 0–037 in this form) |
| 1–2 | sector in the zone |

For example `4010410000670025` reads zone 5, sector 1 to 02000. The
translator's own phase words (aitm6 06760–06763) have the same layout
for drum 21, without the 04000.

The record is a new catalogue entry: the old entry with that name is
freed (−1), and the record goes to the free zone. Its descriptor has
bit 48 = 0, which marks a stored program instead of a module. Bits
33–47 hold the length in words, and bits 1–10 the first zone. The
record itself:

| Words | Contents |
|---|---|
| 0 | root length (from address 0, table included) << 33 \| segments << 22 |
| 1 | export words << 36 \| table address << 15 \| start |
| 2 … | root image from address 0, already linked (cell 0 is not loaded) |
| then | exports: (name, address) of the root, `СЕГn` included |
| from the next sector | the segments, sector after sector, as the table reads them |

All words are written with the instruction tag (dispak keeps it in bit
49 of a volume word), so code read by Э70 can be executed.

`tools/itmload.py 'ИМЯ!' LIB` recognises a stored program by bit 48.
It does not link it again: the job loads the root and segment
`--seg`, taken from the volume through the table, and mounts the volume
as `ЛЕНТ 67(--vol)`. `tools/vol.py` prints such an entry as
`stored program`.

Relocation follows sections 3–4:
- A long half-word (bit 20 set) has a 15-bit address.
- A short one has 12 bits, and bit 19 set adds 070000: `СЧ-Р2` in
  `ext1` is the half `01107770` [опыт]. A value from 010000 to 067777
  does not fit a short command and is an error.
- A `Л;` field is changed in place by its record. The value from bits
  16–30 is resolved like a half-word of the record's kind.

**The dispak job.** dispak loads `С` cards as numbers, and executing a
number stops the job with «КОНТРОЛЬ КОМАНДЫ» (`cu.c`, `CV_NUMBER`). The
job therefore loads every word as a `К` card: 9 octal digits per
half-word, of 1, 3, 2 and 6×3 bits. Reading such words as data is
allowed.

**Test** (`make link`):
- `jobs/link1.b6` stores the subroutine `ПЕЧ` (entries `ПЕЧ`, `ДВА`).
  It has a `Р` area, and an `Л;` word `ИС2:КТ3/30=КТ4/0` serves as the
  Э064 information word.
- `jobs/link2.b6` stores `ГЛАВ`: `12ПВПЧ=,12ПВДВ=,12ПВПЧ(2)=,=Э074,`
  with `Э;ПЧ:Н=ПЕЧ,ДВ:Н=ДВА,`.
- `jobs/link3.b6` stores `ПЕЧБ`: the same entries `ПЕЧ` and `ДВА`
  with other texts.
- `tools/itmload.py 'РАК,ГЛАВ(ПЕЧ)!' traces/link2.vol` places `ПЕЧ` at
  014. The job prints «ПРИВЕТ ВСЕМУ» and «ПОКАЖИ ЛЮДЯМ» twice and ends
  at 013 [опыт]. This checks:
  - the relocation of kind 1 (`ИС`, `12ПБ` returns);
  - kinds 5 and 6;
  - the `Л;` record;
  - a store into the `Р` area.
- `jobs/link4.b6` stores `ГЛАВ2`, which reads segment 2 by `СЕГ2`.
- `ГЛАВ(Л.ПЕЧ/Л.ПЕЧБ)` puts both segments at 02000, with the `Р` areas
  at 02015 and 02021. With `--seg 1` the job prints the texts of `ПЕЧ`,
  with `--seg 2` «ЗДРАВСТВУЙТЕ» and «ПРОЩАЙТЕ ВСЕ» twice
  (`traces/ovl1.txt`, `traces/ovl2.txt`) [опыт].
- `ГЛАВ2(Л.ПЕЧ/Л.ПЕЧБ)` is stored as `ПРОГ` (`traces/prog.vol`, zone 5:
  the record in sector 0, segments in sectors 1 and 2). The job of
  `ПРОГ!` starts with segment 1. The program prints «ПРИВЕТ ВСЕМУ»,
  reads segment 2 by Э70 and prints «ЗДРАВСТВУЙТЕ» (`traces/prog.txt`)
  [опыт].

## 8. Loader in BEMSH for zone 0414 (`zagr/`)

`zagr/parts/zagr.be` is a BEMSH program with the functions of
`tools/itmload.py`. It links the main module and the list, resolves
external names and handles overlays. Then it either starts the program
or stores it in the library in the format of `--store` (section 7). It
lies in zone 0414 of a copy of 2148, where `ЗАВЕР` expects the lost
loader.

**Run or store.** A name before `:` in the key,
`РАГК,ПРОГ:ГЛАВ2(Л.ПЕЧ/Л.ПЕЧБ)!`, asks the loader to store the linked
program under that name instead of starting it. The translator puts
that name in word 3 of the key block (010003; LIBRARY.md, «Key Р»), and
the loader reads it from 05003 before it reads the catalogue.
`tools/itmload.py` accepts the same key and then wants `--store ИМЯ
OUT.vol`.

Build and tests:

```
make -C zagr              # zagr/parts/zagr.new (tools/reasm.pl, no original to compare)
make zagr                 # traces/zagr.2148 (tools/mkz14.py --image), jobs zl1–zl5
```

**What it receives** [трасса]:
- `ЗАВЕР` reads zone 0414 over page 0 and jumps to 011.
- The main module, as `ВЫВМ` built it, is still at 014000. Its name is
  in 06501 and its `Р` size in 05740.
- The key block is on drum 020 tract 016 from word 01000: names and the
  control words of `/`, `А.`, `Л.`, ending with 0 (LIBRARY.md).
- The catalogue is zone 0 of unit 067.

**Memory.** Short commands address only 0–07777, so the loader stays in
page 0, where it is read:

| Addresses | Contents |
|---|---|
| 0–01777 | the loader: a copy of the pager plus its own code and data |
| 02000–03777 | pager windows |
| 04000–05777 | key block, then the 067 catalogue |
| 06000 | list; 06100–06477 module table (8 words per module; word 3 is the alignment mask, or the address with bit 16 for `НАЗ`) |
| 010000–010377 | zeros for filling the image |
| 014000 … | the main module |
| 030000–047777 | buffer for one library module (4 zones) |
| 050000–051764 | names (3 words each, about 338) |
| 051775–051777 | the starting stub |

**Building through the pager.**
- **Virtual memory.** The image is built in virtual memory on drums
  020–027, so the segments together can be much larger than core:
  - the root and segment 1 go to v060000 + address, as the translator
    lays out a program;
  - segment s ≥ 2 goes to v160000 + (s − 2)·0100000 + address, which
    limits the list to 7 segments;
  - when storing, segment 1 gets its own range too (as segment 2 does,
    the others shift by one, so at most 6 segments), so that a segment
    overlapping the root's addresses does not overwrite the root image.
- **A copy of the pager.** The pager `ОБМЕН`/`ЛСТБАР` lives in the
  resident page 0, which zone 0414 replaces, so the loader carries a
  copy of it at the same addresses 00014–00160. It has to stay there:
  `уиа 49(М3)` followed by `по (М3)` jumps to 061.
- **Moved data.** The pager's data block (00660–00712 in `aitm0`) and
  its constants are copied under their labels to other places in page
  0. The mask at 011 moves away, because 011 is the entry point.
- **Zero filling.** A tract touched for the first time is written from
  core page 0 (VM.md), so the loader first fills the run image with
  zeros.

**Steps.**
1. Lay out the modules as in section 7.
2. Pass 1 collects the export tables of all modules. The main module is
   read in place; the others are read from 067 into the buffer.
3. Pass 2 relocates each module in place, by its scale and `Л;`
   records, and writes it to its virtual range. Every segment is
   linked, not only segment 1.
4. Start:
   - write back the dirty windows;
   - read pages 1 … L of the run image from drum 020 tracts 031 … with
     Э70;
   - copy a 3-word stub to 051775. With the information word in 051777,
     the stub reads page 0 (tract 030) and jumps to `НАЧ` or 010.
5. **Storing** (name before `:`). The layout follows section 7:
   - the first module of every segment goes to an абзац boundary;
   - the `Р` areas start on an абзац;
   - the root gets the table of Э70 words, one per sector of each
     segment, ended by 0. The layout is repeated until the size of the
     table settles;
   - the names `СЕГ1`, `СЕГ2`, … are entered before pass 1;
   - the catalogue entry of the old program with that name is freed
     (−1), and the record goes to the free zone.

   After pass 2 the loader writes, by sector exchanges on unit 067:
   - the record, built at 030000: header, root (read back from virtual
     memory), root exports;
   - every segment, read sector by sector from its virtual range;
   - zero sectors up to the end of the zone, so that no filler of the
     fresh zone is left. They are not counted in the length;
   - the catalogue (zone 0).

   It prints «ЗАГР: ЗАПИСАНО ИМЯ» and ends with Э74. The sector form of
   Э70 reaches zones 0–037 only.
6. Errors are printed by Э64 as «ЗАГР: …» followed by a name, and the job
   ends with Э74. The cases are:
   - НЕТ МОДУЛЯ;
   - НЕТ ИМЕНИ;
   - ИЗ СЕГМЕНТА;
   - РАЗНЫЙ АДР.;
   - КОРОТК. АДР.;
   - МНОГО ПАМЯТИ: more than 7 segments, more than 31 list modules, the
     run image past 050000, or the name table full;
   - БОЛЬШОЙ МОД.: a library module longer than 4 zones, or the main
     module past 030000.

The program must end below 050000, because page 024 holds the stub and
the jobs order `ЛИСТ 0-24`.

**BEMSH details.** BEMSH puts an extracode in the right half of a word,
with `мода 0` in the left half. Execution then goes on in the next word,
whose left half is the `дк 0,0` written after the extracode, i.e. a
`зп` to cell 0. The translator uses that as a no-op too.

**Check** (`make zagr`, `tools/memcmp.py`). Each job is translated with
key `РАГК,ИМЯ(…)!` on a library volume of the `link`/`lib` chains. The
job runs under the dispak debugger with a breakpoint at 051776, after
page 0 is read and before the jump. Every word that
`tools/itmload.py -o` loads for the same key is dumped and compared:

| Job | Key | Printout | Memory vs itmload |
|---|---|---|---|
| `zl1` | `ГЛАВ(ПЕЧ)` | «ПРИВЕТ ВСЕМУ», «ПОКАЖИ ЛЮДЯМ» ×2 | 17 words, equal |
| `zl2` | `ГЛАВ(Л.ПЕЧ/Л.ПЕЧБ)` | the same: segment 1 at 02000 | 17 words, equal |
| `zl3` | `ГЛАВ(ПЕЧ+НЕТУ)` | «ЗАГР: НЕТ МОДУЛЯ  НЕТУ» | — |
| `zl4` | `СЛОЖН(ПЕЧ)` | «ПРИВЕТ ВСЕМУ» | 22 words, equal |
| `zl5` | `ГЛ5(Л.ВТОР/Л.ТРЕТ+ВТОР/ВТОР+ПЕРВ)` | — | 1113 words, equal |

What the jobs cover:
- `zl4` has kinds 1–4 in half-words, kinds 5 and 6 with and without
  minus, and `Л;` records of kinds 1, 2, 5 and 6.
- `zl5` builds three segments of up to 02130 words through the pager,
  across tract boundaries.

Storing is checked by `traces/zsN.zscmp` (`tools/volcmp.py`). The
volume after the job is compared word for word with the one
`tools/itmload.py --store` writes. The reference is made on the volume
as the translator left it, by the same job run with the probe of zone
0414 (`traces/z14mock.2148`):

| Job | Key | Result |
|---|---|---|
| `zs1` | `ПРОГ:ГЛАВ2(Л.ПЕЧ/Л.ПЕЧБ)` | «ЗАГР: ЗАПИСАНО    ПРОГ»; 6 zones equal. `itmload 'ПРОГ!'` runs it: «ПРИВЕТ ВСЕМУ», then segment 2 read by `СЕГ2`: «ЗДРАВСТВУЙТЕ» |
| `zs2` | `ПРГ5:ГЛ5(Л.ВТОР/Л.ТРЕТ+ВТОР/ВТОР+ПЕРВ)` | 3 segments, zones 6–11; 10 zones equal |

All results are [опыт].

## 9. Dogfooding: АИТМ rebuilt with its own tools

The translator itself is the test program. Its parts (`parts/*.be`,
which BEMSH reassembles byte for byte, README.md) are rewritten in ITM
autocode, translated by АИТМ 2148 into the module library, linked by
`zagr` with overlays and stored. The stored program matches the
original zones of 2148 [опыт]:

```
make parts check        # parts/*.bin, parts/*.be.lst
make itm                # itm/*.itm from parts/*.be (tools/be2itm.py)
make dogfood            # tools/dogfood.sh -> traces/dog/cmp.txt
```

**Rewriting** (`tools/be2itm.py`). Every word of a part becomes one
statement:
- **Command words** (also `кк`, `дк` and `конк` halves) become `К;`.
  Each half is decoded from the binary: index register, ITM mnemonic or
  `Эnnn`/`Эnn` for codes without one, and the address. A numeric
  address after `Э` is written with `+` (`Э070+1065`): digits right after
  the code would be read as part of it.
- **Addresses.** An address is symbolic when the BEMSH operand names a
  label (`G04721(5)` for `G04721+5`), so ITM gives it the same
  relocation. Otherwise it is the octal number, negative when bit 19 of
  a short command is set.
- **Data words** (`конд`, `текст`, `пам`) become `С;` with their 16
  octal digits.
- **Text words.** A data word that the BEMSH comment marks as ITM text
  (`ITM 'ОШИБКА'`) becomes an `А;` constant of its six characters,
  decoded from the binary (`D01112:ОШИБКА,`, ` МЛ31 ,` with its spaces).
  Words holding codes that a dispak deck cannot type stay in `С;`: 040,
  0140 (end of information), 0142 (set position) and 0173 (end of
  line). On a terminal these are entered as `:×`, `::`, `:>`, but
  dispak reads deck text only through `gost_to_itm`, and in `А;` such
  pairs give error 23. Such a word keeps the BEMSH comment as an ITM
  note (`3043731443546615,‘{ПОЗ}(ИСПР‘`). Of the 38 marked
  words, 29 are written as text.
- **Block structure.** The outer block holds `Э;НАЗ:П=адрес,` and the
  external names (`X:Н=X,`) of the labels the part uses from other
  modules, as its `внеш` lines say. Everything else is in an inner block,
  and only the labels other modules use are marked `*`, so the export
  tables hold 248 names, not every label.
- **References between different overlay segments** are written as
  numbers, since the addresses are fixed: `ФАЗ2В` lies over the upper
  half of `ФАЗ2А` and refers to it and to `ФАЗ2Б`, which flat segments
  cannot express.
- **The root module** `АИТМ` is `aitm0` and `aitm6` in one text, with
  `НАЗ` = 1 and `Н;6407,` before `aitm6`. The part starts at 1, and the
  module's first word is 010.

| Module | Parts | НАЗ | Segment |
|---|---|---|---|
| `АИТМ` | `aitm0`, `aitm6` | 1 | root |
| `ФАЗ1А`, `ФАЗ1Б` | `f1a`, `f1b` | 04000, 06000 | 1 |
| `ФАЗ2А`, `ФАЗ2Б` | `f2a`, `f2b` | 04000, 06000 | 2 |
| `ФАЗ2В` | `f2c` | 05000 | 3 |

**Long texts.** Each module is one job (`tools/itmdeck.py`); `f1a` is
24 468 characters. The deck puts the text at 07000 and 06776 + N
(N words) into cell 3; the loader of the deck passes it on in the
accumulator. `ПУСК1` then goes to 04667, which copies the N words to
the drum itself (`ТЕКСТП`; README.md). Earlier this was taken for data.

The sector 0414.3 (`z14` in `parts.txt`) is not part of the
translator. It is what is left of the zone of the lost loader, which
`ЗАВЕР` reads only to start the loader; here `zagr` takes its place. So
`z14` is not rebuilt.

**Chain.** The five phase modules are translated job after job onto one
library: the first with key `РАНГК`, then `РАГК`. The last job
translates `АИТМ` with key
`РАГК,АИТМЗ:АИТМ(ФАЗ1А+ФАЗ1Б/ФАЗ2А+ФАЗ2Б/ФАЗ2В)!` on the copy of 2148
with `zagr`, which links the modules and stores `АИТМЗ` (zones
015–023).

**Checks.**
- `tools/itmcmp.py stored` takes the root and the three segments from the
  record through its Э70 words and compares them with `parts/*.bin`. All
  seven parts match word for word: `aitm0` 1–01777, `aitm6`, `f1a`,
  `f1b`, `f2a`, `f2b` and `f2c`.
- `tools/volcmp.py` finds the volume identical to the one
  `tools/itmload.py --store` writes from the same library.
- Each module alone, placed at its `НАЗ`, also matches its parts
  (`tools/itmcmp.py module`).

**What it took in the loaders:**
- the `НАЗ` placement;
- the stored root from address 0, for the words 1–7 of `aitm0`;
- a larger name table in `zagr` (257 names: 248 entries, the `НАЗ` of
  each module and `СЕГ1`–`СЕГ3`);
- segment 1 in its own virtual range when storing. Before that, `ФАЗ1А`
  and `ФАЗ1Б` overwrote the part of the root image that lies under them
  (02000–06377 between `aitm0` and `aitm6`), and the stored root
  differed from `itmload`'s.

