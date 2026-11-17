#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全掲載ホテルを週1回だけ再クロールして IN/OUT・部屋数・設備・料金を更新する。"""
import concurrent.futures, html, io, os, re, time
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(ROOT, "hotel-pick.html")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
TAG = re.compile(r"<[^>]+>"); WS = re.compile(r"\s+")
DAY_KEYS = ("weekday", "fri", "sat", "eve", "sun")
AMENITY_KEYS = ['wifi','sauna','jacuzzi','karaoke','openair','massageChair','handMassage','cosplayFree','cosplaySale','toysSale','lotion','mat','beauty','headspa','washer','nonsmoke','three','sameSex','solo','food','drinkFree','videos','bigTV','bathTV','fridge','microwave','charger','bathrobe','amenities','outside','parking','card','web','game','projector','stoneBath','footbath','waterbed','jacuzziBath']
KW = {
 "wifi":["wi-fi","wifi","wireless lan","フリーwi-fi","無料wi-fi","lan"],
 "sauna":["サウナ"],
 "jacuzzi":["ジェットバス","ブロアバス","ジャグジー","マイクロバブル"],
 "karaoke":["カラオケ"],
 "openair":["露天風呂","露天"],
 "massageChair":["マッサージチェア"],
 "handMassage":["ハンドマッサージャー","電気マッサージ器","マッサージャー"],
 "cosplayFree":["コスプレ無料","無料レンタルコスプレ","コスプレ１着目無料","コスプレ1着目無料","コスプレ無料レンタル"],
 "cosplaySale":["コスプレ販売","コスチューム販売"],
 "toysSale":["玩具販売","玩具（販売）","玩具(販売)"],
 "lotion":["ローション"],
 "mat":["マット（貸出）","マット(貸出)","ローションマット","マット貸出"],
 "beauty":["美顔器","スチーマー","美容機器","ReFa","ドライヤー","ヘアアイロン"],
 "headspa":["ヘッドスパ"],
 "washer":["和室"],
 "nonsmoke":["禁煙ルーム","禁煙"],
 "three":["3名以上利用可","３人以上利用可","3人以上利用可","３名以上"],
 "sameSex":["同性利用可","女性同士","レズ"],
 "solo":["お一人様OK","一人利用可","1名利用可","お一人様利用可"],
 "food":["ルームサービス","フードメニュー","朝食","モーニング","食事","お茶","缶コーヒー"],
 "drinkFree":["アルコール1杯無料","アルコール一杯無料","ウェルカムドリンク","ドリンク無料","飲み物無料"],
 "videos":["vod","ビデオオンデマンド","ブルーレイ","dvd","dvdプレーヤー"],
 "bigTV":["大型tv","大型テレビ","50インチ","55インチ","65型","75インチ"],
 "bathTV":["浴室tv","浴室テレビ"],
 "fridge":["冷蔵庫"],
 "microwave":["電子レンジ"],
 "charger":["充電器","usb","type-c","iphone充電"],
 "bathrobe":["バスローブ"],
 "amenities":["アメニティ","シャンプー","化粧品","タオル","歯ブラシ"],
 "outside":["外出ok","外出可"],
 "parking":["駐車場"],
 "card":["カード可","クレジットカード","visa","mastercard","jcb"],
 "web":["ネット予約","web予約","予約可"],
 "game":["tvゲーム","ゲーム機","nintendo switch","プレステ"],
 "projector":["プロジェクター"],
 "stoneBath":["岩盤浴"],
 "footbath":["足湯"],
 "waterbed":["ウォーターベッド"],
 "jacuzziBath":["ジェットバス"],
}

def clean(s): return WS.sub(" ", html.unescape(TAG.sub(" ", s))).strip()

def fetch(url):
    for i in range(2):
        try:
            r = requests.get(url, headers=UA, timeout=18)
            if r.status_code == 200 and len(r.text) > 5000:
                return r.text
            if r.status_code == 429:
                time.sleep(4 * (i + 1))
        except Exception:
            time.sleep(1)
    return ""

def keys_for(label):
    ks=[]
    if ("月" in label and ("木" in label or "金" in label)) or ("日" in label and "木" in label): ks.append("weekday")
    if "金" in label: ks.append("fri")
    if "土" in label: ks.append("sat")
    if "祝前" in label: ks.append("eve")
    if "日" in label and "祝" in label: ks.append("sun")
    if "全日" in label or "毎日" in label: ks=list(DAY_KEYS)
    return ks

def parse_couples(p):
    out={"ok":True}
    m=re.search(r"部屋数\s*(\d+)\s*室",p) or re.search(r"ルーム数\s*(\d+)\s*室",p)
    if m and 1<=int(m.group(1))<=1000: out["rooms"]=int(m.group(1))
    times={}
    for m in re.finditer(r"宿泊\s*\[([^\]]{1,30})\][^（\[]{0,120}?（\s*(\d{1,2}:\d{2})\s*[〜～~]\s*翌?\s*(\d{1,2}:\d{2})",p):
        for k in keys_for(m.group(1)): times.setdefault(k,[m.group(2),m.group(3)])
    if not times:
        m=re.search(r"宿泊[^（]{0,100}?（\s*(\d{1,2}:\d{2})\s*[〜～~]\s*翌?\s*(\d{1,2}:\d{2})",p)
        if m:
            for k in DAY_KEYS: times[k]=[m.group(1),m.group(2)]
    out["times"]=times
    out["amenities"]={k:any(w.lower() in p.lower() for w in KW[k]) for k in AMENITY_KEYS}
    return out

def parse_happy(p):
    out={"ok":True}
    m=re.search(r"部屋数\s*(\d+)\s*部屋",p) or re.search(r"ルーム数\s*(\d+)\s*室",p)
    if m and 1<=int(m.group(1))<=1000: out["rooms"]=int(m.group(1))
    times={}
    for m in re.finditer(r"宿泊(?:STAY)?\s*[【\[]([^】\]]{1,40})[】\]]?[^◇]{0,20}◇\s*(\d{1,2}:\d{2})\s*[〜～~]\s*翌?\s*(\d{1,2}:\d{2})",p):
        for k in keys_for(m.group(1)): times.setdefault(k,[m.group(2),m.group(3)])
    out["times"]=times
    out["amenities"]={k:any(w.lower() in p.lower() for w in KW[k]) for k in AMENITY_KEYS}
    return out

def one(task):
    hid,kind,ident=task
    url=("https://couples.jp/hotel-details/"+ident) if kind=="cp" else ("https://happyhotel.jp/hotels/"+ident)
    t=fetch(url)
    if not t: return hid,None
    p=clean(t)
    return hid,(parse_couples(p) if kind=="cp" else parse_happy(p))

def js(s): return "null" if s is None else "'"+str(s).replace("'","\\'")+"'"

def main():
    s=io.open(HTML_PATH,encoding="utf-8").read()
    b=s[s.index("const HOTELS = ["):s.index("const HH = {")]
    hhmap=dict(re.findall(r"(\w+):(\d+)",s[s.index("const HH = {"):s.index("const RESERVE = {")]))
    tasks=[]
    for hid in re.findall(r"id:'([^']+)'",b):
        if hid.startswith("cp"): tasks.append((hid,"cp",hid[2:]))
        elif hid.startswith("hh"): tasks.append((hid,"hh",hid[2:]))
        elif hid in hhmap: tasks.append((hid,"hh",hhmap[hid]))
    print("targets",len(tasks))
    res={}
    done=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for hid,r in ex.map(one,tasks):
            if r: res[hid]=r
            done+=1
            if done%500==0: print("done",done)
    parts=re.split(r"(?=\n    \{\n)",b)
    cr=ct=ca=0
    for i,part in enumerate(parts):
        m=re.search(r"id:'([^']+)'",part)
        if not m: continue
        hid=m.group(1); r=res.get(hid)
        if not r: continue
        if r.get("rooms"):
            part,n=re.subn(r"rooms:\s*(?:\d+|null)","rooms:%d"%r["rooms"],part,count=1); cr+=n
        t=r.get("times") or {}
        if t:
            inb=",".join("%s:%s"%(js(k),js(v[0])) for k,v in t.items() if k in DAY_KEYS)
            outb=",".join("%s:%s"%(js(k),js(v[1])) for k,v in t.items() if k in DAY_KEYS)
            fri=t.get("fri") or t.get("weekday") or next(iter(t.values()))
            part,n=re.subn(r"checkin:[^,\n]+, checkout:[^,\n]+(?:, inBy:\{[^}]*\}, outBy:\{[^}]*\})?",
                           "checkin:%s, checkout:%s, inBy:{%s}, outBy:{%s}"%(js(fri[0]),js(fri[1]),inb,outb),part,count=1); ct+=n
        for k,v in (r.get("amenities") or {}).items():
            part,n=re.subn(r"\b%s:(?:true|false)"%k,"%s:%s"%(k,"true" if v else "false"),part,count=1); ca+=n
        parts[i]=part
    io.open(HTML_PATH,"w",encoding="utf-8").write(s[:s.index("const HOTELS = [")]+"".join(parts)+s[s.index("const HH = {"):])
    print("rooms",cr,"times",ct,"amenities",ca)

if __name__=="__main__": main()
