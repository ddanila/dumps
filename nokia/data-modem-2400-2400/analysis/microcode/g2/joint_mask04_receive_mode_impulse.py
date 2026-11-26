"""Test one ADC pulse under held candidate controller mode bytes at 3EB."""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_receive_impulse_memory as impulse
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured as original_configured
from reference_modem import transmit

MODES = (0x01, 0x81, 0xA1)
SOURCE = HERE / 'results/joint-mask04-receive-impulse-memory.json'


def capture_with_mode(mapping, base, values, mode):
    def configured(base_, values_, timing, source, polarity):
        scenario = original_configured(base_, values_, timing, source, polarity)
        scenario['io']['read']['pc_sequences'][str(0x3EB)] = [mode] * (
            4 * impulse.ADC_VISITS + 1)
        scenario['io']['read']['evidence'] += (
            '; candidate held controller frame byte at 3EB D; wire untraced')
        return scenario
    with patch.object(impulse, 'configured', configured):
        return impulse.capture(mapping, base, values)


def run(out=HERE / 'results/joint-mask04-receive-mode-impulse.json'):
    prior = json.loads(SOURCE.read_text())
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    samples = [127 - value for value in transmit(impulse.VARYING_DIBITS)]
    if (len(samples) != impulse.SAMPLES or
            samples[impulse.VARYING_PULSE_SAMPLE] != 0x51):
        raise ValueError('varying ADC fixture changed')
    cases = []
    comparisons = {}
    for mode in MODES:
        streams = {}
        for name, pulse in (('baseline', None),
                            ('high_nibble_pulse', impulse.VARYING_HIGH_PULSE_ADC),
                            ('low_nibble_pulse', impulse.VARYING_LOW_PULSE_ADC)):
            values = impulse.held_samples(
                samples, impulse.VARYING_PULSE_SAMPLE, pulse)
            rows, trace = capture_with_mode(mapping, base, values, mode)
            streams[name] = rows
            entry = dict(mode=f'{mode:02X}', name=name, pulse_adc=pulse,
                         adc_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                         **trace)
            cases.append(entry)
            if mode == 0x01:
                old = next(c for c in prior['cases']
                           if c['fixture'] == 'varying' and c['name'] == name)
                if (entry['trace_digest'] != old['trace_digest'] or
                        entry['row_sha256'] != old['row_sha256'] or
                        entry['adc_sha256'] != old['adc_sha256']):
                    raise ValueError('held 01 control differs from saved pulse')
            print(f'{mode:02X}', name, trace['trace_digest'], flush=True)
        comparisons[f'{mode:02X}'] = {
            name: impulse.compare(streams['baseline'], streams[name],
                                  impulse.VARYING_PULSE_SAMPLE)
            for name in ('high_nibble_pulse', 'low_nibble_pulse')}
    paths = (Path(__file__), SOURCE, Path(impulse.__file__),
             HERE / 'receiver_mask04_frame_mode_3eb.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(
        experiment='matched-tail ADC pulse under held 3EB controller-mode candidates',
        fixture=dict(modes=[f'{mode:02X}' for mode in MODES],
                     reference_dibits=impulse.VARYING_DIBITS,
                     samples=impulse.SAMPLES,
                     pulse_sample=impulse.VARYING_PULSE_SAMPLE,
                     base_adc=samples[impulse.VARYING_PULSE_SAMPLE],
                     high_pulse_adc=impulse.VARYING_HIGH_PULSE_ADC,
                     low_pulse_adc=impulse.VARYING_LOW_PULSE_ADC,
                     adc_visits=impulse.ADC_VISITS,
                     cycles=impulse.CYCLES,
                     channels=impulse.CHANNELS,
                     wrapper='held 3EB D; 01 baseline or observed controller 81/A1',
                     dispatch='four-row; previous overflow'),
        cases=cases, comparisons=comparisons,
        limitations=[
            'The controller-to-3EB data route and held mode timing are untraced hypotheses.',
            'One varying reference waveform and one sample pulse do not cover every receiver mode or training sequence.',
            'The external RAM and any output circuit are not modeled in these runs.',
            'A transient state difference is not a decoded receive bit or echo residual.'],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
