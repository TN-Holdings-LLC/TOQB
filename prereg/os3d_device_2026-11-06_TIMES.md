# Correction of recorded times (2026-11-06; the declared file prereg/os3d_device_2026-11-06.md is not changed)

The home Claude set the commit dates of these commits by hand, and they ran ahead of the clock (found by the
workplace, 06e). The wall-clock times, from the owner's messages (JST - 8 h = CET):

| commit | commit date as recorded | actual (CET) |
|---|---|---|
| e5f95b5 (psf-os, grid3d.prepare) | 07:29 | between 07:09 and 07:16 |
| b34689a (TOQB, os3d_compare_build) | 07:30 | between 07:09 and 07:16 |
| f630bf3 (TOQB, the declaration) | 07:50 | between 07:16 (owner's go) and 07:32 |

The order is unchanged (the owner's go at 07:16, then the declaration; no device record of the night fetched yet).
What makes "declared before the fetch" checkable by others is the GitHub push of f630bf3 before the night's fetch and
the IBM job timestamps, not the commit date. From this commit on, commit dates are the machine's clock
(TZ=Europe/Zurich), not set by hand.
