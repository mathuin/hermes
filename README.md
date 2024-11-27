[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

# radio-browser

Browses radio schedules to tell you what to tune into right now or in the future.

## Quickstart

```zsh
% poetry install
% poetry run flask init-db --drop
% poetry run flask load-schedule tests/test_commands/arrl.json
% poetry run flask run --debug
```

Now open up a web browser to http://127.0.0.1:5000/.

You should see a list of schedules with one entry, a list of stations with one entry, and a datetime widget.  Change the datetime widget to Monday, 2300 to 0100 and click `Filter Schedule`.

A table should be displayed showing three events:  Morse code practice, a bulletin transmitted in Morse code, and the same bulletin transmitted with digital modes like PSK31.

## Docker support

The software can be built and deployed as a Docker image.

```zsh
% docker build -t radio_browser --file docker/Dockerfile .
% docker run --name radio_browser -p 8888:8888 -it radio_browser
```

In another window, copy your schedule files to the container, then enter the container to complete configuration:

```zsh
% docker cp tests/test_commands/arrl.json radio_browser:/root
% docker exec -it radio_browser bash
# flask --app radio_browser init-db
# flask --app radio_browser load-schedule /root/arrl.json
```

How open up a web browser to http://127.0.0.1:8888/ to see the app.

## Schedule tools

In addition to the above commands, there is another command that will build a new ARRL-based schedule, given the most recent ARRL operating schedule bulletin.  The ARRL bulletins are archived [here](https://www.arrl.org/w1aw-bulletins-archive).

```zsh
% poetry run flask make-arrl-schedule bulletin.txt > arrlnew.json
```

A similar command exists for WEFAX schedules. The current worldwide schedule is available [here](https://www.weather.gov/media/marine/rfax.pdf) in PDF, and also in text format for the five US stations:
* NOJ (Kodiak, AK) - https://www.weather.gov/media/marine/hfak.txt
* NMG (New Orleans, LA) - https://www.weather.gov/media/marine/hfgulf.txt
* KVM70 (Honolulu, HI) - https://www.weather.gov/media/marine/hfhi.txt
* NMF (Boston, MA) - https://www.weather.gov/media/marine/hfmarsh.txt
* NMC (Pt. Reyes, CA) - https://www.weather.gov/media/marine/hfreyes.txt

Retrieve the text files, and run the following command:

```zsh
% poetry run flask make-wefax-schedule hf*txt > wefaxnew.json
```

Both new files can be imported as per above.

## More information

There's a complete REST API available for nosing about through schedules, stations, frequencies, transmissions, and map areas.
