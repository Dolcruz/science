# Independent station check for the Brawley event

Five stations with phase picks for CI41460424 were chosen outside the six used for detection and ranking. Four provided continuous records at the predicted candidate arrivals. CI.COK2 had an acquisition gap. Individual station channels, their public requests and file hashes are listed in `sources.csv`.

The transfer uses the published reference origin at 03:16:47.510 UTC and the candidate grid epoch at 03:30:01.960 UTC on 10 May 2026. The S-wave correlations at SB.WLA, NP.5056 and NP.5062 are 0.814, 0.622 and 0.723 at the predicted times. Each exceeds the result at all 595 local comparison times on the same channel. Two of the four P-wave correlations exceed all their local comparison values. NP.5062 has a weak P phase. Channel-level comparisons share an earthquake sequence and cannot be pooled as independent false-alarm probabilities.

Each phase uses a 1.6-second record starting 0.10 seconds before the network pick, filtered at 3–14 Hz. The plot overlays each pair at fixed time with mean and scale normalized separately. The CSV also reports the best correlation within ±0.12 seconds as a diagnostic. Controls repeat the fixed-time calculation at alternative placements every two seconds. The NPZ stores paired filtered sample windows in reference, candidate order. The image filename includes the number of stations attempted.

Install Python with numpy, scipy, matplotlib, requests and pymseed. Run `python phase_test.py cache results` to fetch the public records and recreate all derived outputs. [SCEDC reference event and phase picks](https://service.scedc.caltech.edu/fdsnws/event/1/query?eventid=41460424&includearrivals=true)
