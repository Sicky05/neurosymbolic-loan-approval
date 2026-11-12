from durable.lang import delete_state, get_state, m, post, ruleset, when_all

from .modulo_neurale import analizza_colloquio

SOGLIA_MINIMA = 1000
SOGLIA_MASSIMA = 1000000

with ruleset('prestito'):
    @when_all((m.reddito == None) | (m.reddito < 0) | (m.reddito > SOGLIA_MASSIMA))
    def guardrail(c):
        c.s.verdetto = "SOSPESA_PER_VERIFICA"

        if c.m.reddito is None:
            c.s.motivazione = (
                "Non risulta dichiarato un reddito univoco nel formato supportato."
            )
        elif c.m.reddito < 0:
            c.s.motivazione = (
                f"Il reddito dichiarato di {c.m.reddito} euro risulta essere negativo."
            )
        else:
            c.s.motivazione = (
                f"Il reddito dichiarato di {c.m.reddito} euro risulta essere superiore "
                f"alla soglia massima di {SOGLIA_MASSIMA} euro."
            )

    @when_all((m.reddito >= 0) & (m.reddito < SOGLIA_MINIMA))
    def rifiuto_reddito_basso(c):
        c.s.verdetto = "RIFIUTATO"

        c.s.motivazione = (
            f"Il reddito dichiarato di {c.m.reddito} euro "
            f"è inferiore alla soglia minima di {SOGLIA_MINIMA} euro."
        )

    @when_all((m.rischio == 'ALTO') & (m.reddito >= SOGLIA_MINIMA) & (m.reddito <= SOGLIA_MASSIMA))
    def rifiuto_rischio_alto(c):
        c.s.verdetto = "RIFIUTATO"

        c.s.motivazione = (
            f"Il rischio finanziario stimato è {c.m.rischio}."
        )

    @when_all((m.rischio == 'BASSO') & (m.reddito >= SOGLIA_MINIMA) & (m.reddito <= SOGLIA_MASSIMA))
    def approvazione(c):
        c.s.verdetto = "APPROVATO"

        c.s.motivazione = (
            f"Il prestito è stato approvato perché il rischio finanziario stimato è {c.m.rischio} "
            f"e il reddito dichiarato di {c.m.reddito} euro soddisfa la soglia minima di {SOGLIA_MINIMA} euro."
        )

def valuta_prestito(testo, sid):
    # 1. Analisi del colloquio
    risultato = analizza_colloquio(testo)
    if risultato['rischio'] not in ('ALTO', 'BASSO'):
        raise ValueError('Classe di rischio non riconosciuta.')

    # 2. Identificazione della pratica
    risultato['sid'] = str(sid)

    # 3. Invio al motore simbolico
    try:
        post('prestito', risultato)
        # 4. Recupero dello stato prima di liberare la pratica.
        stato = get_state('prestito', str(sid))
    finally:
        delete_state('prestito', str(sid))

    # 5. Costruzione del risultato finale
    return {
        'sid': risultato['sid'],
        'rischio': risultato['rischio'],
        'reddito': risultato['reddito'],
        'verdetto': stato['verdetto'],
        'motivazione': stato['motivazione']
    }

def mostra_valutazione(valutazione):
    # Formattazione e stampa del risultato

    print("=" * 60)
    print(f"VALUTAZIONE PRESTITO - PRATICA #{valutazione['sid']}")
    print("=" * 60)

    print(f"Rischio finanziario: {valutazione['rischio']}")

    if valutazione['reddito'] is None:
        print("Reddito dichiarato: Non disponibile")
    else:
        print(f"Reddito dichiarato: {valutazione['reddito']} €")

    print("-" * 60)

    print(f"Verdetto: {valutazione['verdetto']}")
    print(f"Motivazione: {valutazione['motivazione']}")

    print("=" * 60)
    print("")

def main():
    testo1 = (
        "Ho una situazione solida, ma ho perso il lavoro temporaneamente. "
        "Ho molti debiti. Il mio reddito mensile è di 1500 euro."
    )

    testo2 = (
        "Lavoro fisso e nessun debito, situazione ottimale. "
        "Il mio reddito mensile è di 1500 euro."
    )

    valutazione1 = valuta_prestito(testo1, '1')
    mostra_valutazione(valutazione1)

    valutazione2 = valuta_prestito(testo2, '2')
    mostra_valutazione(valutazione2)


if __name__ == '__main__':
    main()
