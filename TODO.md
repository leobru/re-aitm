# Open questions

Marks as in [README.md](README.md); details in [LIBRARY.md](LIBRARY.md).

## Text library (key Л, tape 30)

- How the МЛ30 catalogue is initialised on a new tape: a never-written
  zone 0 reads as the 2525… fill, and the translator has no key for it.
- The deck for reading a text back: `Л20,` gives error 22, and
  `Л20,В;Е;` loops at address 010. `КАТМЛ` (read by key) has never
  run; `ЧТМЛ` and `ИЩ12` run under `Б;`, `ЗПМЛ` under key `Ф` (`flist`).
- Exact packing of the catalogue words 0720 + i (start zone in the low
  12 bits, the rest unknown).
- `Б;` sections: covered by `sb1`–`sb5`. Open: the next-page step of
  an insertion (05604–05606) — needs a library text longer than a page,
  but a 120-line text breaks the write (errors 02, 11 until killed);
  why that text fails is unknown.
- Key `Л` second digit: `punch` runs `МЛКОП` (with key `П`), but the
  card images produced by Э71 4155/4154 were not inspected, and how Y
  maps to operators per card is unchecked.

## Module library (key Р, volume 067)

- The linking loader. With a `(` list, `ЗАВЕР` loads zone 0414 to 0 and
  jumps to 011, but 0414.0–2 is zeros on 2148 and 2248. No other copy
  was found on 2048, 2148 or 2248 (see LIBRARY.md, "Search of the
  volumes"). What it receives and must do: LIBRARY.md, "Linking loader:
  expected behaviour". The probe (`z14p`, `z14pn`) shows that the key
  block is no longer at 010000 when 011 is entered: where did the pager
  put it (word `06470 << 15 | D05051`, virtual page, drum 20 or 23)?
- Literals and reference records: section `Э;` (LIBRARY.md). Open:
  - the 04000 flag on a literal number (f2a 05513–05514, 05457 ≠ 0);
  - literal-table overflow (05507);
  - `ЭКСТР` with 0203 ≠ 0 (05434);
  - is error 13 for `ВН+1` and `Р1+1` (a name at address 0) intended?
  - the silent loss of the 1 in `СЧ1+ВН`;
  - where `Р=2000=10` puts the area without key `Р` (`ext2` runs, but
    the addresses were not checked).
- The descriptor flag (bit 48, always 1).
- The `/` and `.` list items, `)`, `:`, `-`, `,`, and the address range
  010001/010002 (numbers in the list).
- `Р…,Б(1)!` corrupts the exchange information word.
- A correct program whose code lies above its last `Н;` (start-address
  operator, or code placed high and data low) is stored truncated:
  the length is the final counter, not the highest address. Is this a
  bug, or was the missing linker meant to work only with programs
  starting at 010? Builds A and B have not been checked for this.

## Translator

- Zone 0411.2–3: code that writes drum zones 012 and 011 back
  (generation or saving of the translator?); no Э70 loads it, so its
  address is unknown.
- Zone 0407.0 is only the initial contents of a pager window; never
  executed.
- `Ф12ПЕЧ,…` without a comma after the number loops on «ОШИБКА В
  ИМЕНИ».
- Macros (key `М`; not in the 1969 manual). Known from `macro2`–`macro4`:
  `Д;ИМЯ,Ф1=Ф2=…,В;…Е;` defines, `М;ИМЯ,А1=А2=…,` expands with the actuals
  substituted by position (not in `С;`/`А;`/`Т;`/`Ч;` bodies). Open: what
  `.` instead of `,` after the name in `М;` changes (012001 without 05360);
  `f1b` 06247–06252 (a sign right after a formal in the body?) and 06316
  (`R…` in a `К;` body not followed by `.`) never run; substitution in
  `Л;` bodies is untested.
- With key `М`, a text with more `В;` than `Е;` loops in phase 1 until
  the 60 s watchdog; without `М` it runs past the end of the text and
  ends with error 36.
- Named registers, not in the 1969 manual: an identifier followed by
  `.` in the register field. With the 0527 source's own description
  `В;R1=3,R2,R3,R7,R4,RA=16,` the deck `R3.ПАИС=R3.Э064` translates and
  prints (R3 = 5); without the description `R3.`/`RE.` give error 06.
  Which code in phase 2 handles the `.` is not yet located.
- Corrections (key `И`, `corr1`–`corr8`): the manual's `И1,В;0,…!`
  (insert right after `В;`) gives error 51 even when descriptions exist;
  `f1a` 04622–04634 in the correction pass never run.
- Debugger (key `О`): `Э066` is emulated through Э67 with the word
  0000657400010010, which dispak treats as a debug trap (jump to 06574,
  «ОБРАЩ.К НЕСУЩ.СП»), so `f2c` 05671–05700 and `D05660` cannot run
  until dispak implements the Диспак Э67. An `Э064` with a three-word
  information list under `О00!` printed nothing (05615 runs). `ОШ2В`
  (05305) never runs, although `dbg` uses `Э20`, `Э21`, `Э32`, `Э33`
  (error 00 comes from elsewhere).

## Other volume contents

- The older AITM build in 2148/2248 zones 0400–0404 (copy in 2248
  1007–1013): what changed compared with 0406–0414.
- Builds A (0477–0502) and B (0531–0535) in 2148: order of the builds
  relative to each other and to 0400–0404 and 0406–0414, and what else
  changed. Build A's resident has not been found. Zones 0511–0526
  (resident-like 0511, 0513–0516; 0520–0526) and 0661/0662, 2248:1144
  (like 0404) are unidentified (0505–0510: see below).
- 2148:0700, a composite zone (phase 2 at 05744, `aitm6`, resident
  quarters): a scratch save of what?
- Zones sharing 160–360 words with the resident at the same addresses
  (2148 0544, 0552, 1070–1074, 1115; 2248 likewise) — probably memory
  images taken with the AITM resident loaded.
- The ITM autocode source fragment «ДЕШИФРАТОР РЕД» (one zone, five
  identical copies) — part of which program? Its messages mention
  descriptors, «ЗОНА СВЯЗИ» and segments. A later (or earlier) revision
  of it is compiled in 2148 0505–0510 at 030000–037777 (LIBRARY.md):
  which system supplies the cells below 010000 and the routines at
  06311–07314, and which revision is older?
- 2248:1145 — one zone of an ITM autocode program with `ЗАГР=77040`,
  `LOAD`, `UNLOAD`, sections `ПРОБ`, `SBIND`, `PRINT`, `NAME`, `ТОVID`,
  `ИНФСБО`.
- 2248:2410–2415 — ITM-coded text in another notation (`ЭКВ`, `БАЗ`,
  `=>`, `<-`).
- Programs using unit 067 that are not AITM: 2048 zones 0044, 1671;
  2148/2248 zones 0375, 0377, 0577 (zones 1 and 2 of 067); 2248 zones
  2540, 2560, 3111, 3210, 3730, 3750.
- 2148:0316: whose code is it? `z14` (0414.3) holds a stale copy of its
  words 0401–0673.
