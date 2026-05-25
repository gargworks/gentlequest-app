# Play Store assets — GentleQuest v1.3.0

## Files

| File                          | Size      | Purpose                                  |
| ----------------------------- | --------- | ---------------------------------------- |
| `feature_graphic.png`         | 1024×500  | Mandatory feature banner on Play listing |
| `feature_graphic.html`        | (source)  | Regen source for the feature graphic     |
| `play_high_res_icon_512.png`  | 512×512   | Mandatory high-res icon on Play listing  |

## Screenshots

Phone screenshots live at `../app_store/frame_*.png` — Play Store accepts
the same 1290×2796 PNGs that Apple uses, since they fall within Play's
phone screenshot aspect range (16:9 to 9:21). Reuse all 6 frames.

## Notes

- Feature graphic is brand-locked to `#667EEA` / `#1F1B3A` / `#F8F7FF` —
  matches app icon + launch screen + in-app theme.
- Play crops the icon corners to a circle at display time. Visual stays
  inside the safe area (centered star + path well within the canvas).
- No alpha on the feature graphic (Play requirement).
- App icon source is iOS Icon-App-1024x1024@1x.png; resized 1024→512
  via ImageMagick for the Play high-res requirement.

## Regen

```bash
chrome --headless --window-size=1024,500 --screenshot=feature_graphic.png file://./feature_graphic.html
magick ../../ai_buddy_web/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png \
  -resize 512x512 play_high_res_icon_512.png
```
