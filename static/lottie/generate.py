import json, random, shutil, os

rng = random.Random(42)

def static_kf(v):
    return {"a": 0, "k": v}

def anim_kf(ks):
    return {"a": 1, "k": ks}

EI = {"x": [0.5], "y": [1.0]}
EO = {"x": [0.5], "y": [0.0]}
LI = {"x": [0.0], "y": [0.0]}
LO = {"x": [0.0], "y": [0.0]}

def kf(t, s, i=None, o=None):
    k = {"t": t, "s": s}
    if i: k["i"] = i
    if o: k["o"] = o
    return k

def pos(x0,y0,x1,y1,t0,t1):
    return anim_kf([kf(t0,[x0,y0,0],i=EI,o=EO), kf(t1,[x1,y1,0])])

def rot(r0,r1,t0,t1):
    return anim_kf([kf(t0,[r0],i=LI,o=LO), kf(t1,[r1])])

def opa(pts):
    ks = []
    for idx,(t,v) in enumerate(pts):
        k = {"t":t,"s":[v]}
        if idx < len(pts)-1:
            k["i"] = EI; k["o"] = EO
        ks.append(k)
    return anim_kf(ks)

def scl(s0,s1,t0,t1):
    return anim_kf([kf(t0,[s0,s0,100],i=EI,o=EO), kf(t1,[s1,s1,100])])

def sl(ind, nm, shapes, ksp, ksr=None, kso=None, kss=None, ksa=None, ip=0, op=90, st=0):
    return {
        "ddd":0,"ind":ind,"ty":4,"nm":nm,"sr":1,
        "ks":{
            "o": kso or static_kf(100),
            "r": ksr or static_kf(0),
            "p": ksp,
            "a": ksa or static_kf([0,0,0]),
            "s": kss or static_kf([100,100,100])
        },
        "ao":0,"shapes":shapes,"ip":ip,"op":op,"st":st
    }

def rc(w,h,r=3,px=0,py=0):
    return {"ty":"rc","nm":"Rect","d":1,"p":{"a":0,"k":[px,py]},"s":{"a":0,"k":[w,h]},"r":{"a":0,"k":r}}

def el(rx,ry,px=0,py=0):
    return {"ty":"el","nm":"Ellipse","d":1,"p":{"a":0,"k":[px,py]},"s":{"a":0,"k":[rx*2,ry*2]}}

def fl(r,g,b,op=100):
    return {"ty":"fl","nm":"Fill","c":{"a":0,"k":[r/255,g/255,b/255,1]},"o":{"a":0,"k":op},"r":1}

def gr(items, nm="Grp"):
    return {"ty":"gr","nm":nm,"it":items}

def tr(px=0,py=0,r=0,sx=100,sy=100,op=100):
    return {"ty":"tr","nm":"Transform","a":{"a":0,"k":[0,0]},"p":{"a":0,"k":[px,py]},
            "s":{"a":0,"k":[sx,sy]},"r":{"a":0,"k":r},"o":{"a":0,"k":op},
            "sk":{"a":0,"k":0},"sa":{"a":0,"k":0}}

def comp(nm, layers, fr=30, op=90, w=600, h=600):
    return {"v":"5.5.9","fr":fr,"ip":0,"op":op,"w":w,"h":h,"nm":nm,"ddd":0,"assets":[],"layers":layers,"markers":[]}

# RAIN
def make_rain():
    L, N = 90, 22
    layers = []
    for i in range(N):
        x = rng.uniform(40, 560)
        wd = rng.uniform(1.5, 2.5)
        hd = rng.uniform(10, 18)
        op = rng.uniform(45, 75)
        st = -(i * L / N)
        layers.append(sl(i+1, f"Drop{i+1}",
            [rc(wd,hd), fl(90,248,251,op)],
            pos(x,-20,x+12,630,0,L-1),
            ksr=static_kf(15), kso=static_kf(op),
            ip=0, op=L, st=st))
    return comp("Rain", layers, op=L)

# SUNNY
def make_sunny():
    L = 150
    layers = []
    # 외곽 대형 글로우 (넓게 퍼지는 빛)
    layers.append(sl(1,"GlowOuter",[el(280,280),fl(255,220,80,20)],
        static_kf([300,300,0]),
        kso=opa([(0,15),(75,35),(150,15)]),
        kss=scl(100,130,0,75),
        ip=0,op=L))
    # 중간 글로우
    layers.append(sl(2,"GlowMid",[el(180,180),fl(255,231,146,40)],
        static_kf([300,300,0]),
        kso=opa([(0,35),(75,60),(150,35)]),
        kss=scl(100,120,0,75),
        ip=0,op=L))
    # 긴 광선 16개 (천천히 회전)
    ray_long = []
    for i in range(16):
        ray_long.append(gr([rc(3,55,3,0,-155),fl(255,231,146,50),tr(r=i*22.5)], f"RayL{i}"))
    layers.append(sl(3,"RaysLong",ray_long,
        static_kf([300,300,0]),
        ksr=rot(0,360,0,L),
        ip=0,op=L))
    # 짧은 광선 16개 (반대방향 회전)
    ray_short = []
    for i in range(16):
        ray_short.append(gr([rc(2,30,2,0,-115),fl(255,245,180,70),tr(r=i*22.5+11.25)], f"RayS{i}"))
    layers.append(sl(4,"RaysShort",ray_short,
        static_kf([300,300,0]),
        ksr=rot(0,-360,0,L),
        ip=0,op=L))
    # 태양 본체
    layers.append(sl(5,"Sun",[el(88,88),fl(255,238,120,98)],
        static_kf([300,300,0]),
        kso=opa([(0,90),(75,100),(150,90)]),
        kss=scl(100,110,0,75),
        ip=0,op=L))
    # 태양 코어 (흰빛)
    layers.append(sl(6,"SunCore",[el(52,52),fl(255,255,220,90)],
        static_kf([300,300,0]),
        kso=opa([(0,80),(75,100),(150,80)]),
        ip=0,op=L))
    # 반짝이 파티클 12개
    for i in range(12):
        sx=rng.uniform(60,540); sy=rng.uniform(60,540); sz=rng.uniform(4,9)
        t1=rng.randint(5,30); t2=rng.randint(35,65); t3=rng.randint(70,100)
        layers.append(sl(i+7,f"Spark{i}",[el(sz,sz),fl(255,231,146,90)],
            static_kf([sx,sy,0]),
            kso=opa([(0,0),(t1,90),(t2,0),(t3,0),(L,0)]),
            ip=0,op=L,st=-(i*L/12)))
    return comp("Sunny",layers,op=L)

# CLOUDY (partly)
def make_cloudy(n=3):
    L = 90
    layers = []
    ys = [rng.uniform(80,200) for _ in range(n)]
    xs = [rng.uniform(100,500) for _ in range(n)]
    for i in range(n):
        drift = rng.uniform(10,22) * (1 if i%2==0 else -1)
        op = rng.uniform(55,75)
        x0,y0 = xs[i],ys[i]
        cloud = [
            gr([el(rng.uniform(50,80),rng.uniform(30,50),rng.uniform(-30,30),rng.uniform(-10,10)),fl(200,210,220,100),tr()]),
            gr([el(rng.uniform(40,65),rng.uniform(25,40),rng.uniform(-50,-20),rng.uniform(-20,0)),fl(200,210,220,100),tr()]),
            gr([el(rng.uniform(40,65),rng.uniform(25,40),rng.uniform(20,50),rng.uniform(-20,0)),fl(200,210,220,100),tr()]),
        ]
        layers.append(sl(i+1,f"Cloud{i+1}",cloud,
            anim_kf([kf(0,[x0,y0,0],i=EI,o=EO),kf(L-1,[x0+drift,y0,0])]),
            kso=static_kf(op),
            ip=0,op=L,st=-(i*L/n)))
    return comp("Cloudy",layers,op=L)

# OVERCAST
def make_overcast():
    L = 120
    layers = []
    configs = [(rng.uniform(80,180),rng.uniform(60,540)) for _ in range(6)]
    for i,(cy,cx) in enumerate(configs):
        drift = rng.uniform(8,16) * (1 if i%2==0 else -1)
        op = rng.uniform(40,60)
        cloud = [
            gr([el(rng.uniform(70,110),rng.uniform(40,60),0,0),fl(170,180,190,100),tr()]),
            gr([el(rng.uniform(55,80),rng.uniform(35,50),-55,rng.uniform(-15,5)),fl(170,180,190,100),tr()]),
            gr([el(rng.uniform(55,80),rng.uniform(35,50),55,rng.uniform(-15,5)),fl(170,180,190,100),tr()]),
        ]
        layers.append(sl(i+1,f"Cloud{i+1}",cloud,
            anim_kf([kf(0,[cx,cy,0],i=EI,o=EO),kf(L-1,[cx+drift,cy,0])]),
            kso=static_kf(op),
            ip=0,op=L,st=-(i*L/6)))
    return comp("Overcast",layers,op=L)

# FOG
def make_fog():
    L = 150
    layers = []
    for i in range(5):
        y = 90 + i*95
        op = rng.uniform(20,35)
        drift = rng.uniform(8,18)
        layers.append(sl(i+1,f"Fog{i+1}",
            [rc(700,28,50),fl(195,205,215,100)],
            anim_kf([kf(0,[300,y,0],i=EI,o=EO),kf(L//2,[300+drift,y,0],i=EI,o=EO),kf(L,[300,y,0])]),
            kso=opa([(0,op),(L//4,op*1.5),(L//2,op*1.8),(L*3//4,op*1.5),(L,op)]),
            ip=0,op=L,st=-(i*L/5)))
    return comp("Fog",layers,op=L)

# THUNDER
def make_thunder():
    L = 90
    layers = []
    layers.append(sl(1,"Flash1",[rc(600,600,0),fl(230,230,150,100)],
        static_kf([300,300,0]),
        kso=opa([(0,0),(5,0),(8,22),(12,0),(13,0)]),
        ip=0,op=L))
    layers.append(sl(2,"Flash2",[rc(600,600,0),fl(200,150,255,100)],
        static_kf([300,300,0]),
        kso=opa([(0,0),(30,0),(33,15),(37,0),(38,0)]),
        ip=0,op=L))
    N = 20
    for i in range(N):
        x=rng.uniform(40,560); hd=rng.uniform(14,22); op=rng.uniform(50,80)
        layers.append(sl(i+3,f"Drop{i}",[rc(2,hd),fl(90,248,251,op)],
            pos(x,-20,x+15,630,0,72),
            ksr=static_kf(15),kso=static_kf(op),
            ip=0,op=L,st=-(i*L/N)))
    return comp("Thunder",layers,op=L)

# ── OUTPUT ──
out = "E:/study/weather-project/static/lottie"
os.makedirs(out, exist_ok=True)

files = {
    "rain.json": make_rain(),
    "sunny.json": make_sunny(),
    "cloudy.json": make_cloudy(3),
    "overcast.json": make_overcast(),
    "fog.json": make_fog(),
    "thunder.json": make_thunder(),
}
for fname, data in files.items():
    with open(os.path.join(out, fname), 'w', encoding='utf-8') as f:
        json.dump(data, f)
    print(f"Created: {fname} ({len(json.dumps(data))} bytes)")

snow_src = "E:/study/refer/Snowing.json"
snow_dst = os.path.join(out, "snow.json")
if os.path.exists(snow_src):
    shutil.copy(snow_src, snow_dst)
    print("Copied: snow.json")
else:
    print("Skipped: snow.json (source not found, keeping existing)")
