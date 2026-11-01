# Počni ovde — LAKI Hybrid firmware (vodič korak po korak)

> **Status 1. novembar 2026.** **V5.1 FULL AUDIO RC1** prošao je offline SHA-256 provere, a zatim je **uspešno flešovan i funkcionalno proveren na jednom već X96-modifikovanom LAKI M6CW4K**. Rade Wi-Fi/internet, Bluetooth uparivanje i zvuk, IPTV, AUX i restart. **Netaknuti fabrički Orion bootloader i druge revizije nisu testirani.** [Zapisnik](V5_1_HARDWARE_VALIDATION_2026-11-01.md).
>
> Ovaj vodič je za **preuzimanje projekta i offline izradu IMG-a**, a ne za flešovanje uređaja. Ne objavljujemo kompletne vlasničke IMG/DTB datoteke.

**Izaberi put:**

- **A. Želim da preuzmem projekat, vidim kod i razumem postupak** → koraci 1–3.
- **B. Imam prethodno izrađene i proverene V4/V4.1/V5 fajlove** → koraci 1–8.
- **C. Imam samo fabrički LAKI box ili samo dva originalna ROM-a** → pročitaj [Šta za sada ne može od nule](#šta-za-sada-ne-može-od-nule). Trenutne skripte **ne mogu** same sastaviti kompletan V4.1/V5.1 IMG iz ta dva preuzeta ROM-a.

## 1. Proveri model uređaja (bez flešovanja)

Dokumentovani test: **Orion LAKI M6CW4K**, **Amlogic S905X3 / SM1**, **AC213**, **2 GB RAM / 16 GB memorija**, **Unisoc UWE5621** Wi-Fi/Bluetooth. Ostale revizije nisu proverene. Ako ADB već radi na tvom uređaju, identifikacija bez upisa na flash:

```bat
adb shell "cat /proc/device-tree/amlogic-dt-id"
adb shell "cat /proc/meminfo | head -n 3"
adb shell "uname -a"
```

Pročitaj [HARDWARE.md](HARDWARE.md). Sličan naziv uređaja **ne** znači da ima isti bootloader, DDR ili čip.

## 2. Preuzmi NAŠ kod sa GitHub-a

1. Otvori [projekat orion-laki-s905x3-hybrid](https://github.com/darkobg79/orion-laki-s905x3-hybrid).
2. Za verziju vezanu za objavljeni kandidat klikni **Releases**, zatim **v5.1.0-rc1**, pa **Source code (zip)**. **Ovaj ZIP sadrži skripte i dokumentaciju, ne gotov firmware IMG.** Ako je vodič dodat posle ovog taga, čitaj najnoviju verziju na grani `main`.
3. Alternativno, za **najnoviji razvojni kod** na početnoj stranici klikni zeleno **Code** → **Download ZIP**. Tu može biti izmena koje nisu deo RC1 izdanja.
4. Raspakuj ZIP, npr. u `C:\GitHub\orion-laki-s905x3-hybrid` (možeš izabrati drugo mesto). Proveri da postoje `scripts\build_laki_v51_full_audio.py` i `docs\V5_1_FULL_AUDIO.md`.

Ako koristiš Git, umesto ZIP-a možeš klonirati repozitorijum. Nije obavezno.

## 3. Preuzmi izvorne ROM-ove samo sa njihovih stranica

To su **izvorni firmveri drugih autora**, a ne naši gotovi hibridi:

| Izvor | Gde kliknuti | Tačna varijanta | Namena |
| --- | --- | --- | --- |
| [slimBOXtv — X96 Max Plus](https://slimboxtv.ru/x96max-plus/) | Nađi odeljak **“Для ревизии Plus 5”** → **“Скачать ATV или AOSP”** | **Plus 5**, slimBOXtv **9.20 ATV** | Referentni X96 DDR/U-Boot delovi |
| [slimBOXtv — Magicsee N5 Max X3](https://slimboxtv.ru/n5max-x3/) | Nađi odeljak **“Для ревизии 152F WiFi чип Unisoc uwe5621ds”** → **“Скачать ATV или AOSP”** | **152F / Unisoc UWE5621DS**, slimBOXtv **9.20 ATV** | Kernel / Android / Unisoc komponente |

Na stranici ili u arhivi **izaberi ATV, ne AOSP**; nemoj nasumično uzimati drugu reviziju ili noviju seriju ROM-a. Izvorne IMG datoteke ne objavljujemo na našem GitHub-u, a nazivi skinutih arhiva mogu biti drugačiji. Preuzimanje može zahtevati dodatnu prijavu ili potvrdu na strani izvornog izdavača. Proveri uslove korišćenja i distribucije.

**Važno:** samo preuzimanje ova dva ROM-a **nije dovoljno** da današnja javna skripta napravi V5.1. Zašto — vidi poslednji odeljak.

## 4. Instaliraj alate na Windows-u (za offline build)

Za **V5.1 builder** su potrebni:

- Windows 10/11;
- **Python 3.9+** ([python.org/downloads](https://www.python.org/downloads/)) sa dostupnom komandom `py -3`;
- **AmlImagePack.exe** iz sopstvenog, legalno pribavljenog Amlogic toolchain-a; predložena putanja je `C:\AmlogicKitchen\bin\windows\AmlImagePack.exe`;
- najmanje **9 GiB slobodnog prostora** na disku za izlaznu sliku i privremene particije;
- lokalne, već napravljene referentne IMG/DTB datoteke iz koraka 5.

U PowerShell-u proveri:

```powershell
py -3 --version
Test-Path 'C:\AmlogicKitchen\bin\windows\AmlImagePack.exe'
Get-PSDrive C
```

Ako gradiš **stariji V5 NOBOOTLOADER od V4 staging direktorijuma**, potrebni su **dodatno WSL2 Ubuntu i ext4/sparse alati**; vidi [BUILD.md](BUILD.md). Sam V5.1 kompozitor ne koristi WSL, ali mu je potrebna prethodno pripremljena V5 FULL slika.

## 5. Pripremi OBAVEZNE lokalne ulaze

U `C:\LakiBox-Backup` stavi **sopstvene ranije napravljene** datoteke:

```text
C:\LakiBox-Backup\
    LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img
    LAKI-Hybrid-V4.1-AUDIO-EARC-TEST.img
```

Potreban je i lokalni referentni `laki-v4-running.dtb` iz prethodnog **V4 audio-test kita ili sopstvenog bekapa** — taj DTB **ne postoji u ovom GitHub repozitorijumu**. Primer putanje:

```text
C:\LakiBox-Backup\V5.1-AUDIO-KIT\laki-v4-running.dtb
```

Ova putanja je **primer**, promeni je da pokazuje na stvarni fajl.

Proveri dva objavljena referentna SHA-256 otiska:

```powershell
Get-FileHash 'C:\LakiBox-Backup\LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img' -Algorithm SHA256
Get-FileHash 'C:\LakiBox-Backup\V5.1-AUDIO-KIT\laki-v4-running.dtb' -Algorithm SHA256
```

Očekivano:

```text
V5 FULL IMG:  AE80E1F705952FB04C3B21C7F4F2E57486FA45E0B2105282CDF70DCDC6D790F9
V4 DTB:       5D3902B74AD206078503051C858BE97963B7307F21D102C20A078C75E5A900FC
```

V4.1 IMG je zasebno napravljen i testiran; njegov ukupni SHA-256 **nije referentno objavljen**. Skripta zato pri build-u proverava da li su njegove dve audio particije **tačno** očekivani eARC patch polaznog V5 FULL firmware-a. **Ne pokušavaj da zameniš bilo koji od ovih fajlova nasumično preuzetim ROM-om.**

## 6. Testiraj skripte i pokreni probnu proveru bez pisanja

Otvori **PowerShell** u raspakovanom repozitorijumu (u File Explorer-u otvori folder pa u adresnu liniju upiši `powershell`):

```powershell
py -3 -m unittest discover -s tests -v
```

Zatim pokreni **preflight**. Zameni putanju do DTB-a ako je drugačija:

```powershell
py -3 scripts\build_laki_v51_full_audio.py --check-only --reference-dtb 'C:\LakiBox-Backup\V5.1-AUDIO-KIT\laki-v4-running.dtb' --output-root 'C:\LakiBox-Backup\LAKI-V5.1-REBUILD'
```

Provera očekuje izvore i paker na gore opisanim putanjama, slobodan prostor i referentne hashove. **`--check-only` ne otvara/raspakuje sve particije**, već radi početnu proveru i ne pravi izlazni IMG. Ako prijavi `STOP`, otkloni tačno navedeni problem; ne isključuj provere SHA-256.

## 7. Napravi V5.1 FULL AUDIO offline

Pokreni istu komandu **bez** `--check-only`:

```powershell
py -3 scripts\build_laki_v51_full_audio.py --reference-dtb 'C:\LakiBox-Backup\V5.1-AUDIO-KIT\laki-v4-running.dtb' --output-root 'C:\LakiBox-Backup\LAKI-V5.1-REBUILD'
```

`--output-root` mora pokazivati na **nov, nepostojeći direktorijum**. Skripta odbija da prepiše postojeće rezultate. Ona će:

1. Raspakovati tvoje lokalne V5 FULL i V4.1 IMG fajlove;
2. Nezavisno potvrditi da je V4.1 audio sadržaj očekivani eARC-off patch;
3. U kopiji V5 FULL zameniti **samo** `boot.PARTITION` i `_aml_dtb.PARTITION`;
4. Spakovati novu Amlogic IMG sliku;
5. Ponovo je raspakovati i proveriti SHA-256 svih particija i manifest FULL bootloadera;
6. Napisati JSON izveštaj.

Očekivane izlazne datoteke:

```text
C:\LakiBox-Backup\LAKI-V5.1-REBUILD\
    LAKI-Hybrid-V5.1-FULL-X96-AUDIO-V4.1-UNTESTED.img
    LAKI-V5.1-FULL-AUDIO-BUILD-REPORT.json
```

## 8. Proveri rezultat — i zaustavi se pre flešovanja

```powershell
Get-FileHash 'C:\LakiBox-Backup\LAKI-V5.1-REBUILD\LAKI-Hybrid-V5.1-FULL-X96-AUDIO-V4.1-UNTESTED.img' -Algorithm SHA256
Get-Content 'C:\LakiBox-Backup\LAKI-V5.1-REBUILD\LAKI-V5.1-FULL-AUDIO-BUILD-REPORT.json'
```

**Poznati otisak ranije izrađenog V5.1 IMG-a:**

```text
B4D2CD269AB8516F123111DB5A234317A258C3D3835AA945EF7A6CED04D8A378
```

Ako nova izrada ima drugačiji ukupni SHA-256, **ne proglašavaj automatski da je dobra ili loša**: uporedi poreklo i JSON izveštaj; pakovanje može promeniti bajtove čak i kad je sadržaj particija isti. Sam uspešan pack/unpack **ne** dokazuje da će uređaj bootovati.

> [!CAUTION]
> **OVDE SE VODIČ ZAVRŠAVA. NE FLEŠUJ AUTOMATSKI.** FULL slika sadrži eksplicitnu X96 `PARTITION/bootloader` stavku. V5.1 jeste uspešno flešovan **na jednom već X96-modifikovanom uređaju**, uz izabrane opcije brisanja podataka i bootloadera, ali neispravna DDR/U-Boot kombinacija može onesposobiti drugi uređaj. **Fabrički netaknuti Orion bootloader i druge revizije nisu testirani; nema univerzalno sigurnih opcija flešovanja.** Pročitaj [FLASHING.md](FLASHING.md) i [hardverski zapisnik](V5_1_HARDWARE_VALIDATION_2026-11-01.md).

## Šta za sada ne može od nule

**Naš javni GitHub još nije „jedan klik od dva originalna ROM-a do V5.1“.**

- [`finalize_laki_v5.py`](../scripts/finalize_laki_v5.py) zahteva unapred pripremljen i odgovarajući **V4 staging direktorijum** i poznati V4 IMG.
- [`build_laki_v5_full.py`](../scripts/build_laki_v5_full.py) zahteva unapred napravljen V5 NOBOOTLOADER i njegov uspešan build izveštaj.
- [`build_laki_v51_full_audio.py`](../scripts/build_laki_v51_full_audio.py) zahteva verifikovani V5 FULL, testirani V4.1 i **lokalni referentni DTB**.
- Automatsko sastavljanje **V4 hibrida direktno iz dva donatorska ROM-a**, kao i potpuni automatizovani V4.1 audio patch/build iz tih izvora, još **nije završeno i javno potvrđeno kao end-to-end postupak**.

To je **poznato ograničenje**, ne greška korisnika. Ako nemaš potrebne ulaze, **stani na koraku 3**: nemoj imitirati nazive lokalnih datoteka ili preskakati hash provere. Planirani sledeći razvojni korak je alat za pouzdano pravljenje V4/V4.1 iz zakonito pribavljenih ulaza uz proveru svake particije.

## Pomoć i prijavljivanje problema

- [Build detalji i istorijski V5 proces](BUILD.md)
- [V4.1 AUX/HDMI dijagnostika](V4_1_AUDIO.md)
- [V5.1 FULL AUDIO tehnički zapisnik](V5_1_FULL_AUDIO.md)
- [Rizici flešovanja i oporavak](FLASHING.md)
- [Hardware compatibility report](../.github/ISSUE_TEMPLATE/hardware-report.md)
- [Otvori GitHub Issue](https://github.com/darkobg79/orion-laki-s905x3-hybrid/issues/new/choose)

U logovima za javno deljenje ukloni lozinke, tokene, serijske brojeve, MAC adrese, naloge i IP adrese.
