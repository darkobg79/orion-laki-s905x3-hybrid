# LAKI Hybrid V6 — od dva originalna ROM-a do jednog IMG-a

**V6 FULL AUDIO by DarkoBG ne zahteva V4, V4.1, V5, V5.1 ni V5.2 IMG ili njihove staging direktorijume.** Preuzimaš dva originalna donatorska ROM-a, pokrećeš jedan builder i dobijaš jednu novu FULL AUDIO sliku. Interno raspakivanje i proveru radi program automatski; nakon uspeha privremeni direktorijumi se brišu.

> [!CAUTION]
> **Status 1.11.2026: V6 je uspešno izgrađen na Windows računaru direktno iz dva donatorska IMG-a, offline verifikovan i fizički testiran na jednom ranije modifikovanom LAKI boxu (9/9 PASS prema izveštaju operatera).** Ovo je **FULL** slika sa eksplicitnom X96 bootloader particijom. Ne koristi je na fabričkom Orion uređaju ili drugoj reviziji ploče samo na osnovu offline provere. Ovo uputstvo je za **izradu firmware-a**, ne bezbedno flešovanje.

## 1. Proveri da li imaš odgovarajući uređaj

Ova konkretna konfiguracija je za **Orion LAKI M6CW4K**, **Amlogic S905X3 / SM1**, **AC213**, **2 GB RAM / 16 GB**, **Unisoc UWE5621**. Model na nalepnici nije dovoljan dokaz kompatibilnosti; proveri reviziju PCB-a, DDR i čipset. Pročitaj [FLASHING.md](FLASHING.md).

## 2. Preuzmi DVA originalna donatorska ROM-a

To nisu fajlovi iz našeg GitHub Release-a. Uzmi ih iz zvaničnih objava autora:

1. **X96 Max Plus — baš „Plus 5“ — slimBOXtv 9.20 ATV:** https://slimboxtv.ru/x96max-plus/ (nađi odeljak *Для ревизии Plus 5*, pa odgovarajući ATV 9 download).
2. **Magicsee N5 Max X3 — baš „152F WiFi Unisoc uwe5621ds“ — slimBOXtv 9.20 ATV:** https://slimboxtv.ru/n5max-x3/ (nađi odeljak *Для ревизии 152F WiFi чип Unisoc uwe5621ds*, pa odgovarajući ATV 9 download).

Ako preuzimanje daje ZIP/7z/RAR, raspakuj ga do **punog Amlogic USB Burning Tool `.img` fajla**, ne pojedinačnih `boot.img` ili `system.img` fajlova. Originalni doslovni nazivi donatorskih arhiva nisu nezavisno potvrđeni, pa builder prihvata **putanje koje mu ti zadaš**, ne izmišljena fabrička imena. Ne preuzimaj pogrešnu reviziju ili AOSP umesto ATV.

**Dijagnostika prepoznaje tačno komponente koje smo koristili 2026-10-31/11-01** (SHA-256 X96 DDR/U-Boot/DTB, Magicsee boot/DTB/vendor/manifest). Ako izdavač zameni ROM drugim izdanjem, builder **staje** umesto da nagađa kompatibilnost. Nikad ne uklanjaj SHA zaštite radi prolaska testa.

## 3. Pripremi Windows 10/11

Instaliraj **Python 3.9+**, **WSL 2 sa Ubuntu** i nabavi **AmlImagePack.exe** iz sopstvenog Amlogic toolchain-a; ovaj projekat ne distribuira taj alat ni vlasnički firmware. Otvori PowerShell:

```powershell
py -3 --version
wsl --status
wsl -u root -e bash -lc "apt update && apt install -y e2fsprogs android-sdk-libsparse-utils python3"
wsl -e bash -lc "command -v simg2img && command -v img2simg && command -v debugfs && command -v e2fsck && command -v python3"
```

Treba da imaš **najmanje 12 GiB slobodnog prostora** na disku na kojem se pravi izlaz. Ovaj zahtev je konzervativna zaštita, ne obećanje da će svi diskovi imati dovoljno mesta. Putanja privremenog WSL radnog direktorijuma ne sme imati razmake; izaberi npr. `C:\LakiBox-Backup\LAKI-V6-BUILD`.

## 4. Preuzmi V6 skripte

Za V6 preuzmi izvorni kod repozitorijuma ili GitHub Release `v6.0.0` (sadrži skripte i dokumentaciju, **ne gotov vlasnički IMG**). Iz komandne linije koristi `scripts/build_laki_v6.py`, a interaktivni pokretač je `tools/v6/RUN-V6.cmd`. Stariji tag `v5.1.0-rc1` ne sadrži V6.

Za potpuno lokalni kit koristi arhivu `LAKI-Hybrid-V6-FINAL-One-Step-by-DarkoBG.zip` iz ovog razgovora: sadrži sve naše skripte, ali ne sadrži originalne ROM-ove, DTB blobove ili AmlImagePack.

## 5. Pokreni jednim postupkom

**Najlakše:** dvoklik `tools/v6/RUN-V6.cmd` iz preuzetog izvornog repozitorijuma. Unesi pune putanje do oba prethodno preuzeta IMG-a. Pritisak na Enter za AmlImagePack koristi podrazumevani `C:\AmlogicKitchen\bin\windows\AmlImagePack.exe`. Izaberi **novi** izlazni direktorijum (interaktivni pokretač sam izabere jedinstveno ime ako podrazumevani već postoji). Program prvo radi proveru bez pisanja, zatim traži da ukucaš `BUILD` i automatski izvodi ceo postupak.

**CMD/PowerShell alternativa — jedna glavna komanda:**

```bat
py -3 scripts\build_laki_v6.py --x96-img "C:\DonorROMs\X96-Plus5-ATV920.img" --magicsee-img "C:\DonorROMs\Magicsee-152F-ATV920.img" --packer "C:\AmlogicKitchen\bin\windows\AmlImagePack.exe" --output-root "C:\LakiBox-Backup\LAKI-V6-BUILD"
```

`C:\DonorROMs\...` su **primeri**, ne navodni originalni nazivi ROM-a. Zameni ih stvarnim putanjama. Ako želiš samo proveru pre rada, dodaj `--check-only`. Ako želiš da sačuvaš sve interne faze radi revizije (više prostora), dodaj `--keep-work`. Builder odbija već postojeći izlazni direktorijum i **ne menja donatorske IMG fajlove**.

## 6. Šta program automatski radi?

| Redosled | Unutrašnji korak | Šta završava u V6 |
| --- | --- | --- |
| 1 | Raspakuje oba originalna IMG-a preko AmlImagePack | Nema ručnih Level-1 direktorijuma |
| 2 | Proverava hashove i `image.cfg` | Odbija nepoznat donor i nepodudaranje revizija |
| 3 | Preuzima X96 `DDR.USB`, U-Boot, `aml_sdc_burn.ini`, `platform.conf` i manifest | **X96 FULL bootloader** |
| 4 | Zadržava Magicsee `system`, `vendor`, `product`, `odm`, `recovery` i ostale Android particije | Magicsee Android 9 i Unisoc sistem |
| 5 | Menja X96 AC213 Wi-Fi IRQ (`0x49→0x54`, LOW→HIGH) i BT `gpio_en→gpio_reset` | Radijska konfiguracija iz proverene V4 procedure |
| 6 | Isključuje eARC i uklanja `aml-audio-card,dai-link@6` | Audio ispravka iz V4.1 |
| 7 | Kombinuje originalni Magicsee kernel sa prilagođenim DTB-om, ažurira Android boot SHA-1 | Jedinstveni `boot.PARTITION` i `_aml_dtb.PARTITION` |
| 8 | Dodaje Bluetooth `READ_CONTACTS` XML **i menja samo 3 Android identifikaciona svojstva** kroz WSL/ext4 u JEDNOM prolazu | `m6cw4k`, `LAKI`, `LAKI Hybrid V6 FULL AUDIO by DarkoBG` |
| 9 | Pakuje jedan Amlogic USB Burning Tool IMG | **V6 FULL AUDIO** |
| 10 | Ponovo raspakuje, poredi sve particije, zapisuje SHA-256 i JSON | Konačna offline provera |

**Nema ulaznih V4/V5 slika.** Fabricki Magicsee `build.prop` sa dozvolama `0600`, vlasništvom `root:root` i SELinux oznakom se čuva sa originalnim dozvolama (`0600` ili `0644`); ne forsira se `0644`. `ro.product.name`, `ro.product.device`, `ro.product.manufacturer`, `ro.build.fingerprint` i `vendor` se ne menjaju. Interni privremeni fajlovi se uklanjaju po završetku uspešne provere. Ako dođe do greške, izlazni direktorijum zadržava oznaku `INCOMPLETE-NOT-VALIDATED.txt`; takvu sliku **ne koristiti**.

## 7. Prepoznaj rezultat i proveri SHA-256

Ako sve prođe, u novom izlaznom direktorijumu se nalaze:

```text
LAKI-V6-BUILD/
  LAKI-Hybrid-V6-FULL-AUDIO-by-DarkoBG.img
  LAKI-V6-BUILD-REPORT.json
  SHA256SUMS.txt
```

U PowerShell-u proveri **stvarni SHA-256 svojeg novog fajla**:

```powershell
Get-FileHash 'C:\LakiBox-Backup\LAKI-V6-BUILD\LAKI-Hybrid-V6-FULL-AUDIO-by-DarkoBG.img' -Algorithm SHA256
```

Uporedi sa poljem `output_sha256` u JSON izveštaju. **Nemoj očekivati stari V5.1 IMG SHA `B4D2...`**: ponovno ext4/sparse pakovanje može proizvesti drugačiji zbir iako ciljane audio particije odgovaraju poznatim hashovima:

```text
boot.PARTITION:     A334E39C6600731A352A2DB259C1B0F6F4D24BA09EFB049BC357DF9F52E91F6B
_aml_dtb.PARTITION: FD33629D04630DF9A437DDDD5F870FE94D6C4EE9755055B5B380DADE625FC13E
```

Ovi hashovi potvrđuju reprodukovane audio particije. **Zasebni V6 hardverski test na jednom ranije modifikovanom boxu prijavljen je kao 9/9 PASS**; time nije dokazana kompatibilnost sa drugim uređajima. Vidi [zapisnik](V6_HARDWARE_VALIDATION_2026-11-01.md).

## 8. Šta V6 *ne* rešava i šta NE treba raditi

- **Nema potvrđenog bezbednog flešovanja na potpuno fabričkom Orion LAKI bootloaderu.** FULL image ima eksplicitnu X96 bootloader particiju. Ne nudimo univerzalna USB Burning Tool čekiranja; čitaj [FLASHING.md](FLASHING.md).
- Potvrđeno je funkcionalno Bluetooth uparivanje bez ručne ADB dodele dozvole na jednom testiranom boxu; zaseban izveštaj `dumpsys` o dozvoli i trajna stabilnost nisu obezbeđeni.
- IPTV aplikacija koju je operater ranije instalirao u `/data`, DRM ključevi, konfiguracije i korisnički podaci ne pojavljuju se automatski u V6 IMG-u.
- **Nema gotovih vlasničkih ROM-ova u repozitorijumu**, niti ova procedura daje dozvolu za njihovu redistribuciju.
- Ovo je **jedan postupak izrade**, ali **nije potvrđen univerzalni one-click flash** na bilo kojoj LAKI hardverskoj reviziji.

## 9. Ako builder stane

- `Unexpected source ... SHA256`: pogrešan donor ili revizija; preuzmi tačno dokumentovane ROM-ove. Ne isključuj zaštitu.
- `Original donor manifests differ`: različite ili izmenjene donatorske verzije; ne spajaj naslepo.
- `No such file / AmlImagePack`: ispravi `--packer` i proveri IMG putanje.
- `WSL sparse/ext4 utilities`: podesi WSL2 Ubuntu i instaliraj `e2fsprogs` i `android-sdk-libsparse-utils`.
- `Output directory already exists`: sačuvaj postojeći rezultat i izaberi potpuno novu putanju.
- `Insufficient space`: obezbedi najmanje 12 GiB slobodnog prostora za bezbedno pakovanje.
- `Unexpected build.prop mode` ili `SELinux` : sačuvaj rezultat i stani; V6 prihvata samo očekivani `0600/0644` i prepoznatu oznaku, ništa se ne forsira.
- `INCOMPLETE-NOT-VALIDATED.txt`: ne flešuj; pregledaj puni tekst greške, sačuvaj izvore.

Razvoj i testovi: `py -3 -m unittest discover -s tests -v`. Testovi su **bezbednosne provere logike i ne predstavljaju fizičku validaciju firmware-a**.

### Ispravka GZIP kompatibilnosti (1.11.2026.)

Prethodni Windows build je mogao da stane na proverenom Wi-Fi/BT DTB-u zbog razlike u GZIP zaglavlju između Python verzija. Novi V6 koristi `gzip.GzipFile(..., mtime=0, filename='', compresslevel=9)` za Wi-Fi i audio DTB i proverava **i raspakovani sadržaj i nepromenjene originalne SHA-256 vrednosti komprimovanih particija**. Nijedna bezbednosna provera nije isključena. Ne briši nepotpun izlaz, već koristi novi izlazni direktorijum.
