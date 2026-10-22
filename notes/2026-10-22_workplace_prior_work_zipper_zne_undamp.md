# Prior work for the zipper, ZNE by zip-unzip folding and the undamped readout (workplace, 2026-10-22, as received; a short search, abstracts mostly; not checked at home)

少し調べました。結論から言うと、どの考え方にもよく似た先行研究があります。私たちに独自なのは組み合わせ方だけで、それも新しいとは言い切れません。

| 私たちの考え | 似た先行研究 | 違い（私たちの側） |
|---|---|---|
| **「ジップ＋アンジップ」でノイズを増やして外挿する** | ゼロノイズ外挿を回路の「折り重ね」で行う方法（G → G G† G）は確立しています（Giurgica-Tiron ら 2020）。指定した層だけを折り重ねて多変数で外挿する方法もあります（Russo と Mari、2024） | 折り重ねる単位に、ジッパーの「行って戻る」組（恒等になる、もつれ部分だけのまとまり）を使う点。考え方そのものは層ごとの折り重ねと同じです |
| **ジッパー（CZ と SWAP をまとめて 2 CZ にする）** | 相互作用ゲートと SWAP を 1 つにまとめる「swap network」は既知です（O'Gorman ら 2019）。CZ 2 個で実現できる場合も実験されています（Hashim ら 2021。こちらはリング状の回路そのものは扱っていません） | 「輪を線の上に、1 層 5n/2 − 4 個の CZ で載せる」具体的な並べ方と、それをテンプレートの選択肢に入れたこと。今回の検索では、同じものは見つかりませんでした |
| **アンダンプ（一様な縮みを式で戻す）** | 全体に一様な縮み（大域的な脱分極）を割り戻す方法は既知です（Vovrosh ら 2021、Urbanek ら PRL 2021。後者は推定用の回路で縮みを測ります） | 縮みの大きさを、実機ではなくツインで、ラベルなしで決める点 |
| **実機の上でノイズの違いを使う** | 量子ビットの配置を巡回させて、誤差の違いから外挿する方法（CLP-ZNE、2026） | ノイズを変える手段が、配置ではなく行って戻る組である点 |

**読み取れること**

- 「ジップしてほどくときにフィルターを掛ける」という発想は、方向として筋がよく、他の研究者も同じ方向で成果を出しています。
- 新しさを主張できる余地があるのは、ジッパーの並べ方そのものと、「ジッパーの往復を折り重ねの単位に使うゼロノイズ外挿」の組み合わせくらいです。ただし、今回の検索は短時間で、要旨中心にしか読めていません。新しいと書く前には、もっと広く調べる必要があります。
- アンダンプの前提（縮みが一様）が成り立つかについても研究があります（浅い回路で局所的なノイズが一様なノイズになるか、2023）。L16 で λ が回路やモデルによって大きく違ったことと関係しそうです。

**書くときの言い方の案：** 「ジッパーは swap network の考え方（O'Gorman ら）を輪の分類器に当てはめたもの。ノイズの軽減は、層ごとの折り重ねによるゼロノイズ外挿（Giurgica-Tiron ら、Russo と Mari）を、ジッパーの往復を単位にして行ったもの」。新しさについては「引用した文献には見当たらない」までにとどめます。

Sources:
- [Digital zero noise extrapolation for quantum error mitigation (arXiv 2005.10921)](https://arxiv.org/pdf/2005.10921)
- [Quantum error mitigation by layerwise Richardson extrapolation (arXiv 2402.04000)](https://www.arxiv.org/pdf/2402.04000)
- [Mitiq: noise scaling methods](https://mitiq.readthedocs.io/en/stable/examples/scaling.html)
- [Best practices for quantum error mitigation with digital ZNE (arXiv 2307.05203)](https://arxiv.org/pdf/2307.05203)
- [Generalized swap networks for near-term quantum computing (arXiv 1905.05118)](https://ar5iv.labs.arxiv.org/html/1905.05118)
- [Optimized fermionic SWAP networks with equivalent circuit averaging for QAOA (arXiv 2111.04572)](https://arxiv.org/pdf/2111.04572)
- [Simple Mitigation of Global Depolarizing Errors in Quantum Simulations (arXiv 2101.01690)](https://arxiv.org/pdf/2101.01690)
- [Mitigating depolarizing noise with noise estimation circuits (PRL 127, 270502)](https://link.aps.org/accepted/10.1103/PhysRevLett.127.270502)
- [Zero-Noise Extrapolation via Cyclic Permutations of Quantum Circuit Layouts (arXiv 2511.02901)](https://arxiv.org/html/2511.02901)
- [Can shallow quantum circuits scramble local noise into global white noise? (arXiv 2302.00881)](https://arxiv.org/pdf/2302.00881)