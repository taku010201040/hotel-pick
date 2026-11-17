# ホテル比較ページ

`hotel-pick.html` を開くだけで、日付・場所・都道府県・地域でホテルを絞り込めます。

## 自動更新

GitHub Actions が裏で情報を集めて更新します。

| 頻度 | スクリプト | 内容 |
|---|---|---|
| 毎朝 7:00 JST | `hotel_auto_update.py` | 詳細調査済みのクーポン・料金を更新 |
| 毎週月曜 3:00 JST | `full_update.py` | 全3,705件の IN/OUT・部屋数・設備を再取得 |

更新結果は自動で commit されます。手動で実行したい場合は Actions タブの **Run workflow** を使ってください。

## GitHub Pages

リポジトリの Settings → Pages で Source を `main` / `root` にすると、
`https://<username>.github.io/<repo>/hotel-pick.html` で公開されます。
