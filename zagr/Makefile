# Загрузчик модулей ИТМ для зоны 0414 (zagr/parts/zagr.be, БЕМШ):
# make - сборка parts/zagr.new; ../traces/zagr.2148 - копия 2148 с ним
# (../tools/mkz14.py --image); проверки - make zagr в корне.
T := ../tools

all: parts/zagr.new

parts/zagr.new: parts/zagr.be macros.be
	$(T)/reasm.pl parts/zagr.be
	@end=$$(awk '/ФИНИШ/ {print $$1}' parts/zagr.be.lst); \
	if [ $$((0$$end)) -gt $$((02000)) ]; then \
	  echo "zagr: код до $$end, зона 0414 - 02000 слов"; rm -f $@; exit 1; fi

clean:
	rm -f 2222 parts/*.new parts/*.b6 parts/*.lst parts/*.obj macros.lib

.PHONY: all clean
