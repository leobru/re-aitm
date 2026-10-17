# Транслятор с автокода ИТМ (АИТМ) с диска 2048, зоны 055-060: старая
# сборка в одну загрузку (колода читает ЛЕНТ 40(2048) в 0-07777).
# Инструменты - общие, из ../tools; задания jobs/*.b6 - задания 2148,
# переведённые ../tools/to2048.py.
DISBESM6 ?= $(HOME)/git/leobru/dispak-tools/disbesm6
export DISBESM6
# phases.py: код читается с ЛЕНТ 40 без сдвига, обмен не физический
export AITM_UNIT = 40
export AITM_OFFSET = 0
export AITM_PHYS = 0
export AITM_VOL = 2048
# после ФИНАЛ (04520) в 1-5 исполняется скопированный загрузчик пуска
export AITM_FINAL = 4520
T := ../tools
PARTS := $(shell grep -v '^\#' parts.txt | awk '{print $$1}')
ZONES := $(shell grep -v '^\#' parts.txt | awk '{for (i = 4; i <= NF; i++) if ($$i !~ /^-/) { sub(/\..*/, "", $$i); print $$i }}' | sort -u)
LIBJOBS := lib1 lib2 lib3 lib4 lib5 lib6
SBJOBS := sb1 sb2 sb3 sb4 sb5
OWNJOBS := macro2n lpun5 ltape errs2 txtcore errs3 errs4 glob dbg2 dbg3 dbg4 \
	corr9 corr10 corr11 corr12 corr13 lfld2 dbg5 end55 dock
JOBS  := aitm $(OWNJOBS) w1 w2 w3 w5 keys corr1 corr2 corr3 corr4 corr5 corr6 corr7 corr8 dbg dbge dbgx errs sect hex lfld rnoa lname punch comm bib tape flist fsb ext1 ext2 $(LIBJOBS) $(SBJOBS)

all: check

# Задания 2148 -> 2048; OWNJOBS - свои (macro2n: macro2 без ключей С и М;
# lpun5: перфорация текста Л05, с печатью; ltape: Л10, -
# текст на ленту 30; errs2: ошибки 32 и 37 по Приложению 4 руководства;
# txtcore: вход в 010 с A = 06776 + N, текст в памяти с 07000).
# Задания покрытия - колоды из jobs/ИМЯ.itm (./covtry.sh jobs/ИМЯ.itm делает
# колоду и показывает прирост): errs3, errs4 - ошибки 04 10 13 14 17 21 30 31
# 35, 27 и операнды; glob - генеральные имена, комментарий, Т;, Л;; dbg2 -
# прокрутка, интервалы со смещением; dbg3, dbg4 - ошибки 72, 74 заголовка
# прокрутки; corr9-corr13 - ошибки 45, 44, 51, 46, 42 заголовка исправления;
# lfld2 - поля Л; со ссылками вперед; dbg5 - ошибка 71 (Э070 на барабан при
# прокрутке); end55 - знак после последнего Е; (ошибка 55); dock - aitm с
# М4 = 010001 при входе (разряд 13 - стыковка, 05550-05574)
jobs: $(addprefix jobs/,$(addsuffix .b6,$(filter-out $(OWNJOBS),$(JOBS))))
jobs/%.b6: ../jobs/%.b6 $(T)/to2048.py
	$(T)/to2048.py $< > $@

# Зоны с диска 2048
zones: $(addprefix zones/,$(addsuffix .bin,$(ZONES)))
zones/%.bin:
	@mkdir -p zones
	besmtool dump 2048 --start=$* --length=1 --to-file=$@ > /dev/null

# Трасса t2 -> покрытие по секторам зон (traces/ИМЯ.cov/ЗЗЗЗ.С.cov)
traces: $(addprefix traces/,$(addsuffix .ev,$(JOBS)))
traces/%.ev: jobs/%.b6
	@mkdir -p traces
	$(T)/trace.sh $< traces/$*.txt | $(T)/phases.py - traces/$*.cov > $@

# Библиотека модулей (ключ Р, ЛЕНТ 67): цепочка, как на 2148
traces/lib%.ev: jobs/lib%.b6
	@mkdir -p traces
	VOLIN=$(VOLIN) VOLOUT=traces/lib$*.vol $(T)/trace.sh $< traces/lib$*.txt | $(T)/phases.py - traces/lib$*.cov > $@
traces/lib%.ev: VOLIN = $(patsubst %.ev,%.vol,$(filter traces/%.ev,$^))
traces/lib2.ev: traces/lib1.ev
traces/lib3.ev: traces/lib2.ev
traces/lib4.ev: traces/lib3.ev
traces/lib5.ev: traces/lib4.ev
traces/lib6.ev: traces/lib5.ev

# Библиотека текстов (ключ Л, разделы Б;, ЛЕНТ 30): цепочка, как на 2148
traces/zero.vol:
	@mkdir -p traces
	python3 -c "open('$@', 'wb').write(bytes(8256 * 12))"
traces/sb%.ev: jobs/sb%.b6
	@mkdir -p traces
	VOLIN=$(VOLIN) VOLOUT=traces/sb$*.vol $(T)/trace.sh $< traces/sb$*.txt | $(T)/phases.py - traces/sb$*.cov > $@
traces/sb%.ev: VOLIN = $(patsubst %.ev,%.vol,$(filter traces/%,$^))
traces/sb1.ev: traces/zero.vol
traces/sb2.ev: traces/sb1.ev
traces/sb3.ev traces/sb4.ev traces/sb5.ev: traces/sb2.ev

# Л10,: текст на обнулённый том ленты 30
traces/ltape.ev: jobs/ltape.b6 traces/zero.vol
	VOLIN=traces/zero.vol VOLOUT=traces/ltape.vol $(T)/trace.sh $< traces/ltape.txt | $(T)/phases.py - traces/ltape.cov > $@

traces/flist.ev: jobs/flist.b6 traces/zero.vol
	VOLIN=traces/zero.vol VOLOUT=traces/flist.vol $(T)/trace.sh $< traces/flist.txt | $(T)/phases.py - traces/flist.cov > $@
traces/fsb.ev: jobs/fsb.b6 traces/flist.ev
	VOLIN=traces/flist.vol $(T)/trace.sh $< traces/fsb.txt | $(T)/phases.py - traces/fsb.cov > $@

# Части (parts.txt): образ, покрытие, сырой вывод disbesm6
parts: zones traces
	$(T)/parts.py

# Размеченные исходники из notes/ЧАСТЬ.py
be:
	$(T)/mkbe.py $(basename $(notdir $(wildcard notes/*.py)))

# Обратная сборка каждой части и побайтное сравнение
check:
	@$(T)/reasm.pl $(addprefix parts/,$(addsuffix .be,$(PARTS)))

clean:
	rm -f 2222 parts/*.new parts/*.b6 parts/*.lst

.PHONY: all jobs zones traces parts be check clean
