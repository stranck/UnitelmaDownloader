# UnitelmaDownloader

Scarica video (anche in batch) da [Unitelma](https://www.unitelmasapienza.it/) in maniera automatica, utilizzando solamente il link!

Creato da [stranck.ovh](https://stranck.ovh/)

## Installazione 4scriptKiddies

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

A questo punto utilizzando uno o più `-F`/`--filter` possiamo selezionare la stream che vogliamo scaricare. I filtri prendono due argomenti: il primo è la chiave su cui vogliamo filtrare (Continuare a leggere il readme per la lista delle chiavi), il secondo è una regex che verrà applicata sul valore di quella chiave. So che a molti la parola "regex" può far paura, ma se dovete semplicemente prendere una determinata stream potete banalmente scrivere il valore completo tra virgolette (Ad esempio: `"Luke4316"` ci matcherà la stringa esatta Luke4316). Un'altra regex che può essere utile è ottenere controllare se una stringa è contenuta nel valore della chiave è questa: `".*VALORE CONTENUTO NELLA STRINGA.*"`. Talvolta esiste una stream che combina già le varie riprese della stessa lezione in un unico file. Per ottenerla (Alla massima qualità) uso il seguente comando: `python3 unitelmaDownloader.py --username USERNAME --password PASSWORD --link LINK --filter name .*mosaic.* --filter qualityId "0" --modeAnd`

Come scritto sopra, è possibile specificare più di un filtro. Di default, una stream per essere una scelta deve rispettare tutti i filtri. Se basta che un filtro sia valido per poter scegliere una stream, si può usare l'argomento `-o`/`--modeOr` (Opposto a `-a`/`--modeAnd`)

Se più stream possono essere considerate valide, verrà presa automaticamente la prima nell'elenco di `--getInfo`. Le stream che compaiono per prime sono (generalmente) quelle con la qualità più alta. Se nessuna stream è considerabile valida, verrà mostrata la schermata di `--getInfo`

Con l'argomento `-n`/`--fileName` è possibile specificare un nome custom da dare alla stream che viene scaricata. Di default è uguale a `nomeStream_idDelCorso_idDelVideo.mp4`

Se si vuole creare un batch di video da scaricare, è possibile creare un file di testo (.txt) e inserire, riga per riga, tutti gli argomenti per scaricare un singolo video. Ad esempio:
```
--link LINK1 --filter name "Automi"
--link LINK2 --filter description ".*Di.*Ciccio.*"
--link LINK3 --filter name "Java" --filter name "programmazione" --modeOr
```
Una volta creato tale file, può essere specificato ad UnitelmaDownloader con l'argomento `-f`/`--file`: `python3 unitelmaDownloader.py -u USERNAME -p PASSWORD -f ./allLinks.txt`

Se si vuole eseguire un comando una volta terminato i download (Ad esempio, spegnere il computer), va fatto utilizzando l'argomento `-c`/`--command` e specificando il comando tra virgolette: `python3 unitelmaDownloader.py -u USERNAME -p PASSWORD -f ./allLinks.txt --command "shutdown -P now"`

Se si vuole riscaricare un file che già esiste, usare l'argomento `-r`/`--redownload`

### Chiavi possibili dentro --filter

| Chiave      | Descrizione                                                     |
| ----------- | --------------------------------------------------------------- |
| internalId  | Numero in ordine della stream                                   |
| qualityId   | Id della qualità di un determinato video (0 = qualità più alta) |
| width       | Larghezza del video                                             |
| height      | Altezza del video                                               |
| bitrate     | Bitrate del video                                               |
| bitrateStr  | Bitrate del video come formattato in --getInfo                  |
| framerate   | Framerate del video                                             |
| flavorId    | Utilizzato da unitelma per la selezione della qualità del video |
| entryId     | Utilizzato da unitelma per l'identificazione del video          |
| size        | Dimensione del video                                            |
| sizeStr     | Dimensione del video come formattata in --getInfo               |
| duration    | Durata in secondi del video                                     |
| durationStr | Durata del video come formattata in --getInfo                   |
| name        | Nome del video                                                  |
| description | Descrizione del video                                           |
| searchText  | Utilizzato da unitelma per l'indexing del video                 |
| tags        | Tag utilizzati da unitelma del video                            |
| tagsStr     | Tags formattati come in --getInfo                               |

## Argomenti

Ecco la lista di argomenti accettati dal programma

| Short           | Nome argomento           | Obbligatorio       | Descrizione                                                          |
| --------------- | ------------------------ | ------------------ | -------------------------------------------------------------------- |
| `-h`            | `--help`                 | :x:                | Mostra la schermata di help                                          |
| `-u` USERNAME   | `--username` USERNAME    | :heavy_check_mark: | Username per loggarti dentro unitelma                                |
| `-p` PASSWORD   | `--password` PASSWORD    | :heavy_check_mark: | Password per loggarti dentro unitelma                                |
| `-f` FILE       | `--file`     FILE        | :x:                | File da cui leggere, linea per linea, l'elenco di video da scaricare |
| `-U` USER_AGENT | `--userAgent` USER_AGENT | :x:                | UserAgent da usare nelle richieste. Default: casuale                 |
| `-c` COMMAND    | `--command`  COMMAND     | :x:                | Comando da eseguire a fine download                                  |
| `-v`            | `--verbose`              | :x:                | Imposta la modalità verbosa. Due livelli possibili                   |

Per ogni linea di --file oppure direttamente da linea di comando (Se si vuole scaricare un solo video) è possibile specificare questi argomenti:

| Short          | Nome argomento         | Obbligatorio       | Descrizione                                                                 |
| -------------- | ---------------------- | ------------------ | --------------------------------------------------------------------------- |
| `-l` LINK      | `--link`     LINK      | :heavy_check_mark: | Link del video da scaricare                                                 |
| `-i`           | `--getInfo`            | :x:                | Ottiene le informazioni sulle stream del video al posto di scaricarlo       |
| `-n` FILENAME  | `--fileName` FILENAME  | :x:                | Nome del file in output                                                     |
| `-r`           | `--redownload`         | :x:                | Riscarica un file, anche se già esiste                                      |
| `-a`           | `--modeAnd`            | :x:                | I filtri per la scelta della stream da scaricare sono in AND **(default)**  |
| `-o`           | `--modeOr`             | :x:                | I filtri per la scelta della stream da scaricare sono in OR                 |
| `-F` KEY REGEX | `--filter`   KEY REGEX | :x:                | Specifica un filtro sul campo KEY delle stream, che deve matchare la REGEX  |

(**NOTA**: Devi selezionare almeno un video da scaricare, tra gli argomenti e --file!)

## :warning: Nota importante

Assicuratevi di avere tutti i permessi del caso per poter veramente scaricare le lezioni da Unitelma. Ricordatevi di NON ricaricarle da altre parti, altrimenti sarebbe minimo violazione di copyright. Non sono responsabile per ciò che farete utilizzando questo software.

Also: Scusate gente esperta se scrivo un po' come un idiota, ma il readme deve essere a prova di scemo
