# Транслятор с автокода ИТМ (АИТМ) с диска 2148, зоны 0406-0414
# (барабан 21 задачи = ЛЕНТ 40(2148) со сдвигом 0400).
DISBESM6 ?= $(HOME)/git/leobru/dispak-tools/disbesm6
export DISBESM6
PARTS := $(shell grep -v '^\#' parts.txt | awk '{print $$1}')
ZONES := $(shell grep -v '^\#' parts.txt | awk '{for (i = 4; i <= NF; i++) { sub(/\..*/, "", $$i); print $$i }}' | sort -u)
LIBJOBS := lib1 lib2 lib3 lib4 lib5 lib6
SBJOBS := sb1 sb2 sb3 sb4 sb5
JOBS  := aitm w1 w2 w3 w5 keys macro macro2 macro3 macro4 corr corr1 corr2 corr3 corr4 corr5 corr6 corr7 corr8 dbg dbge dbgx errs sect hex lfld rnoa lname punch comm rerr bib tape flist fsb ext1 ext2 ext3 ext4 txt48 $(LIBJOBS) $(SBJOBS)

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

# Раздел Э; под ключом Р: литералы и записи ссылок в модуле (traces/ext1.lib);
# ext3 - внешние имена, ext4 - таблица входов и описатели полей Л; (AITM-object.md)
traces/ext1.ev traces/ext3.ev traces/ext4.ev: traces/%.ev: jobs/%.b6
	VOLOUT=traces/$*.vol tools/trace.sh $< traces/$*.txt | tools/phases.py - traces/$*.cov > $@
	tools/vol.py traces/$*.vol > traces/$*.lib

# Загрузчик (tools/itmload.py вместо утраченной зоны 0414): link1 кладёт
# в библиотеку подпрограмму ПЕЧ, link2 - главную программу ГЛАВ с внешними
# именами ПЕЧ и ДВА; связанная программа печатает ПРИВЕТ ВСЕМУ и дважды
# ПОКАЖИ ЛЮДЯМ (traces/link.txt), карта памяти - traces/link.map.
# Оверлеи: link3 кладёт ПЕЧБ с теми же входами ПЕЧ, ДВА и другими
# текстами; ГЛАВ(Л.ПЕЧ/Л.ПЕЧБ) - два сегмента с листа 02000, задание с
# сегментом 1 печатает тексты ПЕЧ (traces/ovl1.txt), с сегментом 2 - ПЕЧБ
# Запись связанной программы: link4 кладёт ГЛАВ2, которая вызывает ПЕЧ,
# читает сегмент 2 экстракодом Э70 по словам у внешнего имени СЕГ2 и
# снова вызывает ПЕЧ; itmload --store пишет ПРОГ = ГЛАВ2(Л.ПЕЧ/Л.ПЕЧБ)
# в traces/prog.vol, задание грузит корень и сегмент 1 (traces/prog.txt:
# ПРИВЕТ ВСЕМУ, ЗДРАВСТВУЙТЕ)
link: traces/link.txt traces/ovl1.txt traces/ovl2.txt traces/prog.txt
traces/link4.ev: jobs/link4.b6 traces/link3.ev
	VOLIN=traces/link3.vol VOLOUT=traces/link4.vol tools/trace.sh $< traces/link4.txt | tools/phases.py - traces/link4.cov > $@
traces/prog.txt: traces/link4.ev tools/itmload.py tools/vol.py
	tools/itmload.py 'РАК,ГЛАВ2(Л.ПЕЧ/Л.ПЕЧБ)!' traces/link4.vol --store ПРОГ traces/prog.vol > traces/prog.map
	tools/itmload.py 'ПРОГ!' traces/prog.vol -o traces/prog.b6 >> traces/prog.map
	tools/vol.py traces/prog.vol > traces/prog.lib
	cd traces && cp prog.vol 2222 && timeout -s KILL 60 dispak --path=.:$${BESM6_PATH:-/usr/local/share/besm6} prog.b6 > prog.txt; rm -f 2222
	grep -q 'ЗДРАВСТВУЙТЕ' $@
traces/link3.ev: jobs/link3.b6 traces/link2.ev
	VOLIN=traces/link2.vol VOLOUT=traces/link3.vol tools/trace.sh $< traces/link3.txt | tools/phases.py - traces/link3.cov > $@
traces/ovl%.txt: traces/link3.ev tools/itmload.py tools/vol.py
	tools/itmload.py 'РАК,ГЛАВ(Л.ПЕЧ/Л.ПЕЧБ)!' traces/link3.vol --seg $* -o traces/ovl$*.b6 > traces/ovl$*.map
	cd traces && timeout -s KILL 60 dispak ovl$*.b6 > ovl$*.txt
	grep -q '$(TEXT)' $@
traces/ovl1.txt: TEXT = ПОКАЖИ ЛЮДЯМ
traces/ovl2.txt: TEXT = ПРОЩАЙТЕ ВСЕ
traces/link1.ev: jobs/link1.b6
	@mkdir -p traces
	VOLOUT=traces/link1.vol tools/trace.sh $< traces/link1.txt | tools/phases.py - traces/link1.cov > $@
traces/link2.ev: jobs/link2.b6 traces/link1.ev
	VOLIN=traces/link1.vol VOLOUT=traces/link2.vol tools/trace.sh $< traces/link2.txt | tools/phases.py - traces/link2.cov > $@
	tools/vol.py traces/link2.vol > traces/link2.lib
traces/link.txt: traces/link2.ev tools/itmload.py tools/vol.py
	tools/itmload.py 'РАК,ГЛАВ(ПЕЧ)!' traces/link2.vol -o traces/link.b6 > traces/link.map
	cd traces && timeout -s KILL 60 dispak link.b6 > link.txt
	grep -q 'ПОКАЖИ ЛЮДЯМ' $@

# Загрузчик на БЕМШ (zagr/parts/zagr.be) в зоне 0414 копии 2148
# (traces/zagr.2148): задания zl1-zl5 переводят главный модуль с ключом
# Р и списком, ЗАВЕР передаёт управление загрузчику. traces/zlN.txt -
# печать, traces/zlN.zcmp - сверка памяти перед пуском с itmload
# (tools/memcmp.py). zl3 - нет модуля в каталоге, zl6 - главный модуль
# с входом НАЗ (03000).
ZLJOBS := zl1 zl2 zl3 zl4 zl5 zl6
zagr: $(addprefix traces/,$(addsuffix .zcmp,$(ZLJOBS))) traces/zs1.zscmp traces/zs2.zscmp traces/zs1.run
zagr/parts/zagr.new: zagr/parts/zagr.be
	$(MAKE) -C zagr
traces/zagr.2148: zagr/parts/zagr.new tools/mkz14.py
	@mkdir -p traces
	tools/mkz14.py $@ --image $<
traces/zl1.txt traces/zl1.zcmp: ZLVOL = traces/link1.vol
traces/zl1.txt traces/zl1.zcmp: ZLKEY = РАК,ГЛАВ(ПЕЧ)!
traces/zl1.txt: ZLTEXT = ПОКАЖИ ЛЮДЯМ
traces/zl2.txt traces/zl2.zcmp: ZLVOL = traces/link3.vol
traces/zl2.txt traces/zl2.zcmp: ZLKEY = РАК,ГЛАВ(Л.ПЕЧ/Л.ПЕЧБ)!
traces/zl2.txt: ZLTEXT = ПОКАЖИ ЛЮДЯМ
traces/zl3.txt traces/zl3.zcmp: ZLVOL = traces/link1.vol
traces/zl3.txt: ZLTEXT = ЗАГР: НЕТ МОДУЛЯ  НЕТУ
traces/zl4.txt traces/zl4.zcmp: ZLVOL = traces/link1.vol
traces/zl4.txt traces/zl4.zcmp: ZLKEY = РАК,СЛОЖН(ПЕЧ)!
traces/zl4.txt: ZLTEXT = ПРИВЕТ ВСЕМУ
traces/zl5.txt traces/zl5.zcmp: ZLVOL = traces/lib5.vol
traces/zl5.txt traces/zl5.zcmp: ZLKEY = РАК,ГЛ5(Л.ВТОР/Л.ТРЕТ+ВТОР/ВТОР+ПЕРВ)!
traces/zl5.txt: ZLTEXT = КОНЕЦ ЗАДАЧИ
traces/zl6.txt traces/zl6.zcmp: ZLVOL = traces/link1.vol
traces/zl6.txt traces/zl6.zcmp: ZLKEY = РАК,ГЛН(ПЕЧ)!
traces/zl6.txt: ZLTEXT = ПОКАЖИ ЛЮДЯМ
traces/zl1.txt traces/zl3.txt traces/zl4.txt traces/zl6.txt: traces/link1.ev
traces/zl2.txt: traces/link3.ev
traces/zl5.txt: traces/lib5.ev
traces/zl%.txt: jobs/zl%.b6 traces/zagr.2148
	VOL2148=traces/zagr.2148 VOLIN=$(ZLVOL) VOLOUT=traces/zl$*.vol tools/trace.sh $< $@ > /dev/null
	grep -q '$(ZLTEXT)' $@
traces/zl%.zcmp: traces/zl%.txt tools/itmload.py tools/memcmp.py
	if [ -n '$(ZLKEY)' ]; then \
	  tools/itmload.py '$(ZLKEY)' traces/zl$*.vol -o traces/zl$*.ref.b6 > /dev/null && \
	  VOL2148=traces/zagr.2148 VOLIN=$(ZLVOL) tools/memcmp.py jobs/zl$*.b6 traces/zl$*.ref.b6 > $@; \
	else echo 'без сверки' > $@; fi

# Запись в библиотеку (имя перед : в ключе, 010003): zs1 - ПРОГ =
# ГЛАВ2(Л.ПЕЧ/Л.ПЕЧБ), zs2 - три сегмента с ВТОР. Том после задания
# (traces/zsN.vol) сравнивается пословно с записью itmload --store на
# томе, где загрузчик не работал (проба z14mock): traces/zsN.zscmp.
# traces/zs1.run - записанная программа: ПРИВЕТ ВСЕМУ, затем сегмент 2
# по СЕГ2 - ЗДРАВСТВУЙТЕ
traces/zs1.zscmp: ZSVOL = traces/link3.vol
traces/zs1.zscmp: ZSKEY = РАК,ГЛАВ2(Л.ПЕЧ/Л.ПЕЧБ)!
traces/zs1.zscmp: ZSNAME = ПРОГ
traces/zs1.zscmp: traces/link3.ev
traces/zs2.zscmp: ZSVOL = traces/lib5.vol
traces/zs2.zscmp: ZSKEY = РАК,ГЛ5(Л.ВТОР/Л.ТРЕТ+ВТОР/ВТОР+ПЕРВ)!
traces/zs2.zscmp: ZSNAME = ПРГ5
traces/zs2.zscmp: traces/lib5.ev
traces/zs%.zscmp: jobs/zs%.b6 traces/zagr.2148 traces/z14mock.2148 tools/itmload.py tools/volcmp.py
	VOL2148=traces/zagr.2148 VOLIN=$(ZSVOL) VOLOUT=traces/zs$*.vol tools/trace.sh $< traces/zs$*.txt > /dev/null
	grep -q 'ЗАГР: ЗАПИСАНО' traces/zs$*.txt
	VOL2148=traces/z14mock.2148 VOLIN=$(ZSVOL) VOLOUT=traces/zs$*.pre tools/trace.sh $< > /dev/null
	tools/itmload.py '$(ZSKEY)' traces/zs$*.pre --store $(ZSNAME) traces/zs$*.ref > /dev/null
	tools/volcmp.py traces/zs$*.vol traces/zs$*.ref > $@
traces/zs1.run: traces/zs1.zscmp
	tools/itmload.py 'ПРОГ!' traces/zs1.vol -o traces/zs1run.b6 > /dev/null
	cd traces && cp zs1.vol 2222 && timeout -s KILL 60 dispak --path=.:$${BESM6_PATH:-/usr/local/share/besm6} zs1run.b6 > zs1.run; rm -f 2222
	grep -q 'ЗДРАВСТВУЙТЕ' $@

# Dogfooding: части, переписанные на автокод ИТМ (tools/be2itm.py ->
# itm/*.itm; нужны parts/*.be.lst и parts/*.bin - make parts check),
# транслируются самим АИТМ в библиотеку, zagr связывает и записывает их
# (АИТМЗ); traces/dog/cmp.txt - сверка записи с частями и с itmload
ITMPARTS := f1a f1b f2a f2b f2c
itm: itm/aitm.itm $(addprefix itm/,$(addsuffix .itm,$(ITMPARTS)))
itm/aitm.itm: parts/aitm0.be parts/aitm6.be tools/be2itm.py
	tools/be2itm.py aitm0 aitm6 -o $@
itm/%.itm: parts/%.be tools/be2itm.py
	tools/be2itm.py $* -o $@
dogfood: itm traces/zagr.2148 traces/z14mock.2148
	tools/dogfood.sh
# Нагрузка на zagr: 1400 имен, модуль длиннее 4 зон (tools/zstress.sh,
# traces/zst/cmp.txt)
zstress: traces/zagr.2148 traces/z14mock.2148
	tools/zstress.sh

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

.PHONY: all zones traces parts be check clean link zagr itm dogfood zstress
