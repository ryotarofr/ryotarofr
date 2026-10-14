<div align="center">

<img src="assets/2026/hero.svg" width="800" alt="2026 年のコミットを 1 日 1 マスで並べたカレンダー。色はその日いちばん多く書いた言語。1〜7 月は Rust と Web が交互に並び、8 月末から GDScript（Godot）の日が続いている。合計 624 コミット、121 日、23 リポジトリ。">

</div>

いま手を動かしているのは `godot/cc_act`。ドット絵エディタ [pxlot.ai](https://pxlot.ai) を公開中。

<sub>2026.10.14 更新</sub>

## 2026 年に書いた言語

前半は Rust と Web、秋からは Godot のゲームづくりで GDScript と Python が一気に増えました。

<img src="assets/2026/languages.svg" width="800" alt="変更行数で見た言語の比率。Web（TypeScript, CSS, HTML, JavaScript）33.4%、Rust 31.2%、GDScript 23.4%、Python 10.8%、その他 1.2%。月ごとの棒では、GDScript と Python が 9〜10 月に集中し、Web は 1〜7 月が中心。">

## 作っていたもの

週ごとのコミット数をプロジェクト別に並べました。鍵の付いたものは非公開リポジトリです。

<img src="assets/2026/timeline.svg" width="800" alt="プロジェクト別のタイムライン。1〜2 月は solorium（Next.js）と tebiki（Tauri, SolidJS）、2〜6 月は Bevy の試作と pxlot（Leptos, wgpu）、4〜7 月は insect_app（SolidStart, Axum）、7〜9 月は pxlot.ai（Topcoat, 生成AI）、8 月末からはカステリア戦記（Godot 4.7, Cloudflare Workers）が中心。">

## 使った道具

右のメモリが 1〜10 月です。点いている月に、その技術を使うリポジトリを触っています。

<img src="assets/2026/inventory.svg" width="800" alt="使った技術の一覧。ゲーム: Godot 4.7, GDScript, Bevy, lightyear, Blender, three.js。生成AI と道具: Claude Code, Gemini 画像生成, Seedance 動画, Tripo 3D, Anthropic API, Pillow と NumPy, bun。Rust のアプリ: Topcoat, Leptos, wgpu と winit, UniFFI, Axum, Tauri, Slint, Dioxus。Web フロント: SolidJS, Astro, Vite, Next.js, TypeScript 7。サーバーとインフラ: Cloudflare Workers と D1, Durable Objects, Cloudflare Pages, PostgreSQL と sqlx, Docker, さくらの VPS, Vercel と Neon, GitHub Actions。業務: AWS Lambda, API Gateway と Cognito, Azure OpenAI, Azure AI Search, Terraform, FastAPI と React。">

## 2027 年へ

1〜4 月と 8〜10 月で書いた行の比率を比べると、重心は Web と Rust からゲームの側へ移っています。

<img src="assets/2026/next.svg" width="800" alt="左は書いた行の比率の変化。1〜4 月から 8〜10 月で、Web 54%→17%、Rust 41%→23%、GDScript 0%→42%、Python 2%→18%。右は 2027 年の見立て。伸ばす: Godot 4.7 でゲーム本編、Cloudflare Workers・D1・Durable Objects、生成AI で素材を作る工程、Blender と Python の素材ツール。続ける: Rust と Topcoat（pxlot.ai）、Claude Code 前提の開発、PostgreSQL・Docker・bun。ひと区切り: Bevy、Leptos、Tauri・Dioxus・Slint の試作、Next.js と Vercel・Neon。">

<details>
<summary>数字の出し方</summary>

<br>

- 対象は 2026/1/1〜10/14 にコミットのある 23 リポジトリ（うち非公開 16）。自分のコミットだけを数え、Copilot や bot のコミットは除いています。
- 言語の量は `git log --numstat` の追加行と削除行の合計です。ビルド成果物、ロックファイル、自動生成ファイル、JSON などのデータは数えていません。
- カレンダーの色は、その日にいちばん多く変更した言語の分類です。コードの変更がない日は「その他・文書」にしています。
- 「Web」は TypeScript, CSS, HTML, JavaScript, Astro をまとめたものです。

| 言語 | 変更行 | 比率 |
| --- | ---: | ---: |
| Rust | 336,043 | 31.2% |
| GDScript | 252,690 | 23.4% |
| TypeScript | 137,191 | 12.7% |
| Python | 116,021 | 10.8% |
| CSS | 90,640 | 8.4% |
| HTML | 66,702 | 6.2% |
| JavaScript | 64,023 | 5.9% |
| SQL | 7,548 | 0.7% |
| Go | 3,049 | 0.3% |
| Astro | 2,087 | 0.2% |
| C# | 1,000 | 0.1% |
| Kotlin, Swift, Shell, Dockerfile, WGSL, C | 1,552 | 0.1% |

図の文字は [DotGothic16](https://github.com/fontworks-fonts/DotGothic16)（SIL Open Font License 1.1）をアウトライン化して使っています。

</details>
