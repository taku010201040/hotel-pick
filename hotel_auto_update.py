#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ホテル比較ページの情報を自動調査して hotel-pick.html に反映する。

使い方:
  python hotel_auto_update.py            # 20サイト + 全ホテルの公式HP/クーポンページを巡回
  python hotel_auto_update.py --quick    # 20サイトのトップ巡回をスキップ(ホテルのページのみ)

出力:
  hotel-pick.html        AUTO_DATA ブロックを更新
  hotel_check_report.md  調査レポート
"""
import concurrent.futures
import datetime
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(ROOT, "hotel-pick.html")
REPORT_PATH = os.path.join(ROOT, "hotel_check_report.md")

SITES = [
    ("ハッピーホテル", "https://happyhotel.jp"),
    ("カップルズ", "https://couples.jp"),
    ("ホテルナビ(hotenavi)", "https://hotenavi.com"),
    ("ラブホ料金ナビ(LH-Price)", "https://lh-price.com"),
    ("WBED(ダブルベッド)", "https://wbed.jp"),
    ("ハピホテガイド", "https://guide.happyhotel.jp"),
    ("ラブコレ&ホテルズ", "http://love-collection.info"),
    ("ラブホテルガイド", "http://www.hotel-guide.jp"),
    ("よるよる", "https://yoruyoru.jp"),
    ("STAY LOVELY(ステラブ)", "https://stay-lovely.jp"),
    ("ラブホテルナビ(nnn-f)", "https://www.nnn-f.jp"),
    ("駅ちか 人気ラブホランキング", "https://ranking-deli.jp"),
    ("Shizuku(シズク)", "https://lovehotel.shizuku-media.com"),
    ("lovehotelmap.com", "https://lovehotelmap.com"),
    ("ラブホガイド", "http://loveho-g.com"),
    ("looking-for-hotels.com", "https://looking-for-hotels.com"),
    ("全国ラブホ検索(エンジョイホテル)", "https://enjoyhotel.info"),
    ("fashionhotel.jp", "https://fashionhotel.jp"),
    ("セキララ女子会", "https://seki-lala.jp"),
    ("Japanese Love Hotel(EN)", "https://www.japaneselovehotel.com"),
]

# id, 表示名, 公式HP, happyhotel id, couples id, hotenavi パス
HOTELS = [
    ("lios3", "HOTEL LiosIII", "", "540232", "", ""),
    ("peace", "HOTEL PEACE", "https://www.hotelpeace.jp/", "25900976", "3170", ""),
    ("oldswing", "OLD SWING", "https://hotel-oldswing.com/wp/", "540062", "70288", ""),
    ("payblanc", "ル・ペイ・ブラン", "https://lepaysblanc.com/", "540061", "2605", ""),
    ("charme", "シャルム目黒", "https://www.hotenavi.com/m/", "541318", "50589", "/m/"),
    ("mare", "ホテル MARE", "https://www.hotenavi.com/mare/", "543796", "11075", "/mare/"),
    ("ramses", "RAMSES COTE", "https://ramses-grp.com/ramses-cote", "540490", "50662", ""),
    ("toumei", "HOTEL 東名", "https://hoteltoumei.web.fc2.com", "540491", "224", ""),
    ("golf", "GOLF 東名川崎", "https://www.hotenavi.com/golf-20/", "741751", "70181", "/golf-20/"),
    ("lirio", "LIRIO", "", "543363", "2901", ""),
    ("bside", "HOTEL B-SIDE", "https://hotel-b-side.com/", "540227", "337", ""),
    ("sara", "SARA GRANDE五反田", "https://sara-grande.jp/", "25901181", "70274", "/sara-gra/"),
    ("sunmarine", "ホテル サンマリン", "http://hotel-sunmarine.com/", "543521", "939", ""),
    ("lafranc", "ラ・フランセパリス", "https://couples.jp/hotel-details/2967", "540006", "2967", ""),
    ("stela", "HOTEL STELA", "https://h-mg.com/stela/", "540120", "147", ""),
    ("verona", "HOTEL VERONA", "https://www.hotenavi.com/verona", "741669", "20403", "/verona"),
    ("seeds", "HOTEL SEEDS 東名店", "https://hotel-seeds.com/tomei/", "", "2143", ""),
    ("paris", "ホテル パリス 渋谷", "http://paris-h.jp/", "543408", "2617", ""),
    ('hotel-grand-ikebukuro', 'ホテル 池袋グランド', 'https://ikebukuro-grand.net/', '', '', ''),
    ('hotel-linden-yushima', 'HOTEL LINDEN 湯島', 'https://hotellinden.jp/yushima/', '', '92', ''),
    ('hotel-mju-asakusa', 'Hotel μ（ホテル ミュー）', 'https://www.asakusa-mju.net/', '5400052', '2442', ''),
    ('hotel-willcity-asakusa', 'HOTEL WILL CITY 浅草', 'https://willasakusa.com/', '', '619', ''),
    ('hotel-linden-oji', 'ホテル リンデン王子店（旧ホテルロンドン王子店）', '', '541335', '120', ''),
    ('hotel-lotus-koiwa', 'HOTEL LOTUS 小岩店', 'https://koiwa-lotus.com/', '540257', '54573', ''),
    ('hotel-rochelle-kamata', 'ロッシェル', 'https://rochelle.hard-love.me/', '25900695', '', ''),
    ('hotel-edoyado-asakusa', 'HOTEL EDOYADO（ホテル エドヤド）', 'https://www.hotel-edoyado.com/', '540132', '50584', ''),
    ('hotel-karuta-akasaka', 'HOTEL KARUTA 赤坂', 'https://hotelkaruta.jp/', '', '', ''),
    ('hotel-smile-ikebukuro', '池袋ホテルスマイル', 'https://www.hotelsmile.jp/', '', '', ''),
    ('hotel-boston-club-asakusa', 'ホテル ボストンクラブ', '', '', '', ''),
    ('hotel-is-ishikawacho', 'HOTEL I/S (ホテル アイエス)', '', '', '1431', ''),
    ('mink-machida', 'ミンク町田', '', '741797', '', ''),
    ('ring-mybell-machida', 'ホテル リングマイベル町田', 'https://www.chapel-hotel.co.jp/kanagawa/h108/', '', '52956', ''),
    ('zero-kawasaki', 'HOTEL ZERO 川崎', 'https://zero-kawasaki.p-door.com/', '', '953', ''),
    ('hotel-ig-kawasaki', 'HOTEL IG (ホテル アイジー)', 'http://hotel-ig.com/', '', '2303', ''),
    ('parthenon-kawasaki', 'ホテル パルティノン', 'https://www.hotenavi.com/parthenon/', '', '50657', ''),
    ('hotel-nuda-yokohama', 'ホテルNUDA横浜 (NUDA by H-SEVEN)', 'https://www.hotenavi.com/nuda/', '667858', '20408', ''),
    ('hotel-roy-yokohama', 'HOTEL ROY (ホテル ロイ)', 'https://www.hotel-roy.jp/', '540433', '', ''),
    ('grand-garden-yokohama', 'EXECUTIVE HOTEL GRAND GARDEN', 'https://exe-hotel.jp/', '', '957', ''),
    ('hotel-heaven-tsurumi', 'HOTEL HEAVEN (ホテル ヘブン)', '', '', '3329', ''),
    ('wandoo-machida', 'HOTEL WANDOO (ワンドゥ)', 'https://wandoo-machida.com/', '', '', ''),
    ('will-marine-fujisawa', 'WILL マリンリゾート藤沢', 'https://willmarineresort-fujisawa.com/', '', '20431', ''),
    ('shijo-hotel', '四条ホテル', '', '612691', '51069', ''),
    ('hotel-rei', 'HOTEL Rei（ホテル レイ）', '', '', '1100', ''),
    ('toiuwakede', 'ホテル と、いうわけで。', '', '610319', '983', ''),
    ('hotel-peach-pai', 'ホテル ピーチパイ', '', '611826', '985', ''),
    ('sunday-brunch-gion', '祇園 ホテル サンデーブランチ', 'http://www.hotelsundaybrunch.com/', '611784', '3025', ''),
    ('rotele-de-fleur-kyogoku', 'ホテル ロテル・デ・フルール京極', 'http://www.us-hotel.co.jp/kyogoku/', '611828', '745', ''),
    ('love-in-part2', 'ホテル ラブインパート2', '', '611788', '', ''),
    ('hotel-saint-martin', 'ホテル サンマルタン', 'https://kyoto-saintmartin.com/', '', '', ''),
    ('hoshinosuna', 'ホテル 星の砂', 'http://k-hoshi.com/', '610754', '2811', ''),
    ('kamen-butoukai-kyoto', 'ホテル 仮面舞踏会 京都', 'https://www.shinki-group.com/kamenbutoukai-kyoto/', '', '', ''),
    ('fine-garden-kyoto-minami', 'ファインガーデン京都南', 'https://www.hotel-fine.co.jp/hotel/g-kyoto/', '', '', ''),
    ('umeda-ravian-soft', '梅田 ラブホテル ラヴィアンソフト', 'https://osaka-umeda-rabuho.com/coupon.html', '6100128', '787', ''),
    ('francesca-umeda', 'ホテル フランチェスカ 大阪梅田店', 'http://umeda-rabuho.com/coupon.html', '', '1225', ''),
    ('togano-hotel', '兎我野ホテル', '', '612052', '3534', ''),
    ('dessan-du-fleur', 'ホテル デッサン・ドゥ・フルール', '', '6100143', '2676', ''),
    ('digadiga-du', 'ホテル ディガ・ディガ・ドゥ', 'https://digadiga.com/', '', '794', ''),
    ('hotel-jay-namba', 'HOTEL jay（ホテル ジェイ）', 'http://hotel-jay.net/plan.html', '', '', ''),
    ('donai-yanen', 'ホテル どないやねん（旧ホテルPUPPY）', 'https://dotonbori-hotel.com/price.html', '39100024', '1200', ''),
    ('coconuts-tennoji', 'ホテル リトルチャペルココナッツ 天王寺', 'https://www.chapel-hotel.co.jp/osaka/h056/plan', '', '1160', ''),
    ('fine-garden-umeda', 'ファインガーデン梅田', 'https://www.hotel-fine.co.jp/', '', '', ''),
    ('hotel-ef-umeda', 'HOTEL ef（ホテル イーエフ）', '', '', '', '')
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
TIMEOUT = 12
CODE_KEYWORD = re.compile(r"(?:クーポン|コード|番号|\bID\b)[^0-9]{0,24}(\d{3,5}-\d{3,6})")
CODE_GENERIC = re.compile(r"\b\d{3,5}-\d{3,6}\b")
EXPIRE_RE = re.compile(r"20\d{2}\s*[年/-]\s*\d{1,2}\s*[月/-]\s*\d{1,2}")
STAY_RE = re.compile(r"宿泊")
DAY_LABEL_RE = re.compile(r"(月[〜～]木|日[〜～]木|金[・、]土[・、]祝前日?|金[・、]祝前日?|土曜日|日[・、]祝日?|平日)")
PRICE_AFTER_RE = re.compile(r"(?:￥|¥)?\s*(\d{1,3}(?:,\d{3})+|\d{4,5})\s*(?:円|～|〜)")
MIN_STAY_RE = re.compile(r"宿泊[^\d]{0,40}(\d{1,3}(?:,\d{3})+|\d{4,5})\s*円[〜～]")
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def fetch(url, limit=350000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read(limit)
            enc = r.headers.get_content_charset() or "utf-8"
            return r.status, raw.decode(enc, "ignore"), ""
    except urllib.error.HTTPError as e:
        return e.code, "", "HTTP %s" % e.code
    except Exception as e:
        return 0, "", str(e)[:160]


def clean(text):
    return WS_RE.sub(" ", html.unescape(TAG_RE.sub(" ", text))).strip()


def extract_codes(text):
    plain = clean(text)
    found = []

    def add(code):
        # 著作権年(2007-2026)や電話番号(03-1234等)は除外
        if re.match(r"^(19|20)\d{2}-(19|20)\d{2}$", code):
            return
        if re.match(r"^0\d{1,3}-\d{3,4}$", code):
            return
        if code not in found:
            found.append(code)

    # 最も確実: 「クーポンID 12345-67890」「クーポンNo 123-4567」
    for m in re.finditer(r"クーポン\s*(?:ID|No|番号)[^\d]{0,12}(\d{3,5}-\d{3,6})", plain, re.I):
        add(m.group(1))
    # 「クーポンID / クーポンNo」が無いサイトはコードなしとみなす
    # (_phone番号 6450-4420 や郵便番号 141-0022 の誤検出を防ぐため)
    return found[:6]


def extract_expiry(text):
    m = EXPIRE_RE.search(clean(text))
    return m.group(0).replace(" ", "") if m else None


def extract_benefit(text, code):
    plain = clean(text)
    idx = plain.find(code)
    if idx < 0:
        return None
    chunk = plain[max(0, idx - 160): idx + 200]
    m = re.search(r"[^。]{0,80}(?:円OFF|割引|無料|OFF|サービス)[^。]{0,60}", chunk)
    return m.group(0).strip()[:110] if m else None


def label_to_days(label):
    days = []
    if ("月" in label and "木" in label) or ("日" in label and "木" in label) or label == "平日":
        days.append("weekday")
    if ("日" in label and "祝" in label) or "日曜" in label:
        days.append("sun")
    if "金" in label:
        days.append("fri")
    if "土" in label:
        days.append("sat")
    if "祝前" in label:
        days.append("eve")
    return days


def _add_price(found, label, value):
    try:
        value = int(value.replace(",", ""))
    except (ValueError, AttributeError):
        return
    if not (2000 <= value <= 60000):
        return
    for day in label_to_days(label):
        if day not in found or value < found[day]:
            found[day] = value


def extract_prices_bracket(plain):
    """ハピホテ / カップルズ: 宿泊セクションの 【月～木】 形式。"""
    found = {}
    anchors = list(re.finditer(r"宿泊(?:[12]部)?\s*[【\[]([^】\]]{1,40})[】\]]", plain))
    for a in anchors:
        seg = plain[a.start():a.start() + 900]
        cut = re.search(r"休憩|サービスタイム|ショートタイム|設備|サービス・その他|クチコミ|アクセス|レビュー|お客様の声", seg[10:])
        if cut:
            seg = seg[:cut.start() + 10]
        for lm in re.finditer(r"[【\[]([^】\]]{1,40})[】\]]", seg):
            chunk = seg[lm.end():lm.end() + 200]
            pm = PRICE_AFTER_RE.search(chunk)
            if pm:
                _add_price(found, lm.group(1), pm.group(1))
    return found


def extract_prices_hotenavi(plain):
    """ホテナビ: 宿泊 日～木・祝日 9,900円 金・土・祝前日 14,000円 ... 形式。"""
    found = {}
    plain = plain.replace("宿 泊", "宿泊")
    for a in re.finditer(r"宿泊\s*(?:日[〜～]木|月[〜～]木)", plain):
        seg = plain[a.start():a.start() + 500]
        cut = re.search(r"宿泊ロング|ご 延 長|ショートタイム|休憩|客室詳細|設備", seg[8:])
        if cut:
            seg = seg[:cut.start() + 8]
        for lm in re.finditer(r"(日[〜～]木[^\d]{0,12}|月[〜～]木曜日?[^\d]{0,6}|金[・、]土[・、]祝前日|金[・、]祝前日|土曜日|日[・、]祝日)\s*(\d{1,3}(?:,\d{3})+|\d{4,5})\s*円", seg):
            _add_price(found, lm.group(1), lm.group(2))
    return found


def extract_prices(text, source_label=""):
    plain = clean(text)
    found = {}
    # 優先: 括弧付き曜日ラベル(ハピホテ/カップルズ/公式HP)
    found.update(extract_prices_bracket(plain))
    if not found or source_label == "ホテルナビ":
        for k, v in extract_prices_hotenavi(plain).items():
            if k not in found:
                found[k] = v
    if not found:
        m = MIN_STAY_RE.search(plain)
        if m:
            _add_price(found, "月〜木", m.group(1))
            for d in ("fri", "sat", "eve", "sun"):
                found[d] = found["weekday"]
    return found


def check_site(item):
    name, url = item
    status, text, err = fetch(url, 120000)
    return name, {"url": url, "status": status, "error": err, "checkedAt": datetime.datetime.now().isoformat(timespec="seconds")}


def hotel_sources(row):
    hid, name, official, hh, couples, hotenavi = row
    out = []
    if official:
        out.append(("公式HP", official))
    if hh:
        out.append(("ハピホテ", "https://happyhotel.jp/hotels/%s/coupons" % hh))
        out.append(("ハピホテ料金", "https://happyhotel.jp/hotels/%s" % hh))
    if couples:
        out.append(("カップルズ", "https://couples.jp/hotel-details/%s/coupon" % couples))
        out.append(("カップルズ料金", "https://couples.jp/hotel-details/%s" % couples))
    if hotenavi:
        out.append(("ホテルナビ", "https://www.hotenavi.com%s" % hotenavi))
        out.append(("ホテルナビ料金", "https://www.hotenavi.com%s/room" % hotenavi.rstrip("/")))
    return out


def check_hotel(row):
    hid, name = row[0], row[1]
    results = []
    for label, url in hotel_sources(row):
        status, text, err = fetch(url)
        codes = extract_codes(text) if text else []
        expiry = extract_expiry(text) if text else None
        benefits = [extract_benefit(text, c) for c in codes] if text else []
        results.append({
            "label": label, "url": url, "status": status, "error": err,
            "codes": codes, "expiry": expiry,
            "benefits": [b for b in benefits if b],
            "prices": extract_prices(text, label) if (text and (label.endswith("料金") or label == "公式HP")) else {},
        })
    coupons = []
    for r in results:
        for i, code in enumerate(r["codes"]):
            coupons.append({
                "site": r["label"], "code": code,
                "benefit": r["benefits"][i] if i < len(r["benefits"]) else None,
                "expiry": r["expiry"], "url": r["url"],
                "days": ["weekday", "fri", "sat", "eve", "sun"],
                "note": "自動検出。条件は出典で要確認",
            })
    # 同一コードは最初のサイトだけ残す
    seen, uniq = set(), []
    for c in coupons:
        if c["code"] not in seen:
            seen.add(c["code"])
            uniq.append(c)
    merged = {}
    for preferred in ("ハピホテ料金", "カップルズ料金", "ホテルナビ料金", "公式HP"):
        for r in results:
            if r["label"] != preferred:
                continue
            for day, value in r["prices"].items():
                if day not in merged:
                    merged[day] = value
    return hid, {"name": name, "sources": results, "coupons": uniq, "prices": merged,
                 "checkedAt": datetime.datetime.now().isoformat(timespec="seconds")}


def update_html(auto):
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        s = f.read()
    data = json.dumps(auto, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    block = "/* AUTO_DATA_START */\n  const AUTO_DATA = %s;\n  /* AUTO_DATA_END */" % data
    new, n = re.subn(r"/\* AUTO_DATA_START \*/.*?/\* AUTO_DATA_END \*/", lambda m: block, s, flags=re.S)
    if n != 1:
        raise RuntimeError("AUTO_DATA markers not found in %s" % HTML_PATH)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new)


def write_report(auto):
    lines = []
    lines.append("# ホテル情報 自動調査レポート")
    lines.append("")
    lines.append("- 実行日時: **%s**" % auto["lastChecked"])
    lines.append("- 対象: 主要まとめサイト %d サイト / ホテル %d 件" % (len(auto["sites"]), len(auto["hotels"])))
    lines.append("- 料金は自動では上書きしません。クーポンコードと到達状況を更新し、最終料金・空室は公式HPで確認してください。")
    lines.append("")
    lines.append("## まとめサイト到達状況")
    lines.append("")
    lines.append("| # | サイト | 結果 | URL |")
    lines.append("|---:|---|---|---|")
    for i, (name, url) in enumerate(SITES, 1):
        st = auto["sites"].get(name, {})
        mark = "✅ %s" % st.get("status") if st.get("status", 0) and st["status"] < 400 else "⚠️ %s" % (st.get("error") or st.get("status") or "未実施")
        lines.append("| %d | %s | %s | %s |" % (i, name, mark, url))
    lines.append("")
    lines.append("## ホテルごとの検出結果")
    lines.append("")
    lines.append("| id | ホテル | 情報源 | 検出コード |")
    lines.append("|---|---|---|---|")
    for hid, info in auto["hotels"].items():
        src = []
        for r in info["sources"]:
            src.append("%s:%s" % (r["label"], "✅" if r["status"] and r["status"] < 400 else "⚠️"))
        codes = ", ".join("`%s`" % c["code"] for c in info["coupons"]) or "—"
        lines.append("| %s | %s | %s | %s |" % (hid, info["name"], " / ".join(src), codes))
    lines.append("")
    lines.append("## 曜日別料金(自動取得・最安値)")
    lines.append("")
    lines.append("| id | ホテル | 月〜木 | 金 | 土 | 日祝 | 祝前 | 取得元 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|")
    for hid, info in auto["hotels"].items():
        p = info.get("prices", {})
        srcs = [r["label"] for r in info["sources"] if r.get("prices")]
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            hid, info["name"],
            "¥%s" % format(p["weekday"], ",") if "weekday" in p else "—",
            "¥%s" % format(p["fri"], ",") if "fri" in p else "—",
            "¥%s" % format(p["sat"], ",") if "sat" in p else "—",
            "¥%s" % format(p["sun"], ",") if "sun" in p else "—",
            "¥%s" % format(p["eve"], ",") if "eve" in p else "—",
            " / ".join(srcs) or "—"))
    lines.append("")
    lines.append("※ 自動取得値は参考。クーポン・会員条件・時間帯により変動するため、最終料金は公式HPで確認してください。")
    lines.append("")
    lines.append("## 検出コードの詳細")
    lines.append("")
    for hid, info in auto["hotels"].items():
        if not info["coupons"]:
            continue
        lines.append("### %s (%s)" % (info["name"], hid))
        for c in info["coupons"]:
            lines.append("- **%s**: `%s` %s 期限:%s 出典:[%s](%s)" % (
                c["site"], c["code"], c.get("benefit") or "", c.get("expiry") or "記載なし", c["site"], c["url"]))
        lines.append("")
    if not any(i["coupons"] for i in auto["hotels"].values()):
        lines.append("コードは検出されませんでした(サイト側のJS表示・ログイン必須などの可能性)。")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    quick = "--quick" in sys.argv
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    sites = {}
    if not quick:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            for name, result in ex.map(check_site, SITES):
                sites[name] = result
                print("SITE", name, result["status"] or result["error"])
    hotels = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for hid, result in ex.map(check_hotel, HOTELS):
            hotels[hid] = result
            codes = ",".join(c["code"] for c in result["coupons"]) or "-"
            print("HOTEL", hid, "codes:", codes)
    auto = {"lastChecked": now, "sites": sites, "hotels": hotels}
    update_html(auto)
    write_report(auto)
    print("\nDONE: %s を更新しました" % os.path.basename(HTML_PATH))
    print("      %s を更新しました" % os.path.basename(REPORT_PATH))


if __name__ == "__main__":
    main()
