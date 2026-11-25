# A fixed reconstruction filter helps, but does not settle the DAC route

The [nonperiodic dibit holdout](PHOTO-RANDOM-DIBIT-VALIDATION.md) reduced
the 12 photo-B5-compatible DAC bus orders to six. The earlier
[waveform-shape screen](PHOTO-JOINT-WAVEFORM-SHAPE.md) ranked a different,
now-rejected order highest at R²≈0.757. Shape fit and generalization
therefore pull in different directions; that old maximum cannot be used
as evidence for the surviving bus family.

The [reproducible continuation](photo_survivor_filter_validation.py) checks
each surviving bus against both standard A3→A4 streams and four independent
64-symbol random streams. It first reconstructs the joined `129` byte path
and matches its full-stream hash to the saved real-PROM execution. The
unfiltered standard-stream fits also match the saved shape report. It then
applies the **same fixed** one-pole rule to every sequence:

`filtered[n] = 0.75 * DAC[n] + 0.25 * filtered[n-1]`

| Stream family | Bus/stream cases | Mean raw R² | Mean filtered R² | Filtered decision errors |
| --- | ---: | ---: | ---: | ---: |
| GPC/GPA A3→A4 | 12 | 0.654 | 0.705 | 0/744 |
| Four seeded 64-symbol streams | 24 | 0.595 | 0.647 | 0/1,488 |

Every one of the 36 shape fits improves; the filtered R² range is
0.628–0.716. All six buses also retain the 2,100 Hz peak in a 32-symbol
candidate tone. The fit still falls well short of the reference's own
R²≈1, so this simple analog continuation does not supply a complete
pulse-shaped line waveform. The [saved report](results/photo-survivor-filter-validation.json)
contains all scores, tone peaks and source hashes.

The filter coefficient is an illustrative fixed hypothesis. No Nokia RC
values, 74LS373/74LS273 clock or full DAC bus have been measured or traced.
Two random streams have full-PROM-checked 32-symbol prefixes; the rest of
the random outputs are recurrence projections. This result keeps the
surviving digital phase path
compatible with modest analog smoothing; it does not establish C2, C3 or C4.
