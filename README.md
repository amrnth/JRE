I'm a hardcore Joe Rogan fan. Through this project, I want to watch some interesting short tangents that have appeared on the past shows of the JRE.

Steps:
1. Get YT video link and download the video in 4k
2. Get subtitles with timestamps
    1. Provided by Youtube
    2. Extracted using AI
3. Prompt LLM to find a short story within the whole video and return exact uttered text with subtitles.
4. Use the timestamps to piece together the short story and then export the video
5. Upload it to my new channel
6. Better Algo to concatenate clips
7. Add subtitle texts to the video
8. Portrait mode - how to focus on the speaker - need computer vision?
9. zoom in and out??
10. Pass in an hour long podcast transcript??


Immediate tasks:
1. Do 4k video download - done
2. Write code to split and combine video and audio
    1. Install FFMPEG
    2. Split and combine 
3. Automate using AI

TODO - 4/1
- [x] Split and combine video and audio
- [x] Publish to Youtube Channel
- [x] Add subtitles to video
- [x] Download video -> Get Subs -> Process subtitles -> LLM prompt -> csv result -> split, combine
- [x] handle the case when multiple lines of text are there at the same time - check the offsetting function
- [x] handle the case of combining audio after merging frames
- [ ] short video aspect ratio
    - [ ] focus on speaker
- [ ] make prompts better, currently stories aren't that great.
- [ ] modify prompt to return title description of the video. save original video metadata
- [ ] extract subtitles with word-by-word timestamp, and use animation.
- [x] Make subtitles bigger, and appear on multiple lines if long
- [ ] Add effects to subtitles, spread words across the whole timestamp
- [x] Make code run on multiple processors - done(beautiful work!)
- [ ] Add zoom-in, zoom-out etc features when transitioning between speakers