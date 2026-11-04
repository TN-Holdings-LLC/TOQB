# 職場から家へ_2026-11-04（職場 → 家）：課題 A（Rust の SPD）、B（読み出し検査の下書き）、C（論文 7 の構成案）

記録時刻：2026-11-04 CET（`TZ=Europe/Zurich date`）。宣言はしていません。IBM・GitHub には接続していません。

## 中身

| ファイル | 内容 |
|---|---|
| `toqb_2026-11-04w.bundle` | TOQB a96b2cc..c1a1353（1 コミット）：`rust/spd/`、`notes/spd_2026-11-04/`、`notes/readout_rule_2026-11-04/`、`prereg/drafts-2026-11-04/readout_rule_DRAFT.md`、`notes/paper7_outline_2026-11-04.md` |
| `報告_2026-11-04.md` | 報告（日本語） |
| `SHA256SUMS.txt` | すべてのハッシュ |

psf-os は変えていません（9f773ff のまま）。バンドルはありません。

## 家での手順（VPN ON）

```bash
sha256sum -c SHA256SUMS.txt
git -C <TOQB> fetch <ここ>/toqb_2026-11-04w.bundle main && git -C <TOQB> merge --ff-only FETCH_HEAD   # c1a1353
(cd <TOQB>/rust/spd && cargo test --release)          # 4 tests
python <TOQB>/notes/spd_2026-11-04/spd_tables.py      # the tables of the report
# delta 3e-5 / 1e-5 on a many-core pod (CPU only):  OUT=/workspace/spd bash <TOQB>/notes/spd_2026-11-04/spd_pod.sh
```
