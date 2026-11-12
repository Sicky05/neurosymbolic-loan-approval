import contextlib
import io
import unittest
from unittest.mock import patch

from neurosymbolic_ai import main
from neurosymbolic_ai import modulo_neurale as neurale
from neurosymbolic_ai import sistema_esperto as esperto


class IncomeTests(unittest.TestCase):
    def test_supported_amounts(self):
        cases = {
            'Il mio reddito mensile è di 1500 euro.': 1500,
            'STIPENDIO NETTO MENSILE: +1500 euro': 1500,
            'Guadagno -1500 euro': -1500,
            'Percepisco 0 euro': 0,
            'Prendo 1.500 euro': 1500,
            'Reddito: € 1.500,75': 1500.75,
            'Reddito: -1.500,75': -1500.75,
            'Guadagno 999,99 euro': 999.99,
            'Guadagno 1500, ma ho debiti.': 1500,
            'Ho 42 anni. Guadagno 1500 euro e pago 500 euro di affitto.': 1500,
            'Reddito 1500 euro e stipendio 1.500 euro': 1500,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(neurale.estrai_reddito(text), expected)

    def test_missing_ambiguous_or_malformed_income(self):
        for text in (
            '', 'Ho 42 anni e 1500 euro di debiti.',
            'Non ho reddito e ho 42 anni.', 'Il reddito manca. Ho 42 anni.',
            'Il sovrareddito è 1500 euro.', 'Reddito 1.50 euro',
            'Reddito 1500,123 euro', 'Reddito 1500abc',
            'Guadagno 1500 euro, ma il mio reddito è 2000 euro.',
            'Reddito ' + '9' * 400 + ' euro',
        ):
            with self.subTest(text=text):
                self.assertIsNone(neurale.estrai_reddito(text))

    def test_normalization_removes_amount_and_preserves_context(self):
        low = 'Guadagno 1.500,50 euro ma ho molti debiti.'
        high = 'Guadagno 9999 euro ma ho molti debiti.'
        self.assertEqual(neurale.normalizza_testo_per_rischio(low),
                         neurale.normalizza_testo_per_rischio(high))
        self.assertIn('ho molti debiti', neurale.normalizza_testo_per_rischio(low))
        self.assertIn('-1500', neurale.normalizza_testo_per_rischio('Debiti: -1500 euro'))


class AnalysisTests(unittest.TestCase):
    def test_empty_and_invalid_input(self):
        for text in ('', '  ', None, 42):
            with self.subTest(text=text), self.assertRaises(ValueError):
                neurale.analizza_colloquio(text)

    def test_unknown_vocabulary(self):
        with self.assertRaises(ValueError):
            neurale.analizza_colloquio('xyzxyzxyz')

    def test_training_data_and_analysis_contract(self):
        self.assertEqual(len(neurale.frasi), len(neurale.etichette))
        result = neurale.analizza_colloquio(
            'Lavoro fisso e nessun debito. Il mio reddito mensile è di 1500 euro.'
        )
        self.assertIn(result['rischio'], ('ALTO', 'BASSO'))
        self.assertEqual(result['reddito'], 1500)
        self.assertIs(neurale._modello(), neurale._modello())


class RuleTests(unittest.TestCase):
    def evaluate(self, income, risk='BASSO', sid='test'):
        with patch.object(esperto, 'analizza_colloquio',
                          return_value={'reddito': income, 'rischio': risk}):
            return esperto.valuta_prestito('testo', sid)

    def test_all_rules_and_boundaries(self):
        cases = (
            (None, 'SOSPESA_PER_VERIFICA'),
            (-1, 'SOSPESA_PER_VERIFICA'),
            (0, 'RIFIUTATO'), (999.99, 'RIFIUTATO'),
            (1000, 'APPROVATO'), (1000000, 'APPROVATO'),
            (1000000.01, 'SOSPESA_PER_VERIFICA'),
        )
        for risk in ('BASSO', 'ALTO'):
            for income, verdict in cases:
                if risk == 'ALTO' and verdict == 'APPROVATO':
                    verdict = 'RIFIUTATO'
                with self.subTest(income=income, risk=risk):
                    result = self.evaluate(income, risk)
                    self.assertEqual(result['verdetto'], verdict)
                    self.assertTrue(result['motivazione'])
                    self.assertEqual(result['reddito'], income)

    def test_reusing_sid_does_not_reuse_old_verdict(self):
        self.assertEqual(self.evaluate(1500)['verdetto'], 'APPROVATO')
        self.assertEqual(self.evaluate(None)['verdetto'], 'SOSPESA_PER_VERIFICA')
        self.assertEqual(self.evaluate(1500, 'ALTO')['verdetto'], 'RIFIUTATO')

    def test_numeric_sid(self):
        self.assertEqual(self.evaluate(1500, sid=123)['sid'], '123')

    def test_unknown_risk_is_rejected(self):
        with self.assertRaises(ValueError):
            self.evaluate(1500, 'SCONOSCIUTO')

    def test_console_demo(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main()
        self.assertEqual(output.getvalue().count('VALUTAZIONE PRESTITO'), 2)
        self.assertIn('Verdetto:', output.getvalue())


if __name__ == '__main__':
    unittest.main()
