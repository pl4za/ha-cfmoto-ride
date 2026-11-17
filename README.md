# CFMOTO RIDE for Home Assistant

Unofficial custom integration that reads your CFMOTO bike's status from the CFMOTO RIDE cloud
(the same backend the CFMOTO RIDE app uses). Your bike needs a **T-Box** with an active
Intelligent Service subscription. Bikes without a T-Box send no telemetry to the cloud.

No Bluetooth and no phone are involved, and the official app keeps working as normal.

## Entities (per bike)

| Entity | Source field | Notes |
|---|---|---|
| Fuel range (km) | `hmiRidableMile` | Same value as the dash |
| Fuel level (%) | `remainingOil` / `totalOilNum` | Bars and status as attributes |
| Odometer (km) | `totalRideMile` | API value is in metres |
| Distance this month (km) | `rideMileageMonth` | Metres in the API |
| Riding time this month | `ridingTimeMonth` | Seconds in the API |
| Speed, Average speed (km/h) | `speed`, `avgRideSpeed` | |
| Fuel consumption (L/100 km) | `powerUseAvg` | Long-term average |
| Battery voltage (V) | `fireVoltage` | 12 V battery |
| Last update | `dataLastUpdateTime` | When the T-Box last reported |
| T-Box SIM remaining, Cellular signal | `simRemainingDays`, `gsmRxLevStr` | Diagnostic |
| Ignition, T-Box online | `kl`, `isOnline` | Binary sensors |
| Location | `geoLocation` | GPS device tracker with altitude and report time |

The integration polls every 5 minutes. While the bike is off, the values are the last ones the T-Box sent.

## Install

1. Copy `custom_components/cfmoto` into your Home Assistant `config/custom_components/`,
   or add this repository to HACS as a custom repository (category: Integration).
2. Restart Home Assistant.
3. Go to Settings → Devices & services → Add integration → **CFMOTO RIDE**, then enter your
   CFMOTO RIDE app email and password, and your country code (e.g. `PT`).

## Testing outside Home Assistant

`tools/cfmoto_test.py` is a standard-library-only script that logs in and prints the status
fields. It reads credentials from `~/.config/cfmoto/credentials.env`:

```
CFMOTO_EMAIL=you@example.com
CFMOTO_PASSWORD=yourpassword
CFMOTO_AREA=PT
```

Run `python3 tools/cfmoto_test.py --raw`. Sensitive fields (VIN, keys, location, Wi-Fi details)
are redacted from the output.

## Credits and caveats

- The API protocol (endpoints and request signing) was reverse-engineered by
  [jhonsbaracaldo/open-cfmoto](https://github.com/jhonsbaracaldo/open-cfmoto). This is an
  independent Python implementation.
- The API is undocumented and unofficial, and CFMOTO says it offers no external API access.
  An app update could change the signing secret and break this integration.
- Tested with CFMOTO RIDE 2.2.14 and a 675NK in Portugal (EU server).
