---
name: procedural-game-music
description: Compose, render, edit and check original game music as code - a numpy synth engine plus a sampled soundfont band, sectioned full-length tracks that share one key and tempo grid so levels or biomes can crossfade, per-stem mixing, numeric balance checks, and a local browser studio for listening, mixing and restructuring with exact re-renders. Use when a project needs locally generated combat, biome, boss or menu music, new track sketches or variants, changes to a track's band, structure or mix, stems, or level and loudness checks; not for editing recorded audio, vocals, or licensed music.
---

# Procedural Game Music

## Scope

- Instrumental tracks written as Python (material + sections + band), rendered offline to 44.1 kHz WAV.
- Sketch -> pick -> full-length workflow, stems, mixing, a local studio (timeline, piano roll, mixer, form editor).
- Out of scope: vocals and lyrics, recorded or licensed audio, platform loudness mastering beyond the engine's
  RMS/peak normalisation, seamless loop export (tracks have an intro and an ending), game-engine integration.

## Prerequisites

Tested on Windows 11 and expected to work on macOS/Linux. Commands use `python3`; on Windows use `python`.

- [Python](https://www.python.org/downloads/) 3.10+ with numpy, scipy and
  [tinysoundfont](https://pypi.org/project/tinysoundfont/) (offline soundfont rendering).
  Install: `python3 <skill>/scripts/setup_env.py` (pip `--user` install of exactly these three packages).
- [GeneralUser GS](https://github.com/mrbumpy409/GeneralUser-GS) v2.0.3 soundfont, 32.3 MB, at
  `soundfonts/GeneralUser-GS.sf2` in the project. Its
  [licence](https://github.com/mrbumpy409/GeneralUser-GS/blob/97049183643d5fc5a9322a69c5b09efb667c6c3a/documentation/LICENSE.txt)
  allows use in the user's own music, including commercial. Download only after the user agrees:
  `python3 <skill>/scripts/setup_env.py --download-soundfont` (pinned v2.0.3 commit; size and RIFF/sfbk header
  are checked and a bad file is deleted).
- Optional [ffmpeg](https://ffmpeg.org/download.html) with libvorbis: OGG stem previews for the studio (the WAV
  fallback is about 5x larger). Suggest it; installing system software is the user's call.
- Verify, after `init_project.py` (step 1): `python3 <skill>/scripts/check_env.py --smoke` exits 0 (`--json` for
  machine-readable output), and `python3 -m unittest discover -s <skill>/tests -v` passes (set
  `GAME_MUSIC_SF2=<path to the .sf2>` to include the sampled render test).

## Inputs

- `music_brief.md` in the project (template copied by `init_project.py`): game and visual style, references,
  shared key/scale and tempo grid, track list with roles and signature sounds, mix taste, rejected directions.
  A missing or empty brief is handled by Stop Conditions.

## Procedure

`<skill>` is this skill's installed folder; commands run from the music project root. Stop Conditions interrupt
any step.

1. Project: if `tracks.py` or `band.py` is missing, run `python3 <skill>/scripts/init_project.py` (keeps existing
   files unless `--force`). The files and their roles are in `<skill>/references/engine.md`.
2. Environment: run `python3 <skill>/scripts/check_env.py --smoke`; on missing packages run `setup_env.py` and tell the user what it
   installed; on a missing soundfont ask the user (file, source, size, licence) before `--download-soundfont`.
   Then render the example: `python3 tracks.py demo` -> `tracks/01_demo.wav`.
3. Brief: read `music_brief.md`; keep every track in its key and tempo grid.
4. Sketch when exploring: several clearly different 20-30 s ideas; the user picks; extend picks to full length
   (about 80 bars = 3.5 min at 90 BPM). The first seconds are already the track - keep intros short.
5. Write each track in `tracks.py` like `demo()`: material lists, `render(S, bar, sec, k, n, occ)` writing one
   bar per section type, a `form` of `(section, bars)`, `arrange(form, render, kit=, boom=)`, `ending(S, root,
   extra)`, `S.mix(spec(stem=dict(...)), rev=(decay, damp))`; add it to `TRACKS` (order = file number). Every
   stem used needs a spec entry (`mix` asserts). Read the Writing and Gotchas parts of `references/engine.md`
   (note caching, MIDI velocity `v` vs amplitude `vel`, preset level differences) before the first track.
6. Track identity, so a set does not blur: each track has its own band (`P` presets), drum kit, grooves and at
   least two middle sections no other track has (solo, chamber break, drum break, acoustic section...); vary
   builds (snare, timpani or taiko roll + reverse crash). Synth voices are accents unless the brief asks for an
   electronic sound.
7. Render: `python3 tracks.py NAME` (WAV) or `--stems NAME` (also `studio_data/NAME/`). About 40 s per
   3.5-minute track; render a whole set in the background.
8. Check with numbers (you cannot listen): `python3 <skill>/scripts/stem_levels.py NAME` - leads or keys more
   than about 10 dB under the guitars disappear; `python3 <skill>/scripts/loudness.py --bpm <brief tempo>` -
   L/R within +-1 dB, breakdowns dip 3-8 dB, peaks -1 dBFS. Fix gains or sections, re-render, re-check.
9. Studio on request: `python3 studio.py` -> http://127.0.0.1:8765/ (localhost only). Faders, pan, reverb,
   mute/solo play live (approximation: no chorus or ping-pong); "Save & re-render" writes
   `mixes/<track>.json`, which every later render applies; a failed render restores the previous edit.

## Boundaries

- Ask before the soundfont download and before any other download or system install; the pip install of
  numpy, scipy and tinysoundfont in step 2 is allowed and reported.
- Never call `tinysoundfont.Synth.start()`: it plays to the speakers.
- `init_project.py --force` replaces the user's `tracks.py`; use it only on the user's request.
- Keep `soundfonts/`, `studio_data/` and rendered WAVs out of version control unless the user wants them.

## Stop Conditions

- A required `check_env.py` item still fails after `setup_env.py` - stop and report the table.
- No brief, or a brief without key and tempo grid (and track roles, for a set) - ask the user, fill
  `music_brief.md` with the answers, then resume at step 3.
- The same render error twice - stop and report the traceback.

## Output Contract

Emit:

`Skill: procedural-game-music - output below`

Then include:

| Field | Content |
| --- | --- |
| Environment | `check_env.py` result, or `not run` |
| Tracks | name -> WAV path, length, RMS / peak |
| Changes | material, band, sections or mix changed per track |
| Checks | `stem_levels.py` / `loudness.py` findings and the fixes made |
| Studio | URL and applied edits, or `not used` |
| Not verified | listening (always the user's), anything skipped |
