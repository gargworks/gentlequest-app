import logging
import os
import requests
import subprocess
import json
from scripts.video_engine.config import NUCLEUS_BRAND_CONFIG, BASE_DIR
from scripts.video_engine.branding import synthesize_end_card
from pathlib import Path
from dotenv import load_dotenv

def get_output_dir():
    return Path("/Users/lokeshgarg/ai-mvp-backend/test_output")

def get_secrets_dir():
    return Path("/Users/lokeshgarg/ai-mvp-backend/.env")

# Load environment variables from secrets directory
load_dotenv(get_secrets_dir() / ".env")

logger = logging.getLogger(__name__)

def validate_video_orientation(video_path):
    """Ensure video is portrait 9:16. Raises ValueError if landscape."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        for stream in data.get('streams', []):
            if stream['codec_type'] == 'video':
                width = int(stream.get('width', 0))
                height = int(stream.get('height', 0))
                
                if width == 0 or height == 0: continue

                # Check if portrait (9:16 ratio)
                ratio = height / width
                expected_ratio = 16 / 9 # 1.77
                
                # Allow small tolerance (1.7+)
                if ratio < 1.7:
                    raise ValueError(
                        f"Video is {width}x{height} (Ratio: {ratio:.2f}). "
                        f"Expected Portrait (Ratio: 1.77+). REJECTED."
                    )
                return True
    except Exception as e:
        logger.error(f"Orientation check failed: {e}")
        # If check fails technicaly, letting it pass (fail open) vs fail closed.
        # Fail closed is safer for quality.
        if isinstance(e, ValueError): raise e
        
    return True

def has_audio(file_path):
    """Check if file has an audio stream."""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_type',
            '-of', 'json',
            str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return len(data.get('streams', [])) > 0
    except Exception:
        return False

def generate_landscape_ab_pairs(video_path):
    """
    Detects if video is landscape. If so, generates:
    1. Cropped Vertical (9:16)
    2. Fit-to-Frame Vertical (Padded 9:16)
    Returns: (cropped_path, fit_path) or (None, None) if not landscape.
    """
    video_path = Path(video_path)
    if not video_path.exists(): return None, None
    
    # 1. Check Dimensions
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        width = 0
        height = 0
        for s in data.get('streams', []):
            if s['codec_type'] == 'video':
                width = int(s.get('width', 0))
                height = int(s.get('height', 0))
                break
        
        if width <= height: # Portrait or Square
            return None, None
            
    except Exception as e:
        logger.error(f"Dimension check failed: {e}")
        return None, None

    logger.info(f"🌄 Landscape detected ({width}x{height}). Generating A/B pairs...")
    
    crop_path = video_path.parent / f"{video_path.stem}_CROPPED.mp4"
    fit_path = video_path.parent / f"{video_path.stem}_FIT.mp4"
    
    # 2. Generate Cropped (Scale height to 1280, crop 720 center)
    if not crop_path.exists():
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-vf", "scale=-1:1280,crop=720:1280",
            "-c:v", "libx264", "-c:a", "copy",
            str(crop_path)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    # 3. Generate Fit (Scale width to 720, pad to 1280 height)
    if not fit_path.exists():
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-vf", "scale=720:-1,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-c:a", "copy",
            str(fit_path)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    return str(crop_path), str(fit_path)

class MediaEngine:
    def __init__(self):
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = NUCLEUS_BRAND_CONFIG["default_voice"]
    
    def generate_audio(self, text, output_path, voice_id=None, simulation=False):
        """
        Generates Audio from text using DUAL AUDIO PROVIDER system.
        """
        # Cleanup: Strip hashtags from spoken text (Hygiene)
        import re
        text = re.sub(r'#\w+', '', text).strip()
        
        metadata = {
            "text": text,
            "voice_id": voice_id or self.voice_id,
            "engine": "Dual Provider",
            "simulated": simulation
        }

        if not simulation:
            try:
                generate_narration(text, output_path)
                logger.info(f"Smart audio provider success: {output_path}")
                return True, metadata
            except Exception as e:
                logger.warning(f"Smart audio provider failed: {e}")

        # Fallback to macOS 'say'
        logger.info("Falling back to local macOS 'say' command...")
        metadata["engine"] = "macOS say"
        metadata["voice_id"] = os.getenv("MAC_VOICE", "Daniel")
        
        try:
            voice = metadata["voice_id"]
            # Use absolute path for safety and use .m4a which is very stable on say
            abs_output = os.path.abspath(output_path)
            temp_m4a = abs_output.replace(".mp3", ".m4a")
            
            subprocess.run(["say", "-v", voice, text, "-o", temp_m4a], check=True)
            
            cmd = [
                "ffmpeg", "-y", "-i", temp_m4a, "-ar", "44100", "-ac", "2", "-b:a", "192k", abs_output
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(temp_m4a):
                os.remove(temp_m4a)
                
            logger.info(f"Local fallback audio success: {output_path}")
            return True, metadata
        except Exception as e:
            logger.error(f"Local fallback failed: {e}")
            success = self._generate_silent_audio(output_path)
            metadata["engine"] = "Silent Fallback"
            return success, metadata

    def _generate_silent_audio(self, output_path):
        logger.warning(f"Generating silent fallback audio: {output_path}")
        try:
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "10", "-q:a", "9", "-acodec", "libmp3lame", output_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception as e:
            logger.error(f"Failed to generate silent audio: {e}")
            return False

    def generate_video(self, prompt, image_path, output_path, negative_prompt=None):
        """Generates Video animation using real VEO 2.0 (Vertex AI)."""
        logger.info(f"Attempting production VEO 2.0 generation for {image_path}...")
        try:
            result = self.veo_client.generate_video(
                prompt=prompt,
                image_path=Path(image_path) if image_path else None,
                output_path=Path(output_path),
                negative_prompt=negative_prompt
            )
            if result and os.path.exists(result):
                return str(result)
            return self._generate_ken_burns(image_path, output_path)
        except Exception as e:
            logger.error(f"Production VEO Error: {e}")
            return self._generate_ken_burns(image_path, output_path)

    def _generate_ken_burns(self, image_path, output_path):
        """Fallback Ken Burns effect."""
        temp_cropped = str(Path(output_path).with_suffix('.cropped.jpg'))
        processed_path = self.image_processor.process_for_veo(image_path, temp_cropped, anchor="center")
        target_path = processed_path if processed_path else image_path
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", target_path,
            "-vf", "scale=iw*2:-1,zoompan=z='min(zoom+0.001,1.5)':d=250:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,setsar=1",
            "-c:v", "libx264", "-t", "10", "-pix_fmt", "yuv420p", "-r", "25", str(output_path)
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if processed_path and os.path.exists(processed_path): os.remove(processed_path)
            return str(output_path)
        except: return image_path

    def assemble_final_cut(self, video_source, audio_path=None, output_path=None, caption_images=None, 
                           subtitle_path=None, final_overlay_path=None, distribution_mode="serial",
                           source_type="veo", brand_id=None, caption_style="standard"):
        """
        PRECISION ASSEMBLY (Quality Preserving when possible):
        - distribution_mode: "serial" (default, clips played fully until duration hit) 
                            or "distribute" (all clips shown equally).
        - source_type: "veo" (default) or "simulation" (local browser recording)
        - brand_id: optional brand for end-card (e.g., "nucleus")
        """
        logger.info(f"Assembling cut: {video_source} (Type: {source_type})")

        def get_duration(path):
            try:
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                return float(result.stdout.strip())
            except: return 0.0

        audio_dur = get_duration(audio_path) if audio_path else 0.0
        target_dur = audio_dur + 0.5
        
        # Determine primary video source(s)
        sources = [video_source] if isinstance(video_source, str) else video_source
        
        # Audio Mixing Parameters
        BG_VOL = os.getenv("VEO_MIX_VOLUME_BG", "0.1")
        NAR_VOL = os.getenv("VEO_MIX_VOLUME_NAR", "1.5")

        cmd = ["ffmpeg", "-y"]
        
        # Handle Multi-Shot / Input Looping
        input_args = []
        for s in sources:
            input_args += ["-i", s]
        
        if audio_path:
            input_args += ["-i", audio_path]
            
        cmd += input_args
        
        # Filter Chains
        video_filters = []
        audio_filters = []
        
        # 1. Video/Audio Prep (Concatenate all sources)
        v_sources = len(sources)
        v_stream = "0:v"
        a_bg_stream = "0:a"
        
        # If we have many captions, process in batches to avoid FFmpeg filtergraph overflows
        MAX_BATCH = 25
        if caption_images and len(caption_images) > MAX_BATCH:
            logger.info(f"Large caption set ({len(caption_images)}). Using batched processing.")
            
            # Step A: Create scaled base video with concatenated audio
            temp_base = Path(output_path).parent / f"temp_base_{os.getpid()}.mp4"
            base_cmd = ["ffmpeg", "-y"] + input_args
            
            # Pre-process each input to 1080x1920 and 44100Hz BEFORE concat
            v_pre_filters = []
            a_pre_filters = []
            v_concat_inputs = ""
            
            # Distributive Logic (Batched Path)
            clip_durations = []
            if distribution_mode == "distribute" and v_sources > 0:
                seg_dur = target_dur / v_sources
                clip_durations = [seg_dur] * v_sources
            
            for i in range(v_sources):
                # Scaling logic for different source types
                if source_type == "simulation":
                    # Scale to fit 1080 width, then pad to 1920 height
                    bg_color = os.getenv("MEDIA_ENGINE_BG_COLOR", "#0a0a0f")
                    scale_filter = f"scale=1080:-1:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color={bg_color}"
                else:
                    # Default VEO style: Scale and crop to fill 1080x1920
                    scale_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

                dur_filter = f",trim=0:{clip_durations[i]},setpts=PTS-STARTPTS" if clip_durations else ""
                v_pre_filters.append(f"[{i}:v:0]{scale_filter},setsar=1,format=yuv420p{dur_filter}[v_prep_{i}]")
                if has_audio(sources[i]):
                    a_dur_filter = dur_filter.replace('trim', 'atrim').replace('setpts', 'asetpts')
                    a_pre_filters.append(f"[{i}:a:0]aresample=44100{a_dur_filter}[a_prep_{i}]")
                else:
                    dur = clip_durations[i] if clip_durations else get_duration(sources[i])
                    a_pre_filters.append(f"anullsrc=channel_layout=stereo:sample_rate=44100:d={dur}[a_prep_{i}]")
                v_concat_inputs += f"[v_prep_{i}][a_prep_{i}]"
                
            base_v_filter = ";".join(v_pre_filters + a_pre_filters) + f";{v_concat_inputs}concat=n={v_sources}:v=1:a=1[v_raw][a_raw];[v_raw]tpad=stop_mode=clone:stop_duration={target_dur}[v_out]"
            base_a_filter = f"[a_raw]apad=whole_dur={target_dur}[a_out]"
            
            base_cmd += ["-filter_complex", f"{base_v_filter};{base_a_filter}", "-map", "[v_out]", "-map", "[a_out]", "-c:v", "libx264", "-preset", "ultrafast", "-t", str(target_dur), str(temp_base)]
            logger.info(f"🚀 Batch Step A: Generating base video with distributive audio mix...")
            subprocess.run(base_cmd, check=True)
            
            current_input = temp_base
            
            # Step B: Apply overlays in batches
            for i in range(0, len(caption_images), MAX_BATCH):
                batch = caption_images[i:i+MAX_BATCH]
                temp_next = Path(output_path).parent / f"temp_batch_{i//MAX_BATCH}_{os.getpid()}.mp4"
                
                batch_cmd = ["ffmpeg", "-y", "-i", str(current_input)]
                batch_v_filters = ["[0:v]"]
                
                for j, cap in enumerate(batch):
                    batch_cmd += ["-loop", "1", "-i", cap["path"]]
                    v_in = f"[v_cap_{j}]" if j > 0 else "[0:v]"
                    v_out = f"[v_cap_{j+1}]"
                    batch_v_filters.append(f"{v_in}[{j+1}:v]overlay=x=(W-w)/2:y=(H-h)/2:enable='between(t,{cap['start']},{cap['end']})'{v_out}")
                
                batch_cmd += ["-filter_complex", ";".join(batch_v_filters[1:]), "-map", v_out, "-map", "0:a", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "copy", "-t", str(target_dur), str(temp_next)]
                logger.info(f"🚀 Batch Step B: Applied overlay batch {i//MAX_BATCH} -> {temp_next}")
                subprocess.run(batch_cmd, check=True)
                
                if current_input != temp_base:
                    try: os.remove(current_input)
                    except: pass
                current_input = temp_next
            
            # Step C: Final assembly with highlight and narration mix
            final_cmd = ["ffmpeg", "-y", "-i", str(current_input)]
            if audio_path:
                final_cmd += ["-i", audio_path]
            
            f_v_stream = "0:v"
            f_a_stream = "0:a"
            f_v_filters = []
            f_a_filters = []
            
            if final_overlay_path:
                # No Redundant Overlay Rule: Skip final-second white text if captions are present
                if caption_images or subtitle_path:
                    logger.info("🚫 Skipping final overlay due to active captions (No Redundant Overlay Rule).")
                else:
                    final_cmd += ["-loop", "1", "-i", final_overlay_path]
                    start_t = max(0, target_dur - 4)
                    ov_idx = 2 if audio_path else 1
                    f_v_filters.append(f"[0:v][{ov_idx}:v]overlay=x=(W-w)/2:y=(H-h)/2:enable='between(t,{start_t},{target_dur})':shortest=1[v_final]")
                    f_v_stream = "[v_final]"
            
            if audio_path:
                f_a_filters.append(f"[0:a]volume={BG_VOL}[bg];[1:a]volume={NAR_VOL}[fg];[bg][fg]amix=inputs=2:duration=longest[a_mixed]")
                f_a_stream = "[a_mixed]"
            
            if f_v_filters or f_a_filters:
                final_cmd += ["-filter_complex", ";".join(f_v_filters + f_a_filters)]
            
            final_cmd += ["-map", f_v_stream, "-map", f_a_stream, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output_path)]
            logger.info(f"🚀 Batch Step C: Final assembly and narration mix...")
            subprocess.run(final_cmd, check=True)
            
            # Cleanup
            try: os.remove(current_input)
            except: pass
            try: os.remove(temp_base)
            except: pass
            # Step D: Final Branding (Append End-Card)
            if brand_id:
                logger.info(f"Appending branded end-card for: {brand_id}")
                try:
                    end_card_clip = synthesize_end_card(brand_id)
                    final_out = output_path
                    temp_main = output_path.replace(".mp4", "_main_segment.mp4")
                    
                    # Move currently produced file to temp_main
                    os.rename(output_path, temp_main)
                    
                    # Concat Main + End Card
                    concat_cmd = [
                        "ffmpeg", "-y", "-i", temp_main, "-i", end_card_clip,
                        "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
                        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", final_out
                    ]
                    subprocess.run(concat_cmd, check=True)
                    
                    # Cleanup
                    try: 
                        os.remove(temp_main)
                        os.remove(end_card_clip)
                    except: pass
                except Exception as e:
                    logger.error(f"Failed to append branding: {e}")

            return output_path
        
        # OLD LOGIC for small overlay sets (optimized for speed)
        # 1. Video/Audio Prep (Concatenate all sources - NOW ALWAYS ENFORCED FOR 1080p)
        v_sources = len(sources)
        v_stream = ""
        a_bg_stream = ""
        
        v_pre_filters = []
        a_pre_filters = []
        v_concat_inputs = ""
        
        # Distributive Logic (Single-Pass)
        clip_durations = []
        if distribution_mode == "distribute" and v_sources > 0:
            # Add a slight overlap or exact division
            seg_dur = target_dur / v_sources
            # 1% Better Guard: Minimum 2.1s per shot to avoid micro-cuts
            if seg_dur < 2.1:
                logger.warning(f"⚠️ Distributive segment ({seg_dur:.2f}s) is too short. Falling back to serial.")
                distribution_mode = "serial"
            else:
                clip_durations = [seg_dur] * v_sources
                logger.info(f"📏 Distributing {v_sources} clips at {seg_dur:.2f}s each (Target: {target_dur}s)")
        
        for i in range(v_sources):
            # 1.1 Process Video (Scale/Crop/Trim)
            # Use exact trim for distributive, otherwise full for serial
            if clip_durations:
                dur_filter = f",trim=0:{clip_durations[i]},setpts=PTS-STARTPTS"
            else:
                dur_filter = ""
            
            v_prep = f"v_prep_{i}"
            # Use source-aware scaling
            if source_type == "simulation":
                bg_color = os.getenv("MEDIA_ENGINE_BG_COLOR", "#0a0a0f")
                scale_filter = f"scale=1080:-1:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color={bg_color}"
            else:
                scale_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
                
            v_pre_filters.append(f"[{i}:v:0]{scale_filter},setsar=1,format=yuv420p{dur_filter}[{v_prep}]")
            
            # 1.2 Process Audio (Resample or Inject Trimmer Silence)
            a_prep = f"a_prep_{i}"
            if has_audio(sources[i]):
                a_dur_filter = dur_filter.replace('trim=', 'atrim=0:').replace('setpts=', 'asetpts=') if dur_filter else ""
                a_pre_filters.append(f"[{i}:a:0]aresample=44100{a_dur_filter}[{a_prep}]")
            else:
                # Use exact segment duration for silence
                dur = clip_durations[i] if clip_durations else 10.0 # Default 10s if serial and no audio
                a_pre_filters.append(f"anullsrc=channel_layout=stereo:sample_rate=44100:d={dur}[{a_prep}]")
            
            v_concat_inputs += f"[{v_prep}][{a_prep}]"
            
        video_filters.append(";".join(v_pre_filters + a_pre_filters))
        video_filters.append(f"{v_concat_inputs}concat=n={v_sources}:v=1:a=1[v_raw][a_raw]")
        # Pad/Loop video to match target duration perfectly
        video_filters.append(f"[v_raw]tpad=stop_mode=clone:stop_duration={target_dur}[v_looped]")
        audio_filters.append(f"[a_raw]apad=whole_dur={target_dur}[a_looped]")
        
        v_stream = "[v_looped]"
        a_bg_stream = "[a_looped]"
            
        # 2. Subtitles / Overlays
        if caption_images:
            for i, cap in enumerate(caption_images):
                img_path = cap["path"]
                start = cap["start"]
                end = cap["end"]
                v_new_stream = f"[v_cap_{i}]"
                overlay_index = v_sources + (1 if audio_path else 0) + i
                cmd += ["-loop", "1", "-i", img_path]
                video_filters.append(f"{v_stream}[{overlay_index}:v]overlay=x=(W-w)/2:y=(H-h)/2:enable='between(t,{start},{end})'{v_new_stream}")
                v_stream = v_new_stream

            if final_overlay_path:
                # No Redundant Overlay Rule: Skip final-second white text if captions are present
                if caption_images or subtitle_path:
                    logger.info("🚫 Skipping final overlay due to active captions (No Redundant Overlay Rule).")
                else:
                    start_t = max(0, target_dur - 4)
                    overlay_index = v_sources + (1 if audio_path else 0) + len(caption_images or [])
                    cmd += ["-loop", "1", "-i", final_overlay_path]
                    v_new_stream = "[v_final]"
                    video_filters.append(f"{v_stream}[{overlay_index}:v]overlay=x=(W-w)/2:y=(H-h)/2:enable='between(t,{start_t},{target_dur})':shortest=1{v_new_stream}")
                    v_stream = v_new_stream

        if subtitle_path:
            escaped_path = subtitle_path.replace("'", "'\\\\''").replace(":", "\\:")
            v_new_stream = "[v_sub]"
            video_filters.append(f"{v_stream}subtitles=filename='{escaped_path}'{v_new_stream}")
            v_stream = v_new_stream

        # 3. Audio Mixing
        a_index = v_sources 
        if audio_path:
            audio_filters.append(f"{a_bg_stream}volume={BG_VOL}[bg];[{a_index}:a]volume={NAR_VOL}[fg];[bg][fg]amix=inputs=2:duration=longest[a_mixed]")
            a_stream = "[a_mixed]"
        else:
            audio_filters.append(f"{a_bg_stream}volume={BG_VOL}[a_out]")
            a_stream = "[a_out]"

        all_filters = video_filters + audio_filters
        if all_filters:
            cmd += ["-filter_complex", ";".join(all_filters)]
            cmd += ["-map", v_stream, "-map", a_stream]
        else:
            cmd += ["-map", "0:v", "-map", "0:a"]
            
        cmd += ["-t", str(target_dur), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", str(output_path)]

        try:
            logger.info(f"Executing Single-Pass Assembly: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            # Step D: Final Branding (Append End-Card)
            if brand_id:
                logger.info(f"Appending branded end-card for: {brand_id}")
                try:
                    end_card_clip = synthesize_end_card(brand_id)
                    final_out = str(output_path)
                    temp_main = final_out.replace(".mp4", "_main_segment.mp4")
                    os.rename(final_out, temp_main)
                    
                    concat_cmd = [
                        "ffmpeg", "-y", "-i", temp_main, "-i", end_card_clip,
                        "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
                        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", final_out
                    ]
                    subprocess.run(concat_cmd, check=True)
                    os.remove(temp_main)
                    os.remove(end_card_clip)
                except Exception as e:
                    logger.error(f"Failed to append branding: {e}")
            
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg Error: {e.stderr.decode() if e.stderr else 'Unknown'}")
            return None

    def generate_dual_format(self, fact_id: str, raw_video: str, audio_path: str, output_dir: str = None, crop_anchor: str = "center"):
        """
        ROBUST PIPELINE: Natively generates both Landscape and Portrait (9:16) versions.
        - Automatically handles orientation checks.
        - Removes recognized watermarks if possible via cropping.
        - Assembles master files.
        - crop_anchor: 'center', 'left', 'right', 'right_center'
        """
        raw_video = Path(raw_video)
        audio_path = Path(audio_path)
        if output_dir is None:
            out_dir = get_output_dir() / "final_videos"
        else:
            out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        if not raw_video.exists() or not audio_path.exists():
            logger.error(f"Missing inputs for {fact_id}")
            return False

        logger.info(f"✨ executing Dual Format Pipeline for {fact_id} (Anchor: {crop_anchor})...")

        # 1. LANDSCAPE MASTER
        # We use a custom assembly that BYPASSES the strict portrait check for this specific step
        landscape_out = out_dir / f"{fact_id}_landscape.mp4"
        cmd_landscape = [
            "ffmpeg", "-y",
            "-i", str(raw_video),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            str(landscape_out)
        ]
        
        try:
            subprocess.run(cmd_landscape, check=True, capture_output=True)
            logger.info(f"   ✅ Landscape Master: {landscape_out}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to assemble landscape: {e.stderr.decode()}")
            return False

        # 2. PORTRAIT CROP (With Smart Anchor)
        portrait_raw = raw_video.parent / f"{fact_id}_portrait_raw.mp4"
        
        # Calculate X offset for 1080x1920 crop from ~1920x1080 input (scaled)
        # We scale height to 1920 first. width becomes ~3413.
        # But wait, input is likely 1920x1080.
        # Target is 1080x1920.
        # We can't actually get 1920 height from 1080 input without upscale.
        
        # Standard Approach for VEO Landscape (1920x1080):
        # 1. Scale Height to 1920? (Width -> 3413). Crop 1080.
        #    This is HUGE zoom.
        # 2. Crop 1080x1920 from original? Original is only 1080 high.
        
        # Let's assume we want to fill the 9:16 frame.
        # Input: 1920x1080 (1.77)
        # Target: 1080x1920 (0.56)
        
        # We validly upscale: scale=-1:1920.
        # 1920x1080 -> 3413x1920.
        # Then we crop 1080x1920 window from that 3413 width.
        
        # X Offset Calculation:
        # Total Width = 3413 (approx)
        # Window Width = 1080
        # Slack = 3413 - 1080 = 2333
        
        x_expr = "(iw-ow)/2" # Center
        if crop_anchor == "left":
            x_expr = "0"
        elif crop_anchor == "right":
            x_expr = "iw-ow"
        elif crop_anchor == "right_center":
            x_expr = "(iw-ow)*0.70" # 70% to the right (User said "mostly right but not extreme")
            
        crop_cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_video),
            "-vf", f"scale=-1:1920,crop=1080:1920:{x_expr}:0",
            "-c:a", "copy",
            str(portrait_raw)
        ]
        
        try:
            subprocess.run(crop_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to crop portrait: {e.stderr.decode()}")
            return False

        # 3. PORTRAIT ASSEMBLY
        portrait_out = out_dir / f"{fact_id}_portrait.mp4"
        final_res = self.assemble_final_cut(
            video_source=str(portrait_raw),
            audio_path=str(audio_path),
            output_path=str(portrait_out)
        )
        
        if final_res:
            logger.info(f"   ✅ Portrait Short: {portrait_out}")
            return True
        return False

    def crop_to_vertical_fill(self, input_path: str, output_path: str):
        """
        Forces a center-weighted 9:16 crop on any input video, removing black bars.
        Used for fixing Fact 100 (Glowing Lady).
        """
        logger.info(f"✂️ Executing Vertical Fill Crop: {input_path}")
        
        # scale=-1:1920 ensures height is 1920, width maintains aspect (e.g. 3413 for 16:9)
        # crop=1080:1920 comes from the center
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", "scale=-1:1920,crop=1080:1920:(iw-ow)/2:0",
            "-c:a", "copy",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"   ✅ Cropped: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to crop: {e.stderr.decode()}")
            return False
