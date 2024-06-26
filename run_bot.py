## totally real newsbot - by jeddyh - v1.1##
import json
import base64
import requests
import time
import os
import random
import re
from mutagen.wave import WAVE
from PIL import Image
from pathlib import Path
import imageio
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
from random import randrange
import time

## Config ##
facebook_post_enable = True 
combineVideos = True
num_of_vids_to_combine = 3
#random_voice_mode = False
generate_hashtags = True

## RVC Config ##
rvc_enabled = True ## If false, it will just use the raw piper/coqui etc wav output
default_rvc_voice = 'MadisonAllworth/model.pth' ## models are in alltalk/models/rvc_voices/*folder*/*model*.pth
random_rvc_voice = False ## models must be in the rvc_voices.txt file in the root with the format '*folder*/*model*.pth' eg; peter/PeterGriffin.pth

## NYT Article Selection Config ##
cata_number = 0 ## Starts from 'arts' then 'automobiles' etc etc until it hits the end of the list and starts again.
select_article = 1 ## Each catagory has an n number of articles associated with it, this selects the first one and moves to the second one once it goes through all the catagories. 
random_topic_mode = True ## Picks a random topic for each generation. Ignores cata_number.
random_article_select = True ## Looks up how many articles are associated with the catagory and picks a random one. Could be a new or old article. Ignores select_article.

## Image and Video Config ##
image_height = "400"
image_width = "400"

video_height = "400"
video_width = "400"

watermark_mode = True

## API Details ##
nyt_apikey = ""

ooba_url = "http://127.0.0.1:5000/v1/completions"
ooba_headers = {"Content-Type": "application/json"}

auto1111_url = 'http://127.0.0.1:7860/sdapi/v1/txt2img'

tts_url = "http://127.0.0.1:7851/api/tts-generate"
tts_headers = {'Content-Type': 'application/x-www-form-urlencoded'}

## Social API Details ##
your_facebook_page_id = 0
your_facebook_page_access_token = ''

## Script variables/arrays ##
starttime = time.time()
global textresult
global latest_article
video_array = []
combined_title_desc = []
hashtag_array = []
vid_combine_counter = 0
total_num_of_vids_gen = 0
gen_info_array = []
tts_output_file_path = ''

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

CATEGORIES = [
    "arts", "automobiles", "business", "fashion", "food", "insider",
    "movies", "nyregion", "obituaries", "opinion", "politics",
    "realestate", "science", "sports", "sundayreview", "technology",
    "theater", "t-magazine", "upshot", "us", "world"
]

def get_category_name(cata_number):
    return CATEGORIES[cata_number % len(CATEGORIES)]

## Coqui default voices - Will look into getting these working again, but for this project I prefer to use piper + RVC models.

# DEFAULT_VOICES = ["female_01.wav","female_02.wav","female_03.wav","female_04.wav",
#                   "female_05.wav","female_06.wav","female_07.wav","male_01.wav",
#                   "male_02.wav","male_03.wav","male_04.wav","male_05.wav","arnold.wav",
#                   "Clint_Eastwood CC3 (enhanced).wav","David_Attenborough CC3.wav",
#                   "James_Earl_Jones CC3.wav","Morgan_Freeman CC3.wav"]

# def getRandomVoice():
#     voiceCount = randrange(len(DEFAULT_VOICES))
#     return DEFAULT_VOICES[voiceCount % len(DEFAULT_VOICES)]

def fetch_nyt_headline(cata_number, select_article):
    cata = get_category_name(cata_number)
    request_url = f"https://api.nytimes.com/svc/topstories/v2/{cata}.json?api-key={nyt_apikey}"
    
    response = requests.get(request_url)
    if response.status_code != 200:
        time.sleep(90)
        response = requests.get(request_url)
    
    nyt_results = response.json().get('results', [])
    
    article = nyt_results[select_article]
    return article['title'], article['abstract'], cata

def get_article_count(cata_number):
    cata_name = get_category_name(cata_number)
    request_url = f"https://api.nytimes.com/svc/topstories/v2/{cata_name}.json?api-key={nyt_apikey}"
    response = requests.get(request_url)
    return response.json().get('num_results', 0)

def get_random_line_from_txt(file_path):
    with open(file_path) as file:
        lines = [line.rstrip() for line in file]
    return random.choice(lines)

def analyze_headline(headline):
    preamble = ("A chat between a curious user and an artificial intelligence assistant. "
                "The assistant gives helpful and detailed answers to the user's questions.")
    prompt = f"{preamble}\n\nUSER: In one word, what is the tone of the following headline {headline}\nASSISTANT:"
    
    request = {
        'prompt': prompt,
        'max_tokens': 16,
        'do_sample': True,
        'temperature': 1.1,
        'top_p': 0.1,
        'typical_p': 1,
        'repetition_penalty': 1.18,
        'top_k': 65,
        'min_length': 16,
        'num_beams': 1,
        'add_bos_token': True,
        'truncation_length': 2048
    }
    
    response = requests.post(ooba_url, headers=ooba_headers, json=request)
    if response.status_code == 200:
        headline_tone = response.json()['choices'][0]['text'].split()[0]
        return headline_tone.strip()
    
def generate_article_hashtags(headline, article_desc):
    prompt = f"Create 5 hashtags based on {headline} - {article_desc}, do not include anymore than 5 hashtags. Only include the answer.\nASSISTANT:"

    request = {
        'prompt': prompt,
        'max_tokens': 40,
        'do_sample': True,
        'temperature': 1.1,
        'top_p': 0.1,
        'typical_p': 1,
        'repetition_penalty': 1.18,
        'top_k': 65,
        'min_length': 16,
        'num_beams': 1,
        'add_bos_token': True,
        'truncation_length': 2048
    }

    response = requests.post(ooba_url, headers=ooba_headers, json=request)
    if response.status_code == 200:
        return response.json()['choices'][0]['text'].strip()

def generate_text(headline, article_desc):
    tone = get_random_line_from_txt("./emotions.txt")
    perspective = get_random_line_from_txt("./descriptive.txt")
    
    prompt = (f"Write a news segment in a {tone} tone about {headline} : {article_desc}, "
              f"strictly between 300 and 400 words, written from the perspective of a {perspective} person, "
              "Only include your answer, no other words. Do not include a title.")
    
    request = {
        'prompt': prompt,
        'max_tokens': 350,
        'do_sample': True,
        'temperature': 1.1,
        'top_p': 0.1,
        'typical_p': 1,
        'repetition_penalty': 1.18,
        'top_k': 65,
        'min_length': 150,
        'num_beams': 1,
        'add_bos_token': True,
        'truncation_length': 2048
    }
    
    response = requests.post(ooba_url, headers=ooba_headers, json=request)
    if response.status_code == 200:
        return response.json()['choices'][0]['text'].strip()

def generate_tts(article_text, file_name):
    if rvc_enabled == True:
        print(f"{bcolors.HEADER}RVC enabled{bcolors.ENDC}")
        if random_rvc_voice == True:
            rvc_voice = get_random_line_from_txt("./rvc_voices.txt")
            print(f"{bcolors.HEADER}Random RVC voice enabled - Voice selected {rvc_voice}{bcolors.ENDC}")
            form_data = {
                'text_input': f'{article_text}',
                'rvccharacter_voice_gen': f'{rvc_voice}',
                'output_file_name': f'{file_name}'
            }
        else:
            form_data = {
                'text_input': f'{article_text}',
                'rvccharacter_voice_gen': f'{default_rvc_voice}',
                'output_file_name': f'{file_name}'
            }
    else:
        form_data = {
            'text_input': f'{article_text}',
            'rvccharacter_voice_gen': 'Disabled',
            'output_file_name': f'{file_name}'
        }

    tts_response = requests.post(tts_url, data=form_data, headers=tts_headers)

    tts_response_json = tts_response.json()
    tts_output_file_path = tts_response_json["output_file_path"]
    print(tts_output_file_path)

    return tts_output_file_path

def save_encoded_image(b64_image, output_path):
    with open(output_path, "wb") as image_file:
        image_file.write(base64.b64decode(b64_image))

def submit_auto1111_post(url, data):
    return requests.post(url, data=json.dumps(data))

def generate_image(headline, epoch_time, headline_tone, headline_topic, filename):
    prompt = f"{headline} in a {headline_tone} tone in a {headline_topic} setting"
    data = {'prompt': f'{prompt}, Wide-angle lens, realistic', 'steps': 20, 'width': f'{image_width}', 'height': f'{image_height}'}
    response = submit_auto1111_post(auto1111_url, data)
    
    if response.status_code == 200:
        save_encoded_image(response.json()['images'][0], f'./outputs/{filename}.png')

def save_article_text(article_text, file_name, mode):
    with open(f'./outputs/{file_name}.txt', f"{mode}", encoding="utf-8") as file:
        file.write(article_text)

def create_video_file(file_name, tts_output_file_path):
    audio_path = f'{tts_output_file_path}'
    images_path = "./outputs"
    
    audio = WAVE(audio_path)
    audio_length = audio.info.length
    
    list_of_images = [] 
    for image_file in os.listdir(images_path): 
        if file_name in image_file and image_file.endswith('.png'):
            image_path = os.path.join(images_path, image_file) 
            image = Image.open(image_path).resize((int(video_height),int(video_width)), Image.Resampling.LANCZOS)
            if watermark_mode == True:
                logo = Image.open("./logo_overlay.png")
                logo = logo.resize((int(image_width), int(image_height)), Image.Resampling.LANCZOS)
                image.paste(logo, (0,0), logo)
            list_of_images.append(image)
    
    duration = audio_length / len(list_of_images)
    imageio.mimsave('images.gif', list_of_images, fps=1/duration)

    print(f'Writing video file...')

    video = VideoFileClip(f"images.gif")
    audio = AudioFileClip(audio_path) 
    final_video = video.set_audio(audio) 
    final_video.write_videofile(fps=30, codec="libx264", verbose=False, filename=f"./videos/{file_name}_video.mp4")

def upload_video_to_facebook(video_path, video_title, video_desc, article_hashtags, combined_title_desc, hashtag_array):
    page_id = your_facebook_page_id
    fb_access_token = your_facebook_page_access_token

    if(combined_title_desc != ''):
        fb_desc = ''.join(str(x) for x in combined_title_desc)
        hashtags = ''.join(str(y) for y in hashtag_array)

        fb_desc = f"{fb_desc} \n {hashtags}"

    else:
        fb_desc = f'{video_title} - {video_desc} - {article_hashtags}'
    
    files = {'source': open(video_path, 'rb')}
    post_url = f'https://graph-video.facebook.com/v20.0/{page_id}/videos'
    payload = {
        'access_token': fb_access_token,
        'title': video_title,
        'description': f'{fb_desc}'
    }
    
    response = requests.post(post_url, files=files, data=payload)
    print(response.text)

def combine_videos(epoch_time):
    video_clips = [VideoFileClip(video) for video in video_array]
    trans_clip = VideoFileClip('./transClip.mp4')
    final_clip = concatenate_videoclips(video_clips, method='compose', transition=trans_clip)
    final_clip.write_videofile(f"./combined/{epoch_time}.mp4")

def saveGenStats(stats):
    with open(f'./generation_stats.txt', 'a', encoding="utf-8") as modified:
        modified.write(f"\n{stats}")

while True:
    overall_tic = time.perf_counter()
    epoch_time = int(time.time())

    print(f'\n{bcolors.WARNING}Facebook posting: {bcolors.ENDC}{bcolors.OKCYAN}{facebook_post_enable}{bcolors.ENDC}{bcolors.WARNING} - Combine videos: {bcolors.ENDC}{bcolors.OKCYAN}{combineVideos}{bcolors.ENDC}{bcolors.WARNING} - Random topic mode: {bcolors.ENDC}{bcolors.OKCYAN}{random_topic_mode}{bcolors.ENDC}{bcolors.WARNING} - Random article select: {bcolors.ENDC}{bcolors.OKCYAN}{random_article_select}{bcolors.ENDC}{bcolors.WARNING} - Random RVC mode: {bcolors.ENDC}{bcolors.OKCYAN}{random_rvc_voice}{bcolors.ENDC}')
    
    if random_topic_mode == True:
        cata_number = randrange(22)
    
    if random_article_select == True:
        select_article = randrange(get_article_count(cata_number))
    
    if random_article_select == False and random_topic_mode == False:
        if cata_number > 21:
            article_count = get_article_count(cata_number)
            cata_number = 1
            if select_article > article_count:
                select_article = 1

    nyt_headline, nyt_article_desc, headline_topic = fetch_nyt_headline(cata_number, select_article)

    cata_name = get_category_name(cata_number)

    print(f'\n{bcolors.HEADER}Generating text for: {nyt_headline}. Category: {cata_name}{bcolors.ENDC}')

    print(f'\n{bcolors.OKCYAN}Analysing headline tone...{bcolors.ENDC}')
    
    analyseHeadline_tic = time.perf_counter()
    headline_tone = analyze_headline(nyt_headline)
    analyseHeadline_toc = time.perf_counter()
    file_name = re.sub('[^A-Za-z0-9]+', '', nyt_headline) + f'_{epoch_time}'

    print(f'{bcolors.OKGREEN}Tone found: {headline_tone}. Time taken: {analyseHeadline_toc - analyseHeadline_tic:0.4f} seconds.{bcolors.ENDC}')

    if generate_hashtags == True:
        print(f'\n{bcolors.OKCYAN}Generating article hashtags...{bcolors.ENDC}')
        genHashtags_tic = time.perf_counter()
        article_hashtags = generate_article_hashtags(nyt_headline, nyt_article_desc)
        genHashtags_toc = time.perf_counter()
        print(f'{bcolors.OKGREEN}Hashtags generated - {article_hashtags.partition('\n')[0]} - Time taken: {genHashtags_toc - genHashtags_tic:0.4f}{bcolors.ENDC}')

    print(f'\n{bcolors.OKCYAN}Generating article text...{bcolors.ENDC}')
    genText_tic = time.perf_counter()
    generated_text = generate_text(nyt_headline, nyt_article_desc)
    genText_toc = time.perf_counter()
    genTextTimeTaken = genText_toc - genText_tic
    gen_info_array.append(f"Article text gen time: {genTextTimeTaken} seconds")

    print(f'{bcolors.OKGREEN}Article text generation complete. Time taken: {genTextTimeTaken:0.4f} seconds.{bcolors.ENDC}')

    print(f'\n{bcolors.OKCYAN}Generating text-to-speech...{bcolors.ENDC}')
    genTTS_tic = time.perf_counter()
    tts_output_file_path = generate_tts(generated_text[:1999], file_name)
    genTTS_toc = time.perf_counter()
    genTTSTimeTaken = genTTS_toc - genTTS_tic
    gen_info_array.append(f"TTS gen time: {genTTSTimeTaken} seconds")

    print(f'{bcolors.OKGREEN}Generating TTS complete. Time taken: {genTTSTimeTaken:0.4f} seconds.{bcolors.ENDC}')

    print(f'\n{bcolors.OKCYAN}Generating images...{bcolors.ENDC}')
    genImages_tic = time.perf_counter()

    for image_count in range(1, 5):
        image_filename = f'{file_name}_{image_count}'
        generate_image(nyt_headline, epoch_time, headline_tone, headline_topic, image_filename)

    genImages_toc = time.perf_counter()
    genImagesTimeTaken = genImages_toc - genImages_tic
    gen_info_array.append(f"Image gen time: {genImagesTimeTaken} seconds")
    print(f'{bcolors.OKGREEN}Generating images complete. Time taken: {genImagesTimeTaken:0.4f} seconds.{bcolors.ENDC}')
    save_article_text(generated_text, file_name, 'w')
    
    print(f'\n{bcolors.OKCYAN}Creating video file...{bcolors.ENDC}')
    createVideo_tic = time.perf_counter()
    create_video_file(file_name, tts_output_file_path)
    createVideo_toc = time.perf_counter()
    print(f'{bcolors.OKGREEN}Creating video file complete. Time taken: {createVideo_toc - createVideo_tic:0.4f} seconds.{bcolors.ENDC}')
    
    if combineVideos == True and vid_combine_counter <= num_of_vids_to_combine:
        video_array.append(f'./videos/{file_name}_video.mp4')
        combined_title_desc.append(f"{nyt_headline} - {nyt_article_desc}\n\n")
        vid_combine_counter += 1

        if generate_hashtags == True:
            formatted_hashtags = article_hashtags.partition('\n')[0]
            hashtag_array.append(f"{formatted_hashtags.replace(",", "")}\n")
        
        if vid_combine_counter == num_of_vids_to_combine:
            print(f'\n{bcolors.WARNING}Combining videos has been enabled.{bcolors.ENDC}')
            print(f'{bcolors.OKCYAN}Combining videos{bcolors.ENDC}\n')
            combine_videos(epoch_time)
            video_array.clear()
            vid_combine_counter = 0
            
            if facebook_post_enable:
                concat_filename = f'./combined/{epoch_time}.mp4'
                print(f'\n{bcolors.OKCYAN}Posting to Facebook{bcolors.ENDC}')
                upload_video_to_facebook(concat_filename, '', '', '', combined_title_desc, hashtag_array)
                print(f'{bcolors.OKGREEN}Posting to Facebook complete.{bcolors.ENDC}')
                combined_title_desc.clear()
                hashtag_array.clear()
    else:
        if facebook_post_enable == True:
            upload_video_to_facebook(f'./videos/{file_name}_video.mp4', nyt_headline, nyt_article_desc, article_hashtags, '', '')
            print(f'\n{bcolors.OKCYAN}Posting to Facebook{bcolors.ENDC}')
    
    total_num_of_vids_gen += 1
    overall_toc = time.perf_counter()
    runtime = round((overall_toc - overall_tic), 2)
    runtime = str(round((runtime/60), 2))
    gen_info_array.append(f"Overall generation time: {runtime} minutes.")
    genInfo = "\n".join(str(x) for x in gen_info_array)
    save_article_text(f'\n\n{genInfo}', file_name, 'a')
    saveGenStats(f'\n\n{nyt_headline}\n{genInfo}')
    gen_info_array.clear()
    tts_output_file_path = ''

    if random_article_select == False and random_topic_mode == False:
        cata_number = cata_number + 1
        select_article = select_article + 1
    
    print(f'\n{bcolors.OKGREEN}Video creation complete for {bcolors.ENDC}{bcolors.OKCYAN}{nyt_headline}{bcolors.ENDC}')
    print(f'{bcolors.OKGREEN}Time taken overall: {bcolors.ENDC}{bcolors.WARNING}{runtime} minutes.')
    print(f'\n{bcolors.OKGREEN}Total number of videos generated so far: {total_num_of_vids_gen}{bcolors.ENDC}')
    
