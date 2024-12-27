# PSI 24Z - mini TLS

## Cel projektu

Zaprojektowanie oraz implementacja
szyfrowanego protokołu opartego na protokole TCP, tzw. mini TLS.

## Wymagania implementacyjne

- Architektura klient serwer.
- Serwer jest w stanie obsłużyć kilku klientów jednocześnie
- Klient inicjuje połączenie z serwerem poprzez wysłanie wiadomości
  ClientHello (nieszyfrowana), na którą serwer odpowiada
  wiadomością ServerHello (nieszyfrowana)
- Sesja może zostać zakończona zarówno przez klienta jak i przez
  serwer poprzez wysłanie wiadomości EndSession. Po odebraniu
  EndSession należy od nowa wysłać ClientHello.
- Wszystko poza ClientHello i ServerHello jest szyfrowane.
- Trzeba zastosować algorytm wymiany kluczy w celu uzgodnienia klucza do szyfrowania symetrycznego.
- Komunikacja ma się odbywać w sieci dockerowej.
- Całość uruchamiać minimalną liczbą komend.

#### Mechanizmy komunikacji obsługiwane z poziomu wiersza poleceń:

- Serwer:
  - Zakończenie połączenia z wybranym klientem.
- Klient:
  - Inicjowanie połączenia z serwerem.
  - Wysyłanie wiadomości (dowolnej treści).
  - Zakończenie połączenia z serwerem.

## Przypadki użycia

#### Inicjacja sesji

Klient wysyła wiadomość ClientHello poleceniem connect <adres serwera>, serwer odpowiada ServerHello,
po czym obie strony ustanawiają wspólny klucz szyfrujący.

#### Wysyłanie wiadomości

Klient wysyła zaszyfrowaną wiadomość do serwera, poleceniem send <treść wiadomości>.
Serwer wyświetla rozszyfrowaną wiadomość wraz z adresem nadawcy.

#### Wyświetlenie listy połączonych do serweraklientów

Na serwerze używając polecenia ls wyświetlamy listę akutalnie aktywnych połączeń numer-adress

#### Zakończenie sesji przez klienta

Klient wysyła wiadomość EndSession, poleceniem end.
Po odebraniu Serwer zakańcza połączenie.
Po wysłaniu wiadomości EndSession klient musi ponownie zainicjować sesję, wysyłając nieszyfrowane ClientHello, aby wznowić komunikację.

#### Zakończenie sesji przez serwer

Na serwerze poleceniem end <numer połączenia> kończymy połączenie
i powiadamia o tym klienta wysyłając wiadomość EndSession.
Po odebraniu wiadomości EndSession klient musi ponownie zainicjować sesję, wysyłając nieszyfrowane ClientHello, aby wznowić komunikację.

## Środowisko

- Języki programowania: Python
- Platforma uruchomieniowa: Docker z siecią wewnętrzną.
- Narzędzia testowe: Wireshark, terminal, logi z Docker Compose.

## Wykorzystane algorytmy

### Wymiana kluczy:

#### Algorytm Diffiego-Hellmana:

- Znane są publiczne wartość g i p gdzie, p jest dużą liczbą pierwszą, g dowolną liczbę nazywaną generator.
- a to wygenerowana prywatna liczba klienta trzymana w tajemnicy.
- b to wygenerowana prywatna liczba serwera trzymana w tajemnicy.
- Klient wysyła swój klucz publiczny A (A = g^a mod p) za pomocą wiadomosci ClientHello.
- Serwer odpowiada swoim kluczem publicznym B (B = g^b mod p) za pomocą wiadomosci ServerHello.
- Obie strony obliczają wspólny klucz K:
    - Klient: K = B^a mod p.
    - Serwer: K = A^b mod p.
- Klucz K będzie używany do symetrycznego szyfrowania komunikacji.

### Szyfrowanie wiadomości:

Algorytm: AES (Advanced Encryption Standard) w trybie CBC.
Klucz szyfrujący: wspólny klucz ustalony podczas wymiany kluczy.

### Integralność i autentyczność:

Mechanizm Encrypt-then-MAC: HMAC z SHA-256.

- Wiadomość jest szyfrowana algorytmem AES, wykorzystując wspólny klucz.
- Na podstawie zaszyfrowanej treści (ciphertext) i klucza generowany jest kod MAC (HMAC).
- Klient wysyła ciphertext oraz MAC w strukturze wiadomości.
- Odbiorca obliczaja HMAC na podstawie otrzymanej zaszyfrowanej wiadomosci i wspólnego klucza.
- Odbiorca weryfikuje obliczony HMAC z przesłanym MAC.
- Po pomyślnej weryfikacji, odbiorca odszyfrowuje wiadomość przy użyciu wspólnego klucza.

## Architektura

Struktury wiadomości:

- ClientHello: Klient wysyła nieszyfrowaną wiadomość inicjującą połączenie, która zawiera:
  - 11B - "ClientHello"
  - 16B - Liczba A
- ServerHello: Serwer odpowiada nieszyfrowaną wiadomością, która zawiera:
  - 11B - "ServerHello"
  - 16B - Liczba B
- Message: szyfrowana Komunikacja
  -  4B - Długość treści wiadomosci
  - 16B - Initialization Vector (IV)
  -  XB - Zaszyfrowana treść (Ciphertext)
  - 32B - Tag uwierzytelniający (MAC)
- EndSession: Wariant zaszyfrowanej wiadmości Message której tekst pod odszfrowaniu jest równy "EndSession",
  służąca do zakończenia połączenia.

## Podział pracy/ plan pracy

15.12.24 - 22.12.24 - Przygotowanie sprawozdania wstępnego

22.12.24 - 29.12.24 - Rozpoczęcie implementacji rozwiązania

29.12.24 - 05.01.24 - Testowanie i walidacja rozwiązania

05.01.24 - 12.01.24 - Opracowanie sprawozdania końcowego