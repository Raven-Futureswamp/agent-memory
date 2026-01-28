# Project: JUCE VST Plugin Development (FutureSwamp Studios)

**Status:** 🟢 ACTIVE
**Created:** 2026-01-27
**Last Updated:** 2026-01-27

## Company
- **Name:** FutureSwamp Studios LLC
- **Website:** futureswamp.com / futureswamp.studio
- **Email:** info@futureswamp.com
- **MuseHub Partner Portal:** partner.musehub.com

## Products

### HellFold 🔥 (FLAGSHIP — NEAR LAUNCH)
- **Type:** Audio distortion/wavefolder plugin
- **Price:** $39 (intro $29)
- **Formats:** VST3, AU (Mac), VST3 (Windows)
- **Version:** v2.3.1
- **Source:** `/Users/studiomac/My Drive/VST_Projects/HellFold/`
- **Windows build:** `/Users/studiomac/My Drive/VST_Projects/HellFold_Build_Windows/`
- **Mac build:** `/Users/studiomac/Documents/JUCE/HellFold_Build/`
- **Website:** `Desktop/futureswamp-website/hellfold.html`
- **Demo video:** `Desktop/HellFold.mov`
- **Manual:** `Desktop/futureswamp-website/HellFold_Manual_v2.3.1.pdf`
- **Presets:** `Library/Audio/Presets/FutureSwamp Studios/HellFold/`
- **DAW tested:** Logic Pro, Reaper, FL Studio, Cubase, Ableton Live

#### HellFold — Where We Left Off
**Last update: Jan 20, 2026 (Alex Gallo from MuseHub)**
Two issues to fix before launch:
1. **SDK dylib resolution** — LC_RPATH points to Jess's local dev machine instead of `@loader_path/../Frameworks/`. Fix: add `-rpath @loader_path/../Frameworks/` to linker flags in CMakeLists.txt
2. **MuseDRM submission** — Need to run `musedrm --sdk_enable` tool on binaries before submitting:
   ```
   ./musedrm --sdk_enable HellFold.app HellFold.vst3 HellFold.component \
     --asset_type pkg --product_version 2.3.1 \
     --product_id d0700a69-caf5-44a0-80b9-a8b8cbf53f39 \
     --api_key <api-key-from-partner-portal>
   ```
3. **Windows code signing** — Waiting on Sectigo USB key for EV code signing
   - Azure Trusted Signing didn't work (requires 3-year business history)
   - Pivoted to Sectigo
   - Jeanette said Mac version can launch first

#### MuseHub Contacts
- **Jeanette Kats** (j.kats@mu.se) — Catalog Manager, main contact
- **Alex Gallo** (alex@musehub.com) — Technical integration
- **Khaled Said** (khaled@musehub.com) — Head of Product & Partnerships

#### Integration Details
- Using **MuseSDK** (not MuseDRM) for licensing
- SDK: `Desktop/MuseClientSDK 1.3.0-f1d0b178 20250805.zip`
- Partner Portal: https://partner.musehub.com
- Developer docs: https://developer.musehub.com
- musedrm tool: https://drive.google.com/drive/folders/1U4EnrPF9RBqVM9A03PvC4_RWDDJnFARj

### VoidCarver (IN DEVELOPMENT)
- **Type:** Spectral analyzer / multiband ducker plugin
- **Source:** `/Users/studiomac/Desktop/VoidCarver/`
- **Build:** CMake, JUCE 8.0.10
- **Formats:** VST3, AU
- **Company code:** FSwp / VdCr

### HardwareInsert (IN DEVELOPMENT)
- **Type:** Hardware insert utility plugin
- **Source:** `/Users/studiomac/Desktop/HardwareInsert/`
- **Build:** CMake, JUCE (find_package)
- **Formats:** VST3, AU
- **Note:** Still has "YourStudio" placeholder — needs company info update

### Other Projects (Google Drive: My Drive/VST_Projects/)
- **RitualChamber / RitualChamber2** — Reverb plugins
- **CloudReverb / CelestialChamber** — Reverb plugins
- **SPL_DeEsser** — De-esser
- **FutureSwampDistortion** — Distortion (also at ~/VST_Projects/)
- **GOATT_BUILD001** — Unknown
- **Reference projects:** wolf-shaper, pamplejuce, NeuralNote, Frequalizer, ZLEqualizer, ZLCompressor, ZLSplitter, KlonCentaur, BYOD, TestToneGenerator

## Build Environment (MacBook)
- **Machine:** Apple M5, 24GB RAM, macOS 26.2
- **JUCE:** v8.0.10 at `/Users/studiomac/JUCE/` and `/Users/studiomac/Documents/JUCE/`
- **Build system:** CMake
- **Code signing (Mac):** Apple Developer ID + notarization
- **Code signing (Win):** Sectigo EV USB key (pending delivery)
- **Projects synced via:** Google Drive (`My Drive/VST_Projects/`)

## Cross-Platform Build Plan
- **Goal:** Build VSTs for Mac AND Windows from one pipeline
- **Mac builds:** MacBook (current)
- **Windows builds:** Need to set up Clawdbot nodes on Jess's Windows PCs
- **Sectigo USB key:** Required for Windows code signing

## Next Steps
1. Fix HellFold LC_RPATH issue (linker flag in CMake)
2. Run musedrm --sdk_enable on Mac binaries
3. Submit Mac version to MuseHub for review
4. Set up Sectigo USB key when it arrives → sign Windows build
5. Submit Windows version
6. Set up Clawdbot nodes on Windows PCs for cross-platform builds
