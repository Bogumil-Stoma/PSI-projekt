# PSI-projekt

## Jak uruchomić zadanie 1.1

- wykonać git clone
- wejść w folder z zadaniem (Zad1-1)
- uruchomić odpowiedni plik sh, np. `./run_python_server.sh` i w drugim terminalu np.: `./run_c_client.sh`

---

## Jak uruchomić zadanie 1.2

- wykonać git clone
- wejść w folder z zadaniem (Zad1-2)
- wykonać komendę `docker-compose up --build` i zaczekać aż się wszystko zbuduje i uruchomi
- w drugim terminalu, aby zasymulować gubienie pakietów wysłanych od klienta, wykonać komendę: `./simulate_packet_loss.sh <ilość_procent>` np `./simulate_packet_loss.sh 50`
- po zakończeniu należy wykonać komendę `docker-compose down` aby usunąć kontenery

---

## Jak uruchomic zadanie 2

- wykonać git clone
- wejść w folder z zadaniem (Zad2)
- wykonać komendę `docker-compose up`

---

## Jak uruchomić projekt

- wykonac git clone
- wejść w folder z zadaniem (projekt)

### Odpalenie lokalne

- uruchamiamy serwer (wersja python przynajmniej 3.11): `python ./server.py`
- uruchamiamy klienta/klientów: `python ./client.py`
- _gdy chcemy uzyskać więcej informacji, możemy dodać flagę `--verbose` do komendy serwera i klienta_

### Odpalenie lokalne przez dockera

- wykonujemy komende `docker-compose up -d`
- aby połączyć się do termianal kontenera z serwerem: `docker attach z35_server_projekt`
- aby połączyć się do termianla kontenera z klientem: `docker attach z35_client_projekt`

### Odpalenie przez dockera na bigubu

- wejść do pliku `docker-compose.yml`
- edytować trzeba plik `docker-compose.yml`, zakomentować aktualnie odkomentowane ustawienia sieci i odkomentować te, które były zakomentowane
- dalej tak jak w przypadku odpalenia lokalnego przez dockera (podpunkt wyżej)
