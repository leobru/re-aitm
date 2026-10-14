import sys, re
sys.path.insert(0,'/home/leob/.cursor/skills/besm6/scripts')
from decode import decode_24
d=open('zones-0406-0414.bin','rb').read()
Z=[int.from_bytes(d[i:i+6],'big') for i in range(0,len(d),6)]
def word(tag,a):
    z,s=tag[4:].split('.'); z=int(z,8); s=int(s)
    return Z[(z-6)*1024+s*256+(a%256)]
src=['img']*32; prev=None; half=0; bad={}; ok=0
for line in sys.stdin:
    if len(line)<7 or line[5] not in ':;' or not line[:5].isdigit(): continue
    a=int(line[:5],8); op=line.split()[1].lower()
    half = 1 if (a==prev and half==0) else 0; prev=a
    if op=='*70':
        w=int(re.search(r'\(=([0-7]{16})\)',line).group(1),8); l=w>>24; r=w&0xffffff
        lop=(l>>12)&0o177; laddr=l&0o7777; rop=(r>>12)&0o177; raddr=r&0o7777
        if lop&0o10:
            page=(laddr&0o3700)<<4; unit=rop; phys=lop&4
            zone=raddr&0o37 if unit<0o30 else raddr&0o7777
            p='P' if phys else 'u'
            if l>>20&8:
                dst=page+(laddr&3)*256
                if dst<0o10000: src[dst//256]='%s%02o:%o.%d'%(p,unit,zone,(raddr>>6)&3)
            else:
                for s in range(4):
                    if page+s*256<0o10000: src[(page+s*256)//256]='%s%02o:%o.%d'%(p,unit,zone,s)
        continue
    if a>=0o10000 or not src[a//256].startswith('P21'): continue
    w=word(src[a//256],a); ins=(w>>24) if half==0 else (w&0xffffff)
    m=decode_24(ins)['eng'].lower()
    if op.startswith('*'): op='$'+op[1:]
    if op==m or (op[0]=='$' and m[0] in '$e'): ok+=1
    else: bad.setdefault('%s %05o'%(src[a//256],a),set()).add((half,op,m))
print('ok',ok,'bad',len(bad))
for k in sorted(bad)[:30]: print(k,bad[k])
