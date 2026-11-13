# Neurosymbolic AI

Prototipo didattico in italiano per la valutazione di una richiesta di prestito.
Combina TF-IDF e una rete neurale `MLPClassifier` di scikit-learn con un motore
di regole `durable_rules`. Il dataset contiene 24 frasi etichettate manualmente.

## Avvio

Il progetto mantiene Python **3.8.20**, già usato dall'ambiente originale,
e scikit-learn 1.3.2. Python 3.8 è fuori supporto: questa configurazione serve
alla riproducibilità del laboratorio; una migrazione va verificata separatamente.
Con [uv](https://docs.astral.sh/uv/getting-started/installation/) disponibile:

```powershell
uv sync --locked
uv run --locked neurosymbolic-ai
```

Il comando mostra due colloqui di esempio con reddito, rischio, verdetto e
motivazione. In alternativa: `uv run --locked python -m neurosymbolic_ai.sistema_esperto`.
`durable-rules` contiene un'estensione C: se manca una wheel compatibile,
l'installazione richiede un compilatore C e gli strumenti di sviluppo Python.

## Interfaccia grafica e PDF

La GUI usa Tkinter (incluso nell'interprete Windows; su Linux richiede il
pacchetto Tk della distribuzione) e un extra opzionale per esportare PDF:

```powershell
uv sync --locked --extra gui
uv run --locked --extra gui neurosymbolic-ai-gui
```

In alternativa: `uv run --locked --extra gui python -m neurosymbolic_ai.gui`.
Il comando originale `neurosymbolic-ai` continua ad avviare i due esempi CLI.

Scrivi il colloquio, premi **Valuta prestito**, quindi **Esporta PDF** e scegli
il percorso. La valutazione avviene in background. Modificare il testo invalida
il risultato precedente e richiede una nuova valutazione prima di esportare.
Il PDF contiene identificativo pratica, reddito, rischio, verdetto e la
motivazione XAI originale restituita da `valuta_prestito()`. Questa motivazione
descrive le regole del sistema esperto, non i pesi o i contributi della rete.
L'esportazione non ricalcola la valutazione. I dati restano locali.

Compatibilità verificata prima dell'installazione sui metadati PyPI:
ReportLab 4.2.5 richiede Python >=3.7,<4; Pillow 10.4.0 richiede >=3.8;
chardet 5.2.0 richiede >=3.7. L'extra vincola Pillow <11 e chardet <6;
il lockfile mantiene le versioni risolte. I font per accenti ed euro sono
inclusi in ReportLab. Nessuna dipendenza GUI/PDF viene importata dalla CLI.

## Uso da Python

```python
from neurosymbolic_ai.sistema_esperto import valuta_prestito

risultato = valuta_prestito(
    "Lavoro fisso e nessun debito. Il mio reddito mensile è di 1500 euro.",
    sid="esempio-1",
)
print(risultato)
```

Il modello viene addestrato alla prima analisi e riutilizzato nel processo.
L'importazione del pacchetto non avvia il training né stampa risultati.
Ogni valutazione libera lo stato della pratica nel motore; è possibile riusare
lo stesso `sid` in chiamate successive. Le chiamate concorrenti con lo stesso
`sid` non sono supportate.

## Regole

| Condizione | Verdetto |
| --- | --- |
| Reddito assente, ambiguo, negativo o superiore a 1.000.000 € | `SOSPESA_PER_VERIFICA` |
| Reddito da 0 € incluso a 1.000 € escluso | `RIFIUTATO` |
| Reddito tra 1.000 € e 1.000.000 € inclusi e rischio `ALTO` | `RIFIUTATO` |
| Reddito tra 1.000 € e 1.000.000 € inclusi e rischio `BASSO` | `APPROVATO` |

L'estrattore riconosce importi associati a `reddito`, `stipendio`, `guadagno`,
`percepisco` e `prendo`, con qualificatori comuni. Supporta segni, separatori
italiani (`1.500,50`) e importi interi. Restituisce `int`, `float` per i centesimi,
oppure `None` se non trova un importo univoco. Non prende il primo numero
arbitrario dopo una parola chiave. Gli importi riconosciuti vengono rimossi
dal testo usato per il rischio, conservando il contesto sia nel training sia
nell'inferenza. I testi vuoti o senza vocaboli riconosciuti generano `ValueError`.

Il colloquio deve dichiarare **un unico reddito mensile in euro**: il prototipo
non converte redditi annuali, altre valute, importi in lettere o formati numerici
inglesi; non interpreta negazioni, periodi temporali o composizioni di entrate.

## Test

```powershell
uv run --locked python -m unittest discover -s tests -v
```

Per includere tutte le verifiche GUI/PDF, usa
`uv run --locked --extra gui python -m unittest discover -s tests -v`.
Queste verifiche richiedono l'extra `gui` e, per Tkinter, un display disponibile;
in assenza di tali requisiti i relativi test sono segnalati come saltati.

I test coprono parsing e normalizzazione, input vuoti e sconosciuti, tutte le
regole con soglie inclusive/esclusive, riuso delle pratiche e comando dimostrativo.
Le regole sono testate con rischio controllato, senza dipendere dalle predizioni
del piccolo modello.

## File

- `src/neurosymbolic_ai/modulo_neurale.py`: dataset, modello ed estrattore.
- `src/neurosymbolic_ai/sistema_esperto.py`: regole, valutazione e demo.
- `src/neurosymbolic_ai/__init__.py`: versione e ingresso del comando.
- `src/neurosymbolic_ai/gui.py`: interfaccia Tkinter e valutazione in background.
- `src/neurosymbolic_ai/report_pdf.py`: esportazione PDF del risultato e della motivazione.
- `tests/test_gui_pdf.py`: test aggiuntivi per interfaccia ed esportazione.
- `pyproject.toml`: metadati, dipendenze e build; `pyproject` rimanda a questo file.
- `.python-version`: interprete usato da uv; `uv.lock`: dipendenze risolte da uv.

Il modello non dispone di un set di valutazione indipendente né di probabilità
calibrate. Le predizioni dimostrano l'integrazione fra rete e regole e non sono
una misura validata di affidabilità creditizia o uno strumento per decisioni reali.
