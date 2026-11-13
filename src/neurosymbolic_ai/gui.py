"""Interfaccia Tkinter opzionale; il comando CLI rimane indipendente."""

import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from uuid import uuid4

from .report_pdf import esporta_pdf
from .sistema_esperto import valuta_prestito


class PrestitiGUI:
    def __init__(self, root):
        self.root = root
        self.risultato = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.root.title('Valutazione prestiti')
        self.root.minsize(620, 580)
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Valutazione prestiti', font=('TkDefaultFont', 18)).pack(anchor='w')
        ttk.Label(frame, text='Inserisci il colloquio con un unico reddito mensile in euro.').pack(anchor='w', pady=(12, 6))
        self.testo = ScrolledText(frame, height=7, wrap='word', undo=True)
        self.testo.pack(fill='both', expand=True)
        self.testo.bind('<<Modified>>', self._modificato)
        actions = ttk.Frame(frame)
        actions.pack(fill='x', pady=12)
        self.valuta_button = ttk.Button(actions, text='Valuta prestito', command=self.valuta)
        self.valuta_button.pack(side='left')
        self.pdf_button = ttk.Button(actions, text='Esporta PDF', command=self.esporta, state='disabled')
        self.pdf_button.pack(side='left', padx=10)
        self.stato = tk.StringVar(value='Pronto.')
        ttk.Label(frame, textvariable=self.stato).pack(anchor='w')
        self.output = ScrolledText(frame, height=12, wrap='word', state='disabled')
        self.output.pack(fill='both', expand=True, pady=(8, 12))
        ttk.Label(frame, text='Prototipo didattico. Non usare per decisioni creditizie reali.').pack(anchor='w')
        self.root.protocol('WM_DELETE_WINDOW', self.chiudi)
        self.testo.focus_set()

    def _mostra(self, text):
        self.output.configure(state='normal')
        self.output.delete('1.0', 'end')
        self.output.insert('1.0', text)
        self.output.configure(state='disabled')

    def _modificato(self, event=None):
        if self.testo.edit_modified():
            self.risultato = None
            self.pdf_button.configure(state='disabled')
            self._mostra('')
            self.stato.set('Testo modificato: esegui una valutazione.')
            self.testo.edit_modified(False)

    def valuta(self):
        testo = self.testo.get('1.0', 'end-1c').strip()
        self.risultato = None
        self.pdf_button.configure(state='disabled')
        self._mostra('')
        if not testo:
            self.stato.set('Inserisci il testo del colloquio.')
            return
        self.testo.configure(state='disabled')
        self.valuta_button.configure(state='disabled')
        self.stato.set('Valutazione in corso...')
        # Training e valutazione fuori dal ciclo Tk; tutti i widget restano sul thread UI.
        future = self.executor.submit(valuta_prestito, testo, 'gui-' + uuid4().hex)
        self.root.after(75, self._attendi, future)

    def _attendi(self, future):
        if not future.done():
            self.root.after(75, self._attendi, future)
            return
        self.testo.configure(state='normal')
        self.valuta_button.configure(state='normal')
        try:
            risultato = future.result()
        except Exception as exc:
            self.stato.set('Valutazione non disponibile.')
            messagebox.showerror('Errore di valutazione', str(exc), parent=self.root)
            return
        self.risultato = risultato
        reddito = risultato['reddito']
        self._mostra(
            'Pratica: {sid}\nRischio finanziario: {rischio}\n'
            'Reddito dichiarato: {reddito}\nVerdetto: {verdetto}\n\n'
            'Motivazione XAI:\n{motivazione}'.format(
                **dict(risultato, reddito='Non disponibile' if reddito is None else '{} €'.format(reddito))))
        self.pdf_button.configure(state='normal')
        self.stato.set('Valutazione completata.')

    def esporta(self):
        if self.risultato is None:
            return
        percorso = filedialog.asksaveasfilename(
            parent=self.root, title='Esporta valutazione', defaultextension='.pdf',
            filetypes=[('Documento PDF', '*.pdf')], initialfile='valutazione_prestito.pdf')
        if not percorso:
            return
        try:
            esporta_pdf(percorso, self.risultato)
        except ImportError:
            messagebox.showerror('PDF non disponibile',
                                 'Installa le dipendenze opzionali: uv sync --locked --extra gui',
                                 parent=self.root)
        except Exception as exc:
            messagebox.showerror('Esportazione non riuscita', str(exc), parent=self.root)
        else:
            self.stato.set('PDF salvato: ' + percorso)

    def chiudi(self):
        self.executor.shutdown(wait=False)
        self.root.destroy()


def main():
    root = tk.Tk()
    PrestitiGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
