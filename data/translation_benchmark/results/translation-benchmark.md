# Translation benchmark

This file is generated from the committed RSS corpus; human references and scores remain blank.

## Runtime

- Measured at (UTC): 2026-08-05T05:37:52.391680+00:00
- Platform: macOS-26.5.2-arm64-arm-64bit
- Python: 3.12.13
- Machine: arm64
- CPU count: 10
- Torch: 2.8.0
- Transformers: 4.57.6

## Candidate measurements

| Candidate     | Status      | Revision                                 | Acquisition ms | Inference total ms | Inference avg ms | Peak MB | Failure/notes                                                                                                                                                                 |
| ------------- | ----------- | ---------------------------------------- | -------------: | -----------------: | ---------------: | ------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| argos-en-ja   | available   | 1.1:en_ja                                |       1717.396 |          21187.471 |          264.843 |  567.22 | —                                                                                                                                                                             |
| opus-mt-en-ja | available   | a863894cdd2b80f3bc1c5966734aee9ffec207d1 |      22723.716 |          18956.901 |          236.961 | 1055.88 | —                                                                                                                                                                             |
| fugumt-en-ja  | available   | fbb91252110cf97d90291eb808629ab0b10f7928 |      18926.575 |           9435.233 |           117.94 |  786.55 | —                                                                                                                                                                             |
| m2m100-418m   | unavailable | unknown                                  |              — |                  — |                — |       — | The M2M100 benchmark process was terminated during generation before the runner wrote result files; timing, memory, acquisition, cache, and revision values are not measured. |

## Quality and fidelity aggregates

| Candidate     | Target  | Available | Gate passed | Gate rejected |  Avg ms | Numbers | URLs | Proper nouns |
| ------------- | ------- | --------: | ----------: | ------------: | ------: | ------: | ---: | -----------: |
| argos-en-ja   | summary |     40/40 |          36 |             4 | 274.959 |   18/18 |  0/0 |        34/36 |
| argos-en-ja   | title   |     40/40 |          40 |             0 | 254.728 |     9/9 |  0/0 |        26/26 |
| opus-mt-en-ja | summary |     40/40 |          13 |            27 | 305.582 |    0/18 |  0/0 |         0/36 |
| opus-mt-en-ja | title   |     40/40 |          14 |            26 |  168.34 |     0/9 |  0/0 |         0/26 |
| fugumt-en-ja  | summary |     40/40 |          32 |             8 |  156.98 |   12/18 |  0/0 |        30/36 |
| fugumt-en-ja  | title   |     40/40 |          34 |             6 |  78.901 |     7/9 |  0/0 |        21/26 |
| m2m100-418m   | title   |      0/40 |           0 |             0 |       — |     0/0 |  0/0 |          0/0 |
| m2m100-418m   | summary |      0/40 |           0 |             0 |       — |     0/0 |  0/0 |          0/0 |
