# The 3D test with the floor probe, second run of 2026-11-06 (prereg/os3d_probe_2026-11-06.md): NOT RUN

- Record fetched 11:32:46 CET (ibm_marrakesh; failed qubits and coupler the same as the first run's record).
- Probe job dbmqpl674qds73dsrnfg (4 circuits, 5.3 s by the model) submitted 11:32:54 CET; the home Claude rebuilt it
  from the same record: the same gates (71a3c2b0d17b).
- The queue had grown (87 pending at about 13:00 CET). The probe stayed pending for 96 min 44 s; the owner cancelled
  it at 13:09 CET (0 s on the QPU). No main job was built or submitted, no answers file written.
- Why stopped: the declaration assumes the main job runs soon after the probe; with the queue, the gap between the
  probe's floors and the main run would have been hours, so the choice would rest on stale floors.
- Also a procedure fault on the home side: the night's command list ran every step without checking that the probe's
  counts were back (the probe was still queued after a 30-minute collect; the later steps failed on missing files
  and did nothing). The commands now go on only when the previous step's file exists.
- Next (draft): the probe inside the main job (every candidate's arm and floors in one job, the arm chosen by its
  floors only), so no queue can separate the reading from the run.
