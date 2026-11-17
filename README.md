# CFMOTO RIDE for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Unofficial Home Assistant integration for CFMOTO motorcycles fitted with a **T-Box**. It shows
fuel range, fuel level, odometer, location and more, read from the CFMOTO RIDE cloud (the same
backend the official app uses).

- No Bluetooth, no phone app changes. The official CFMOTO RIDE app keeps working as normal.
- Works while you're away from the bike, because the T-Box reports over its own mobile connection.
- Set up from the UI (config flow). No YAML needed.

> [!IMPORTANT]
> This project is not affiliated with, endorsed by, or supported by CFMOTO. It uses an
> undocumented API that may change or stop working at any time. Use at your own risk.

## Requirements

- A CFMOTO bike with a **T-Box** bound to your CFMOTO RIDE account. Bikes without a T-Box send
  no telemetry to the cloud, so this integration cannot help with those.
- An active **Intelligent Service** subscription (shown in the app as the remaining T-Box/SIM days).
- A CFMOTO RIDE account that logs in with **email and password**. Phone-number logins are untested,
  and accounts that only use Google/Apple/Facebook sign-in are not supported.
- Home Assistant 2025.1 or newer.

## Installation

### HACS (recommended)

1. In HACS, open the menu (⋮) → **Custom repositories**.
2. Add `https://github.com/pl4za/ha-cfmoto-ride` with category **Integration**.
3. Search for **CFMOTO RIDE**, install it, then restart Home Assistant.

### Manual

1. Copy `custom_components/cfmoto` into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.

## Configuration

Go to **Settings → Devices & services → Add integration → CFMOTO RIDE** and enter:

| Field | Description |
|---|---|
| Email | Your CFMOTO RIDE login email |
| Password | Your CFMOTO RIDE password |
| Country code | The country your account is registered in, as a two-letter code (e.g. `PT`, `DE`, `GB`) |
| API server | Leave as the default `https://tapi.cfmoto-oversea.com/v1.0` unless login fails (see [Troubleshooting](#troubleshooting)) |

Each bike on the account becomes a device. Demo/virtual vehicles are ignored. If your password
changes, Home Assistant asks you to re-authenticate.

## Entities

For each bike, named after the bike (e.g. `sensor.675nk_fuel_range`):

| Entity | Type | Notes |
|---|---|---|
| Fuel range | sensor (km) | The range shown on the dash |
| Fuel level | sensor (%) | Calculated from the fuel bars. Attributes: `bars`, `total_bars`, `status` |
| Odometer | sensor (km) | |
| Distance this month | sensor (km) | As calculated by CFMOTO |
| Riding time this month | sensor (duration) | |
| Speed | sensor (km/h) | Last reported speed |
| Average speed | sensor (km/h) | |
| Fuel consumption | sensor (L/100 km) | Long-term average |
| Battery voltage | sensor (V) | 12 V battery |
| Last update | sensor (timestamp) | When the T-Box last reported |
| Location | device tracker (GPS) | Attributes: `altitude`, `reported_at` |
| Ignition | binary sensor | |
| T-Box online | binary sensor | Diagnostic |
| T-Box SIM remaining | sensor (days) | Diagnostic: days left on the Intelligent Service |
| Cellular signal | sensor | Diagnostic |

### How fresh is the data?

The integration polls the cloud every **5 minutes**. The T-Box reports while the bike is on and
occasionally while it is parked. When the bike is off, the values are the last ones it sent.
Use the **Last update** sensor to see how old they are. Rides shorter than a polling interval
may never show the ignition as on.

## Example automation

Remind yourself to fill up after parking at home with little range left:

```yaml
alias: "Motorbike: fuel up reminder"
triggers:
  - trigger: state
    entity_id: binary_sensor.675nk_ignition
    from: "on"
    to: "off"
conditions:
  - condition: state
    entity_id: device_tracker.675nk_location
    state: home
  - condition: numeric_state
    entity_id: sensor.675nk_fuel_range
    below: 80
actions:
  - action: notify.notify
    data:
      title: Fuel up the bike
      message: "Parked with {{ states('sensor.675nk_fuel_range') | round(0) }} km of range."
```

Replace the entity IDs with your bike's.

## Troubleshooting

- **"Login failed"**: check the email, password and country code are exactly what you use in the
  app. Accounts on some regional servers may need a different API server. If the app works but
  the integration does not, open an issue.
- **"No real bike is bound to this account"**: the login worked, but the account only has the demo
  vehicle. Bind the bike (and its T-Box) in the CFMOTO RIDE app first.
- **Values never change**: check the T-Box SIM remaining sensor, and the Intelligent Service in
  the app. When the service expires, the cloud stops receiving data.
- **Debug logs**: add this to `configuration.yaml` and restart:
  ```yaml
  logger:
    logs:
      custom_components.cfmoto: debug
  ```

## Privacy

Your CFMOTO credentials are stored in your Home Assistant config entry, like any other cloud
integration. The integration only talks to CFMOTO's servers (`tapi.cfmoto-oversea.com`), and
nothing is sent anywhere else.

## Testing outside Home Assistant

`tools/cfmoto_test.py` uses only the Python standard library. It logs in and prints the status
fields, which is handy for checking that your account works or for finding new fields. It reads
credentials from `~/.config/cfmoto/credentials.env`:

```
CFMOTO_EMAIL=you@example.com
CFMOTO_PASSWORD=yourpassword
CFMOTO_AREA=PT
```

Run `python3 tools/cfmoto_test.py --raw`. Sensitive fields (VIN, keys, location, Wi-Fi details)
are redacted from the output, but check it before sharing it anywhere.

## Contributing

Issues and pull requests are welcome, especially:

- Confirmation of which models and regions work
- Fields your bike reports that aren't exposed yet (share redacted `--raw` output)

## Credits

The cloud API protocol (endpoints and request signing) was reverse-engineered by
[jhonsbaracaldo/open-cfmoto](https://github.com/jhonsbaracaldo/open-cfmoto). This integration is an
independent Python implementation.

Tested with CFMOTO RIDE app 2.2.14 and a CFMOTO 675NK on the EU server.

## License

Copyright (C) 2026 Jason Costa

This program is free software: you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version. See [LICENSE](LICENSE).

CFMOTO and CFMOTO RIDE are trademarks of their respective owner and are used here only to describe
compatibility.
