"""Screen hypothetical 8251A FF sync hunt and character alignment."""

import hashlib
import json
from pathlib import Path

from receiver_mask04_serial_candidate import HERE, SOURCE, bytes_lsb_first, decode
from common import save


def recovered_bits(case):
    dibits = decode(case)
    bits = [bit for dibit in dibits[1:]
            for bit in (dibit & 1, (dibit >> 1) & 1)]
    if len(bits) != 94 or bits[:62] != [1] * 62:
        raise ValueError('recovered preamble or data changed')
    return bits


def hunt(bits, leading_ones, hunt_start):
    """First all-one eight-bit window locks; group later bits into bytes.

    This is a deliberately simple external 8251A model, not an emulated chip.
    leading_ones includes the first preamble dibit, which has no measured
    differential phase, and possibly earlier FF fill. hunt_start is a
    hypothetical RxC/hunt-entry phase.
    """
    stream = [1] * leading_ones + bits
    data_start = leading_ones + 62
    sync_end = next((end for end in range(hunt_start + 8, data_start + 1)
                     if stream[end - 8:end] == [1] * 8), None)
    if sync_end is None:
        raise ValueError('FF sync not detected within preamble')
    residue = (data_start - sync_end) % 8
    sync_fill = bytes_lsb_first(stream[sync_end:data_start]) if residue == 0 else None
    data_bytes = (bytes_lsb_first(stream[data_start:data_start + 32])
                  if residue == 0 else None)
    return dict(leading_unobserved_ones=leading_ones,
                hunt_start_bit=hunt_start,
                first_sync_end_bit=sync_end,
                data_start_bit=data_start,
                data_start_offset_in_character=residue,
                whole_ff_characters_before_data=len(sync_fill) if sync_fill is not None else None,
                received_data_bytes=[f'{value:02X}' for value in data_bytes]
                if data_bytes is not None else None)


def run(out=HERE / 'results/receiver-mask04-sync-hunt-alignment.json'):
    source = json.loads(SOURCE.read_text())
    cases = []
    for case in source['cases']:
        bits = recovered_bits(case)
        grid = [hunt(bits, leading, start)
                for leading in range(8) for start in range(8)]
        aligned = [cell for cell in grid
                   if cell['data_start_offset_in_character'] == 0]
        if (len(aligned) != 8 or
                any(cell['received_data_bytes'] != aligned[0]['received_data_bytes']
                    for cell in aligned) or
                hunt(bits, 2, 0)['whole_ff_characters_before_data'] != 7):
            raise ValueError('sync-hunt alignment invariant changed')
        cases.append(dict(degrees=case['degrees'], seed=case['seed'],
                          trace_digest=case['trace_digest'],
                          recovered_bit_sha256=hashlib.sha256(bytes(bits)).hexdigest(),
                          measured_preamble_ones=62, data_bits=32,
                          nominal_32_symbol_ff_case=hunt(bits, 2, 0),
                          aligned_phase_pairs=[dict(leading_unobserved_ones=cell['leading_unobserved_ones'],
                                                    hunt_start_bit=cell['hunt_start_bit'])
                                               for cell in aligned],
                          offsets_by_leading_ones=[
                              [grid[leading * 8 + start]['data_start_offset_in_character']
                               for start in range(8)] for leading in range(8)]))
    if (len(cases) != 4 or
            any(cases[0]['aligned_phase_pairs'] != item['aligned_phase_pairs']
                for item in cases[1:])):
        raise ValueError('four-case phase screen changed')
    paths = (Path(__file__), SOURCE,
             HERE / 'receiver_mask04_serial_candidate.py')
    report = dict(experiment='hypothetical FF sync-hunt and eight-bit character alignment',
                  model=dict(sync_character='FF', bit_order='least significant bit first',
                             leading_unobserved_one_bits=list(range(8)),
                             hunt_start_bit_offsets=list(range(8)),
                             first_matching_eight_bit_window_ends_hunt=True,
                             character_groups_begin_immediately_after_match=True),
                  cases=cases,
                  conclusion='The FF preamble permits character acquisition but does not uniquely locate the first data-byte boundary without a known first dibit and RxC/hunt-entry phase.',
                  limitations=['The first preamble dibit is unobserved in the decoded output; two leading ones would reproduce the supplied reference preamble, while other leading counts also allow earlier fill or truncated observation.',
                               'Sync hunt is a simplified external model, not an executed DSC instruction or observed 8251A receive event.',
                               'The RxD route, RxC phase, oscillator divisor and initial hunt-entry timing remain untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
