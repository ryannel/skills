# Route Age

A phone app for a climbing gym's setting crew. It answers one question: which routes have been up longest, and what should be stripped next. The rule built in is that nothing stays up more than 6 weeks.

It works with no signal. Each phone keeps its own full copy of the data, and changes made offline are sent the next time the phone has a connection.

## Run it

Needs Node 18 or newer. There is nothing to install.

```
node server.js
```

Then open http://localhost:8080.

Settings are environment variables:

| Variable | Default | What it does |
| --- | --- | --- |
| `PORT` | `8080` | Port to listen on |
| `DATA_FILE` | `./data/routes.json` | Where the shared copy of the data is kept |
| `CREW_CODE` | none | If set, each phone must enter this code once before it can sync |

## Putting it in front of the crew

The server has to be reachable from the setters' phones over **HTTPS**. Phones refuse to keep an app for offline use unless it is served over HTTPS, so a plain `http://` address on the gym wifi will not work offline.

Any host that runs a Node process and keeps a file on disk will do. Point `DATA_FILE` at storage that survives restarts, and set `CREW_CODE` so that strangers who find the address cannot change your data.

Each setter then opens the address once while they have signal, enters their name, and adds it to their home screen (Share → Add to Home Screen on iPhone, menu → Install app on Android).

## Getting started in the gym

1. Tap the status button top right and add your walls.
2. Walk the gym and log what is up now. Use the "~3w ago" style buttons for a best guess at age, and "Save + another" to move quickly along a wall.
3. From then on: tap + when you set a route, tap Strip when you take one down.

## How it works

- `public/` is the app. `sw.js` keeps the app files on the phone; data is held in the phone's local storage.
- `server.js` serves the app and has one endpoint, `POST /api/sync`. A phone sends the records it changed and gets back everything it has not seen. If two phones change the same route, the most recent change wins.
- Stripped routes are kept in the data, marked with the date and who stripped them, but are not shown.
- The 6 week limit and the 4 week amber warning are `MAX_DAYS` and `WARN_DAYS` at the top of `public/app.js`.
- After changing files in `public/`, phones pick the new version up the second time they open the app with signal.

## Backups

All shared data is the one file at `DATA_FILE`. Copy it to back it up. If the file is ever lost, the next phone to sync restores everything it holds.
