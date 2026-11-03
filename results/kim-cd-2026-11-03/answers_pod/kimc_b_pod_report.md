# kimc POD 実行報告（VS Code の Claude、2026-11-03、2回目）

結果：**DONE**（`== DONE: /workspace/kimc_answers.zip`）。キット、スクリプト、許容値、lattice.json は変更していない。結果の解釈はしていない。

## 実行環境
- POD：RunPod ymtve9s3pdghw3、**NVIDIA H200**（143771 MiB）、Secure Cloud、5.29 USD/時
  - 作成時に H100 80GB の空きがなく、作成スクリプトの第3候補（du2 の指示書で代わりとして認められていた H200）が割り当てられた
- イメージ：runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04、Python 3.11
- キット：1回目と同じ kimc_pod_kit_2026-11-03.zip、sha256 1f3ef2a0ae87b047…（手元と POD で一致）、COMMIT.txt `e55e98a`
- pip：`pip install "qiskit==2.5.2" "qiskit-aer==0.18.0" "cupy-cuda12x==14.2.0" pytest` → qiskit 2.5.2、qiskit-aer 0.18.0、cupy 14.2.0、numpy 2.4.6、pytest 9.2.0
- 起動：`OUT=/workspace/kimc nohup bash TOQB/gpu/kim_answers_pod.sh > kimc.txt 2>&1 < /dev/null &`
- 安全装置：POD の中に「4時間後に POD を止める」待機処理を置いた（キットの外）。POD は削除済み

## times.txt
```
toqb e55e98a P5 stages C/D: job built from the fetch of 11:14:47
note a07dad9f74a2df4984bca777b53be2ef08537d4a48e6c2dcec3af21411175006  prereg/drafts-2026-11-03/kim_cd_note.md
lattice 5896ff1d398463cf8f26674f235897c3916053a91ac1146110415205279b1240  /workspace/lattice.json
script 46036286f1471e0de83a9664188fc28cf516075f402cf11c24df669b96f4fc2d  gpu/kim_answers.py
NVIDIA H200, 143771 MiB
start 2026-11-03 11:26:58 CET
end 2026-11-03 12:06:29 CET
```

## テストと照合（kimc.txt より、そのまま）
- テスト：`6 passed in 0.67s`
```
K1 theta 0.8 t 5: max |GPU - CPU| 2.09e-06
K2 cones [30, 30, 31, 31, 31]: max |single - double| 3.56e-06
K3 theta pi/2 t 6: 151 qubits, max |GPU - stabilizer| 0.00e+00
K3 theta pi/2 t 7: 122 qubits, max |GPU - stabilizer| 0.00e+00
answers_C.json sha256 b11c30e8e06c18b8d047f63580431175f94d7af1fbb31bdeb5d5e18b00797c09
```
本計算の行（θ 3種 × t=6,7,8）は kimc.txt を参照。時間は t=6 が各 31 秒、t=7 が各 299 秒、t=8 が各 328 秒。

## 回収したファイル（このフォルダ）
| ファイル | sha256（先頭16桁） |
|---|---|
| kimc_answers.zip | 7e35000ea8bbf1a9 |
| kimc.txt | b46199a753d89de8 |
| kimc/answers_C.json | b11c30e8e06c18b8（kimc.txt の answers_C.json sha256 の行と一致） |
| kimc/checks.json | bd3d387d99d0717e |
| kimc/progress.txt | b386183b476a0a75 |
| kimc/times.txt | 93fcc4635a81d516 |
| kimc/check_tests.log | f7c1fdc3644d020b |

## POD の費用
- 作成 19:25:27、削除 20:07:35（このPCの時計）。約42分 × 5.29 USD/時 ≈ **3.71 USD**
- RunPod の残高：作業前 30.86 USD → 削除後 27.33 USD（反映の遅れがあり得る）
- 削除後、残っている POD は0台、課金は 0 USD/時
