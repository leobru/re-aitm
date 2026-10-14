import sys, re, collections
# track which source fills each 256-word sector of 0..07777, attribute executed PCs
src=['img']*32          # initial: whatever the deck/loader put
cov=collections.defaultdict(set)   # source -> set of addrs
seq=[]
on=False; n=0
for line in sys.stdin:
    if len(line)<7 or line[5] not in ':;' or not line[:5].isdigit(): continue
    a=int(line[:5],8); n+=1
    parts=line.split()
    op=parts[1]
    if op=='*70':
        m=re.search(r'\(=([0-7]{16})\)',line); w=int(m.group(1),8)
        l=w>>24; r=w&0xffffff
        lreg=l>>20; lop=(l>>12)&0o177; laddr=l&0o7777
        if lop>=0o100: pass
        rop=(r>>12)&0o177; raddr=r&0o7777
        read=bool(lop&0o10); phys=bool(lop&4)
        page=(laddr&0o3700)<<4
        unit=rop
        zone=raddr&0o37 if unit<0o30 or unit>=0o70 else raddr&0o7777
        if read:
            if lreg&8:
                sec=(raddr>>6)&3; dst=page+(laddr&3)*256
                tag='%s%02o:%o.%d'%('P' if phys else 'u',unit,zone,sec)
                if dst<0o10000: src[dst//256]=tag
                seq.append((n,'%05o'%a,'%06o'%dst,tag))
            else:
                for s in range(4):
                    if page+s*256<0o10000: src[(page+s*256)//256]='%s%02o:%o.%d'%('P' if phys else 'u',unit,zone,s)
                seq.append((n,'%05o'%a,'%06o'%page,'%s%02o:%o'%('P' if phys else 'u',unit,zone)))
        continue
    if a<0o10000:
        cov[src[a//256]].add(a)
for x in seq: print('LOAD',*x)
for k,v in sorted(cov.items()):
    print('COV',k,len(v),'%05o-%05o'%(min(v),max(v)))
import pickle; pickle.dump(dict(cov),open(sys.argv[1],'wb'))
