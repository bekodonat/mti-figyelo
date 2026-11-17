# Codebook — MTI Hírátvételi és Közpolitikai Napirend-kutatás

**Szerző:** Bekó Donát
**Dátum:** 2026. november 17.  
**Verzió:** 2.0  
**Projekt:** MTI Figyelő (Magyar Távirati Iroda online sajtóátvételeinek és közpolitikai keretezésének vizsgálata)  
**Tárhely és forráskód:** https://github.com/bekodonat/mti-figyelo  
**Licenc:** Creative Commons Attribution 4.0 International (CC-BY 4.0)  

---

## Bevezetés

A jelen adatbázis és kódkönyv a Magyar Távirati Iroda (MTI) közleményeinek és a magyar online sajtó híranyagainak kapcsolatát dokumentálja. A korpusz lehetővé teszi annak vizsgálatát, hogy a hazai hírportálok milyen arányban, mekkora késleltetéssel és mely közpolitikai témákban veszik át a hivatalos hírügynökségi anyagokat, valamint feltárja, hogy az átvétel során hogyan transzformálódik a semleges MTI-hírek hangneme (szentimentje) az egyes médiumok címeiben és felvezetőiben (lead).

A kódkönyv rögzíti az adatgyűjtési időszakot, a mintavételi szabályokat, az adatbázis relációs szerkezetét, a változók definícióit, valamint a témakódolási és szentiment-elemzési besorolási rendszert.

---

## Adatgyűjtés és lefedettség

Az adatgyűjtés automatizált módon, az MTI hivatalos RSS-csatornájának és 15 vezető magyar online hírportál folyamatos monitorozásával történt.

- **Időszak:** 2026. november 9. 11:25:03 CET – 2026. november 15. 23:59:59 CET (lezárt, 7 napos teljes heti ciklus).
- **Megfigyelési egység:** 
  1. Hírügynökségi szinten: egy kiadott MTI-hír (`mti_news`).
  2. Sajtócikk szinten: egy közzétett online újságcikk (`articles`).
  3. Átvételi szinten: egy azonosított cikk–MTI egyezéspár (`matches`).
- **Összes rekordszám:** 8 464 sajtócikk, 890 MTI hírközlemény, 547 ellenőrzött átvételi kapcsolat.

### 1. táblázat: Az adatbázis lefedettsége portálonkénti bontásban

| Portál | Összes cikk ($N$) | MTI-hivatkozást tartalmazó cikk | Azonosított MTI-egyezés ($N$) |
| :--- | :--- | :--- | :--- |
| Blikk | 1074 | 41 | 21 |
| Origo | 921 | 26 | 34 |
| Index | 832 | 157 | 60 |
| 24.hu | 831 | 86 | 55 |
| Portfolio | 782 | 87 | 18 |
| HVG | 727 | 32 | 51 |
| Magyar Hírlap | 678 | 259 | 139 |
| Infostart | 559 | 50 | 114 |
| Telex | 552 | 50 | 27 |
| Magyar Nemzet | 458 | 1 | 0 |
| Világgazdaság | 390 | 10 | 1 |
| 444 | 340 | 48 | 27 |
| Bors | 216 | 0 | 0 |
| 168.hu | 68 | 1 | 0 |
| Népszava | 36 | 0 | 0 |
| **Összesen** | **8464** | **848** | **547** |

---

## Adatszerkezet és változók

Az adatok elérése SQLite relációs formátumban (`news_database.db`) és UTF-8 kódolású CSV állományokban biztosított. A nyers szövegek (`content_raw`) mellett a tisztított szövegmezők is megőrzésre kerültek a reprodukálhatóság érdekében.

A korpusz tábláit egyértelmű azonosítók kötik össze:
- `mti_id`: Az MTI-hír egyedi kulcsa.
- `article_id`: A sajtócikk egyedi kulcsa.
- `outlet_id`: A hírforrás azonosítója.

### 2. táblázat: Az MTI hírek alapadatai (`mti_news`)

| Változó | Leírás |
| :--- | :--- |
| `id` | Az MTI-hír egyedi numerikus azonosítója (`mti_id`) |
| `guid` | Az MTI hírfolyamból származó globális hivatkozási azonosító |
| `url` | Az MTI hír eredeti elérhetősége |
| `title` | A kiadott hírügynökségi cím |
| `lead` | A hír bevezető összefoglalója |
| `content_raw` | A hír teljes szövege |
| `published_at` | A megjelenés hivatalos időbélyege (ISO 8601 formátumban) |
| `word_count` | A hír szószáma |
| `primary_topic` | A hír elsődleges témakódja (CAP/MTA 1–33) |
| `secondary_topic` | A hír másodlagos témakódja összetett hírek esetén (opcionális, CAP/MTA 1–33) |

### 3. táblázat: A sajtócikkek alapadatai (`articles`)

| Változó | Leírás |
| :--- | :--- |
| `id` | Az újságcikk egyedi numerikus azonosítója (`article_id`) |
| `outlet_id` | A közzétevő hírportál azonosítója (külső kulcs: `outlets.id`) |
| `url` | A sajtócikk állandó hivatkozása |
| `title` | A cikk portálon megjelent címe |
| `lead` | A cikk felvezető szövege |
| `content_raw` | A letöltött cikk teljes törzsszövege |
| `published_at` | A publikálás időbélyege |
| `has_mti_citation` | Bináris jelölő: 1, ha a szövegben MTI hivatkozás vagy fotókredit található, egyébként 0 |
| `citation_excerpt` | Az MTI-re hivatkozó kifejezés környezete a cikkből (pl. hírforrásként vagy fotókreditként) |
| `citation_type` | A hivatkozás jellege: `TEXT` (szöveges hírforrás-megjelölés), `PHOTO_ONLY` (kizárólag illusztrációs képaláírás, szövegegyezés nélkül), `NONE` (nincs hivatkozás) |
| `word_count` | A cikk szószáma |

### 4. táblázat: Az átvételek és szentiment-transzformáció adatai (`matches`)

| Változó | Leírás |
| :--- | :--- |
| `id` | Az átvételi rekord egyedi azonosítója |
| `mti_id` | A hivatkozott MTI-hír kulcsa |
| `article_id` | Az átvevő sajtócikk kulcsa |
| `similarity_score` | Szöveghasonlósági érték a cikk és az MTI-hír között (0.00 és 1.00 között) |
| `latency_minutes` | A portálcikk és az MTI-hír nyilvános webes megjelenése közötti időkülönbség percekben (tájékoztató jellegű, negatív érték is lehetséges a közvetlen hírügynökségi előfizetői drót feedek miatt) |
| `sentiment_delta` | A portál cím/lead megfogalmazásának szentiment-elmozdulása a semleges MTI-hírhez képest (-1: negatív/dramatizált, 0: semleges átvétel, +1: pozitív/felmentő) |
| `sentiment_reason` | A szentiment-osztályozás szöveges indoklása és az azt alátámasztó kifejezések |

---

## Témakódolási kategóriarendszer (CAP / MTA TK PTI Média-kódkönyv)

A témák besorolása a Magyar Tudományos Akadémia Társadalomtudományi Kutatóközpontjának (MTA TK PTI) és a nemzetközi Comparative Agendas Projectnek (CAP) a hazai sajtóra kiegészített rendszerét követi (Boda–Sebők 2018, 49–52. o.).

### I. Közpolitikai főkategóriák (1–21)

- **1. Makrogazdasági politika:** Államháztartás, infláció, GDP, jegybanki alapkamat, adórendszer, gazdasági növekedés.
- **2. Emberi jogok és kisebbségek:** Alapjogok, kisebbségvédelem, vallásszabadság, diszkriminációellenes ügyek, egyenlő bánásmód.
- **3. Egészségpolitika:** Kórházak, gyógyszerellátás, egészségbiztosítás, járványügy, orvos- és ápolóbérek.
- **4. Agrárpolitika:** Mezőgazdaság, erdőgazdálkodás, élelmiszeripar, földművelés, agrártámogatások.
- **5. Foglalkoztatáspolitika:** Munkaerőpiac, munkanélküliség, munkajog, szakszervezetek, minimálbér.
- **6. Oktatáspolitika:** Közoktatás, felsőoktatás, szakképzés, pedagógusok helyzete, egyetemi autonómia.
- **7. Környezetpolitika:** Hulladékgazdálkodás, klímavédelem, környezetszennyezés, nemzeti parkok.
- **8. Energiapolitika:** Földgáz- és áramellátás, atomerőművek, megújuló energia, rezsicsökkentés.
- **9. Bevándorláspolitika:** Migráció, menekültügy, határőrizet, menedékkérők ellátása.
- **10. Közlekedéspolitika:** Vasút, közútfejlesztés, tömegközlekedés, légiközlekedés, hídépítés.
- **11. Igazságügy és büntetőpolitika:** Bírósági szervezet, törvényalkotás, Btk. módosítások, ügyészség, börtönügy.
- **12. Szociálpolitika:** Családtámogatások, nyugdíjak, rászorulók ellátása, szociális segélyezés, gyermekvédelem.
- **13. Területpolitika és lakásügy:** Településfejlesztés, önkormányzati fejlesztési források, lakáshitelek, CSOK.
- **14. Pénzügyi szabályozás és kereskedelempolitika:** Bankrendszer felügyelete, tőzsde, versenyhivatal, fogyasztóvédelem.
- **15. Honvédelem:** Magyar Honvédség, haditechnika, hadgyakorlatok, katonai védelem, szövetségi védelmi kötelezettségek.
- **16. Tudomány- és technológiapolitika:** Tudományos kutatás, akadémiai hálózat, innováció, információs társadalom.
- **17. Külgazdasági politika:** Nemzetközi kereskedelmi egyezmények, export-import, külföldi működőtőke-befektetések (FDI).
- **18. Külpolitika:** Diplomácia, nemzetközi konfliktusok, háborúk, Európai Unió, nemzetközi csúcstalálkozók.
- **19. Kormányzati működés:** Közigazgatás, állami intézmények átalakítása, közbeszerzések, állami kinevezések.
- **20. Földpolitika és természeti erőforrások:** Állami földvagyon kezelése, bányászat, vízkészlet-gazdálkodás.
- **21. Kulturális politika:** Állami kulturális támogatások, színházak, múzeumok és könyvtárak fenntartása.

### II. Média-specifikus kiegészítő kategóriák (22–33)

- **22. Időjárás és természeti katasztrófák:** Viharok, árvizek, rendkívüli hideg/meleg, földrengések.
- **23. Balesetek és katasztrófák:** Közlekedési balesetek, üzemtüzek, emberi mulasztásból fakadó szerencsétlenségek.
- **24. Művészetek, kultúra és szórakozás:** Filmpremierek, zenei koncertek, kulturális rendezvények (nem szakpolitikai döntések).
- **25. Sporthírek és rekreáció:** Bajnokságok, mérkőzéseredmények, sportolók hírei, olimpia.
- **26. Halálesetek és gyászjelentések:** Nekrológok, temetések, neves személyek elhalálozása.
- **27. Egyházak és vallás:** Vallási ünnepek, liturgia, egyházi események (nem állami finanszírozási kontextusban).
- **28. Politikai pártok:** Pártpolitikai csatározások, kampányhírek, sajtótájékoztatók, kongresszusok.
- **29. Bulvárhírek és hírességek:** Celebek élete, bulváresemények, életmód, könnyed színes hírek.
- **30. Bűnügyek:** Rendőrségi hírek, rablások, gyilkosságok, helyi bűncselekmények (nem jogpolitikai szinten).
- **31. Politikai korrupció:** Konkrét korrupciós botrányok, vagyonosodási vizsgálatok, etikai visszaélések.
- **32. Hírösszefoglalók, hírek röviden:** Több különböző témát felsoroló hírfolyamok, reggeli gyorshírek.
- **33. Egyéb:** Semelyik fenti kategóriába nem sorolható,Marginális vagy egyedi hírek.

---

## Döntési szabályok és fotókreditek kezelése

### A fotókreditek kezelése (`citation_type`)
A magyar online médiában gyakori, hogy a szerkesztőség saját önálló cikkéhez kizárólag illusztrációként használja az MTI fotószolgálatát. Annak érdekében, hogy ezek a technikai hivatkozások ne torzítsák a tartalmi hírátvételi és szentiment-statisztikákat, a következő kétlépcsős döntési szabály érvényesül:

1. **Kizárólag fotót átvevő cikkek (`PHOTO_ONLY`):**
   - Ha a cikkben szerepel az MTI fotókreditje (pl. *„Fotó: MTI / Koszticsák Szilárd”*, *„Címlapkép: MTI”*), **DE a cikk szövege önálló** (nincs azonosított MTI hírkapcsolat, vagy a szöveghasonlóság elhanyagolható: `similarity_score < 0.40`).
   - **Módszertani kezelés:** Ezeket a cikkeket a tartalmi átvételi és szentiment-elemzésből **kizárjuk**.
2. **Kettős átvétel (szövegátvétel fotókredittel):**
   - Ha a cikkben fotókredit szerepel, **DE a szövegtörzs érdemben megegyezik a kiadott MTI hírrel** (`similarity_score >= 0.40`, szerepel a `matches` táblában).
   - **Módszertani kezelés:** Ez **valós hírátvételnek minősül**, mivel a szerkesztőség magát a közleményt dolgozta fel, a fotóhasználat csupán másodlagos.

---

## Szentiment-transzformáció

### Döntési szabályok és fotókreditek kezelése

### A fotókreditek kezelése (`citation_type`)
A magyar online médiában gyakori, hogy a szerkesztőség saját önálló cikkéhez kizárólag illusztrációként használja az MTI fotószolgálatát. Annak érdekében, hogy ezek a technikai hivatkozások ne torzítsák a tartalmi hírátvételi és szentiment-statisztikákat, a következő kétlépcsős döntési szabály érvényesül:

1. **Kizárólag fotót átvevő cikkek (`PHOTO_ONLY`):**
   - Ha a cikkben szerepel az MTI fotókreditje (pl. *„Fotó: MTI / Koszticsák Szilárd”*, *„Címlapkép: MTI”*), **DE a cikk szövege önálló** (nincs azonosított MTI hírkapcsolat, vagy a szöveghasonlóság elhanyagolható: `similarity_score < 0.40`).
   - **Módszertani kezelés:** Ezeket a cikkeket a tartalmi átvételi és szentiment-elemzésből **kizárjuk**.
2. **Kettős átvétel (szövegátvétel fotókredittel):**
   - Ha a cikkben fotókredit szerepel, **DE a szövegtörzs érdemben megegyezik a kiadott MTI hírrel** (`similarity_score >= 0.40`, szerepel a `matches` táblában).
   - **Módszertani kezelés:** Ez **valós hírátvételnek minősül**, mivel a szerkesztőség magát a közleményt dolgozta fel, a fotóhasználat csupán másodlagos.

---

## Szentiment-transzformáció (`sentiment_delta`)
A vizsgálat kiindulópontja, hogy a hivatalos MTI-közlemény tájékoztató jellegű, intézményi semlegességre törekvő alaphangot képvisel (bázisérték = 0). A mutáció elemzése azt vizsgálja, hogy az átvevő portál címe és leadje ehhez képest milyen irányba hangolja a hírt:

- **`-1` (Negatív / dramatizált eltolódás):** A cím és lead a fenyegetést, a veszteséget, a botrányt, a bírálatot vagy a konfliktust helyezi előtérbe vészjósló vagy pejoratív stíluseszközökkel.
- **`0` (Semleges megőrzés):** A portál megtartja a tényszerű, tárgyilagos, leíró megfogalmazást, érdemi érzelmi moduláció nélkül.
- **`+1` (Pozitív / felmentő eltolódás):** A cím és lead a sikert, a megnyugtató fejleményt, a stabilitást vagy a felelősség alóli mentesülést hangsúlyozza elismerő szavakkal.

---

## Adatérvényesítés és hozzáférés

Az adatbázis integritása a következő lépésekkel került hitelesítésre:
1. **Előfizetői hírfolyam és időeltolódás kezelése:** A portálok az MTI zárt, fizetős előfizetői felületéről (hírügynökségi drótszolgálat) közvetlenül veszik át az anyagokat. Emiatt a nyilvános mti.hu weboldalon történő megjelenés és a portálcikk élesítése között időkülönbség mutatkozhat (akár negatív késleltetés is), amelyet az adatbázis tényadatként rögzít anélkül, hogy mesterségesen kizárná ezeket a valós híregyezéseket.
2. **Kettős ellenőrzés:** Minden átvételi kapcsolat rendelkezik mind szöveghasonlósági értékkel, mind kulcsszavas hivatkozásvizsgálattal.
3. **Reprodukálhatóság:** Az adatbázisban a nyers forrásszövegek (`content_raw`) és az eredeti webcímek (`url`) hiánytalanul elérhetők.

**Adathozzáférés:** A projekt adatai és elemző szkriptjei elérhetők a kutatási GitHub-tárhelyen: https://github.com/bekodonat/mti-figyelo
