A simple python program for exposing hidden rent on olx.pl and otodom.pl

## Czynszododawacz
Prosty program pokazujący prawdziwe koszty wynajmu w ofertach na olx, bez ukrytego dodatkowego czynszu.

Na podstawie podanego linku generuje dokument html, który jest kopią oryginalnej strony, ale z kosztami we wszystkich ogłoszeniach uwzględniającymi dodatkowy czynsz.

Działa na ogłoszeniach hostowanych zarówno na olx jak i otodom.

## Konfiguracja

Program tworzy plik konfiguracyjny w folderze w którym się znajduje.

- Link do olx (olx_url) - Stały link, na podstawie którego można generować dokument komendą 'refresh'.

- Maksymalna cena (cost_limit) - Maksymalny koszt, uwzględniając ukryty czynsz, powyżej którego ogłoszenia nie będą pojawiać się w gotowym dokumencie.

- Opóźnienie (sleep_time) - Czas pomiędzy każdym wczytanym ogłoszeniem. Ustawiaj na 0 na własne ryzyko. Wysyłanie żądań do serwera olx zbyt często może skutkować blokadą (przetestowane)
