<div align="center">

<img src="assets/2026/overview.svg" width="800" alt="2026 年に作っていたものと使った技術を週ごとに並べた図。作っていたもの: 1〜2 月は solorium と tebiki、1〜6 月は Bevy の試作、3〜6 月は pxlot、4〜7 月は insect_app、7〜9 月は pxlot.ai、8 月末からカステリア戦記。使った技術: ゲームは Godot 4.7、Bevy と lightyear、Blender。Rust は Topcoat、Leptos と wgpu、Axum、Tauri・Slint・Dioxus。Web は SolidJS と Vite、Next.js と Drizzle、Astro、three.js。インフラは Cloudflare、PostgreSQL と Docker、さくらの VPS、Vercel と Neon。AI は Claude Code、Gemini と Seedance、Tripo 3D。色は書いた言語で、比率は Rust 31%、GDScript 23%、TypeScript 13%、JavaScript 6%、Python 11%、CSS・HTML ほか 16%。合計 624 コミット、121 日、23 リポジトリ（うち非公開 16）。">

</div>

いま手を動かしているのは `godot/cc_act`。ドット絵エディタ [pxlot.ai](https://pxlot.ai) を公開中。<sub>2026.10.14 更新</sub>

<details>
<summary>数字の出し方</summary>

<br>

- 対象は 2026/1/1〜10/14 にコミットのある 23 リポジトリ（うち非公開 16）。自分のコミットだけを数え、Copilot や bot のコミットは除いています。
- 「作っていたもの」の棒の高さは週のコミット数、色の積み重ねはその週に書いた行の言語の内訳、右端の数字は年間の合計です。
- 技術の行は、その技術を使うリポジトリにその週コミットがあればマスが点きます。色はその技術で書く言語で、インフラは灰色、AI サービスはピンクです。
- 言語の比率は `git log --numstat` の追加行と削除行の合計です。ビルド成果物、ロックファイル、自動生成ファイル、JSON などのデータは数えていません。TS には Astro を、「CSS・HTML ほか」には SQL, Go, C# なども含めています。

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
