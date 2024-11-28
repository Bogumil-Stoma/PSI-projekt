# PSI-projekt

## Jak uruchomić zadanie 1.1

- wykonać git clone
- wejść w folder z zadaniem (Zad1-1)
- uruchomić odpowiedni plik sh, np. `./run_python_server.sh` i w drugim terminalu np.: `./run_c_client.sh`

## Jak uruchomić zadanie 1.2

- wykonać git clone
- wejść w folder z zadaniem (Zad1-2)
- wykonać komendę `docker-compose up --build` i zaczekać aż się wszystko zbuduje i uruchomi
- w drugim terminalu, aby zasymulować gubienie pakietów wysłanych od klienta, wykonać komendę: `./simulate_packet_loss.sh <ilość_procent>` np `./simulate_packet_loss.sh 50`
- po zakończeniu należy wykonać komendę `docker-compose down` aby usunąć kontenery

## Jak uruchomic zadanie 2

- wykonać git clone
- wejść w folder z zadaniem (Zad2)
- wykonać komendę `docker-compose up`
