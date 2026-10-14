# ITM character encoding

The ITM code (Автокод ИТМ) is an 8-bit encoding of the МТК-2 teletype code with the shift states flattened into the code itself. The low 5 bits are the МТК-2 key, read with bit 1 as the most significant bit. The high bits say which register (Latin, Russian or figures) the key was in, and digits get their own binary codes.

The full per-code table is in `itm-encoding.txt`.

## Where the table comes from

The mapping was decoded from the OS's own GOST-to-ITM conversion table `ИТАБЛ` in `re-dispak/v6v7.be` (16 words plus the word `ИТАБ`) and then inverted.

- The lookup is done in the routine labelled `ПРИ4Д`–`ПРИ4К`.
- Each table word holds six 8-bit codes. A GOST code c < 0140 is found at byte (c mod 6), counted from the right, of word (c div 6). The byte is selected with `СБР КОНСБР+k` and `СДА 64+40`.
- GOST codes 0172–0177 use the word `ИТАБ = 2007336661140`.
- The decode is consistent: digits map to themselves and every letter falls in the expected block.

Each row of `itm-encoding.txt` also shows dispak's `itm_to_gost` result and the МТК-2 key for that position.

## Structure

Here x is the МТК-2 key code with bit 1 as the high bit.

| ITM range | Meaning |
|---|---|
| 000–011, 017 | Binary digits 0–9, and 017 is a space |
| 040 + x | Figures register |
| 0140 + x, 0134–0137 | Extra symbols and control codes |
| 0200 + x | Latin register |
| 0300 + x | Russian register |

So bit 0200 means "letter", bit 0100 within a letter means "Russian register", and bit 040 means "figures".

## Comparison with МТК-2

### Latin, 0200 + x

This is an exact match. All 26 letters are at their ITA2 positions (T=01, E=020, A=030, and so on). The six unused codes in the block are exactly the МТК-2 control codes:

| ITM | МТК-2 control code |
|---|---|
| 0200 | Russian shift (blank) |
| 0202 | Carriage return |
| 0204 | Space |
| 0210 | Line feed |
| 0233 | Figures shift |
| 0237 | Latin shift |

### Cyrillic letters

These follow a visual rule rather than МТК-2's phonetic one.

- **Look-alikes share the Latin code.** А В Е К М Н О Р С Т У Х are encoded as the Latin letters that look the same. So В is 0223 (Latin B), whereas in МТК-2 В is on W. Likewise Н is on Latin H (МТК-2 puts Х there), Р on P, С on C, У on Y and Х on X. Text was evidently printed by shape, not by sound.
- **The rest keep their МТК-2 Russian positions** under 0300: Б Г Д Ж З И Й Л П Ф Ц Ы Ь Я.
- **Five letters move.** In МТК-2, Э Ш Щ Ю are in the figures register (on F G H J), and Ч shares the "4" key (R). ITM moves them into Russian slots freed by the look-alikes:

  | Letter | МТК-2 position | ITM key | ITM code |
  |---|---|---|---|
  | Э | figures F | E | 0320 |
  | Ш | figures G | S | 0324 |
  | Щ | figures H | T | 0301 |
  | Ю | figures J | U | 0334 |
  | Ч | figures R (shared with 4) | W | 0331 |

  The pairing is partly mnemonic: Э resembles E, Ш and Щ sit on the neighbouring S and T, and Ю is pronounced "yu". Why Ч went to W is not clear; this explanation is a guess, not documented.
- **Empty slots.** The Russian-block slots for A, H, K, M, N, O and R (0330, 0305, 0336, 0307, 0306, 0303, 0312) stay empty.

### Figures, 040 + x

Ten symbols are at their МТК-2 places: `, . ) : = + ‘ / - (`. The other positions are reused.

- **Digit keys.** Digits have their own binary codes, so the ten digit keys of the figures register are freed:

  | МТК-2 figure | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 0 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | Key | Q | W | E | R | T | Y | U | I | O | P |
  | ITM code | 075 | 071 | 060 | 052 | 041 | 065 | 074 | 054 | 043 | 055 |
  | ITM symbol | ≡ | ∧ | ∨ | unused | ’ | ÷ | ⩽ | ⩾ | _ | ⊃ |

  The "4/Ч" slot (052) is never used, possibly because МТК-2 treats 4 and Ч as one character.
- **National-use keys.** The three positions ITA2 reserves for national use (F, G, H, which are Э Ш Щ in МТК-2) become `]` (066), `[` (053) and `;` (045).
- **Other keys.**
  - "?" on B becomes `!` (063); GOST has no `?`.
  - "Who are you" on D becomes `%` (062).
  - The bell on J becomes `×` (072).
- **Control-code slots.**

  | ITM | МТК-2 code at that position | ITM meaning |
  |---|---|---|
  | 040 | Blank / Russian shift | Space |
  | 042 | Carriage return | ◇ |
  | 044 | Space | `\|` |
  | 050 | Line feed | Overline ‾ |
  | 073 | Figures shift | Carriage return |
  | 077 | Latin shift | Unused |

### The 0140 block

This looks like an upper case of the figures keys.

| ITM | Key (МТК-2 figure) | Meaning |
|---|---|---|
| 0140 | Blank | End of information |
| 0142 | Carriage return | Set position |
| 0143 | O (9) | ↑ |
| 0145 | H (Щ) | ¬ |
| 0146 | N (,) | < |
| 0147 | M (.) | > |
| 0150 | Line feed | ― |
| 0152 | R (4) | ≠ |
| 0170 | A (-) | * |
| 0173 | Figures shift | End of line; also the repeat code |
| 0176 | K (() | ⏨ |

`<` and `>` sit on the comma and period keys, as on a typewriter.

GOST 0134–0137 (`" Ъ ° ′`) map to themselves (ITM 0134–0137). This may just mean "no ITM equivalent" rather than real ITM codes.

## Two-character input sequences

The terminal input routine (`ПРИ4И`/`ПРИ4К` in `v6v7.be`) glues two-character sequences that start with ':' into one ITM code:

| Input | ITM | Meaning |
|---|---|---|
| `:×` | 0140 | End of information |
| `::` | 0142 | Set position |
| `:>` | 0173 | End of line / repeat |
| `:<` | 073 | Carriage return |

A ':' followed by anything else is output as 056, and the next character is processed normally.

The ":×" sequence is very likely the `:х` terminator for `Т;` constants. The source comment there reads ":°", so the label conflicts with the code; this has not been tested in the emulator.

## Disagreements with dispak

Dispak's `itm_to_gost` (`dispak/encoding.c`) disagrees with the OS table in three ways.

**Approximations:**

| ITM | OS table | dispak |
|---|---|---|
| 054 | ⩾ | `>` |
| 074 | ⩽ | `<` |
| 060 | ∨ | `V` |
| 072 | × | Cyrillic `Х` |
| 0176 | ⏨ | `Е` |
| 0137 | ′ | `’` |
| 0150 | ― | `-` |

**Wrong symbols:**

| ITM | OS table | dispak |
|---|---|---|
| 055 | ⊃ | `°` |
| 065 | ÷ | `:` |
| 075 | ≡ | `‘` |

**Not decoded:** 073, 0136, 0140, 0142 and 0173.

Dispak's `gost_to_itm` also differs from the OS table at GOST 020, 024, 035, 036, 116, 117, 120, 124, 125, 131, 135–137 and 172–176.

## Sources

- `re-dispak/v6v7.be`: the `ИТАБЛ` table and the conversion routine.
- `re-dispak/kit.be`: the `КОНСБР` byte masks.
- `dispak/gost10859.h`: the meanings of GOST codes 0172–0176.
- МТК-2 tables:
  - [Wikipedia: МТК-2](https://ru.wikipedia.org/wiki/%D0%9C%D0%A2%D0%9A-2)
  - [Crypto Museum: MTK-2](https://www.cryptomuseum.com/ref/mtk2/)
  - ГОСТ 15607-70
