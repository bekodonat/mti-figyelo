# MTI-figyelő: Hírátvételi és Közpolitikai Napirend-kutatás

A projekt a Magyar Távirati Iroda (MTI) közleményeinek és 15 országos magyar online hírportálnak az empirikus kapcsolatát vizsgálja automatizált adatgyűjtési, szövegbányászati és relációs adatbázis-eszközökkel.

## Adatbázis és mintavétel

- **Időszak:** 2026. november 9. 11:25:03 CET – 2026. november 15. 23:59:59 CET (7 napos lezárt ciklus)
- **MTI hírek (N):** 890 kiadott híranyag
- **Sajtócikkek (N):** 8 464 publikált online cikk 15 portálról
- **Azonosított átvételek:** 547 hírpár (316 önálló MTI-hírhez kapcsolódva)
- **Fotókredites szűrés:** 110 kizárólag képet átvevő cikk (`PHOTO_ONLY`) kiszűrve a tartalmi átvételekből

## Adatszerkezet (`data/`)

- `data/news_database.db`: SQLite adatbázis (`outlets`, `articles`, `mti_news`, `matches` táblák)
- `data/articles.csv`: A vizsgált 15 portál letöltött cikkei
- `data/mti_news.csv`: Az MTI kiadott hírei (elsődleges és másodlagos CAP/MTA kódokkal)
- `data/matches.csv`: Azonosított átvételi kapcsolatok (szöveghasonlósági érték, látencia, szentiment delta)
- `data/outlets.csv`: Monitorozott médiumok jegyzéke

## Módszertan és kódkönyv

A kutatás változóit, a döntési szabályokat és a 33 kategóriás tematikus felosztást a [`codebook.md`](codebook.md) tartalmazza.
A kutatás 3 oldalas formai összefoglalója az [`elemzes.pdf`](elemzes.pdf) fájlban érhető el.

## Reprodukálhatóság és futtatás

A teljes adatgyűjtő és elemző motor a `hirfigyelo/` mappában található Python környezetben futtatható:

```bash
cd hirfigyelo
pip install -r requirements.txt
python run_pipeline.py
```

## Eredmények és bemutató felület

Az interaktív kutatási adatvizualizáció elérhető a GitHub Pages felületén:
https://bekodonat.github.io/mti-figyelo/
