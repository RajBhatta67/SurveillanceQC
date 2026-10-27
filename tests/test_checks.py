import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from surveillanceqc import Config, check_csv
from surveillanceqc.cli import main

HEADER = 'country,period,total_cases,lab_confirmed\n'


class ChecksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'input.csv'

    def check(self, text, cfg=None):
        self.path.write_text(text, encoding='utf-8')
        before = self.path.read_bytes()
        report = check_csv(self.path, cfg)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(report['source']['sha256'], hashlib.sha256(before).hexdigest())
        json.dumps(report, allow_nan=False)
        return report

    def codes(self, report):
        return [f['code'] for f in report['findings']]

    def test_valid_zero_large_integer_and_decimal_integer(self):
        r = self.check(HEADER + 'A,2024-01,0,0\nA,2024-02,9007199254740993,2.0\n')
        self.assertEqual(r['findings'], [])

    def test_missing_columns(self):
        r = self.check('country,period\nA,2024-01\n')
        self.assertEqual(self.codes(r), ['MISSING_COLUMNS'])
        self.assertFalse(r['analysis_complete'])

    def test_duplicate_records_and_locations(self):
        r = self.check(HEADER + 'A,2024-01,2,1\nA,2024-01,3,1\n')
        self.assertEqual(self.codes(r), ['DUPLICATE_KEY'])
        self.assertEqual(r['findings'][0]['rows'], [2, 3])

    def test_separate_groups_are_not_duplicates(self):
        r = self.check(HEADER + 'A,2024-01,2,1\nB,2024-01,2,1\n')
        self.assertEqual(r['findings'], [])

    def test_disease_strata(self):
        r = self.check('country,period,disease,cases\nA,2024-01,measles,2\nA,2024-01,rubella,1\n',
                       Config(counts=('cases',), key_columns=('disease',)))
        self.assertEqual(r['findings'], [])

    def test_invalid_numeric_values(self):
        for value in ['NaN', 'Infinity', '-Infinity', 'abc', '1.5', '1_000', '1,000', 'true']:
            with self.subTest(value=value):
                r = self.check(HEADER + f'A,2024-01,"{value}",1\n')
                self.assertIn('INVALID_COUNT', self.codes(r))

    def test_negative_count(self):
        r = self.check(HEADER + 'A,2024-01,-1,0\n')
        self.assertEqual(self.codes(r), ['NEGATIVE_COUNT'])

    def test_missing_is_warning_not_zero(self):
        r = self.check(HEADER + 'A,2024-01,,1\n', Config(subset_basis='Synthetic lab subset of same-period total'))
        self.assertEqual(self.codes(r), ['MISSING_COUNT'])
        self.assertEqual(r['summary'], {'error': 0, 'warning': 1})

    def test_missing_tokens_explicit_and_case_sensitive(self):
        self.assertIn('INVALID_COUNT', self.codes(self.check(HEADER + 'A,2024-01,NA,0\n')))
        r = self.check(HEADER + 'A,2024-01,NA,0\n', Config(missing_tokens=('NA',)))
        self.assertEqual(self.codes(r), ['MISSING_COUNT'])

    def test_invalid_months(self):
        for period in ['2024-00', '2024-13', '2024-2', '0000-01', '2024-02-30', ' 2024-01']:
            with self.subTest(period=period):
                self.assertIn('INVALID_PERIOD', self.codes(self.check(HEADER + f'A,{period},2,1\n')))

    def test_missing_identity_and_period(self):
        r = self.check(HEADER + ',,2,1\n')
        self.assertEqual(set(self.codes(r)), {'MISSING_KEY', 'MISSING_PERIOD'})

    def test_explicit_missing_period_not_used_for_gaps(self):
        r = self.check(HEADER + 'A,2024-01,2,1\nA,2024-03,2,1\n',
                       Config(missing_tokens=('2024-01',)))
        self.assertEqual(self.codes(r), ['MISSING_PERIOD'])

    def test_surge_and_falling_share_are_not_errors(self):
        r = self.check(HEADER + 'A,2024-01,10,9\nA,2024-02,10000,100\n',
                       Config(subset_basis='Synthetic subset, same scope'))
        self.assertEqual(r['findings'], [])

    def test_repeated_runs_deterministic(self):
        self.check(HEADER + 'A,2024-01,,1\n')
        self.assertEqual(check_csv(self.path), check_csv(self.path))

    def test_subset_with_custom_mappings(self):
        r = self.check('place,year,all,lab\nA,2024,2,3\n',
                       Config(country='place', period='year', counts=('all', 'lab'),
                              frequency='year', lab='lab', total='all',
                              subset_basis='Synthetic subset, same scope'))
        self.assertEqual(self.codes(r), ['SUBSET_EXCEEDS_TOTAL'])

    def test_month_gap_across_year(self):
        r = self.check(HEADER + 'A,2025-02,2,1\nA,2024-12,2,1\n')
        self.assertEqual(self.codes(r), ['PERIOD_GAP'])
        context = r['findings'][0]['context']
        self.assertEqual(context['first_missing'], '2025-01')
        self.assertEqual(context['missing_period_count'], 1)

    def test_annual_gap(self):
        r = self.check(HEADER + 'A,2022,2,1\nA,2024,2,1\n', Config(frequency='year'))
        self.assertEqual(r['findings'][0]['context']['first_missing'], '2023')

    def test_no_global_range_or_country_roster_assumed(self):
        r = self.check(HEADER + 'A,2020-01,2,1\nB,2026-01,2,1\n')
        self.assertEqual(r['findings'], [])

    def test_subset_disabled_by_default(self):
        r = self.check(HEADER + 'A,2024-01,1,2\n')
        self.assertEqual(r['findings'], [])
        self.assertEqual(r['subset_check'], 'skipped_no_definition')

    def test_subset_enabled_equality_zero_and_exceedance(self):
        r = self.check(HEADER + 'A,2024-01,0,0\nA,2024-02,2,2\nA,2024-03,0,1\n',
                       Config(subset_basis='Synthetic: same population/period, lab included in total'))
        self.assertEqual(self.codes(r), ['SUBSET_EXCEEDS_TOTAL'])
        self.assertEqual(r['findings'][0]['rows'], [4])

    def test_invalid_counts_not_compared(self):
        r = self.check(HEADER + 'A,2024-01,-1,2\n', Config(subset_basis='Synthetic subset'))
        self.assertEqual(self.codes(r), ['NEGATIVE_COUNT'])

    def test_key_whitespace_is_not_merged(self):
        r = self.check(HEADER + 'A,2024-01,2,1\n A,2024-01,2,1\n')
        self.assertEqual(self.codes(r), ['KEY_WHITESPACE'])

    def test_bad_headers(self):
        for text in ['country,period,total_cases,total_cases\n', 'country,,total_cases,lab_confirmed\n']:
            self.assertEqual(self.codes(self.check(text)), ['INVALID_HEADER'])

    def test_empty_file_and_header_only(self):
        self.assertEqual(self.codes(self.check('')), ['EMPTY_FILE'])
        self.assertEqual(self.codes(self.check(HEADER)), ['NO_OBSERVATIONS'])

    def test_ragged_rows_and_csv_error(self):
        r = self.check(HEADER + 'A,2024-01,2\nA,2024-02,2,1,extra\n')
        self.assertEqual(self.codes(r), ['ROW_WIDTH', 'ROW_WIDTH'])
        r = self.check(HEADER + '"unfinished')
        self.assertEqual(self.codes(r), ['MALFORMED_CSV'])
        self.assertFalse(r['analysis_complete'])

    def test_bom_unicode_crlf_quoted_fields(self):
        r = self.check('\ufeff' + HEADER + '"Synthetic, नेपाल",2024-01,2,1\r\n')
        self.assertEqual(r['findings'], [])

    def test_config_validation(self):
        for kwargs in [dict(frequency='week'), dict(counts=()), dict(counts=('country',)),
                       dict(subset_basis=' '), dict(subset_basis='yes', counts=('cases',))]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Config(**kwargs)

    def test_cli_json_exit_and_text(self):
        self.path.write_text(HEADER + 'A,2024-01,,1\n')
        for extra, expected in [([], 0), (['--fail-on', 'warning'], 1)]:
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main([str(self.path), *extra]), expected)
            self.assertEqual(json.loads(stdout.getvalue())['summary']['warning'], 1)
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(main([str(self.path), '--format', 'text']), 0)
        self.assertIn('WARNING MISSING_COUNT', stdout.getvalue())
        self.path.write_text(HEADER + 'A,2024-13,2,1\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(self.path)]), 1)

    def test_operational_failure_exit(self):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(main([str(self.path)]), 2)
        self.assertIn('surveillanceqc:', stderr.getvalue())
        self.path.write_bytes(b'\xff')
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main([str(self.path)]), 2)


if __name__ == '__main__':
    unittest.main()
