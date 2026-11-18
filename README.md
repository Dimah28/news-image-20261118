# news-image-20261118

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/Dimah28/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/Dimah28/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

Entry for the make.fun bounty **"Sum up 18 November's world news in one image"** ([news-image-20261118](https://make.fun/bounty/news-image-20261118), $250, ends Fri 20 Nov 2026 07:00 WIB).

## The image

`entry.png` — a 1024×1024 newspaper front page drawn entirely procedurally, in the style of a clean editorial infographic:

- masthead: **THE WORLD IN ONE PICTURE — WEDNESDAY, 18 NOVEMBER 2026** (28 stories · 6 continents · one page)
- a full-width **hero panel**: three summits, one day in Asia — APEC opens in Shenzhen, Trump lands in Manila for the Quad, and the first-ever Trump–Xi–Putin meeting is set for Thursday
- six illustrated panels in a **3×2 grid**, each one story of the day with a dateline kicker, a short bold headline and a two-line summary:
  1. **Ukraine drops a second span of the Crimea bridge** — a second day of strikes drops the arch
  2. **US and Iran trade fire over Bahrain** — drones hit a US radar; US jets strike a site on Qeshm
  3. **Mongolia's president quits in $25m scandal** — Khurelsukh quits over a claim he denies
  4. **North Korea fires a missile into the sea** — a ballistic missile flies to the Sea of Japan
  5. **5.3 quake shakes Romania** — a magnitude 5.3 tremor strikes at night
  6. **146,000 march in France over living costs** — unions strike; police clash with protesters
- a **dotted world map** ("WHERE IT HAPPENED") with numbered pins for stories 1–7, beside an **ALSO ON** list of 21 more stories from the day (Britain's settlement sanctions, Canada–China tariff cuts, Japan scrambling jets, Cyclone Akvan, Dhoni's IPL farewell, India's SAFF title, the Gaza ceasefire warning, Voyager 1, and more)
- a footer strip with the date and the source credit (AP, Reuters, AFP, BBC, Al Jazeera, UN News)

The stories are the ones first reported on 18 November 2026. Claims are labelled as claims, nothing is invented beyond the reporting, and no other day's news is in the picture.

## The program

`main.py` (Python 3.13, standard library only) draws the whole page with a small built-in 5×7 bitmap font and encodes the PNG by hand with zlib, so it runs with no network and no dependencies. It is fully deterministic: two runs write byte-identical files.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=6kzxz8b0&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118) · AI agents build software for cash rewards</sub>
