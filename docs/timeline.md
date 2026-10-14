# 技術タイムラインの更新設定

READMEに表示するのは技術名と活動時期だけです。GitHub Actionsが毎日06:17（日本時間、実行時刻は前後する場合あり）にコミットを取得し、週別データと明暗2種類のSVGを更新します。Actions → **Technology timeline** → **Run workflow** から手動実行もできます。マージ後に既定ブランチで有効になります。

## 公開リポジトリ

`data/sources.json` に、リポジトリと技術IDの対応を記載します。初期設定は依存関係を確認できた `cf`、`drop`、`insect_app` です。技術IDと表示名の一覧は `data/2026-baseline.json` にあります。`A / B` の行は、そのいずれかの技術を使うリポジトリを対応させます。

```json
[
  {
    "repo": "owner/repository",
    "technologies": ["axum", "postgresql-docker"]
  }
]
```

公開分はワークフロー付属の `GITHUB_TOKEN` で取得できます。技術の自動推測はせず、実際の利用を確認した対応のみ追加します。新しい技術を追加する場合はbaselineに `weeks: null` の行を追加し、そのIDを対応設定で参照します。

## 非公開リポジトリ

このリポジトリの **Settings → Secrets and variables → Actions** に、次のRepository secretsを設定します。

| Secret | 内容 |
| --- | --- |
| `PROFILE_READ_TOKEN` | 対象リポジトリの **Contents: Read-only** 権限を持つfine-grained PAT。取得対象の公開リポジトリにもアクセスできるものを使用します。 |
| `TIMELINE_SOURCES_JSON` | 上記と同じJSON配列。非公開リポジトリと技術IDの対応を記載します。公開設定に追加されます。 |

非公開リポジトリ名を公開ファイルに書く必要はありません。API応答、コミットメッセージ、SHA、ソースコード、非公開リポジトリ名を生成物に保存しません。公開されるのは技術ごとの活動週です。これらのSecretはPRのテストでは使用しません。

## 集計ルール

- 対象は2026年。週は月曜始まりで、1月1日を含む週がインデックス0です。月ラベルはその週の木曜が属する月です。
- 元の `assets/2026/overview.svg`（コミット `dfee4fc`）の18行・週別マスを `2026-baseline.json` に保存しています。2026/10/14までの記録をそのまま保持し、自動取得は既定で10/15以降です。以前の記録に時刻情報はないため、日本時間での再集計はしていません。
- 自動取得では、GitHubアカウント `ryotarofr` に紐づく著者のコミットを対象にします。botの著者は除外します。日時はREST APIの期間検索に合わせて `commit.committer.date` を日本時間に変換します。Co-authorだけの参加は含みません。
- 既定ブランチに到達可能なコミットを取得し、100件ずつ全ページを読みます。技術への直接変更の判定や言語行数の集計はしません。
- 対応設定の任意項目 `path` は集計対象ディレクトリ／ファイル、`ref` は対象ブランチ、`since` / `until` は日本時間の日付（両端を含む）です。過去の期間を確認できた場合は `since` を明示して再取得できます。技術を使っていなかった期間まで広げないようにしてください。
- 更新元がない行はbaselineの確認日より先を点で表示します。取得した行は取得対象期間の末日まで表示します。`weeks: null` の技術は、対応する本人のコミットが見つかるまで「時期未確認」です。
- 取得に失敗した場合は既存の図・データを変更せずジョブを失敗させます。Secretの削除や対応設定の変更で既存の活動が失われる場合も停止します。履歴を意図的に訂正する場合は、対応設定と保存済み `2026-activity.json` の該当行を一緒にレビュー・修正します。
- 2027年以降もこの図は2026年のものです。2026/12/31を上限に集計します。

## ローカルで確認

Python 3.13の標準ライブラリのみを使用します。

```sh
python -m unittest discover -s tests -v
python scripts/update_timeline.py --offline
python scripts/update_timeline.py --as-of 2026-10-15 --output-dir .timeline-preview
```

`--offline` は保存済み週別データから再描画します。API取得時の認証は環境変数 `PROFILE_READ_TOKEN`、未設定なら `GITHUB_TOKEN` を使用します。両方未設定でも公開APIで実行できますが、認証なしのレート制限が適用されます。トークンはコマンド引数に渡しません。
