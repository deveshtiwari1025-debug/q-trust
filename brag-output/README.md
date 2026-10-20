# Q-Trust launch video (`brag` workflow)

The Q-Trust launch film, built with the
[`brag`](https://github.com/latent-spaces/brag) workflow as a
[HyperFrames](https://hyperframes.heygen.com) composition.

| File | What it is |
|---|---|
| `brag.mp4` | Rendered master — 1920x1080, 30 fps, 21.5 s, H.264 + AAC, -18.7 LUFS integrated / -3.1 dBFS true peak |
| `brag.jpg` | Poster frame (20.2 s, the light finale) |
| `brag-plan.md` | Creative contract: narrative, scene timing, copy, audio direction |
| `composition-brief.md` | Implementation brief for the composition |
| `composition/` | The HyperFrames composition (HTML + CSS + assets) |

## Scenes

| Window | Scene |
|---|---|
| 0.0 – 3.7 s | The deadline — NIST IR 8547, `2030—2035` |
| 3.7 – 7.9 s | The claim — "Make trust verifiable", scan / score / attest |
| 7.9 – 14.1 s | The workspace — 284 assets, 39 at risk, 68 % PQC ready |
| 14.1 – 18.5 s | The proof — public verifier, no wallet, verified seal |
| 18.5 – 21.5 s | The finale — the light editorial canvas, `q-trust-nu.vercel.app` |

The on-screen data is the real seeded workspace and the real Base Sepolia
records (migration `0x014e6d93…a794fe8e`, verification tx
`0x2070b8ec…7d16ee`). No mock numbers are shown in the product surfaces.

## Re-render

```bash
cd composition
npx hyperframes check                                   # lint + runtime + layout + motion + contrast
npx hyperframes render -o ../brag.mp4 --quality delivery --fps 30
```

`npx hyperframes check` currently reports 0 errors across lint, runtime,
layout and motion, with 156/156 WCAG AA contrast checks passing.

### Assets

`assets/music/bed.mp3` is not committed — it is a third-party library track.
Restore it from `happy-beats-business-moves-vol-11-by-ende-dot-app.mp3`
(first 21.5 s) before re-rendering. The local fonts (Inter, Inter Tight,
JetBrains Mono), the SFX and the logo are committed under `composition/assets/`.
