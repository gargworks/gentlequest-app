# Task: Add voiceover, music, and subtitles to 6 GentleQuest YT Shorts

## What you have

6 silent vertical videos (1080x1920, 30s each, H.264, no audio stream):

```
marketing/shorts/out/gq_short_v7_journal.mp4
marketing/shorts/out/gq_short_v8_privacy.mp4
marketing/shorts/out/gq_short_v9_grounding.mp4
marketing/shorts/out/gq_short_v10_community.mp4
marketing/shorts/out/gq_short_v11_onboarding.mp4
marketing/shorts/out/gq_short_v12_screening.mp4
```

Per-scene transcripts with timing, voiceover copy, subtitle text, and tone notes:
```
marketing/shorts/transcripts/v7_journal_transcript.txt
```
(5 more transcripts to be generated — same format. Ask for them if not present.)

## What to produce

For each video, output a final MP4 with:
1. **Voiceover** — calm, gentle, neutral or soft female voice, close-mic, minimal reverb. ~90 wpm. Not salesy. Not energetic.
2. **Music bed** — royalty-free ambient piano or soft pad, ~-20dB under the voice. No vocals. Must be commercially safe (YouTube Audio Library, Pixabay Music, or similar — include source URL for verification).
3. **Subtitles** — burned-in (hardcoded), white sans-serif, bottom-third, max 2 lines, matching the subtitle text in the transcript exactly (lowercase intentional). Center-aligned. Semi-transparent black background bar for readability.
4. **Format** — 1080x1920, 30fps, H.264 yuv420p, AAC audio 192kbps stereo. MP4 container.

## Output naming

Save finals as:
```
marketing/shorts/out/final/gq_short_v7_journal_final.mp4
marketing/shorts/out/final/gq_short_v8_privacy_final.mp4
...etc
```

## Technical approach (suggested)

1. Generate voiceover audio for each scene's VO copy using a TTS service (ElevenLabs, OpenAI TTS, or similar). Export as WAV/MP3 per scene.
2. Concat scene VO clips with 0.3s silence between them to match the 30s timeline.
3. Layer a royalty-free music track underneath at -20dB, faded in/out over 1s at start/end.
4. Generate an SRT subtitle file from the transcript timings, then hardcode it with ffmpeg:
   ```
   ffmpeg -i input.mp4 -i audio_mix.aac -vf "subtitles=subs.srt:force_style='FontName=Helvetica,FontSize=22,PrimaryColour=&Hffffff&,BackColour=&H80000000&,BorderStyle=4,Alignment=2,MarginV=80'" -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k output.mp4
   ```
5. Verify final duration = 30s, has audio stream, subtitles visible.

## Constraints

- Do NOT change the video visuals. Only add audio + subtitles.
- Music MUST be royalty-free / commercially safe. Include the source URL.
- Subtitle text must match transcript exactly (lowercase, punctuation as written).
- Keep file size under 15MB per video (YT Shorts limit).
- If a TTS service costs money, use the cheapest acceptable voice. Total budget for all 6: under $2.

## Deliverables

1. 6 final MP4 files in `marketing/shorts/out/final/`
2. A `CREDITS.md` file listing the music track name + source URL for each video
3. The SRT subtitle files in `marketing/shorts/transcripts/` (one per video)

## Reference

Example transcript format (v7):
```
[0:00–0:04] CARD: "a journal / that is just yours"
VOICEOVER: A journal that is just yours.
SUBTITLE: a journal that is just yours
```

Read `marketing/shorts/transcripts/v7_journal_transcript.txt` for the full example.
