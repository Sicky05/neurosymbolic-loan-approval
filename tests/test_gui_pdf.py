"""Verifiche della nuova interfaccia, senza cambiare i test preesistenti."""

import importlib.util
import tempfile
import unittest
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import patch

from neurosymbolic_ai.report_pdf import esporta_pdf


RISULTATO = {
    'sid': 'gui-test', 'reddito': 1500.75, 'rischio': 'BASSO',
    'verdetto': 'APPROVATO',
    'motivazione': 'Il reddito è sufficiente: 1500,75 € < 2000 & rischio BASSO.',
}


@unittest.skipUnless(importlib.util.find_spec('reportlab'), 'Extra gui non installato')
class PDFTests(unittest.TestCase):
    def test_exports_all_verdicts_without_mutating_result(self):
        with tempfile.TemporaryDirectory() as directory:
            for verdict in ('APPROVATO', 'RIFIUTATO', 'SOSPESA_PER_VERIFICA'):
                result = dict(RISULTATO, verdetto=verdict, reddito=None)
                original = result.copy()
                path = Path(directory) / (verdict + '.pdf')
                esporta_pdf(path, result)
                self.assertTrue(path.read_bytes().startswith(b'%PDF-'))
                self.assertEqual(result, original)

    def test_long_explanation_and_literal_markup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'lungo.pdf'
            esporta_pdf(path, dict(RISULTATO, motivazione=RISULTATO['motivazione'] * 500))
            self.assertGreater(path.stat().st_size, 10000)

    def test_invalid_destination_reports_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(OSError):
                esporta_pdf(Path(directory) / 'inesistente' / 'report.pdf', RISULTATO)


class GUITests(unittest.TestCase):
    def setUp(self):
        try:
            import tkinter as tk
            from neurosymbolic_ai import gui
            self.gui = gui
            self.root = tk.Tk()
        except (ImportError, RuntimeError) as exc:
            self.skipTest(str(exc))
        except Exception as exc:
            if exc.__class__.__name__ == 'TclError':
                self.skipTest('Display Tk non disponibile: ' + str(exc))
            raise
        self.root.withdraw()
        self.app = gui.PrestitiGUI(self.root)

    def tearDown(self):
        if hasattr(self, 'app'):
            self.app.chiudi()

    def test_empty_input_does_not_evaluate(self):
        with patch.object(self.gui, 'valuta_prestito') as evaluate:
            self.app.valuta()
        evaluate.assert_not_called()
        self.assertIsNone(self.app.risultato)
        self.assertIn('disabled', self.app.pdf_button.state())

    def test_result_is_invalidated_when_input_changes(self):
        future = Future()
        future.set_result(RISULTATO.copy())
        self.app._attendi(future)
        self.assertIn(RISULTATO['motivazione'], self.app.output.get('1.0', 'end'))
        self.assertNotIn('disabled', self.app.pdf_button.state())
        self.app.testo.insert('1.0', 'Testo modificato')
        self.app._modificato()
        self.assertIsNone(self.app.risultato)
        self.assertIn('disabled', self.app.pdf_button.state())

    def test_evaluation_error_prevents_export(self):
        future = Future()
        future.set_exception(ValueError('Testo non riconosciuto'))
        with patch.object(self.gui.messagebox, 'showerror') as error:
            self.app._attendi(future)
        error.assert_called_once()
        self.assertIsNone(self.app.risultato)
        self.assertIn('disabled', self.app.pdf_button.state())

    def test_export_cancellation_and_write_error(self):
        self.app.risultato = RISULTATO.copy()
        with patch.object(self.gui.filedialog, 'asksaveasfilename', return_value=''), \
                patch.object(self.gui, 'esporta_pdf') as export:
            self.app.esporta()
            export.assert_not_called()
        with patch.object(self.gui.filedialog, 'asksaveasfilename', return_value='report.pdf'), \
                patch.object(self.gui, 'esporta_pdf', side_effect=PermissionError('Accesso negato')), \
                patch.object(self.gui.messagebox, 'showerror') as error:
            self.app.esporta()
            error.assert_called_once()

    def test_calls_existing_evaluator_with_input_and_unique_sid(self):
        self.app.testo.insert('1.0', 'Lavoro stabile. Reddito 1500 euro.')
        self.app._modificato()
        future = Future()
        future.set_result(RISULTATO.copy())
        with patch.object(self.app.executor, 'submit', return_value=future) as submit:
            self.app.valuta()
        args = submit.call_args[0]
        self.assertIs(args[0], self.gui.valuta_prestito)
        self.assertEqual(args[1], 'Lavoro stabile. Reddito 1500 euro.')
        self.assertTrue(args[2].startswith('gui-'))


if __name__ == '__main__':
    unittest.main()
