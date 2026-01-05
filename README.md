<div align="right">
    <a href="README.md">English</a> | <a href="README.ja.md">日本語</a>
</div>

<div align="center">

<img src="src/assets/icon.png" width="128" alt="SeatXray Logo">

# SeatXray

**X-ray vision for flight seats.**
**See beyond "Unavailable". Know if it's Occupied or Blocked.**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/Flet-0.80.1-purple.svg)](https://flet.dev/)
[![Amadeus API](https://img.shields.io/badge/Amadeus-Flight%20Offers%20%26%20SeatMap-blue)](https://developers.amadeus.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-red.svg)](LICENSE)

</div>

## Overview

**SeatXray** is a desktop & mobile application designed to analyze and visualize flight seat availability in depth.
It distinguishes whether seats that are grayed out and unavailable on standard sites are **"actually occupied"** or **"merely blocked by the airline"**.

It uses the Amadeus Self-Service API to retrieve information more detailed than what is typically available on airline official websites. Currently available for Windows and Android.

> ### Notice
>
> This application is currently in the development stage and may contain unexpected bugs.
> Be aware that optimization for the smartphone (Android) version is not yet complete, and issues such as reduced performance or layout glitches may occur.
>
> Plans for iOS and macOS versions exist, but development is currently paused due to developer environment constraints.

## Features

- Search for flights
- Display seat maps with color-coded status for Available, Occupied, and Blocked seats
- All data including search history and API keys are held only by the user and never sent to the developer
- Supports English and Japanese, with future expansion planned (translators wanted)

## Installation

### Windows
Download and install from the Microsoft Store.

<a href="https://apps.microsoft.com/detail/9PB4V9J3LRQH" target="_blank">
<img src="https://get.microsoft.com/images/en-us%20dark.svg" width="200"/>
</a>

### Android
Download the latest APK file (`app-release.apk`) from the [Releases page](https://github.com/SeatXray/seatxray/releases) and install it on your Android device.

* Note: Currently not available on the Google Play Store.

### macOS / Linux / iOS
Currently not supported.

## Usage

### Get Amadeus API Keys
To use this app, you need an Amadeus for Developers API key. Please register for an account at the [official portal](https://developers.amadeus.com/), create a new app in `My Apps`, and obtain your `API Key` and `API Secret`.

To access all data, switching to commercial usage is required. If you wish to retrieve production data, please upgrade by clicking "Get production environment" on the app details page.

### App Settings
Launch SeatXray, open the Settings screen, enter your keys, and run the "Test Connection". A success dialog indicates you are ready to go.

### Search Flights
Enter your Origin, Destination, and Date/Time on the main screen, select a search range (how many hours from that time to search), and click Search. Click on any flight in the results list to start the detailed seat analysis.

Note: If the search range is too large on popular routes, results may be truncated, potentially causing information for higher classes to be missing. It is recommended to set a shorter search range for major domestic routes.

## Development

Steps to run from source.

### Prerequisites
- Python 3.12+
- Flutter (Required for building Flet apps)

### Setup
```bash
# Clone repository
git clone https://github.com/ryyr-ry/seatxray.git
cd seatxray

# Install dependencies
pip install -r requirements.txt

# Run (Windows)
flet run src/main.py

# Run (Android)
# Check device/emulator ID
flet devices
# Specify using --device-id option
flet debug android --device-id emulator-XXXX
```

### Windows Build
```powershell
# Build using the auto-fix script (To avoid bugs in Flet 0.80.1 windows build)
.\build_windows.ps1

# Package (MSIX)
.\package_msix.ps1
```

### Android Build
```bash
# No special command required
flet build apk
```

## Disclaimer

The data displayed by this app is retrieved from the Amadeus Self-Service API, but there is no guarantee that it perfectly matches the airline's real-time seat availability.

Usage of the Amadeus API incurs fees as per their schedule. Different free tiers and pricing apply to each API; please refer to the [pricing page](https://developers.amadeus.com/pricing) on Amadeus for Developers for details.

This app is provided "as is", and the developer assumes no responsibility for any fees incurred related to Amadeus for Developers, or for any bookings made or other issues arising from the information provided by this app.

## License

This project is released under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.
See the [LICENSE](LICENSE) file for details.

<br>

<div align="right">
    Created by <a href="https://github.com/SeatXray">SeatXray</a> / <a href="https://github.com/ryyr-ry">ryyr-ry</a>
</div>
