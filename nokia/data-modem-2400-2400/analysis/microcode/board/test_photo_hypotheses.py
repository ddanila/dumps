import json
import tempfile
import unittest
from pathlib import Path

from engine import Engine, validate
from photo_hypotheses import HERE, candidate, experiment, scenario
from run_board import run


class PhotoHypothesisTests(unittest.TestCase):
    def test_real_rom_path_preserves_unknown_startup(self):
        board = candidate('q3')
        self.assertFalse(validate(board)['errors'])
        engine = Engine(board, HERE)
        engine.initialize(scenario(0)['initial_inputs'])
        self.assertTrue(all(value.integer() is None for value in engine.state['U2']['ram']))
        report, trace, _ = experiment(board, scenario(0), 64)
        self.assertEqual(report['completed_cycles'], 64)
        self.assertEqual(report['last_pc'], '084')
        self.assertEqual(report['max_known_ram_bytes'], 0)
        self.assertEqual(trace[4]['next_pc'], '06F')
        self.assertEqual(trace[13]['next_pc'], '005')
        self.assertFalse(report['g2_acceptance'])

    def test_indirect_stimulus_distinguishes_missing_bus_from_literal_stub(self):
        fixture = scenario('pulse17')
        missing, trace, _ = experiment(candidate('q3', branch_source='unknown'), fixture, 64)
        literal, literal_trace, _ = experiment(candidate('q3'), fixture, 64)
        self.assertEqual(missing['completed_cycles'], 17)
        self.assertEqual(missing['last_pc'], '008')
        self.assertIn('unresolved', missing['stop'])
        self.assertEqual(trace[-1]['branch'], 'XXXXXXXXXX')
        self.assertEqual(literal_trace[17]['next_pc'], '300')
        self.assertEqual(literal['completed_cycles'], 64)
        self.assertGreater(literal['max_known_ram_bytes'], 0)

    def test_exported_configuration_replays_in_standard_runner(self):
        board = candidate('q3', branch_source='unknown')
        fixture = scenario('pulse17')
        expected, _, _ = experiment(board, fixture, 20)
        for cell in board['components'].values():
            if 'rom' in cell:
                cell['rom']['path'] = str((HERE / cell['rom']['path']).resolve())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / 'board.json').write_text(json.dumps(board))
            (path / 'scenario.json').write_text(json.dumps(fixture))
            actual = run(path / 'board.json', path / 'scenario.json', path / 'result', 20)
            self.assertEqual(actual['completed_cycles'], expected['completed_cycles'])
            self.assertEqual(actual['stop'], expected['stop'])
            rows = [json.loads(s) for s in (path / 'result/trace.jsonl').read_text().splitlines()]
            self.assertTrue(any(r['phase'] == 'cycle=17 external stimulus' for r in rows))
            self.assertEqual(rows[-1]['signals']['U9.A'], '0000001000')


if __name__ == '__main__':
    unittest.main()
