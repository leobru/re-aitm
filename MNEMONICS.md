# BESM-6 instruction mnemonics and how they are derived

Every BESM-6 instruction, with its English (Madlen/dispak/b6as) and
Russian (Bemsh/disbesm6) mnemonic and what each abbreviation stands
for. The official operation names (column "ТО") come from
`besm6/micro-besm/doc/opcodes/besm6.json`, which follows the technical
description (ТО IX, «Описание системы команд»). Semantics follow
`besm6/v7besm/doc/Besm6_Instruction_Set.md`; Диспак extracode meanings
follow `dispak/dispak/cu.c` and `extra.c`.

Expansions marked *(?)* are inferred from the pattern and the
operation, not quoted from a source.

The two-letter mnemonics of the ITM autocode itself (`СЧ`, `ЗЧ`, `ПБ`,
`СД`, …) are in the last section, [ITM autocode](#itm-autocode-автокод-итм).

## English mnemonics: the letter code

The English set is a register-transfer notation: most mnemonics read
"source To destination" or "A op X".

| Letter | Meaning |
|---|---|
| A | accumulator (сумматор) |
| X | memory word at the effective address, `mem[U]` |
| Y | younger-bits register (РМР) |
| R | AU mode register (РР) |
| E | exponent of A (порядок) |
| N | the address itself used as a number (`U[7:1]`) |
| I | index register selected by the address (`U[4:1]`) |
| J | index register selected by the address without modifier (`V[4:1]`) |
| M | index register named in the instruction's M field |
| S | stack (магазин): M[017] |
| U | effective address with modifier (исполнительный адрес) |
| V | address without the M contribution (`offset + C`) |
| C | address-modification register (C) |
| W | low 15 bits of X |
| T | "to" |
| Z, 1 | condition: zero / non-zero |
| J (in UJ, VJM, IJ) | "jump" |
| L | loop |
| `+ - * /` | the arithmetic operation itself |

Patterns:

- **xTy** — transfer: `XTA` X→A, `ATX` A→X, `YTA`, `XTR`, `NTR`, `RTE`,
  `ATI`, `ITA`, `MTJ`, `UTC`, `WTC`, `VTM`; with **S** for the stack:
  `XTS` (X→stack: push A, load X), `STX` (stack→X: store, pop),
  `STI`, `ITS`.
- **AoX** — A combined with X by operation o: `AAX` (and), `AOX` (or),
  `AEX`, `ARX`, `AVX`, `AMX`, `APX`, `AUX`, `ACX`, `ANX`, `ASX`.
- **…X / …N** pairs — the same operation with a memory operand or with
  the address as an immediate: `E+X`/`E+N`, `E-X`/`E-N`, `ASX`/`ASN`,
  `XTR`/`NTR`.
- **Branches** — target kind, condition, tested register: `UZA` (to U if
  Zero A), `U1A` (to U if 1 = non-zero A), `VZM`, `V1M`, `VLM` (to V,
  Loop on M), `UJ` (U, Jump), `VJM` (V, Jump, link in M).

## Russian mnemonics: the word code

The Russian set abbreviates the Russian operation name, usually by
initial letters or syllables. Fixed suffixes:

| Suffix | Meaning | Examples |
|---|---|---|
| -а | по **а**дресу: the address is the operand | `слпа`, `вчпа`, `сда`, `ржа`, `уиа`, `слиа`, `мода` |
| -м | **м**агазинная: stack variant | `зпм`, `счм`, `уим`, `счим` |
| -и | **и**ндекс (модификатор) | `уи`, `счи`, `уии`, `сли` |
| п- | **п**ереход: branch | `пб`, `пв`, `по`, `пе`, `пио`, `пино` |

## Format 1 (bit 20 = 0), opcodes 000–047

With the S bit set, the same instruction is written 100–147 in the
traditional numbering.

| Op | Eng | English reading | Rus | Russian reading | ТО |
|---|---|---|---|---|---|
| 000 | ATX | A To X | зп | **з**а**п**ись | запись сумматора в память |
| 001 | STX | Stack To X: store A, then pop | зпм | **з**а**п**ись **м**агазинная | запись числа магазинная |
| 002 | MOD | MODe/internal registers *(?)* | рег | **рег**истры | (supervisor: CPU registers) |
| 003 | XTS | X To Stack: push A, load X | счм | **сч**итывание **м**агазинное | считывание магазинное |
| 004 | A+X | A plus X | сл | **сл**ожение | арифметическое сложение (плавающая запятая) |
| 005 | A-X | A minus X | вч | **в**ы**ч**итание | арифметическое вычитание |
| 006 | X-A | X minus A | вчоб | **в**ы**ч**итание **об**ратное | обратное вычитание |
| 007 | AMX | A Minus X, moduli | вчаб | **в**ы**ч**итание **аб**солютных величин | вычитание модулей |
| 010 | XTA | X To A | сч | **сч**итывание | считывание числа |
| 011 | AAX | A And X | и | логическое «**и**» | логическое умножение |
| 012 | AEX | A Exclusive-or X *(?)* | нтж | **н**е**т**о**ж**дественность | сравнение |
| 013 | ARX | A plus X, Ring (end-around) carry *(?)* | слц | **сл**ожение **ц**иклическое | циклическое сложение |
| 014 | AVX | A, inVert by sign of X *(?)* | знак | изменение **знака** | изменение знака числа на сумматоре |
| 015 | AOX | A Or X | или | логическое «**или**» | логическое сложение |
| 016 | A/X | A divided by X | дел | **дел**ение | деление |
| 017 | A*X | A times X | умн | **умн**ожение | умножение |
| 020 | APX | A Packed by mask X | сбр | **с**бо**р**ка | сборка по маске |
| 021 | AUX | A Unpacked by mask X | рзб | **р**а**зб**орка | разборка по маске |
| 022 | ACX | A: Count of ones + X | чед | **ч**исло **ед**иниц | выдача числа единиц |
| 023 | ANX | A: Number of the highest one + X | нед | **н**омер **ед**иницы | выдача номера старшей единицы |
| 024 | E+X | Exponent plus X | слп | **сл**ожение **п**орядков | сложение порядка с кодом |
| 025 | E-X | Exponent minus X | вчп | **в**ы**ч**итание **п**орядков | вычитание из порядка кода |
| 026 | ASX | A Shifted by X | сд | **сд**виг | сдвиг логический по коду |
| 027 | XTR | X To R | рж | **р**е**ж**им | установка РР по коду |
| 030 | RTE | R To E (A's exponent field) | счрж | **сч**итывание **р**е**ж**има | выдача РР |
| 031 | YTA | Y To A | счмр | **сч**итывание **м**ладших **р**азрядов | выдача регистра младших разрядов |
| 032 | — | — | `кк 26,` | (Bemsh: short command, decimal opcode) | (supervisor, undocumented) |
| 033 | EXT | EXTernal devices | увв | **у**правление **в**нешними устройствами (**в**вод-вывод) | (supervisor I/O) |
| 034 | E+N | Exponent plus N | слпа | **сл**ожение **п**орядка с **а**дресом | сложение порядка с адресом |
| 035 | E-N | Exponent minus N | вчпа | **в**ы**ч**итание **п**орядка, **а**дрес | вычитание из порядка адреса |
| 036 | ASN | A Shifted by N | сда | **сд**виг по **а**дресу | сдвиг логический по адресу |
| 037 | NTR | N To R | ржа | **р**е**ж**им по **а**дресу | установка РР по адресу |
| 040 | ATI | A To I | уи | **у**становка **и**ндекса | запись кода в модификатор |
| 041 | STI | Stack To I: set index, pop | уим | **у**становка **и**ндекса **м**агазинная | запись кода в модификатор магазинная |
| 042 | ITA | I To A | счи | **сч**итывание **и**ндекса | выдача модификатора |
| 043 | ITS | I To Stack: push A, load index | счим | **сч**итывание **и**ндекса **м**агазинное | выдача модификатора магазинная |
| 044 | MTJ | M To J | уии | **у**становка **и**ндекса **и**ндексом | передача из модификатора в модификатор |
| 045 | J+M | J plus M | сли | **сл**ожение **и**ндексов | сложение модификаторов |
| 046 | — | — | соп | **с**пециальное **о**бращение к **п**амяти *(?)* | (special memory access; illegal) |
| 047 | — | — | э47 | **э**кстракод 47 | (illegal; a no-op trap in dispak) |

## Format 2 (bit 20 = 1), opcodes 20–37

Format-2 opcodes collide numerically with Format-1 020–037 and are
different instructions; Bemsh and Madlen tell them apart by the field
widths, and so does the bit layout.

| Op | Eng | English reading | Rus | Russian reading | ТО |
|---|---|---|---|---|---|
| 20, 21 | — | — | `э20`, `э21` | extracodes 0200/0210 | (extra system calls) |
| 22 | UTC | U To C | мода | **мод**ификация **а**дресом | префиксация адресом |
| 23 | WTC | W To C | мод | **мод**ификация (кодом из памяти) | префиксация кодом |
| 24 | VTM | V To M | уиа | **у**становка **и**ндекса **а**дресом | установка адреса на модификатор |
| 25 | UTM | add U(V) To M | слиа | **сл**ожение **и**ндекса с **а**дресом | сложение модификатора с адресом |
| 26 | UZA | to U if Zero A (ω) | по | **п**ереход по **о**меге / по нулю | условный переход «по нулю» сумматора |
| 27 | U1A | to U if 1 (not ω) A | пе | **п**ереход по **е**динице (не нулю) | условный переход «по не нулю» сумматора |
| 30 | UJ | U Jump | пб | **п**ереход **б**езусловный | безусловный переход |
| 31 | VJM | V Jump, link in M | пв | **п**ереход с **в**озвратом | переход с возвратом |
| 32 | IJ | Interrupt Jump (return) | выпр | **вы**ход из **пр**ерывания | (supervisor return) |
| 33 | STOP | STOP | стоп | **стоп**, останов | (halt; Madlen has no mnemonic, writes `,33,`) |
| 34 | VZM | to V if Zero M | пио | **п**ереход, **и**ндекс = **о** (ноль) | условный переход по нулю модификатора |
| 35 | V1M | to V if 1 (non-zero) M | пино | **п**ереход, **и**ндекс **н**е **о** | условный переход по не нулю модификатора |
| 36 | *36 | — | `дк 30,` / э36 | (Bemsh: long command, decimal opcode) | as VZM, plus a БРЗ flush in the original manual |
| 37 | VLM | to V, Loop on M | цикл | конец **цикл**а | конец цикла с увеличением модификатора |

UTM breaks the pattern: it adds V, not U, to M; the name keeps the
"U" of the long-address group.

## Instructions without a mnemonic

| Op | Status | How assemblers write it | Derived name |
|---|---|---|---|
| F1 032 | supervisor, no documented function | Madlen `*32`, Bemsh `кк 26,` | none: there is no function to name |
| F1 046 | illegal in all modes | Bemsh `соп` | English `SMA` (Special Memory Access) *(proposed)* |
| F1 047 | illegal / trap | `*47`, `э47` | keep the extracode form |
| F2 033 | halt | Madlen `,33,` | `STOP` / `стоп` exist in b6as and Bemsh |
| F2 036 | VZM with БРЗ flush | `*36`, `дк 30,`, `э36` | English `VZF` (V if Zero M, Flush) / Russian `пиоб` (пио + **б**уфер) *(proposed)* |

In Bemsh, `кк N,` (короткая команда) and `дк N,` (длинная команда),
with N the opcode **in decimal**, write any Format-1 or Format-2
instruction by number; disbesm6 uses them for the unnamed codes.

## Extracodes (Format 1 050–077)

Every assembler spells an extracode by number: Madlen `,*74,`, Bemsh
`э74`, b6as `$74`. In Диспак the effective address (in M[016] for the
handler) usually selects a sub-function, so one mnemonic per opcode
names only the family. The proposed names below are *(proposed)*.

| Op | Диспак function (dispak) | Proposed Eng | Proposed Rus |
|---|---|---|---|
| 050 | elementary functions by EA: 0 √, 1 sin, 2 cos, 3 arctg, 4 arcsin, 5 ln, 6 exp, 7 entier; also service functions (text decoder 012, conversions 014–017, user name 0104, …) | FUN | элф (элементарные функции) |
| 051 | sin (EA = 0) / cos (EA ≠ 0) | SIN | син |
| 052 | cos | COS | кос |
| 053 | events, time, asynchronous processes (010 time since midnight, 011 handler, 012 mask, …) | EVT | соб (события) |
| 054 | arcsin | ASIN | асин |
| 055 | ln | LN | лн |
| 056 | exp | EXP | эксп |
| 057 | entier (integer part) | ENT | цел |
| 060 | input from the job's input stream | INP | ввод |
| 061 | read the front-panel switches | SWR | пульт |
| 062 | job control: unconditional termination (0), stream requests (041 output stream) | JOB | упр |
| 063 | time: remaining job time and the like | TIM | время |
| 064 | formatted print | PRT | печ |
| 065 | system information (physical address, ПРЕДЕЛ …) | SYS | сист |
| 066 | call a standard program (СП) from the drum | SP | сп |
| 067 | debugging: watch and transfer points | DBG | отл |
| 070 | exchange with drums, discs, tapes (info word; "Э70") | XCH | обм |
| 071 | terminal I/O and card punch | TTY | терм |
| 072 | resources: release volumes, intercept addresses | RES | рес |
| 073 | (not handled by dispak; goes to the supervisor) | — | — |
| 074 | end of job | END | кон |
| 075 | store A at EA (special cases 0, 1) | — | — |
| 076 | (not handled by dispak) | — | — |
| 077 | trace switch (dispak extension) | TRC | трас |

The v7 Unix port reassigns several of these (for example 077 as the
system-call trap); see the extracode table in
`Besm6_Instruction_Set.md`.

## Notes on the uncertain expansions

- **AEX / нтж.** The ТО calls 012 «сравнение» (comparison): the result
  is zero exactly when A equals X. `нтж` is read as нетождественность,
  "non-identity", i.e. bitwise XOR; "E" may stand for "Exclusive" or
  "Equivalence".
- **ARX / слц.** «Циклическое сложение» (end-around-carry add); "R" is
  read as "ring" (cyclic), but no source spells it out.
- **AVX / знак.** Negate A if X is negative; the "V" has no documented
  expansion.
- **MOD / рег.** The English name collides with the Russian `мод`
  (WTC); Russian `рег` (регистры) describes the instruction better.
- **по / пе.** Usually explained as "переход по ω" and "переход по
  единице (не ω)"; the ТО names say "по нулю" / "по не нулю".
- **соп.** Only the name and "special memory access" are known; the
  expansion is a guess.

## ITM autocode (Автокод ИТМ)

The autocode writes a command as `[index] op [address]`, for example
`СЧЧА` (СЧ, address ЧА), `ЗЧА=ЗЧБ`, `4Э070=10ЗЧ`, `=12ПБ`. The
operation is a two-letter name, or `Э` plus an octal code. The 1969
manual lists the names in Appendix 3, but in the text copy that
appendix is only an image. The list below is taken from the
translator: table `ТКОП` in `f2a` (04456–04516), searched by `ИЩКОП`
(05224) through a hash of the letters [код].

Each table word holds two 24-bit entries, an 8-bit code and a 16-bit
name in ITM code. A Format-1 opcode is stored as is (000–045); a
Format-2 opcode is stored shifted left by 3 (0220–0370 = 022–037).
Readings follow the ТО operation names; the ones that don't match a
ТО word directly are marked *(?)*.

| Op | ITM | Reading | Bemsh | Eng |
|---|---|---|---|---|
| 000 | ЗЧ, ЗП | **з**апись **ч**исла; **з**а**п**ись | зп | ATX |
| 001 | ЗМ | **з**апись **м**агазинная | зпм | STX |
| 003 | СМ | **с**читывание **м**агазинное | счм | XTS |
| 004 | АС | **а**рифметическое **с**ложение | сл | A+X |
| 005 | АВ | **а**рифметическое **в**ычитание | вч | A-X |
| 006 | ОВ | **о**братное **в**ычитание | вчоб | X-A |
| 007 | МВ | вычитание **м**одулей (**м**одульное **в**ычитание) | вчаб | AMX |
| 010 | СЧ | **сч**итывание | сч | XTA |
| 011 | ЛУ | **л**огическое **у**множение | и | AAX |
| 012 | СР, ЛВ | **ср**авнение; **л**огическое **в**ычитание *(?)* | нтж | AEX |
| 013 | ЦС | **ц**иклическое **с**ложение | слц | ARX |
| 014 | ИЗ | **и**зменение **з**нака | знак | AVX |
| 015 | ЛС | **л**огическое **с**ложение | или | AOX |
| 016 | АД | **а**рифметическое **д**еление | дел | A/X |
| 017 | АУ | **а**рифметическое **у**множение | умн | A*X |
| 020 | СБ | **с**борка | сбр | APX |
| 021 | РБ | **р**аз**б**орка | рзб | AUX |
| 022 | ВЧ | **в**ыдача **ч**исла единиц | чед | ACX |
| 023 | ВН | **в**ыдача **н**омера старшей единицы | нед | ANX |
| 024 | СП | **с**ложение **п**орядка с кодом | слп | E+X |
| 025 | ВП | **в**ычитание из **п**орядка кода | вчп | E-X |
| 026 | СК | **с**двиг по **к**оду | сд | ASX |
| 027 | РК | установка **р**ежима по **к**оду | рж | XTR |
| 030 | ВР | **в**ыдача **р**ежима (РР) | счрж | RTE |
| 031 | МР | (выдача) **м**ладших **р**азрядов | счмр | YTA |
| 034 | КС | **к**оррекция порядка **с**ложением *(?)* | слпа | E+N |
| 035 | КВ | **к**оррекция порядка **в**ычитанием *(?)* | вчпа | E-N |
| 036 | СД, СD | **сд**виг (по адресу); also with Latin D | сда | ASN |
| 037 | РА | установка **р**ежима по **а**дресу | ржа | NTR |
| 040 | УИ | **у**становка **и**ндекса (запись в модификатор) | уи | ATI |
| 041 | УМ | **у**становка индекса **м**агазинная | уим | STI |
| 042 | ВИ | **в**ыдача **и**ндекса (модификатора) | счи | ITA |
| 043 | ВМ | **в**ыдача модификатора **м**агазинная | счим | ITS |
| 044 | ПИ | **п**ередача **и**ндекса (из модификатора в модификатор) | уии | MTJ |
| 045 | СИ | **с**ложение **и**ндексов | сли | J+M |
| 022 | ИА | **и**ндексация (префиксация) **а**дресом *(?)* | мода | UTC |
| 023 | ИК | **и**ндексация (префиксация) **к**одом *(?)* | мод | WTC |
| 024 | ПА | **п**ересылка **а**дреса на модификатор *(?)* | уиа | VTM |
| 025 | СА | **с**ложение модификатора с **а**дресом | слиа | UTM |
| 026 | У0 | **у**словный переход по **0** | по | UZA |
| 027 | У1 | **у**словный переход по **1** (не нулю) | пе | U1A |
| 030 | ПБ | **п**ереход **б**езусловный | пб | UJ |
| 031 | ПВ | **п**ереход с **в**озвратом | пв | VJM |
| 034 | И0 | переход по **и**ндексу (модификатору) = **0** | пио | VZM |
| 035 | И1 | переход по **и**ндексу ≠ 0 (**1**) | пино | V1M |
| 037 | КЦ | **к**онец **ц**икла | цикл | VLM |

The pattern: the first letter is the action (**С**ложение / **С**читывание,
**В**ычитание / **В**ыдача, **З**апись, **У**становка, **П**ереход /
**П**ередача, **Р**ежим), the second its object or kind (**Ч**исло,
**М**агазин, **И**ндекс, **А**дрес, **К**од, **П**орядок); for the
arithmetic group it is the other way round — the kind first
(**А**рифметическое, **Л**огическое, **Ц**иклическое, **О**братное,
**М**одулей), then the operation (**С**ложение, **В**ычитание,
**У**множение, **Д**еление). Digits 0/1 in `У0`, `У1`, `И0`, `И1` are
the branch conditions.

Not in the table: the supervisor instructions (002, 032, 033, F2 032,
033) and 046, 047, F2 036. These and the extracodes are written as `Э`
plus the code ("почти совпадающий с машинным", the manual says):
three digits give the Format-1 code (`Э074` → `00 074 0000`), two digits
the Format-2 code as is: `Э20ЧС=Э21ЧС,5Э32НАЧ=5Э33НАЧ` translates to
`00 20 00103 00 21 00103 05 32 00100 05 33 00100`, i.e. the Format-2
extracodes 0200/0210 and `выпр`/`стоп` [опыт].
