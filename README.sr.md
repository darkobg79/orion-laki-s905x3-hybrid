# Orion LAKI M6CW4K TV Box (S905X3) — Hibridni Android TV firmware

**Tehnička dokumentacija za Orion LAKI M6CW4K, V6 izradu iz dva donatorska IMG-a i istorijske V5/V5.1 offline alate.**

[English README](README.md) · [**Počni ovde — korak po korak**](docs/START_HERE.sr.md) · [**Start Here (English)**](docs/START_HERE.md) · [V4.1 audio provera](docs/V4_1_AUDIO.md) · [V5.1 FULL AUDIO](docs/V5_1_FULL_AUDIO.md) · [Uputstvo za izradu](docs/BUILD.md) · [Hardver](docs/HARDWARE.md) · [Problemi i rešenja](docs/TROUBLESHOOTING.md) · [Rizici flešovanja](docs/FLASHING.md)

> [!IMPORTANT]
> **Najnovija V6.0.0 je prema izveštaju prošla 9/9 fizičkih provera na jednom već modifikovanom LAKI boxu; V5.1 FULL AUDIO ostaje rezervna hardverski potvrđena verzija.** Starije zasebne V5 NOBOOTLOADER/V5 FULL slike su samo offline proverene. Fabrički Orion bootloader nije testiran. [V6 zapisnik](docs/V6_HARDWARE_VALIDATION_2026-11-01.md). Gotovi IMG nisu objavljeni.

<!-- LAKI-V6-2026-11-01-RELEASE -->
## ✅ LAKI Hybrid V6.0.0 FULL AUDIO by DarkoBG — 9/9 fizičkih testova PASS

**Nova izrada u jednom postupku:** X96 Max Plus 5 ATV 9.20 + Magicsee N5 Max X3 152F ATV 9.20 → **jedan V6 FULL AUDIO IMG**, bez V4/V4.1/V5/V5.1 međuslika. Sačuvane su proverene AC213 Wi-Fi/Bluetooth i eARC audio korekcije.

- **Fizička potvrda 1.11.2026:** uspešno flešovanje i pokretanje na jednom Orion LAKI M6CW4K prema izveštaju operatera, uz **9/9 PASS**: Android, model i naziv, Wi-Fi/internet, Bluetooth pronalaženje/uparivanje/zvuk, IPTV bez zastajkivanja, AUX, restart i Bluetooth dozvola bez ručnog ADB odobravanja.
- **Identitet:** `ro.product.model=m6cw4k`, `ro.product.brand=LAKI`, `ro.build.display.id=LAKI Hybrid V6 FULL AUDIO by DarkoBG`.
- **SHA-256 IMG-a:** `ABB9B548159192D7379BEFBB2D34B45FF85DACF2A6EB4209631635AD8F079F9E` (posebno potvrđeno komandom Windows `certutil`).
- **Dokumentacija:** [V6 uputstvo](docs/V6_ONE_STEP.sr.md) · [English guide](docs/V6_ONE_STEP.md) · [zapisnik 9/9](docs/V6_HARDWARE_VALIDATION_2026-11-01.md) · [release beleške](docs/V6_RELEASE_NOTES_2026-11-01.md).
- **Rezervna verzija:** V5.1 FULL AUDIO ostaje prethodno hardverski proverena slika; zasebne starije V5 NOBOOTLOADER i V5 FULL slike ostaju samo offline proverene.

**Ograničenje:** potvrda je sa jednog ranije modifikovanog boxa; **netaknuti fabrički Orion bootloader i druge revizije nisu testirani**. FULL sadrži X96 bootloader zapis. Gotove vlasničke IMG datoteke nisu objavljene. Vidi [rizike flešovanja](docs/FLASHING.md).

## Kako je sve počelo

Orion LAKI Box (S905X3, 2 GB RAM, 16 GB memorije) ima **Unisoc UWE5621** modul. Mnogi S905X3 custom ROM-ovi se pokreću, ali Wi-Fi i Bluetooth ne rade zbog neodgovarajućeg kernela i vendor komponenti.

- **SlimBOXtv 9.20 ATV za X96 Max Plus 5:** Android, Ethernet i daljinski su radili, ali nisu Wi-Fi i Bluetooth.
- Pokušaj ručnog učitavanja originalnih Unisoc `.ko` modula nije uspeo zbog nekompatibilnih kernel simbola.
- **Magicsee N5 Max X3** imao je Unisoc kernel/vendor/BT HAL, ali kompletan ROM se zaustavljao na oko **7%** sa `Uboot/Get result/DiskInitial error`.
- Rešenje je bio **Hybrid V4**: X96 DDR/U-Boot delovi, prilagođeni AC213 Device Tree i Magicsee kernel/sistem/vendor/Unisoc drajveri.

V4 je uspešno flešovan (`[0x00000000] Burning successfully`), Android se pokrenuo, **Wi-Fi se povezao na mrežu**, a **Bluetooth je pronašao, upario i reprodukovao zvuk na Xiaomi Desktop Speaker-u**.

## Izvorni ROM-ovi i nazivi hibridnih IMG datoteka

Za hibridni firmware korišćene su **slimBOXtv 9.20 ATV** verzije namenjene sledećim revizijama uređaja:

| Izvorni ROM | Potvrđena revizija na sajtu | Stranica za preuzimanje | Uloga u hibridnom ROM-u |
| --- | --- | --- | --- |
| X96 Max Plus | **Plus 5** | [slimBOXtv — X96Max Plus](https://slimboxtv.ru/x96max-plus/) | DDR inicijalizacija i U-Boot komponente koje rade na testiranom uređaju |
| Magicsee N5 Max X3 | **152F**, Unisoc UWE5621DS | [slimBOXtv — N5 Max X3](https://slimboxtv.ru/n5max-x3/) | Kernel, Android sistem i Wi-Fi/Bluetooth podrška |

**Na odgovarajućoj stranici treba izabrati tačnu reviziju uređaja.** Doslovni nazivi originalnih preuzetih IMG datoteka nisu nezavisno potvrđeni, pa ih ne navodimo napamet. Direktno flešovanje Magicsee ROM-a zaustavljalo se na približno **7%** uz grešku `Uboot/Get result/DiskInitial error`. X96 ROM se pokretao, ali Wi-Fi i Bluetooth nisu radili.

### Nazivi naših hibridnih IMG datoteka

| Naziv IMG datoteke | Potvrđeni status |
| --- | --- |
| `LAKI-Hybrid-V4-NOBOOTLOADER-UNTESTED.img` | **Testiran na uređaju:** Android, Wi-Fi i Bluetooth zvuk rade, uz ručno dodeljenu Bluetooth dozvolu |
| `LAKI-Hybrid-V4.1-AUDIO-EARC-TEST.img` | **Fizički flešovan i testiran:** IPTV slika, analogni AUX, Bluetooth zvuk i Wi-Fi rade; kompletan SHA-256 IMG fajla nije objavljen. |
| `LAKI-Hybrid-V5-FINAL-WiFi-BT.img` | Uspešno spakovan i offline proveren; **nije fizički testiran** |
| `LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img` | Uspešno spakovan i offline proveren; **nije fizički testiran** |
| `LAKI-Hybrid-V5.1-FULL-X96-AUDIO-V4.1-UNTESTED.img` | **Fizički testiran 1.11.2026.** Wi-Fi, Bluetooth/BT zvuk, IPTV, AUX, restart i Android boot rade na jednom već modifikovanom uređaju. |

Ovi nazivi odnose se na naše lokalno izrađene IMG datoteke, a ne na ROM-ove dostupne za preuzimanje iz ovog repozitorijuma. Oznaka `UNTESTED` u nazivu V4 datoteke istorijska je: V4 je naknadno uspešno testiran. Skripte za V5 zahtevaju prethodno pripremljenu V4 sliku; ne sastavljaju V4 automatski iz dva izvorna ROM-a.

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

## V4.1 — ispravka IPTV slike i analognog AUX zvuka

U V4 ALSA zvučna kartica nije bila registrovana (`No soundcards found`), pa se IPTV slika mogla zamrznuti pri otvaranju audio toka. U **V4.1** su lokalno izmenjeni audio DTB podaci u `boot.PARTITION` i `_aml_dtb.PARTITION`: isključen je nekompatibilni eARC čvor i uklonjen `dai-link@6`. Kartica `AML-AUGESOUND` zatim se registrovala, a IPTV video je normalno reprodukovan.

Direktni `tinyplay` na **TDM-B/T9015** potvrdio je da AV/AUX fizički proizvodi zvuk. Kod Android reprodukcije početna jačina `STREAM_MUSIC` bila je **17/65**, što je bilo gotovo nečujno; nakon povećanja na 50/65 ili 55/65 zvuk se čuo. Nije bilo potrebe za izmenom GPIO polariteta niti audio HAL biblioteke. Pri prebacivanju ONTEN HDMI switcha HPD i režim slike jesu se menjali, ali se **AUX glasnoća izjednačila pri istoj Android jačini 50/65**. Uzrok ranijih promena jačine nije dokazan.

```bat
adb shell media volume --stream 3 --get
adb shell media volume --stream 3 --set 50
```

Pre povećanja smanjiti fizičku jačinu zvučnika. Detaljna dijagnostika: [V4.1 audio provera](docs/V4_1_AUDIO.md). V4.1 je potvrđen na **jednom** boxu; IMG heš nije objavljen, a postojeće V5 skripte **ne sadrže** ovu V4.1 korekciju. Ranije zasebne V5 varijante **nisu fizički testirane**; V5.1 FULL AUDIO je naknadno fizički potvrđen.

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

Na testiranom V4 uređaju sa root pristupom problem je rešen komandom:

```bat
adb shell pm grant com.android.bluetooth android.permission.READ_CONTACTS
```

Nakon toga `dumpsys bluetooth_manager` prikazivao je `state: ON`, uređaji su uspešno otkrivani, a upareni Xiaomi zvučnik je reprodukovao zvuk.

**V5/V5.1** uključuje podrazumevanu Bluetooth dozvolu preko `/system/etc/default-permissions/laki-bluetooth.xml`. Posle brisanja podataka na V5.1 Bluetooth uparivanje i zvuk rade, ali **još nije zasebno dokazano** da je dozvola automatski dodeljena bez ručne intervencije (nedostaje zapis provere dozvole).

## Verzije i provereni SHA-256

**V4.1** (`LAKI-Hybrid-V4.1-AUDIO-EARC-TEST.img`) fizički je testiran, ali njegov SHA-256 nije ovde potvrđen. Ne koristiti heš stare V4 slike kao heš V4.1.

| Verzija | Status | SHA-256 |
| --- | --- | --- |
| V4 NOBOOTLOADER | **Fizički testiran**; Wi-Fi + Bluetooth zvuk rade | `D22AB3AAFBE71C9201360BA15762952C3CD94C0D14BE788AD8EE8B4D3FF200BF` |
| V5 NOBOOTLOADER | Offline proveren; **nije flešovan** | `900DCEF88826BEC6F77516788B5612022C338515E945E309CC41EDCE1631CD4B` |
| V5 FULL X96 BOOTLOADER | Offline proveren; **nije flešovan** | `AE80E1F705952FB04C3B21C7F4F2E57486FA45E0B2105282CDF70DCDC6D790F9` |
| V5.1 FULL AUDIO | **Fizički flešovan i funkcionalno potvrđen na jednom već modifikovanom uređaju** | `B4D2CD269AB8516F123111DB5A234317A258C3D3835AA945EF7A6CED04D8A378` |

**FULL** ima eksplicitnu `PARTITION/bootloader` stavku sa X96 komponentama. **NOBOOTLOADER** nema tu eksplicitnu stavku, ali sadrži DDR i U-Boot elemente potrebne za USB proces. Naziv ne garantuje šta će stvarno biti upisano — ponašanje zavisi i od USB Burning Tool podešavanja.

## Izrada (Windows CMD / PowerShell + WSL 2)

Za izradu V5 potreban je prethodno sastavljen V4 firmware u `C:\LakiBox-Backup`, Python, Ubuntu/WSL 2, ext4/sparse alati i `AmlImagePack.exe`. Izvorni ROM-ovi dostupni su na sajtu [slimBOXtv](https://slimboxtv.ru/): [X96 Max Plus — revizija Plus 5](https://slimboxtv.ru/x96max-plus/) i [Magicsee N5 Max X3 — revizija 152F, Unisoc UWE5621](https://slimboxtv.ru/n5max-x3/). Skripte za V5 ne sastavljaju V4 od početka.

```powershell
wsl -u root -e bash -lc "apt update && apt install -y e2fsprogs android-sdk-libsparse-utils"
py -3 scripts\finalize_laki_v5.py --packer "C:\AmlogicKitchen\bin\windows\AmlImagePack.exe"
```

Kada V5 NOBOOTLOADER prođe offline proveru i postoji njegov JSON izveštaj:

```powershell
py -3 scripts\build_laki_v5_full.py --packer "C:\AmlogicKitchen\bin\windows\AmlImagePack.exe"
```

Više detalja u [BUILD.md](docs/BUILD.md). Skripte **samo rade sa lokalnim fajlovima**; ne šalju komande uređaju i ne flešuju ga. GitHub verzija prve skripte uključuje naknadnu ispravku za kreiranje direktorijuma za verifikaciju; ta konkretna revizija još nije ponovo testirana od početka do kraja.

## V5.1 FULL AUDIO — fizički testiran na jednom uređaju

### Potvrđeni rezultati testiranja — 1.11.2026.

**V5.1 FULL AUDIO je uspešno flešovan i fizički testiran na jednom prethodno X96-modifikovanom Orion LAKI M6CW4K uređaju.**

| Funkcionalnost | V5.1 FULL AUDIO |
| --- | --- |
| Flešovanje uz brisanje podataka i bootloadera | ✅ PASS |
| Pokretanje Androida | ✅ PASS |
| Wi-Fi povezivanje | ✅ PASS |
| Internet pristup | ✅ PASS |
| Bluetooth pronalaženje uređaja | ✅ PASS |
| Bluetooth uparivanje | ✅ PASS |
| Bluetooth zvuk | ✅ PASS |
| IPTV slika bez zamrzavanja | ✅ PASS |
| Analogni AUX zvuk | ✅ PASS |
| Restart uređaja | ✅ PASS |
| Automatska dodela Bluetooth dozvole | ⚪ Nije zasebno proverena |
| Flešovanje na fabrički Orion bootloader | ⚪ Nije testirano |
| Ostale hardverske funkcionalnosti | ⚪ Nisu testirane |

**Status: ✅ V5.1 FULL AUDIO — HARDWARE TESTED / PASS**

Stariji V5 NOBOOTLOADER i V5 FULL predstavljaju zasebne slike i nisu fizički testirani. Oznaka `UNTESTED` u istorijskom nazivu V5.1 IMG fajla ne predstavlja više stvarni status testiranja.

[Detaljan zapisnik hardverskog testa](docs/V5_1_HARDWARE_VALIDATION_2026-11-01.md).


Dana 1.11.2026. uspešno je spakovana V5.1 FULL AUDIO slika sa dve proverene V4.1 audio particije (`boot.PARTITION` i `_aml_dtb.PARTITION`), uz očuvane V5 `system` i `vendor` particije i X96 FULL bootloader zapis. Slika je raspakovana i proverena po particijama, a posebno Windows SHA-256 očitavanje potvrdilo je:

`B4D2CD269AB8516F123111DB5A234317A258C3D3835AA945EF7A6CED04D8A378`

**V5.1 FULL AUDIO uspešno je flešovan i testiran 1.11.2026.** Uz uključene opcije brisanja podataka i bootloadera, Android se pokrenuo i potvrđeni su Wi-Fi/internet, Bluetooth uparivanje i zvuk, IPTV bez zamrzavanja, analogni AUX i restart. **Netaknuti fabrički Orion bootloader i druge revizije nisu testirani.** Detalji: [zapisnik hardverskog testa](docs/V5_1_HARDWARE_VALIDATION_2026-11-01.md) i [V5.1 build uputstvo](docs/V5_1_FULL_AUDIO.md). Gotov IMG nije objavljen u repozitorijumu.

## Bezbednost i odgovornost

Prvi box je već dobio X96 bootloader prilikom ranijeg flešovanja. Uspeh V4 zato **nije dokaz** da V5 FULL može bezbedno da se instalira na drugi box koji je još na fabričkom bootloaderu.

**Ne uključivati naslepo `Erase flash` ili `Erase bootloader`.** Pogrešan DDR/U-Boot može sprečiti ulazak u USB Burning režim. Potreban je bekap i realan plan oporavka. Pročitaj [FLASHING.md](docs/FLASHING.md).

Repozitorijum sadrži V6 One-Step skripte za izradu direktno iz dva originalna donatorska IMG-a, kao i istorijske V5 alate. Gotove vlasničke IMG slike nisu uključene. Za V6 nije potrebna izrada V4/V5 međuslika.

Skripte i dokumentacija dostupne su pod [MIT licencom](LICENSE). Projekat je nezavisan i namenjen eksperimentisanju, razmeni iskustava i daljem razvoju firmware-a za Orion LAKI TV Box.

Ovo je nezavisan eksperimentalni projekat, a ne zvaničan firmware proizvođača.
