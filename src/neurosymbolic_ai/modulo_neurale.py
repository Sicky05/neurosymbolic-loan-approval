import re
from functools import lru_cache
from math import isfinite

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier

# DATASET

frasi = [
    "Ho un lavoro stabile e sono senza debiti",
    "Sono disoccupato temporaneamente, ma ho già trovato un lavoro stabile che a breve comincerò",
    "Ho un lavoro, però sono in una situazione di precariato",
    "Sono disoccupato e pieno di debiti",
    "Lavoro, però la mia famiglia mi deve aiutare",
    "Ho finito di lavorare e ho tanti investimenti nei mercati finanziari e nel mercato immobiliare",
    "Ho un lavoro, però ho tanti debiti",
    "Ho un lavoro, una casa e una famiglia. La situazione è stabile",
    "Sono stato licenziato e ho bisogno di soldi",
    "Ho perso il mio incarico e non ho più soldi",
    "Sono economicamente indipendente e sono un lavoratore regolare",
    "Sono benestante e ho un impiego in un'azienda",
    "Ho un reddito netto mensile di 1750 euro, un contratto stabile e nessun debito.",
    "Guadagno 2300 euro netti al mese e pago regolarmente tutte le rate.",
    "Il mio stipendio netto mensile è di 1100 euro, ho entrate regolari e non ho debiti.",
    "Percepisco 3200 euro netti al mese e non ho finanziamenti aperti.",
    "Prendo 1450 euro netti al mese, lavoro stabilmente e non ho rate arretrate.",
    "Guadagno 2600 euro netti al mese, possiedo risparmi e ho poche spese fisse.",
    "Ho un reddito netto mensile di 1750 euro, ma ho diverse rate in arretrato.",
    "Guadagno 2300 euro netti al mese, però ho debiti che non riesco a pagare.",
    "Il mio stipendio netto mensile è di 1100 euro e il contratto scade a breve senza rinnovo.",
    "Percepisco 3200 euro netti al mese, ma ho saltato diverse rate del mutuo.",
    "Prendo 1450 euro netti al mese, ma ho perso diversi incarichi e il mio lavoro è instabile.",
    "Guadagno 2600 euro netti al mese, ma ho diversi debiti insoluti."
]


etichette = [
    "BASSO",
    "BASSO",
    "ALTO",
    "ALTO",
    "ALTO",
    "BASSO",
    "ALTO",
    "BASSO",
    "ALTO",
    "ALTO",
    "BASSO",
    "BASSO",
    "BASSO",
    "BASSO",
    "BASSO",
    "BASSO",
    "BASSO",
    "BASSO",
    "ALTO",
    "ALTO",
    "ALTO",
    "ALTO",
    "ALTO",
    "ALTO"
]

# NORMALIZZAZIONE DEL TESTO

IMPORTO = r'[+-]?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{1,2})?'
REDDITO = re.compile(
    r'\b(?:stipendio|reddito|guadagno|percepisco|prendo)\b'
    r'\s*(?:(?:netto|mensile|netti|lordo|lordi|è|e|di|:|pari|a)\s*)*'
    r'(?:€\s*)?(?P<importo>' + IMPORTO + r')'
    r'(?!\w|[.,]\d)',
    re.IGNORECASE,
)


def normalizza_testo_per_rischio(testo):
    """Rimuove gli importi, conservando il contesto utile alla stima del rischio."""
    return REDDITO.sub(
        lambda match: match.group(0)[:match.start('importo') - match.start()],
        testo,
    ).strip()

# TRAINING DEL VECTORIZER

@lru_cache(maxsize=1)
def _modello():
    """Addestra una sola volta, alla prima analisi, senza effetti all'import."""
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    X = vectorizer.fit_transform([
        normalizza_testo_per_rischio(frase) for frase in frasi
    ])
    clf = MLPClassifier(solver='lbfgs', random_state=1).fit(X, etichette)
    return vectorizer, clf

# ESTRAZIONE DEL REDDITO
def estrai_reddito(testo):
    """Estrae un importo univoco nel formato numerico italiano."""
    importi = {
        float(match.group('importo').replace('.', '').replace(',', '.'))
        for match in REDDITO.finditer(testo)
    }
    # Dichiarazioni contraddittorie richiedono una verifica umana.
    if len(importi) != 1:
        return None
    reddito = importi.pop()
    if not isfinite(reddito):
        return None
    return int(reddito) if reddito.is_integer() else reddito

# ANALISI COLLOQUIO
def analizza_colloquio(testo):
    if not isinstance(testo, str) or not testo.strip():
        raise ValueError('Il colloquio deve essere un testo non vuoto.')
    vectorizer, clf = _modello()
    testo_rischio = normalizza_testo_per_rischio(testo)
    vettore = vectorizer.transform([testo_rischio])
    if vettore.nnz == 0:
        raise ValueError('Il testo non contiene termini riconosciuti dal modello.')
    predizione = clf.predict(vettore)
    return {
        'rischio': predizione[0],
        'reddito': estrai_reddito(testo)
    }

if __name__ == '__main__':
    testo1 = (
        "Ho una situazione solida, ma ho perso il lavoro temporaneamente. "
        "Ho molti debiti. Il mio reddito mensile è di 1500 euro."
    )

    testo2 = (
        "Lavoro fisso e nessun debito, situazione ottimale. "
        "Il mio reddito mensile è di 1500 euro."
    )

    print(analizza_colloquio(testo1))
    print(analizza_colloquio(testo2))
