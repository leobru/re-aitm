# Транслятор с автокода ИТМ (АИТМ) с диска 2148, зоны 0406-0414
# (барабан 21 задачи = ЛЕНТ 40(2148) со сдвигом 0400).
DISBESM6 ?= $(HOME)/git/leobru/dispak-tools/disbesm6
export DISBESM6
PARTS := $(shell grep -v '^\#' parts.txt | awk '{print $$1}')
ZONES := $(shell grep -v '^\#' parts.txt | awk '{for (i = 4; i <= NF; i++) { sub(/\..*/, "", $$i); print $$i }}' | sort -u)
LIBJOBS := lib1 lib2 lib3 lib4 lib5 lib6
SBJOBS := sb1 sb2 sb3 sb4 sb5
JOBS  := aitm w1 w2 w3 w5 keys macro macro2 macro3 macro4 corr corr1 corr2 corr3 corr4 corr5 corr6 corr7 corr8 dbg dbge dbgx errs sect hex lfld rnoa lname punch comm rerr bib tape flist fsb ext1 ext2 $(LIBJOBS) $(SBJOBS)

all: check

# Зоны с диска 2148
zones: $(addprefix zones/,$(addsuffix .bin,$(ZONES)))
zones/%.bin:
	@mkdir -p zones
	besmtool dump 2148 --start=$* --length=1 --to-file=$@ > /dev/null

# Трасса t2 -> покрытие по секторам зон (traces/ИМЯ.cov/ЗЗЗЗ.С.cov)
traces: $(addprefix traces/,$(addsuffix .ev,$(JOBS)))
traces/%.ev: jobs/%.b6
	@mkdir -p traces
	tools/trace.sh $< traces/$*.txt | tools/phases.py - traces/$*.cov > $@

# Библиотека модулей (ключ Р, ЛЕНТ 67): цепочка заданий над одним томом,
# libN начинает с тома libN-1; traces/libN.vol - том после задания,
# traces/libN.lib - его разбор.  Зоны 0414.0-2 на 2148 нулевые: ЗАВЕР (lib6)
# проходит по ним в данные z14, это покрытие не учитывается.
traces/lib%.ev: jobs/lib%.b6
	@mkdir -p traces
	VOLIN=$(VOLIN) VOLOUT=traces/lib$*.vol tools/trace.sh $< traces/lib$*.txt | tools/phases.py - traces/lib$*.cov > $@
	rm -f traces/lib$*.cov/0414.*.cov
	tools/vol.py traces/lib$*.vol > traces/lib$*.lib
traces/lib%.ev: VOLIN = $(patsubst %.ev,%.vol,$(filter traces/%.ev,$^))
traces/lib2.ev: traces/lib1.ev
traces/lib3.ev: traces/lib2.ev
traces/lib4.ev: traces/lib3.ev
traces/lib5.ev: traces/lib4.ev
traces/lib6.ev: traces/lib5.ev

# Библиотека текстов (ключ Л, разделы Б;, ЛЕНТ 30): sb1 начинает с
# обнулённого тома (на незаписанном томе каталог - заполнитель 2525...),
# sb2 - с тома sb1, sb3-sb5 - с тома sb2.
traces/zero.vol:
	@mkdir -p traces
	python3 -c "open('$@', 'wb').write(bytes(8256 * 12))"
traces/sb%.ev: jobs/sb%.b6
	@mkdir -p traces
	VOLIN=$(VOLIN) VOLOUT=traces/sb$*.vol tools/trace.sh $< traces/sb$*.txt | tools/phases.py - traces/sb$*.cov > $@
traces/sb%.ev: VOLIN = $(patsubst %.ev,%.vol,$(filter traces/%,$^))
traces/sb1.ev: traces/zero.vol
traces/sb2.ev: traces/sb1.ev
traces/sb3.ev traces/sb4.ev traces/sb5.ev: traces/sb2.ev

# Ключ Ф: блок 1 в библиотеку на обнулённом томе как ЛЕНТ 31(-ЗП);
# fsb берёт его оттуда же как ЛЕНТ 30 разделом Б;
traces/flist.ev: jobs/flist.b6 traces/zero.vol
	VOLIN=traces/zero.vol VOLOUT=traces/flist.vol tools/trace.sh $< traces/flist.txt | tools/phases.py - traces/flist.cov > $@
traces/fsb.ev: jobs/fsb.b6 traces/flist.ev
	VOLIN=traces/flist.vol tools/trace.sh $< traces/fsb.txt | tools/phases.py - traces/fsb.cov > $@

# Раздел Э; под ключом Р: литералы и записи ссылок в модуле (traces/ext1.lib)
traces/ext1.ev: jobs/ext1.b6
	VOLOUT=traces/ext1.vol tools/trace.sh $< traces/ext1.txt | tools/phases.py - traces/ext1.cov > $@
	tools/vol.py traces/ext1.vol > traces/ext1.lib

# Зона 0414 (связывающий загрузчик) с пробой (tools/mkz14.py) на копии 2148:
# lib6 (с А) и lib6n (без А) на томе lib5; проба читает входы загрузчика
# и кончает Э74.  Не в JOBS: покрытие частей не учитывает пробу.
traces/z14mock.2148: tools/mkz14.py
	@mkdir -p traces
	tools/mkz14.py $@
traces/z14p.ev: jobs/lib6.b6 traces/lib5.ev traces/z14mock.2148
traces/z14pn.ev: jobs/lib6n.b6 traces/lib5.ev traces/z14mock.2148
traces/z14p.ev traces/z14pn.ev:
	VOL2148=traces/z14mock.2148 VOLIN=traces/lib5.vol tools/trace.sh $< $(@:.ev=.txt) > $(@:.ev=.log)
	tools/phases.py $(@:.ev=.log) > $@
	tail -2000 $(@:.ev=.log) > $(@:.ev=.tr)
	rm -f $(@:.ev=.log)

# Части (parts.txt): образ, покрытие, сырой вывод disbesm6
parts: zones traces
	tools/parts.py

# Размеченные исходники из notes/ЧАСТЬ.py (остальные части - сырой вывод)
be:
	tools/mkbe.py $(basename $(notdir $(wildcard notes/*.py)))

# Обратная сборка каждой части и побайтное сравнение
check:
	@tools/reasm.pl $(addprefix parts/,$(addsuffix .be,$(PARTS)))

clean:
	rm -f 2222 parts/*.new parts/*.b6 parts/*.lst

.PHONY: all zones traces parts be check clean
