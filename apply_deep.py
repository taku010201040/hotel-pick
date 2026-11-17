# -*- coding: utf-8 -*-
"""詳細設備フラグを HOTELS に反映する。"""
import io, json, os, re
BASE=os.path.dirname(os.path.abspath(__file__))
HTML=r'C:\Users\81704\Downloads\hotel-pick.html'
SRC=os.path.join(BASE,'hotel_amenities_deep.json')
data=json.load(io.open(SRC,encoding='utf-8')) if os.path.exists(SRC) else {}
FIELDS=[
 "wifi","sauna","jacuzzi","karaoke","openair","massageChair","handMassage",
 "cosplayFree","cosplaySale","toysSale","lotion","mat","beauty","headspa",
 "washboard","nonsmoke","three","sameSex","solo","food","drinkFree","videos",
 "bigTV","bathTV","fridge","microwave","charger","bathrobe","amenities",
 "outside","parking","card","web","game","projector","stoneBath","footbath","waterbed"
]
KEYWORDS={
 "wifi":["wi-fi","wifi"],"sauna":["サウナ"],"jacuzzi":["ジェットバス","ブロアバス","マイクロバブル"],
 "karaoke":["カラオケ"],"openair":["露天"],"massageChair":["マッサージチェア"],
 "handMassage":["ハンドマッサージャー","電気マッサージ器"],
 "cosplayFree":["コスプレ無料","コスプレ1着目無料","コスプレ１着目無料"],
 "cosplaySale":["コスプレ販売","コスチューム販売"],"toysSale":["玩具販売"],
 "lotion":["ローション"],"mat":["マット"],"beauty":["美顔器","スチーマー","reFa","ドライヤー","ヘアアイロン"],
 "headspa":["ヘッドスパ"],"washboard":["和室"],"nonsmoke":["禁煙"],
 "three":["3名以上","３人以上"],"sameSex":["同性利用可","女性同士"],"solo":["お一人様","1名利用可","一人利用可"],
 "food":["ルームサービス","フード","朝食","モーニング","お茶","缶コーヒー"],
 "drinkFree":["アルコール1杯無料","アルコール一杯無料","ウェルカムドリンク","ドリンク無料"],
 "videos":["vod","ビデオオンデマンド","ブルーレイ","dvd"],"bigTV":["大型tv","大型テレビ","50インチ","55インチ","65型","75インチ"],
 "bathTV":["浴室tv","浴室テレビ"],"fridge":["冷蔵庫"],"microwave":["電子レンジ"],
 "charger":["充電器","usb","type-c"],"bathrobe":["バスローブ"],
 "amenities":["アメニティ","シャンプー","化粧品","歯ブラシ"],"outside":["外出ok","外出可"],
 "parking":["駐車場"],"card":["カード可","クレジットカード","visa","mastercard","jcb"],
 "web":["ネット予約","web予約","予約可"],"game":["tvゲーム","ゲーム機","nintendo switch"],
 "projector":["プロジェクター"],"stoneBath":["岩盤浴"],"footbath":["足湯"],"waterbed":["ウォーターベッド"]
}
s=io.open(HTML,encoding='utf-8').read()
start=s.index('const HOTELS = ['); end=s.index('const HH = {')
head,block,tail=s[:start],s[start:end],s[end:]
parts=re.split(r'(?=\n    \{\n)',block)
added=0; updated=0
for i,part in enumerate(parts):
    m=re.search(r"id:'([^']+)'",part)
    if not m: continue
    hid=m.group(1)
    flags=data.get(hid)
    if flags is None:
        note=(re.search(r"note:'([^']*)'",part) or [None,''])[1].lower()
        flags={k:any(w in note for w in KEYWORDS[k]) for k in FIELDS}
    chunks=[]
    for k in FIELDS:
        val='true' if flags.get(k) else 'false'
        if re.search(r"\b%s:(?:true|false)"%k,part):
            part=re.sub(r"\b%s:(?:true|false)"%k,"%s:%s"%(k,val),part,count=1); updated+=1
        else:
            chunks.append("%s:%s"%(k,val))
    if chunks:
        add=','.join(chunks)+','
        part2,k=re.subn(r"(\n      note:'[^']*')", r"\1,\n      "+add, part, count=1)
        if not k:
            part2,k=re.subn(r"(\n      badge:[^\n]*)", r"\1,\n      "+add, part, count=1)
        part=part2; added+=k
    parts[i]=part
io.open(HTML,'w',encoding='utf-8').write(head+''.join(parts)+tail)
print('new fields',added,'updated',updated)
