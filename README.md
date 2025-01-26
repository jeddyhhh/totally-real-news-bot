# totally-real-news-bot
Here's some examples of output: https://www.facebook.com/profile.php?id=61560732713412&sk=videos

Generates AI text/images/video based on a NYT news headline, can be modified to create other content.



Update 26/1/25 - Added some stuff, see annotations in run_bot.py for more details

Update 6/7/24 - I need to rewrite this, check code annotations for more info.


Update - 16/6/24 - Project uses a standalone version of AllTalk TTS v2 BETA, it works pretty much the same as the TWGUI extension but has its own install location, read more here:<br>
https://github.com/erew123/alltalk_tts/tree/alltalkbeta<br>


Requires:<br>
- Python 3<br>
- A working install of text-generation-webui with the --api flag enabled<br>(https://github.com/oobabooga/text-generation-webui)<br>
- A working AllTalk TTS v2 BETA installation with api access enabled.<br>(I'm using the standalone version but the TWGUI extension should work)<br>(https://github.com/erew123/alltalk_tts/tree/alltalkbeta)<br>
- A working install of stable-diffusion-webui with  --api enabled in COMMANDLINE_ARGS<br>(https://github.com/AUTOMATIC1111/stable-diffusion-webui)<br>
- A New York Times API access key<br>(https://developer.nytimes.com/get-started)<br>
- (optional) A working install of my fork of sadtalker-api (https://github.com/jeddyhhh/sadtalker-api)<br>
- (optional) A Facebook page access token<br><br>

Usage:<br>
1. Clone this repository<br>
2. Run `pip install -r requirements.txt`<br>
3. In run_bot.py, under "API Details", double check that your text-generation-webui, stable-diffusion-webui and alltalk_tts API paths are correct as well as your NYT API key is set<br>
4. In run_bot.py, confirm bot settings under "Config", use True and False to set options.
5. Make sure both text-generation-webui, alltalk_tts v2 BETA and stable-diffusion-webui are running with api enabled<br>
6. Go to alltalk's settings page and enable RVC models under "Global Settings", then tick "Enable RVC" and hit "Update RVC Settings", it will download base models and create a "rvc_voices" folder in the "models" folder.
7. If using random RVC selection mode, edit "rvc_voices.txt" in the root to include your RVC model paths, the ones in there at the moment are examples of how it should be formatted.<br>
RVC models go in alltalk_tts/models/rvc_voices/*folder*/*model*.pth<br>
8. Run `python run_bot.py` in console<br><br>

Basic process overview:<br>
1. Bot grabs a NYT headline and short description<br>
2. Bot uses text-generation-webui to analyse the headline for tone and stores it.<br>
3. Bot trys to make up hashtags related to the headline and article summary<br>
4. Bot trys to make up "importaant words" based on the headline and description, this is fed into Stable Diffusion for image creation.
5. Bot generates a news article text based on the headline and short description, asks bot to write in a randomly selected tone from emotions.txt and from a random perpective from descriptive.txt<br>
6. Bot uses Alltalk_tts to generate speech based on the generated article text, outputs a .wav file
7. Bot starts generating 4 images based on the "important words" generated, stored from step 4, it will start generating using what ever model is loaded into stable-diffusion-webui, outputs .png files<br>
- If enabled, bot will overlay a watermark to the images, logo_overlay.png in the root is the watermark file, it can be changed to whatever you want.<br>
8. Bot combines the images and speech into a .mp4 file<br>
- If enabled, bot will combine videos together to form a longer video with multiple articles in it, transClip.mp4 in the root is the video that goes in between your generated videos, you can change this to whatever you want<br>
- If enabled, bot will post the .mp4 to a Facebook page.<br>
- If enabled, bot will post a Facebook comment on the uploaded video, pulling data from urls.txt, this data could be anything as long as its on its own line, the bot will randomly select a line to post as a comment.
- If enabled, bot will add the generated hashtags to the end of the video description on Facebook.<br>
9. Bot will continue to generate until the python script is stopped.<br>

Models I'm using:<br>
LLM - Meta-Llama-3.1-8B-Instruct.i1-Q4_K_M.gguf or Qwen2.5-7B-Instruct.Q5_K_M.gguf<br>
Stable Diffusion - v2-1_512-ema-pruned.safetensors<br> 
TTS - Piper with various RVC models.<br>
