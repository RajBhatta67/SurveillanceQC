"""Synthetic tests for the new handoff adapter; no private data are bundled."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('handoff_audit', Path(__file__).resolve().parents[1] / 'tools/check_research_handoff.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class HandoffTest(unittest.TestCase):
    def test_period_join_keeps_original_fields_and_counts(self):
        rows = [dict(year='2024', month='01', count='', iso3='ZZZ')]
        converted = audit.normalize(list(rows[0]), rows, 'month')
        self.assertEqual(converted[0]['qc_period'], '2024-01')
        self.assertEqual(converted[0]['count'], '')
        self.assertEqual(converted[0]['month'], '01')
        self.assertNotIn('qc_period', rows[0])

    def test_invalid_period_is_not_repaired(self):
        self.assertTrue(audit.period_text(dict(year='2024', month='13'), 'month').startswith('INVALID_MONTH'))
        self.assertTrue(audit.period_text(dict(year='', month='1'), 'month').startswith('INVALID_YEAR'))
        self.assertEqual(audit.period_text(dict(year='2024'), 'year'), '2024')

    def test_subset_eligibility_requires_all_four_valid(self):
        row = {f'measles_{c}': '1' for c in audit.COMPONENTS}
        self.assertTrue(audit.eligible(row, 'measles'))
        for value in ['', 'NA', '-1', '1.5']:
            with self.subTest(value=value):
                self.assertFalse(audit.eligible(dict(row, measles_clinical=value), 'measles'))

    def test_compare_missing_tokens_and_numeric_format(self):
        row = dict(iso3='ZZZ', year='2024', month='1', region='AFRO', count='', other='2')
        other = dict(row, region='AFR', count='NA', other='2.0', month='01')
        comparison = audit.compare_rows([row], [other], 'month')
        self.assertEqual(comparison['differences_by_column'], {'region': 1})

    def test_compare_refuses_duplicate_overwrite(self):
        row = dict(iso3='ZZZ', year='2024', month='1', count='2')
        with self.assertRaises(ValueError):
            audit.compare_rows([row,row], [row], 'month')

    def test_compare_refuses_fractional_calendar_key(self):
        row = dict(iso3='ZZZ', year='2024', month='1.5', count='2')
        result = audit.compare_rows([row], [row], 'month')
        self.assertFalse(result['analysis_complete'])
        self.assertEqual(result['skipped_left_records'][0]['source_record'], 2)

    def test_outputs_cannot_be_inside_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                audit.run(root, root/'output')


    def test_invalid_is_distinct_from_missing_and_zero(self):
        self.assertEqual(audit.parse_number('NA').status, 'missing')
        self.assertEqual(audit.parse_number('').status, 'missing')
        self.assertEqual(audit.parse_number('0').status, 'valid')
        for value in ['oops', 'NaN', 'Infinity', '1_000', '1,000']:
            with self.subTest(value=value):
                self.assertEqual(audit.parse_number(value).status, 'invalid')
        self.assertEqual(audit.parse_number('1.5', whole=True).status, 'invalid')
        self.assertEqual(audit.parse_number('1.5').status, 'valid')

    def test_invalid_count_does_not_abort_eligibility(self):
        row = {f'measles_{c}': '1' for c in audit.COMPONENTS}
        self.assertFalse(audit.eligible(dict(row, measles_clinical='oops'), 'measles'))

    def test_invalid_period_token_preserved_in_projection(self):
        row = dict(iso3='ZZZ', year='oops', month='1', measles_total='text')
        result = audit.normalize(list(row), [row], 'month')[0]
        self.assertEqual(result['year'], 'oops')
        self.assertEqual(result['measles_total'], 'text')
        self.assertEqual(result['qc_period'], 'INVALID_YEAR:oops')
        issues = audit.numeric_issues([row])
        self.assertEqual({r['column'] for r in issues}, {'year', 'measles_total'})
        self.assertTrue(all(r['source_record'] == 2 for r in issues))

    def test_invalid_operand_skips_comparison_instead_of_equal_or_difference(self):
        row = dict(iso3='ZZZ', year='2024', month='1', measles_total='oops')
        for right in [dict(row), dict(row, measles_total='0'), dict(row, measles_total='NA')]:
            with self.subTest(right=right):
                result = audit.compare_rows([row], [right], 'month')
                self.assertFalse(result['analysis_complete'])
                self.assertEqual(result['differences_by_column'], {})
                self.assertEqual(result['skipped_numeric_comparisons'][0]['left'], 'oops')

    def test_missing_does_not_compare_equal_to_zero(self):
        row = dict(iso3='ZZZ', year='2024', month='1', measles_total='')
        result = audit.compare_rows([row], [dict(row, measles_total='0')], 'month')
        self.assertEqual(result['differences_by_column'], {'measles_total': 1})
        self.assertTrue(result['analysis_complete'])

    def test_empty_comparison(self):
        self.assertEqual(audit.compare_rows([], [], 'month')['shared_keys'], 0)

    @staticmethod
    def synthetic_row(frequency):
        row = dict(region='SYNTHETIC', country='Exampleland', iso3='ZZZ', year='2024')
        if frequency == 'month':
            row['month'] = '1'
        counts = audit.MONTH_COUNTS if frequency == 'month' else audit.YEAR_COUNTS
        row.update({c: '1' for c in counts})
        row.update(measles_total='3', rubella_total='3')
        if frequency == 'year':
            row['discarded_non_measles_rubella_cases_per_100000_total_population'] = '1.25'
        return row

    def test_reconciliation_skips_entire_invalid_monthly_sum(self):
        annual = self.synthetic_row('year')
        valid = self.synthetic_row('month')
        invalid = dict(valid, month='2', measles_total='oops')
        result = audit.reconcile_annual([annual], [valid, invalid])
        self.assertFalse(result['analysis_complete'])
        totals = result['measles']['measles_total']
        self.assertEqual(totals['observed_monthly_sums'], 0)
        self.assertEqual(totals['unequal_available_monthly_sums'], 0)
        self.assertEqual(len(totals['skipped_comparisons']), 1)

    def test_invalid_rate_is_not_reported_as_missing(self):
        annual = dict(self.synthetic_row('year'), discarded_non_measles_rubella_cases_per_100000_total_population='oops')
        result = audit.reconcile_annual([annual], [self.synthetic_row('month')])
        stats = result['annual_2012_2024']
        self.assertEqual(stats['discarded_present_rate_missing'], 0)
        self.assertEqual(stats['invalid_numeric_cells'], 1)
        self.assertFalse(result['analysis_complete'])

    def test_full_synthetic_audit_with_invalid_tokens_finishes_and_preserves_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, output = Path(tmp)/'handoff', Path(tmp)/'output'
            records = []
            for label, (path, frequency, _) in audit.SOURCES.items():
                row = self.synthetic_row(frequency)
                if label == 'original_monthly':
                    row['measles_clinical'] = 'oops'
                if label == 'original_annual':
                    row['discarded_cases'] = 'NaN'
                if label == 'later_monthly':
                    row['year'] = 'not-a-year'
                target = root/'research_v6'/path
                audit.write_csv(target, list(row), [row])
                records.append(dict(path=target.relative_to(root).as_posix(), sha256=audit.sha(target), bytes=target.stat().st_size))
            audit.write_json(root/'FILE_MANIFEST.json', dict(files=records))
            (root/'SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['path']+'\n' for r in records))
            result = audit.run(root, output)
            self.assertFalse(result['analysis_complete'])
            self.assertTrue(result['originals_unchanged'])
            self.assertEqual(result['invalid_numeric_cells'], 3)
            invalid = json.loads((output/'evidence/invalid_numeric_values.json').read_text())
            self.assertEqual({r['value'] for r in invalid}, {'oops','NaN','not-a-year'})
            source = result['sources']['original_monthly']
            self.assertEqual(source['findings_by_code']['INVALID_COUNT'], 1)
            self.assertFalse(source['subset']['measles']['analysis_complete'])
            self.assertEqual(source['subset']['measles']['eligible_rows'], 0)
            _, converted = audit.read_csv(output/'normalized/original_monthly.csv')
            self.assertEqual(converted[0]['measles_clinical'], 'oops')
            # All synthetic counts are nonnegative: an empty negative table
            # must still be written successfully.
            _, negatives = audit.read_csv(output/'evidence/negative_counts.csv')
            self.assertEqual(negatives, [])


@unittest.skipUnless(importlib.util.find_spec('openpyxl'), 'optional openpyxl dependency required')
class WorkbookMappingTest(unittest.TestCase):
    def make_workbook(self, labels=None):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = 'WEB'
        row = HandoffTest.synthetic_row('month')
        row['measles_clinical'] = '4'
        row['measles_epi_linked'] = '3'
        row['measles_lab_confirmed'] = '5'
        row['measles_total'] = '12'
        labels = list(audit.WORKBOOK_FIELDS) if labels is None else labels
        ws.append(labels)
        ws.append([row[audit.WORKBOOK_FIELDS[label]] for label in labels])
        wb.create_sheet('Read Me')['B12'] = 'SYNTHETIC'
        return wb, row

    def test_reordered_csv_columns_cannot_change_workbook_extraction(self):
        wb, row = self.make_workbook()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root/'research_v6/validation2026/data/b5efa946-404-table-web-epi-curve-data.xlsx'
            path.parent.mkdir(parents=True)
            wb.save(path)
            audit.write_csv(root/'normal.csv', list(row), [row])
            audit.write_csv(root/'reordered.csv', list(reversed(row)), [row])
            _, normal_rows = audit.read_csv(root/'normal.csv')
            _, reordered_rows = audit.read_csv(root/'reordered.csv')
            first = audit.workbook_comparison(root, root/'first', normal_rows)
            second = audit.workbook_comparison(root, root/'second', reordered_rows)
            self.assertTrue(first['analysis_complete'])
            self.assertTrue(second['analysis_complete'])
            self.assertEqual(second['differences_by_column'], {})
            self.assertEqual(first['new_extraction_sha256'], second['new_extraction_sha256'])
            self.assertEqual((root/'first/normalized/later_workbook_new_extraction.csv').read_bytes(),
                             (root/'second/normalized/later_workbook_new_extraction.csv').read_bytes())
        wb.close()

    def test_reordered_workbook_headers_map_to_same_fields(self):
        wb, row = self.make_workbook(list(reversed(audit.WORKBOOK_FIELDS)))
        extracted, mapping = audit.extract_workbook(wb)
        self.assertEqual(extracted, [row])
        self.assertEqual(mapping, [2])
        wb.close()

    def test_unknown_or_duplicate_workbook_headers_rejected(self):
        for replacement in ['Unreviewed', 'Country']:
            with self.subTest(replacement=replacement):
                wb, _ = self.make_workbook()
                wb['WEB']['A1'] = replacement
                with self.assertRaises(ValueError):
                    audit.extract_workbook(wb)
                wb.close()


if __name__ == '__main__':
    unittest.main()
