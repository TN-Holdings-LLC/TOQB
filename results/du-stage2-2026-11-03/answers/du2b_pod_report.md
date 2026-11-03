# du2b POD 実行報告（VS Code の Claude、2026-11-03、2回目）

結果：**DONE**（`== DONE: /workspace/du2_answers.zip`）。キットのファイルは変更していない。結果の解釈はしていない。

## 実行環境
- POD：RunPod unuxvjb0h3oh3n、**NVIDIA H100 80GB HBM3**（81559 MiB）、Secure Cloud、3.99 USD/時
- イメージ：runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04、Python 3.11
- キット：du2_pod_kit_2026-11-03b.zip、sha256 3a8996dc…5cb2f1bc（手元と POD で一致）、COMMIT.txt `fa6b9eb`、du_answers.py 138行目 `-std=c++17`
- pip：`pip install "qiskit==2.5.2" "cupy-cuda12x==14.2.0" pytest` → qiskit 2.5.2、cupy 14.2.0、numpy 2.4.6、pytest 9.2.0（指示どおりの版）
- 起動：`OUT=/workspace/du2 nohup bash TOQB/gpu/du_answers_pod.sh > du2.txt 2>&1 < /dev/null &`（新しい POD、/workspace/du2 は無い状態から）

## times.txt
```
toqb fa6b9eb gpu/du_answers.py: compile the CUDA kernels with -st
note cb97a0c200635320dec2d3f63b5f312aad8210defceefea7009f9a0ac1764d65  prereg/drafts-2026-11-03/du_stage2_note.md
script 9e35e8889ea76e06a22ef4e0b2a255565d0284d03cf670912ca2ff1441ae6cbb  gpu/du_answers.py
NVIDIA H100 80GB HBM3, 81559 MiB
start 2026-11-03 02:46:36 CET
end 2026-11-03 03:00:25 CET
```

## テストと照合（du2.txt より、そのまま）
- テスト：`4 passed in 0.51s`
```
C1 b 0.785398 single: max |GPU - numpy| 1.03e-05
C1 b 0.785398 double: max |GPU - numpy| 2.11e-15
C1 b 0.685398 single: max |GPU - numpy| 8.63e-06
C1 b 0.685398 double: max |GPU - numpy| 2.11e-15
C1 b 0.585398 single: max |GPU - numpy| 2.86e-06
C1 b 0.585398 double: max |GPU - numpy| 2.11e-15
C2 b 0.685398: max |single - double| 1.29e-05
C2 b 0.585398: max |single - double| 3.56e-06
C3 h 0.0: max |GPU - closed form| 3.47e-05, norm 3.47e-05
C3 h 0.15: max |GPU - closed form| 2.03e-05, norm 4.22e-05
answers.json sha256 b5ba060d0411b0bde8dd48fe64b9d548d3fd1022bcf398b1996bfdb1f214b4b7
```
本計算（N=33、t≤16）は4設定とも各 124 秒。

## 回収したファイル（このフォルダ）
| ファイル | sha256（先頭16桁） |
|---|---|
| du2_answers.zip | 7b5ea110e253223d |
| du2.txt | ce9c1cff38b669fd |
| du2/answers.json | b5ba060d0411b0bd（du2.txt の answers.json sha256 の行と一致） |
| du2/checks.json | bbe89123b2f42f21 |
| du2/progress.txt | b1a48dda06c535e5 |
| du2/times.txt | fdab8975784d15f2 |
| du2/check_tests.log | d23041cfe2de1c1c |

## 指示書にない点（報告のみ）
- b キットの psf-os は、1回目のキットと比べて `circuits.py` の `kising_forward_cone` と `job.py` の `cone_answers`（および kising_forward の cone 分岐）が無い。dual.py は1回目と同一で、dual.py・du_answers.py・テストのどれもこの2関数を使わないため、今回の計算には関係しない。
- 起動に使った SSH は計算が終わるまで戻らなかった（計算には影響なし）。終了の確認は別の SSH で1分ごとに行った。

## POD の費用
- 作成 10:45:18、削除 11:01:26（このPCの時計）。約16分 × 3.99 USD/時 ≈ **1.07 USD**
- RunPod の残高：作業前 32.13 USD → 削除後 31.07 USD（1回目の約 0.20 USD を含めて反映されている可能性がある）
- 削除後、残っている POD は0台、課金は 0 USD/時
