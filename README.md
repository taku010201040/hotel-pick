# ホテル比較ページ

`hotel-pick.html` を開くだけで、日付・場所・都道府県・地域・設備でホテルを絞り込めます。

## 自動更新（クラウドで動くのでPCは消してOK）

GitHub Actions が裏で情報を集めて更新します。**あなたのパソコンは電源OFFでも動きます。**

| 頻度（JST） | ジョブ | 内容 |
|---|---|---|
| 毎朝 7:00 | `hotel_auto_update.py` | クーポンID・料金の軽更新 |
| 毎週月曜 3:00 | `full_update.py` | 全3,705件の IN/OUT・部屋数・設備（39項目）を再取得 |
| 手動 | Actions タブ → Run workflow | 今すぐ更新 |

更新結果は自動で commit され、GitHub Pages に反映されます。

## 設備情報

カップルズ／ハピホテの詳細ページから、コスプレ無料・ハンディマッサージャー・美顔器・大型TV・Wi-Fi など **39項目** を抽出しています。
## GitHub Pages

https://taku010201040.github.io/hotel-pick/
