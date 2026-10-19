# Загрузчик модулей ИТМ для зоны 0414 (zagr/parts/zagr.be, БЕМШ):
# make - сборка parts/zagr.new; ../traces/zagr.2148 - копия 2148 с ним
# (../tools/mkz14.py --image); проверки - make zagr в корне.
T := ../tools

all: parts/zagr.new

parts/zagr.new: parts/zagr.be macros.be
	$(T)/reasm.pl parts/zagr.be

clean:
	rm -f 2222 parts/*.new parts/*.b6 parts/*.lst parts/*.obj macros.lib

.PHONY: all clean
