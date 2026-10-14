# Virtual memory of the ITM autocode translator (2148)

The translator keeps its text, the program being built and most of its
tables in a **virtual address space** on the task's drums. The resident
(`aitm0`) contains a small pager, `ОБМЕН` (00014). It moves words
between core and virtual addresses through four 256-word windows at
02000–03777. Everything here is about the 2148 build.

Evidence marks as in [README.md](README.md): **[трасса]** — seen in an
instruction trace, **[опыт]** — seen in a test job's output, **[код]** —
read from the code only, **[вывод]** — follows from the code but not
checked. Addresses are octal. Virtual addresses are written `vNNNNNN`.
The traces are full `t2` traces (`tools/trace.sh`) of the jobs `w3`,
`aitm`, `keys`, `dbg`, `ext1`, `lib6` and `z14pn`, scanned for every
entry to 00014 and every Э70.

## Address space

A virtual address has 18 bits. It is a position in the space of the
logical drums 020–027, each 040 tracts (zones) of 1024 words, and each
tract four sectors of 256 words [код, трасса]:

| Bits of the virtual address | Meaning |
|---|---|
| 1–8 | word in the page (sector) |
| 9–10 | sector in the tract |
| 11–15 | tract |
| 16–18 | drum − 020 |

So `v = (drum − 020) · 0100000 + tract · 02000 + word in tract`. For
example, v060000 is drum 020 tract 030, v300000 is drum 023 tract 0, and
v160100 is drum 021 tract 030 [трасса]. A page is one sector, 0400
words. The page number `v >> 8` is what the pager keeps in its tags.

The pager's exchanges are logical, without the physical-exchange bit.
So its drum 021 is the task's own scratch drum, not the 2148 volume
behind `ФИЗО МБ21` [код, dispak `ddio`].

**Direct range.** v040000–v057777 does not go through the windows. It
is core 010000–027777 (`v − 030000`), copied word by word [код,
трасса]. This is how phase 2 reaches its fixed tables through the same
calls: the name table at 010000 (v040000), the literals at 023000
(v053000) and the forward-reference table at 024000 (v054000).

### Map

| Virtual | Drum: tract | Contents | Evidence |
|---|---|---|---|
| v000006 … | 020:0 | the main module with its 2-word header (013776 …), written by `ЗАВЕР` with key `Р` without `А` | [трасса z14pn] |
| v001000–v005777 | 020:0.2–2.3 | relocation scale (`ОТМЕТ`, `ВЫВМ`); cleared at the start of phase 2 when key `Р` is given | [трасса lib6, ext1] |
| v006000 … | 020:3 | pairs (literal text, literal number) for `Н=` names of `Э;`; `ВЫВМ` puts them back into 023000 | [трасса ext1] |
| v010000 … | 020:4 | reference records (`ЗПКОМ`, `ЛИТПУЛ`) | [трасса ext1] |
| v035000 … | 020:016.2 | key `Р` block: 06470 words copied from 010000 at the closing `!` (f1a 05164) | [трасса lib6] |
| v036000–v037777 | 020:017 | not paged: `БАРАБ` keeps the МЛ30 catalogue here with its own Э70 ([LIBRARY.md](LIBRARY.md)) | [код] |
| v040000–v057777 | — | core 010000–027777 (direct range) | [трасса] |
| v060000–v157777 | 020:030 – 021:027 | the program: program address `a` is at `v060000 + a` (v060010 is address 010, v157777 is 077777) | [трасса] |
| v160000 … | 021:030 … | in passes 2 and 3 (key `О`), one word per program address: text position and counter (`СВЯЗЬ`, f2a 05256) | [трасса dbg] |
| v300000 … | 023:0 | the source text, as the deck's loader wrote it | [трасса] |

The program's pages are whole tracts: page `k` of the program
(addresses `k · 02000 …`) is tract 030 + `k` of drum 020, continuing into
drum 021 after tract 037.

## The exchange word (00712, `СЛОБМ`)

| Bits | Meaning |
|---|---|
| 1–15 | core address |
| 16–29 | number of words |
| 30–47 | virtual address |
| 48 | 1 — read (virtual → core), 0 — write |

Examples: `0164000001010000` writes 010 words from 010000 to v035000.
`0260000000100631` writes cell 0631 to v054000 (direct range) [трасса].

The fields are taken apart with `рзб` (unpack) by the masks
`0000177777737777` (direct range) and `4017770037737777` (paged), at
00013 and 01147. The direct-range test is `(word >> 40) & 0174 = 010`,
that is, virtual bits 14–18 = 00100 [код].

## The pager, `ОБМЕН` (00014–00111)

Call: put the word in 00712 and `ПВ ОБМЕН(М1)` (or set М1 and `ПБ ОБМЕН`).
М1–М4 are saved in 00702–00705 and restored; М16 is not. On return the
accumulator holds the last word moved [код, трасса].

For the paged range, word by word:

1. Split the address into page (00711) and word in page (00710).
2. Look for the page among the four tags 00670–00673.
3. **Miss:** first refresh the LRU stamps of the two pinned text pages
   (00676, 00677; see below), so that they look newest. Then take the
   window with the oldest stamp. If its dirty flag is set, write it back
   (`ЛСТБАР` with `D00150`, a sector write). Clear the flag, set the tag
   and read the new page (`ЛСТБАР` with `D00144`, a sector read). A page
   is read even when it is about to be fully overwritten.
4. **Hit (or after the read):** stamp the window with the clock 00674 + 1.
   Copy words between core and window, and set the dirty flag on a write.
   When the transfer crosses the end of the page, go on with the next
   page from step 2. So one call can move any number of words, e.g.
   05000 words in phase 2 [трасса lib6].

The window whose tag is in 00673 + М4 (М4 = −3 … 0) is at
`02000 + (М4 & 3) · 0400`:

| Tag | LRU stamp | Dirty | Window |
|---|---|---|---|
| 00670 | 00660 | 00664 | 02400 |
| 00671 | 00661 | 00665 | 03000 |
| 00672 | 00662 | 00666 | 03400 |
| 00673 | 00663 | 00667 | 02000 |

A tag of −1 means empty. The windows start with zone 0407, which the
loader reads there. Its contents are not used as pages, and the tags are
all −1 [код; README «Карта загрузки»].

### Drum exchange, `ЛСТБАР` (00112–00141)

`ЛСТБАР` builds the Э70 word from the window's tag. The word is a sector
exchange with the window's quarter of page 02000 and the drum, tract and
sector from the page number, e.g. `4010010300200030` reads drum 020
tract 030 sector 0 into 03400. Return is by М3 [трасса].

**First touch of a tract.** Before the first sector exchange with a
tract, `ЛСТБАР` writes the whole tract from core 0–01777 (the resident)
by a separate Э70, and marks the tract in the scale 00151–00160 (bit
`tract & 037` of word `00151 + (tract >> 5)`, counting tracts of drums
020–027 from 0). Examples: `0000000000200030` (tract 020:030) and
`0000000000200016` [трасса]. A never-written virtual address therefore
reads as a word of the resident, not as 0. That is why phase 2 clears
v001000–v005777 itself (below). Why the tract is written first at all
is not known [вывод: perhaps a sector read of a never-written tract
fails on the real drums].

Phase 1 (`НАЧФ1` through `БИТ`, f1a 04710) marks the text tract 023:0 in the scale
beforehand, so the text is not overwritten [трасса w3, aitm].

### Entry points

| Address | Name | Does |
|---|---|---|
| 00454 | `ЗПВ0` | write cell 0630 to the virtual address in the accumulator |
| 00556 | `ЗПВ1` | write cell 0631 likewise |
| 00557 | `ОБМВ` | take the whole exchange word from the accumulator |
| 00560 | `ЧТВ1` | read the word at the address in the accumulator into 0631 |
| 00571, 00572 | `ЧТВС`, `ЗПВС` | `ЧТВ1`, `ЗПВ1` at the address + 1 |
| 01652 | `ОБМ13` | exchange at the address + (М13), then load (М17) (`f2c`) |
| f2a 05630 | `ОБМЕНМ` | build the word from М13 (count), М14 (virtual), М15 (core) |

The one-word routines put the address into bits 30–47 (`сда 64-29`) and
add `00100630`, `00100631` or `4000000000100631` (count 1, cell, read)
[код].

## Pinned text pages

Text is read a letter at a time, so the reader does not call the pager
for every word. `НЛИТ` (00223) keeps the virtual base of the current
text page in 00676 and the window offset in 00700, and reads the word
directly as `мод 00700; сч (М17)`. The text pointer holds the virtual
word address from bit 25 and the letter shift in the low bits. Only when
the pointer moves to another page does it look up the tags, and on a
miss call `ЧТВ1` once to bring the page in [код, трасса]. The phase-1
editor's writer `ЗПЛИТ1` (f1a 04641) does the same for its output
pointer with 00677/00701, and sets the window's dirty flag itself. The
edited text goes back over the same pages at v300000 … [трасса].
`ФАЗА2` sets 00677 to 0 [код].

Because the pager refreshes these two pages' stamps before it picks a
victim, they stay in core while other pages come and go [код].

## Life of the virtual memory in a job

1. **Deck loader.** `Э70 4245` writes core 020000–021777 (the text read
   by `В 20000`) to drum 023 tract 0, which is v300000 [трасса].
2. **Phase 1.** The text is read and edited in place through the pinned
   pages. With key `Р` and a `(` list, the block at 010000 goes to
   v035000 at the closing `!` (see [LIBRARY.md](LIBRARY.md), "Linking
   loader") [трасса lib6].
3. **Phase change** (`ФАЗА2`, 01607). The windows and their tags stay as
   they are; the pager is resident. With key `Р` (06502 ≠ 0), core
   010000–014777 is cleared and written to v001000–v005777, so the scale
   starts as zeros. That is 12 pages through the 4 windows, so every
   page written in phase 1 except the pinned text page is on the drum
   by then [трасса lib6; вывод for other jobs].
4. **Phase 2.** The program goes to v060000 + address. The scale,
   reference records and `Н=` pairs go to their areas. Tables in core
   010000–027777 are reached directly or through the direct range. Each
   pass re-reads the text, e.g. 9 times for each text page in `aitm`
   [трасса].
5. **End**, in one of three ways:
   - **No key `Р`** (`ФИНАЛ`, f2a 05302): put one word (05317) at program
     address 6. Write back every dirty window (loop over 00055 with М3 =
     05305). Copy the starter `ПУСКЗ` to 1–031 and jump to 1. The starter
     reads every program page marked in the bit mask 0656 from drum 020
     tract 030 + `k`, page 0 last, and starts the program. The tract
     field begins at 07770, so adding 1 after 07777 carries into the drum
     number: tract 037 of drum 020 is followed by tract 0 of drum 021
     [трасса w3, aitm].
   - **Key `Р` without `А`** (`ЗАВЕР`, 06506): write the header and module
     (013776 …) to v000006, write back every dirty window (06515–06516),
     then Э74 or the linking loader [трасса z14pn].
   - **Key `Р` with `А`** (`КОНВЫВ` → 06517): the module goes to volume
     067. The windows are **not** written back before Э74 or the jump to
     the loader. In `lib6` at that point all four windows are dirty:
     v060000, v005400, v001000 (program and scale) and v300000 (text)
     [трасса lib6].

The drums are scratch: nothing in the virtual memory is kept after the
job.

## What the linking loader can find

Zone 0414 is read over page 0, which holds the pager and its tags. The
windows at 02000–03777 survive, but nothing tells the loader which pages
they hold. What is reliably on the drums [трасса lib6, z14pn; вывод for
the general case]:

- the key `Р` block at v035000 = drum 020 tract 016, words 01000 …
  (sector 2). Step 3 above always pushes it out, since key `Р` is given;
- without `А`, the main module at v000006 (drum 020 tract 0, words 6 …)
  and everything else, since `ЗАВЕР` writes back all windows first;
- with `А`, the module is on volume 067 and in core at 014000, but the
  program image and scale pages last used are only in the windows.

## Open

- Programs whose image reaches drum 021 (addresses ≥ 020000) and texts
  longer than one tract were not traced.
- `ВЫГР` (01667) reads program pages through the pager and writes them
  out with Э70 by the word in 0631, up to the zone in 0630. It has not
  run in any job, so its purpose and caller are unknown [код].
- v000000–v000005 and v020000–v034777 were not seen in use.
- Overflow of the LRU clock 00674 was not looked at.
