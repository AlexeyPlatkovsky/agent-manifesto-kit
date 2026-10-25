# Engine reference

The files `init_project.py` copies into the music project, and what each one owns.

| File | Owns |
| --- | --- |
| `synth.py` | PolyBLEP oscillators, synth voices (`bass`, `pluck`, `pad`, `lead`, `bell`, `piano`, `choir`...), synth drums, FX (`reverb`, `delay`, `chorus`, `duck`, `crush`), `master()`, `Song` (stems, `note`/`seq`/`hits`, `mix`, note events, studio hooks), `sf()` sampled notes, `write()` |
| `band.py` | `P` soundfont presets by GM program, `SCALES`, `sfkit(kit)` GM drum kits (0 Standard, 1 Standard 2, 8 Room, 16 Power, 32 Jazz, 40 Brush, 48 Orchestral), `GT`/`riffT` double-tracked guitars, `strum`, `runs` (generated solos), `arrange`/`mark`/`fill`/`build`/`ending`, `spec` mix defaults + studio edits, `updown` arpeggios |
| `tracks.py` | The project's songs, `TRACKS` (order = output number) and the CLI (`--list`, `--stems`) |
| `studio_export.py` | `--stems` output: `studio_data/<track>/session.json` + per-stem OGG/WAV previews |
| `studio.py`, `studio/index.html` | Localhost studio; edits go to `mixes/<track>.json` |
| `music_brief.md` | The consumer's direction: key, tempo grid, track roles, rejected directions |

## Writing a track

- Material as lists: a note is `'E4'` or a MIDI number, `None` is a rest, `(note, steps)` sets a length, a list of
  notes is a chord. `S.seq(stem, fn, notes, bar, step=0.25)` places them; `S.hits(stem, sample, 'x.o-', bar)`
  places drum hits (`x` full, `o` medium, `-` ghost).
- `render(S, bar, sec, k, n, occ)` is called once per bar: `sec` section name, `k` bar inside the section, `n`
  section length, `occ` how many times this section has appeared. Put melodies at `k == 0`.
- `mix(spec(stem=dict(g=gain, pan=-1..1, rv=reverb send, dl=(beats, feedback, amount), ch={} for stereo chorus,
  sc=sidechain depth, cr=(bits, hold) bitcrush, hp=, lp=)), rev=(decay_s, damp_hz))`.

## Gotchas

- `Song.note` caches identical notes, so repeats are sample-identical; pass different kwargs (velocity `v`,
  length) when variation matters.
- `sf(..., v=)` is MIDI velocity; `vel` in `note`/`seq` is a linear amplitude scale.
- Soundfont presets differ in level by up to ~8 dB (Distortion vs Overdrive guitar); `GT` level-matches the two
  guitar sides, other stems are balanced through `spec` gains and `stem_levels.py`.
- Stems are float32 so 4-minute songs with ~20 stems fit in memory; `--stems` previews are 22.05 kHz mono.
- `tinysoundfont.Synth.start()` opens the audio device and plays to the speakers; `sf()` renders offline only.
