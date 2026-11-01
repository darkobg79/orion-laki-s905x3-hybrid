# Orion LAKI M6CW4K TV Box (S905X3) — Hibridni Android TV firmware

**Dokumentacija i alati za pravljenje hibridnog ROM-a za Orion LAKI TV Box sa Amlogic S905X3 / AC213 pločom i Unisoc UWE5621 Wi-Fi/Bluetooth modulom.**

[English README](README.md) · [Uputstvo za izradu](docs/BUILD.md) · [Hardver](docs/HARDWARE.md) · [Problemi i rešenja](docs/TROUBLESHOOTING.md) · [Rizici flešovanja](docs/FLASHING.md)

> [!IMPORTANT]
> **V4 je stvarno testiran na fizičkom uređaju. V5 NOBOOTLOADER i V5 FULL su spakovani i verifikovani offline, ali još nisu fizički flešovani ni testirani posle čistog brisanja.** U ovom repozitorijumu nema gotovih IMG fajlova niti vlasničkih ROM-ova.

## Kako je sve počelo

Orion LAKI Box (S905X3, 2 GB RAM, 16 GB memorije) ima **Unisoc UWE5621** modul. Mnogi S905X3 custom ROM-ovi se pokreću, ali Wi-Fi i Bluetooth ne rade zbog neodgovarajućeg kernela i vendor komponenti.

- **SlimBOXtv 9.20 ATV za X96 Max Plus 5:** Android, Ethernet i daljinski su radili, ali nisu Wi-Fi i Bluetooth.
- Pokušaj ručnog učitavanja originalnih Unisoc `.ko` modula nije uspeo zbog nekompatibilnih kernel simbola.
- **Magicsee N5 Max X3** imao je Unisoc kernel/vendor/BT HAL, ali kompletan ROM se zaustavljao na oko **7%** sa `Uboot/Get result/DiskInitial error`.
- Rešenje je bio **Hybrid V4**: X96 DDR/U-Boot delovi, prilagođeni AC213 Device Tree i Magicsee kernel/sistem/vendor/Unisoc drajveri.

V4 je uspešno flešovan (`[0x00000000] Burning successfully`), Android se pokrenuo, **Wi-Fi se povezao na mrežu**, a **Bluetooth je pronašao, upario i reprodukovao zvuk na Xiaomi Desktop Speaker-u**.

## Nazivi originalnih ROM-ova (IMG)

Ovo su tačni nazivi SlimBOXtv ATV 9.20 firmware fajlova koje sam koristio:

| Uređaj / ROM | Naziv IMG fajla | Namena |
| --- | --- | --- |
| X96 Max Plus 5 | `sbx_x96max_plus_5_atv_9_20.img` | Funkcionalna DDR inicijalizacija i U-Boot |
| Magicsee N5 Max X3 152F | `sbx_n5max_x3_152f_atv_9_20.img` | Kernel, Android sistem i Unisoc Wi-Fi/Bluetooth drajveri |

X96 ROM se uspešno pokretao, ali Wi-Fi i Bluetooth nisu radili. Magicsee ROM je sadržao potrebne komponente, ali se direktno flešovanje zaustavljalo na približno **7%**, uz grešku `Uboot/Get result/DiskInitial error`.

Rešenje je bilo kombinovanje odgovarajućih komponenti oba ROM-a i prilagođavanje Device Tree konfiguracije za AC213 ploču.

### Nazivi hibridnih IMG fajlova

| Naziv IMG fajla | Status |
| --- | --- |
| `LAKI-Hybrid-V4-NOBOOTLOADER-UNTESTED.img` | Fizički testiran: Android TV, Wi-Fi i Bluetooth zvuk rade |
| `LAKI-Hybrid-V5-FINAL-WiFi-BT.img` | Uspešno spakovan i offline proveren; nije fizički testiran |
| `LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img` | Uspešno spakovan i offline proveren; nije fizički testiran |

Nazivi su navedeni radi lakšeg pronalaženja i identifikacije odgovarajućih ROM-ova. Gotove IMG datoteke nisu uključene u repozitorijum.

**Važno:** Pre flešovanja obavezno proveriti kompatibilnost hardvera, posebno reviziju ploče, DDR konfiguraciju i bootloader.

## Potvrđeni hardver

| Komponenta | Vrednost |
| --- | --- |
| Model boxa | `M6CW4K` |
| SoC | Amlogic S905X3 (`sm1`) |
| Ploča | AC213 |
| Fabrički DT | `sm1_ac213_g10xc2g` |
| Hibridni DT | `sm1_ac213_2g` |
| RAM / memorija | 2 GB / 16 GB |
| Wi-Fi / Bluetooth | Unisoc UWE5621 |
| Kernel hibridnog ROM-a | Linux 4.9.113 |

**Drugi LAKI Box ne mora biti identičan samo zato što ima isto komercijalno ime.** Obavezno proveriti reviziju ploče, DDR i eMMC pre bilo kakvog flešovanja.

## Bluetooth — ključni problem i rešenje

Sva tri Unisoc kernel modula bila su učitana:

```text
sprdwl_ng
sprdbt_tty
uwe5621_bsp_sdio
```

Međutim, Android Bluetooth servis se rušio stotinama puta. `logcat -b crash` pokazao je:

```text
Process: com.android.bluetooth
java.lang.SecurityException: Permission Denial
... requires android.permission.READ_CONTACTS or android.permission.WRITE_CONTACTS
... BluetoothPbapService.start(...)
```

Na našem rootovanom V4 uređaju problem je rešen komandom:

```bat
adb shell pm grant com.android.bluetooth android.permission.READ_CONTACTS
```

Nakon toga `dumpsys bluetooth_manager` prikazivao je `state: ON`, uređaji su uspešno otkrivani, a upareni Xiaomi zvučnik je reprodukovao zvuk.

**V5** pokušava da ovu dozvolu dodeli automatski kroz `/system/etc/default-permissions/laki-bluetooth.xml`. Fajl je uspešno upisan u sliku i offline proveren, ali **primena nakon fabričkog resetovanja još nije potvrđena na stvarnom uređaju**.

## Verzije i provereni SHA-256

| Verzija | Status | SHA-256 |
| --- | --- | --- |
| V4 NOBOOTLOADER | **Fizički testiran**; Wi-Fi + Bluetooth zvuk rade | `D22AB3AAFBE71C9201360BA15762952C3CD94C0D14BE788AD8EE8B4D3FF200BF` |
| V5 NOBOOTLOADER | Offline proveren; **nije flešovan** | `900DCEF88826BEC6F77516788B5612022C338515E945E309CC41EDCE1631CD4B` |
| V5 FULL X96 BOOTLOADER | Offline proveren; **nije flešovan** | `AE80E1F705952FB04C3B21C7F4F2E57486FA45E0B2105282CDF70DCDC6D790F9` |

**FULL** ima eksplicitnu `PARTITION/bootloader` stavku sa X96 komponentama. **NOBOOTLOADER** nema tu eksplicitnu stavku, ali sadrži DDR i U-Boot elemente potrebne za USB proces. Naziv ne garantuje šta će stvarno biti upisano — ponašanje zavisi i od USB Burning Tool podešavanja.

## Izrada (Windows CMD / PowerShell + WSL 2)

Potreban je sopstveni, zakonito pribavljen V4 sadržaj u `C:\LakiBox-Backup`, Python, Ubuntu/WSL 2, ext4/sparse alati i `AmlImagePack.exe` (nabavlja se zasebno).

```powershell
wsl -u root -e bash -lc "apt update && apt install -y e2fsprogs android-sdk-libsparse-utils"
py -3 scripts\finalize_laki_v5.py --packer "C:\AmlogicKitchen\bin\windows\AmlImagePack.exe"
```

Kada V5 NOBOOTLOADER prođe offline proveru i postoji njegov JSON izveštaj:

```powershell
py -3 scripts\build_laki_v5_full.py --packer "C:\AmlogicKitchen\bin\windows\AmlImagePack.exe"
```

Više detalja u [BUILD.md](docs/BUILD.md). Skripte **samo rade sa lokalnim fajlovima**; ne šalju komande uređaju i ne flešuju ga. GitHub verzija prve skripte uključuje naknadnu ispravku za kreiranje direktorijuma za verifikaciju; ta konkretna revizija još nije ponovo testirana od početka do kraja.

## Bezbednost i odgovornost

Prvi box je već dobio X96 bootloader prilikom ranijeg flešovanja. Uspeh V4 zato **nije dokaz** da V5 FULL može bezbedno da se instalira na drugi box koji je još na fabričkom bootloaderu.

**Ne uključivati naslepo `Erase flash` ili `Erase bootloader`.** Pogrešan DDR/U-Boot može sprečiti ulazak u USB Burning režim. Potreban je bekap i realan plan oporavka. Pročitaj [FLASHING.md](docs/FLASHING.md).

U ovom repozitorijumu nalaze se dokumentacija, konfiguracioni fajlovi i skripte za izradu LAKI Hybrid firmware-a. Gotove IMG slike nisu uključene; za samostalnu izradu potrebno je obezbediti odgovarajuće ulazne ROM-ove.

Skripte i dokumentacija dostupne su pod [MIT licencom](LICENSE). Projekat je nezavisan i namenjen eksperimentisanju, razmeni iskustava i daljem razvoju firmware-a za Orion LAKI TV Box.

Ovo je nezavisan eksperimentalni projekat, a ne zvaničan firmware proizvođača.
