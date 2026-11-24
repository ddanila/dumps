# Robotron PC1715

ROMs from three PC1715 machines and two keyboards. Board IDs (MB001, MB002,
PC002) are the owner's labels for each unit, not factory provenance.

| Folder | Contents | Result |
| --- | --- | --- |
| [mb001/](mb001/) | A25.3 boot, A25.1/A25.2 character ROMs | Known S502 boot; S643/S605 character ROMs |
| [mb002/](mb002/) | A25.3 boot (chip originally from MB001) | S502, identical to MB001; the reported boot issue is not explained by ROM contents |
| [pc002/](pc002/) | A25.3 boot, A25.1/A25.2 character ROMs | S502 boot as MB001; S619 character ROM differs |
| [keyboard-s642-jcuken/](keyboard-s642-jcuken/) | S642 keyboard firmware, ЙЦУКЕН/JCUKEN legends | Matrix, modifier and language-toggle tests pass in MAME |
| [keyboard-s642-qwerty/](keyboard-s642-qwerty/) | S642 keyboard firmware, QWERTY/ЯВЕРТЫ legends | Differs from JCUKEN only in keycode tables; end-to-end tests pass |
