# isingL 2026-11-10: device

- Queue 11:23:22 CET: marrakesh 0, fez 0, kingston 0; by the declared order (ties: marrakesh, fez, kingston) the
  first is ibm_marrakesh, where a 4 x 2 x 2 fold translation fits.
- On ibm_marrakesh (failed qubits 30, 32, 34, 41, 46, 47, 48, 56, 73, 82, 113, 119, 130, 136; coupler 113-119) the
  build stops at the ring sentinel: psf_os.sentinel.build "the sentinel did not land on the user's ring" (twice,
  the second after 523 s). The declared job (arms, floors, mirrors and one ring sentinel) cannot be built there.
- Owner, 2026-11-10 19:51 JST (choice 1 of three offered): treat this as not placeable and take the next device in
  the declared order: ibm_fez. The partial marrakesh builds are kept outside the repository (_to_delete).
