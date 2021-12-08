# UnitelmaDownloader

Scarica video (anche in batch) da [Unitelma](https://www.unitelmasapienza.it/) in maniera automatica, utilizzando solamente il link!

## Istallazione 4scriptKiddies

Per funzionare UnitelmaDownloader, ha bisogno di [python3](https://www.python.org/downloads/) installato nella propria macchina (Testato con Python 3.8.10)

Una volta che python è disponibile, bisogna installare le **dipendenze** con questo comando: `python -m pip install tqdm argparse requests`

Bisogna poi clonare questa repo oppure [scaricare a manella](https://raw.githubusercontent.com/stranck/UnitelmaDownloader/main/unitelmaDownloader.py) UnitelmaDownloader

A questo punto, dal cmd, ci posizioniamo nella stessa cartella della repo/del py e possiamo eseguire `python3 unitelmaDownloader.py`

## Utilizzo

Per scaricare una lezione innanzitutto il programma ha bisogno dei vostri dati di accesso ad Unitelma. **NON ABBIATE PAURA:** Il codice del programma è completamente trasparente/open source e consultabile da voi stessi (o da qualcuno che conosce python); in questo modo potete notare leggere voi stessi come i vostri dati di accesso non vengono né salvati né utilizzati per altri fini se non per loggarsi dentro la piattaforma Unitelma.

Per specificare il vostro username e la vostra password, usate gli argomenti `-u`/`--username` e `-p`/`--password`: `python3 unitelmaDownloader.py -u USERNAME -p PASSWORD`

Una volta inseriti i nostri dati di accesso (Operazione che va fatta ad ogni download), possiamo specificare il link del video con l'argomento `-l`/`--link`: `python3 unitelmaDownloader.py -u USERNAME -p PASSWORD --link LINK`

Ogni lezione su unitelma è caratterizzato da più stream, ovvero video a qualità differente oppure diverse visuali della stessa lezione (Ad esempio la registrazione della lavagna e la webcam del prof). Per poter avere l'elenco ed i dettagli delle varie stream, utilizzare il parametro `-i`/`--getInfo`: `python3 unitelmaDownloader.py -u USERNAME -p PASSWORD --link LINK --getInfo`. Otterrete una schermata tipo questa, con i nomi dei vari campi della stream ed accanto il loro valore. ATTENZIONE: Non sempre sarà possibile ottenere tutti i metadati di una stream.

![image](https://user-images.githubusercontent.com/16164827/145217845-2dd92bdc-ca8d-4a4b-bc41-041422859a5f.png)

