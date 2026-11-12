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

I test coprono parsing e normalizzazione, input vuoti e sconosciuti, tutte le
regole con soglie inclusive/esclusive, riuso delle pratiche e comando dimostrativo.
Le regole sono testate con rischio controllato, senza dipendere dalle predizioni
del piccolo modello.

## File

- `src/neurosymbolic_ai/modulo_neurale.py`: dataset, modello ed estrattore.
- `src/neurosymbolic_ai/sistema_esperto.py`: regole, valutazione e demo.
- `src/neurosymbolic_ai/__init__.py`: versione e ingresso del comando.
- `pyproject.toml`: metadati, dipendenze e build; `pyproject` rimanda a questo file.
- `.python-version`: interprete usato da uv; `uv.lock`: dipendenze risolte da uv.

Il modello non dispone di un set di valutazione indipendente né di probabilità
calibrate. Le predizioni dimostrano l'integrazione fra rete e regole e non sono
una misura validata di affidabilità creditizia o uno strumento per decisioni reali.
