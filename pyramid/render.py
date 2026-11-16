import math, random, subprocess, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DUR=1280,720,30,5
S=2; w,h=W*S,H*S
random.seed(4)
def lerp(a,b,t): return a+(b-a)*t
def mix(c1,c2,t): return tuple(int(lerp(a,b,t)) for a,b in zip(c1,c2))
def ease(t): t=max(0,min(1,t)); return 1-(1-t)**3
def back(t):
    t=max(0,min(1,t)); c=1.7; return 1+(c+1)*(t-1)**3+c*(t-1)**2
# palette
SK1,SK2,SK3=(34,22,84),(122,48,120),(255,134,92)
SUN=(255,214,102)
cx,gy=640*S,520*S
PW,PH=620*S,380*S
apex=(cx,gy-PH); L=(cx-PW//2,gy); R=(cx+PW//2,gy-14*S); F=(cx+30*S,gy+34*S)
LIT,DARK=(247,178,84),(184,98,76)
def face(img_size):
    lit=Image.new('RGBA',img_size,(0,0,0,0)); d=ImageDraw.Draw(lit)
    d.polygon([apex,L,F],fill=LIT+(255,))
    d.polygon([apex,F,R],fill=DARK+(255,))
    N=10
    for i in range(1,N):
        y=apex[1]+(gy+34*S-apex[1])*i/N
        for pts,col in (((apex,L,F),mix(LIT,(120,50,60),.28)),((apex,F,R),mix(DARK,(40,20,60),.3))):
            d.line([(0,y),(w,y)],fill=(0,0,0,0))
        # joint lines clipped later via mask
    return lit
base=face((w,h))
# joint lines drawn only inside faces
mask=Image.new('L',(w,h),0); md=ImageDraw.Draw(mask)
md.polygon([apex,L,F,R],fill=255)
lines=Image.new('RGBA',(w,h),(0,0,0,0)); ld=ImageDraw.Draw(lines)
N=10; top=apex[1]; bot=gy+34*S
for i in range(1,N):
    y=top+(bot-top)*i/N
    ld.line([(0,y),(w,y)],fill=(90,36,60,90),width=3*S)
    off=0 if i%2 else 30*S
    for x in range(-200*S,w,60*S):
        ld.line([(x+off,y),(x+off,y+(bot-top)/N)],fill=(90,36,60,60),width=2*S)
lines.putalpha(Image.composite(lines.split()[3],Image.new('L',(w,h),0),mask))
base=Image.alpha_composite(base,lines)
# background
bg=Image.new('RGB',(w,h)); bd=ImageDraw.Draw(bg)
for y in range(h):
    t=y/(gy)
    c=mix(SK1,SK2,t/0.6) if t<.6 else mix(SK2,SK3,min(1,(t-.6)/.4))
    bd.line([(0,y),(w,y)],fill=c)
stars=[(random.randint(0,w),random.randint(0,int(h*.45)),random.uniform(1,3.2)*S,random.random()*6) for _ in range(70)]
def dune(d,y0,amp,ph,col,wl):
    pts=[(0,h)]+[(x,y0+amp*math.sin(x/wl+ph)+amp*.4*math.sin(x/(wl*.43)+ph*2)) for x in range(0,w+20,20)]+[(w,h)]
    d.polygon(pts,fill=col)
def worker(d,x,y,s,carry,col):
    d.ellipse([x-5*s,y-26*s,x+5*s,y-16*s],fill=(255,226,190))
    d.rounded_rectangle([x-6*s,y-16*s,x+6*s,y],radius=3*s,fill=col)
    if carry: d.rectangle([x-9*s,y-34*s,x+9*s,y-18*s],fill=(255,235,200),outline=None)
def frame(i):
    t=i/(FPS*DUR); sec=t*DUR
    img=bg.copy(); d=ImageDraw.Draw(img,'RGBA')
    # stars
    for sx,sy,sr,ph in stars:
        a=int(120+110*math.sin(sec*4+ph)); r=sr*(0.8+0.2*math.sin(sec*4+ph))
        d.ellipse([sx-r,sy-r,sx+r,sy+r],fill=(255,240,220,max(40,a)))
    # sun
    sxp,syp=int(lerp(1020,960,t)*S),int(lerp(250,300,t)*S)
    for r,a in ((230,30),(175,45),(125,70)):
        d.ellipse([sxp-r*S,syp-r*S,sxp+r*S,syp+r*S],fill=(255,170,100,a))
    d.ellipse([sxp-85*S,syp-85*S,sxp+85*S,syp+85*S],fill=SUN)
    # far dunes
    dune(d,gy-30*S,18*S,1,(140,56,110),170*S)
    dune(d,gy+0*S,22*S,3,(206,96,98),210*S)
    n=N; start,span=0.25,3.3
    built=0
    for k in range(N):
        if (sec-(start+span*k/N))/0.45>=1: built=k+1
    cur_top=bot-(bot-top)*built/N
    # ramp on right
    rx0=R[0]+250*S
    rtop=cur_top+(0 if built<n else 0)
    ramp_a=ease((sec-0.1)/0.5)*(1-ease((sec-4.0)/0.7))
    if ramp_a>0:
        ex=cx+ (R[0]-cx)*(1-(cur_top-top)/(bot-top)) *0.0
        # attach point on right face edge at height cur_top
        frac=(cur_top-top)/(gy-14*S-top); frac=max(0,min(1,frac))
        ax=lerp(cx,R[0],frac) if built>0 else R[0]
        pts=[(rx0,gy+10*S),(rx0,gy+10*S),(ax-10*S,cur_top+4*S),(ax+10*S,cur_top+4*S)]
        poly=[(rx0+60*S,gy+16*S),(ax+8*S,cur_top-2*S),(ax+8*S,cur_top+22*S),(rx0+60*S,gy+16*S)]
        ov=Image.new('RGBA',(w,h),(0,0,0,0)); od=ImageDraw.Draw(ov)
        od.polygon([(rx0+70*S,gy+16*S),(ax,cur_top),(ax+0,cur_top+26*S),(rx0+70*S,gy+16*S)],fill=(255,200,130,int(255*ramp_a)))
        od.polygon([(rx0+70*S,gy+16*S),(ax,cur_top+26*S),(rx0+70*S,gy+16*S)],fill=(120,60,70,int(255*ramp_a)))
        # ramp body (wedge)
        od.polygon([(ax,cur_top),(rx0+70*S,gy+16*S),(ax,gy+16*S)],fill=(224,150,100,int(255*ramp_a)))
        od.line([(ax,cur_top),(rx0+70*S,gy+16*S)],fill=(255,222,170,int(255*ramp_a)),width=4*S)
        img.paste(ov,(0,0),ov); d=ImageDraw.Draw(img,'RGBA')
        # workers climbing
        for j in range(5):
            q=(sec*0.35+j/5)%1.0
            wx=lerp(rx0+60*S,ax+14*S,q); wy=lerp(gy+14*S,cur_top-2*S,q)
            worker(d,wx,wy,S*1.05,True,[(70,120,200),(240,90,110),(90,190,170)][j%3])
        # ground workers
        for j in range(3):
            wx=rx0+(90+j*55)*S+math.sin(sec*5+j)*3*S
            worker(d,wx,gy+22*S,S*1.05,j!=1,[(70,120,200),(240,90,110),(90,190,170)][j])
    # pyramid tiers
    n=N; per=1.05/ n*0  # placeholder
    for k in range(n):  # k=0 bottom
        t0=start+span*k/n; p=(sec-t0)/0.45
        if p<=0: continue
        dy=(1-back(p))*-180*S if p<1 else 0
        a=int(255*min(1,p*2.5))
        y1=bot-(bot-top)*k/n; y0=bot-(bot-top)*(k+1)/n
        band=base.crop((0,int(y0),w,int(y1)+1))
        if a<255: band.putalpha(band.split()[3].point(lambda v:v*a//255))
        img.paste(band,(0,int(y0+dy)),band)
    # capstone glint
    if sec>3.7:
        p=ease((sec-3.7)/0.5)
        cap=Image.new('RGBA',(w,h),(0,0,0,0)); cd=ImageDraw.Draw(cap)
        gx,gyy=apex[0],apex[1]+8*S
        cd.polygon([apex,(apex[0]-40*S,apex[1]+64*S),(apex[0]+50*S,apex[1]+66*S)],fill=(255,222,110,int(255*p)))
        img.paste(cap,(0,0),cap); d=ImageDraw.Draw(img,'RGBA')
        pulse=(sec-3.9)*3
        if pulse>0:
            r=(30+60*((pulse)%1))*S; al=int(220*(1-(pulse%1)))
            d.ellipse([gx-r,gyy-r,gx+r,gyy+r],outline=(255,245,200,al),width=4*S)
        sp=int(40*S*p)
        for ang in (0,45,90,135):
            a=math.radians(ang+sec*30)
            d.line([(gx-math.cos(a)*sp,gyy-math.sin(a)*sp),(gx+math.cos(a)*sp,gyy+math.sin(a)*sp)],fill=(255,250,220,200),width=3*S)
    # front dunes
    dune(d,gy+60*S,26*S,5,(120,40,92),240*S)
    dune(d,gy+120*S,30*S,2,(70,28,88),300*S)
    # title
    try: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',46*S); f2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',22*S)
    except: f=f2=ImageFont.load_default()
    ta=ease((sec-0.2)/0.5)*(1-ease((sec-4.6)/0.4)) if False else ease((sec-0.2)/0.5)
    if ta>0:
        d.text((70*S,60*S+int((1-ta)*20*S)),"HOW WERE THE",font=f2,fill=(255,200,150,int(255*ta)))
        d.text((70*S,92*S+int((1-ta)*20*S)),"PYRAMIDS BUILT?",font=f,fill=(255,255,255,int(255*ta)))
    # fade in/out
    fa=1-ease((sec-0.0)/0.3)
    out=Image.new('RGBA',(w,h),(0,0,0,0))
    if fa>0:
        img=Image.blend(img,Image.new('RGB',(w,h),(20,12,50)),fa)
    return img.resize((W,H),Image.LANCZOS)
os.makedirs('/tmp/pyr_frames',exist_ok=True)
for i in range(FPS*DUR): frame(i).save(f'/tmp/pyr_frames/f{i:04d}.png')
