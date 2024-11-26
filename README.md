[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

# radio-browser

Browses radio schedules to tell you what to tune into right now or in the future.

## Quickstart

```zsh
% poetry install
% poetry run flask init-db --drop
% poetry run flask load-schedule tests/data/arrl.json
% poetry run flask run --debug
```

Now open up a web browser to http://127.0.0.1:5000/.

You should see a list of schedules with one entry, a list of stations with one entry, and a datetime widget.  Change the datetime widget to Monday, 2300 to 0100 and click `Filter Schedule`.

A table should be displayed showing three events:  Morse code practice, a bulletin transmitted in Morse code, and the same bulletin transmitted with digital modes like PSK31.

## Schedule tools

In addition to the above commands, there is another command that will build a new ARRL-based schedule, given the most recent ARRL operating schedule bulletin.

```zsh
% poetry run flask make-arrl-schedule bulletin.txt > arrlnew.json
```

This new schedule can be loaded as shown above.

Another tool needs to be written to support weather fax schedules.  The current worldwide schedule is available [here](https://www.weather.gov/media/marine/rfax.pdf) in PDF, and also in text format for the five US stations:
* NOJ (Kodiak, AK) - https://www.weather.gov/media/marine/hfak.txt
* NMG (New Orleans, LA) - https://www.weather.gov/media/marine/hfgulf.txt
* KVM70 (Honolulu, HI) - https://www.weather.gov/media/marine/hfhi.txt
* NMF (Boston, MA) - https://www.weather.gov/media/marine/hfmarsh.txt

## More information

There's a complete REST API available for nosing about through schedules, stations, frequencies, transmissions, and map areas.
