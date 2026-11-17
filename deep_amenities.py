# -*- coding: utf-8 -*-
"""設備・サービスを詳細に抽出する(カップルズ中心、ハピホテは低レートで補完)。"""
import concurrent.futures, html, io, json, os, re, time
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "hotel_amenities_deep.json")
HTML_PATH = r"C:\Users\81704\Downloads\hotel-pick.html"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
TAG = re.compile(r"<[^>]+>"); WS = re.compile(r"\s+")

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
            r=requests.get(url,headers=UA,timeout=18)
            if r.status_code==200 and len(r.text)>5000: return r.text
            if r.status_code==429: time.sleep(4*(i+1))
        except Exception: time.sleep(1)
    return ""

def extract(text):
    p=clean(text).lower()
    return {k:any(w.lower() in p for w in ws) for k,ws in KW.items()}

def one(cid):
    t=fetch("https://couples.jp/hotel-details/"+cid)
    return "cp"+cid, (extract(t) if t else None)

def one_happy(hid):
    t=fetch("https://happyhotel.jp/hotels/"+hid)
    return "hh"+hid, (extract(t) if t else None)

def main():
    s=io.open(HTML_PATH,encoding="utf-8").read()
    b=s[s.index("const HOTELS = ["):s.index("const HH = {")]
    cps=sorted(set(re.findall(r"id:'cp(\d+)'",b)))
    hhs=sorted(set(re.findall(r"id:'hh(\d+)'",b)))
    print("couples",len(cps),"happy",len(hhs))
    res={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for i,(k,v) in enumerate(ex.map(one,cps),1):
            if v: res[k]=v
            if i%400==0: print("cp",i)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        for i,(k,v) in enumerate(ex.map(one_happy,hhs),1):
            if v and k not in res: res[k]=v
            if i%100==0: print("hh",i)
    json.dump(res,io.open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("saved",OUT,len(res))

if __name__=="__main__": main()
