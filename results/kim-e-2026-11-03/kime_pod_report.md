# kime POD 実行報告（VS Code の Claude、2026-11-03〜04、1回目）

結果：**K、X ともに DONE**（`== DONE: /workspace/eK_answers.zip`、`== DONE: /workspace/eX_answers.zip`）。キット、スクリプト、許容値、lattice_*.json は変更していない。結果の解釈はしていない。

## 実行環境
- POD：RunPod 8xnzyk6nfnqk18、**NVIDIA H100 80GB HBM3**（81559 MiB）、Secure Cloud、3.99 USD/時
- イメージ：runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04、Python 3.11
- キット：kime_pod_kit_2026-11-03.zip、sha256 e243cb099e64142c…（指示書・手元・POD で一致）
  - COMMIT.txt：`39eba6f P5 stage E: queue read at 15:04:01 CET (ibm_fez 1, i`（先頭のみ表示される行。指示書の宣言コミットは a7ad206）
  - kim_e_note.md sha256 c3dca91e89bc2b2166d179c0ed0d118fd696c56a961516dfd22e0e78538e4528（指示書と一致）
  - lattice_K.json sha256 6f7be4d1ebc811a1e9b908207536900066dc0543710a1c7b68c7e53a4a000252
  - lattice_X.json sha256 f155e92511f0633c892b1d277acc04fd0d333d2c18577bdb6e2b09b5dbde03be
- pip：指示どおり → qiskit 2.5.2、qiskit-aer 0.18.0、cupy 14.2.0、numpy 2.4.6、pytest 9.2.0
- 起動：指示書の `nohup bash -c 'OUT=/workspace/eK ... && OUT=/workspace/eX ...' ... &` をそのまま実行
- 安全装置：POD の中に「4時間後に POD を止める」待機処理を置いた（キットの外）。POD は削除済み

## K（lattice_K.json）
- 開始 2026-11-03 15:17:19 CET、終了 2026-11-03 16:03:43 CET
```
K1 theta 0.8 t 5: max |GPU - CPU| 2.09e-06
K2 cones [28, 29, 29, 30, 30]: max |single - double| 3.43e-06
K3 theta pi/2 t 6: 125 qubits, max |GPU - stabilizer| 0.00e+00
K3 theta pi/2 t 7: 108 qubits, max |GPU - stabilizer| 0.00e+00
answers_C.json sha256 07d6aaa48b69b01bd2c49933d3290b39f28a332239e90822c6121af56a4b86e0
```

## X（lattice_X.json）
- 開始 2026-11-03 16:03:45 CET、終了 2026-11-03 17:00:02 CET
```
K1 theta 0.8 t 5: max |GPU - CPU| 2.09e-06
K2 cones [31, 31, 31, 31, 31]: max |single - double| 3.56e-06
K3 theta pi/2 t 6: 153 qubits, max |GPU - stabilizer| 0.00e+00
K3 theta pi/2 t 7: 95 qubits, max |GPU - stabilizer| 0.00e+00
answers_C.json sha256 4c0b7ce9e0236e5940d78cddb3ca63c2f36f343beb28e9d17332817bc53f6b64
```
本計算の行（θ 3種 × t=6,7,8）は eK.txt、eX.txt を参照。

## 回収したファイル（このフォルダ）
| ファイル | sha256（先頭16桁、POD 上と一致） |
|---|---|
| eK_answers.zip | b75efe2255bca799 |
| eX_answers.zip | aba9aeabc5572cb8 |
| eK.txt | 291d35aedaff8778 |
| eX.txt | 1366add58fcd9b5c |
| eK/answers_C.json | 07d6aaa48b69b01b |
| eK/checks.json | 2bbc222d0c355867 |
| eK/check_tests.log | 349608bc56172095 |
| eK/progress.txt | db9d599cd58a5d77 |
| eK/times.txt | d641a4f72240a3ee |
| eX/answers_C.json | 4c0b7ce9e0236e59 |
| eX/checks.json | 406aa5d4174bb68e |
| eX/check_tests.log | b73d935be7a6cc24 |
| eX/progress.txt | c2697c6de8bb0de7 |
| eX/times.txt | 13cf6e79920a01df |

## POD の費用
- 作成 2026-11-03 23:16:06、削除 2026-11-04 01:01:48（このPCの時計）。約106分 × 3.99 USD/時 ≈ **7.03 USD**
- RunPod の残高：作業前 27.33 USD → 削除後 20.15 USD（差 7.18 USD。反映の遅れ・端数があり得る）
- 削除後、残っている POD は0台、課金は 0 USD/時
