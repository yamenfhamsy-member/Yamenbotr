import os
import time
import json
import threading
import requests
from datetime import datetime, date, timedelta
import feedparser
from gtts import gTTS
import telebot
from telebot import types
from bs4 import BeautifulSoup
from moviepy.editor import VideoFileClip
import speech_recognition as sr
from pydub import AudioSegment

BOT_TOKEN="8548973430:AAEcIZKQlDZcsjUVcBg7PDSyOv5SNmh00Ak"
bot=telebot.TeleBot(BOT_TOKEN)
USERS_FILE="users_data.json"
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; Bot/1.0)"}

STATE_WAIT_COUNTRY="WAIT_COUNTRY"
STATE_WAIT_CITY="WAIT_CITY"
STATE_TTS_WAIT="TTS_WAIT"
STATE_TRANSLATE_WAIT="TRANSLATE_WAIT"
STATE_VIDEO_WAIT="VIDEO_WAIT"
STATE_STT_WAIT="STT_WAIT"
STATE_ANIME_SEARCH="ANIME_SEARCH_WAIT"
STATE_ANIME_IMAGE_SEARCH="ANIME_IMAGE_SEARCH_WAIT"
STATE_FOOTBALL_WAIT="FOOTBALL_WAIT"
STATE_GENERAL_SEARCH="GENERAL_SEARCH_WAIT"

users={}
prayer_times_cache={}

ARAB_COUNTRIES={"السعودية":"Saudi Arabia","مصر":"Egypt","الإمارات":"United Arab Emirates","المغرب":"Morocco","الجزائر":"Algeria","تونس":"Tunisia","العراق":"Iraq","لبنان":"Lebanon","الأردن":"Jordan","فلسطين":"Palestine","ليبيا":"Libya","السودان":"Sudan","الكويت":"Kuwait","البحرين":"Bahrain","عمان":"Oman","اليمن":"Yemen","موريتانيا":"Mauritania","سوريا":"Syria","قطر":"Qatar"}

FOOTBALL_LEAGUES={"الدوري الإنجليزي":"https://www.espn.com/soccer/league/_/name/eng.1/rss","الدوري الإسباني":"https://www.espn.com/soccer/league/_/name/esp.1/rss","الدوري الإيطالي":"https://www.espn.com/soccer/league/_/name/ita.1/rss","الدوري الألماني":"https://www.espn.com/soccer/league/_/name/ger.1/rss","الدوري الفرنسي":"https://www.espn.com/soccer/league/_/name/fra.1/rss","الدوري البرتغالي":"https://www.espn.com/soccer/league/_/name/por.1/rss","الدوري الهولندي":"https://www.espn.com/soccer/league/_/name/ned.1/rss","الدوري البلجيكي":"https://www.espn.com/soccer/league/_/name/bel.1/rss","الدوري الروسي":"https://www.espn.com/soccer/league/_/name/rus.1/rss","الدوري التركي":"https://www.espn.com/soccer/league/_/name/tur.1/rss","الدوري السعودي":"https://www.kooora.com/rss/saudi-league","الدوري المصري":"https://www.kooora.com/rss/egypt-league","الدوري الإماراتي":"https://www.kooora.com/rss/uae-league","الدوري القطري":"https://www.kooora.com/rss/qatar-league","الدوري العراقي":"https://www.kooora.com/rss/iraq-league","الدوري الجزائري":"https://www.kooora.com/rss/algeria-league","الدوري المغربي":"https://www.kooora.com/rss/morocco-league","الدوري التونسي":"https://www.kooora.com/rss/tunisia-league","الدوري الأردني":"https://www.kooora.com/rss/jordan-league","الدوري اللبناني":"https://www.kooora.com/rss/lebanon-league","الدوري الليبي":"https://www.kooora.com/rss/libya-league","الدوري السوداني":"https://www.kooora.com/rss/sudan-league","الدوري الكويتي":"https://www.kooora.com/rss/kuwait-league","الدوري البحريني":"https://www.kooora.com/rss/bahrain-league","الدوري العماني":"https://www.kooora.com/rss/oman-league","الدوري اليمني":"https://www.kooora.com/rss/yemen-league","الدوري السوري":"https://www.kooora.com/rss/syria-league","الدوري الفلسطيني":"https://www.kooora.com/rss/palestine-league","الدوري الموريتاني":"https://www.kooora.com/rss/mauritania-league","الدوري الأمريكي":"https://www.espn.com/soccer/league/_/name/usa.1/rss","دوري أبطال أوروبا":"https://www.espn.com/soccer/league/_/name/uefa.champions/rss","الدوري الأوروبي":"https://www.espn.com/soccer/league/_/name/uefa.europa/rss","كأس العالم":"https://www.fifa.com/rss-feeds/news"}

def load_users():
    global users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE,"r",encoding="utf-8") as f:
            data=json.load(f)
            users={int(k):v for k,v in data.items()}
    else:
        users={}

def save_users():
    with open(USERS_FILE,"w",encoding="utf-8") as f:
        json.dump({str(k):v for k,v in users.items()},f,ensure_ascii=False,indent=2)

load_users()

def translate_text(text,target):
    try:
        url="https://translate.googleapis.com/translate_a/single"
        params={"client":"gtx","sl":"auto","tl":target,"dt":"t","q":text}
        r=requests.get(url,params=params,timeout=10,headers=HEADERS)
        return r.json()[0][0][0]
    except:
        return text

def text_to_speech_ar(text,lang="ar",filename="tts.mp3"):
    try:
        tts=gTTS(text=text,lang=lang)
        tts.save(filename)
        return filename
    except:
        return None

def extract_audio_from_video(video_path,audio_path="extracted_audio.mp3"):
    try:
        video=VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()
        return audio_path
    except:
        return None

def speech_to_text(audio_path):
    try:
        if audio_path.endswith(".ogg"):
            sound=AudioSegment.from_ogg(audio_path)
            wav_path=audio_path.replace(".ogg",".wav")
            sound.export(wav_path,format="wav")
            audio_path=wav_path
        r=sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio=r.record(source)
        return r.recognize_google(audio,language="ar-SA")
    except:
        return None

def get_prayer_times(city,country):
    today_str=date.today().isoformat()
    cache_key=f"{city}_{country}_{today_str}"
    if cache_key in prayer_times_cache:
        return prayer_times_cache[cache_key]
    try:
        url="https://api.aladhan.com/v1/timingsByCity"
        params={"city":city,"country":country,"method":4}
        r=requests.get(url,params=params,timeout=10,headers=HEADERS)
        data=r.json()
        t=data["data"]["timings"]
        times={k:t[k].split(" ")[0] for k in ["Fajr","Sunrise","Dhuhr","Asr","Maghrib","Isha"]}
        prayer_times_cache[cache_key]=times
        return times
    except:
        return None

def ensure_user(chat_id):
    if chat_id not in users:
        users[chat_id]={"state":None,"notify_enabled":False,"country":"","city":"","notified_for_date":{}}
        save_users()

def main_menu():
    m=types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("🎧 تحويل نص لصوت","🌐 ترجمة")
    m.row("🕌 أوقات الصلاة","🔔 التنبيهات")
    m.row("📰 أخبار الأنمي","🎥 استخراج صوت من فيديو")
    m.row("🔊 تحويل صوت لنص","🔍 بحث عن أنمي")
    m.row("🖼️ بحث أنمي بالصورة","⚽ أخبار كرة القدم")
    m.row("🔎 بحث عام")
    return m

def country_menu():
    m=types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in ARAB_COUNTRIES.keys():
        m.row(name)
    m.row("⬅️ رجوع")
    return m

def notify_menu(chat_id):
    m=types.ReplyKeyboardMarkup(resize_keyboard=True)
    state=users.get(chat_id,{}).get("notify_enabled",False)
    if state:
        m.row("⛔ إيقاف التنبيهات")
    else:
        m.row("✅ تفعيل التنبيهات")
    m.row("⬅️ رجوع")
    return m

def football_league_menu():
    m=types.ReplyKeyboardMarkup(resize_keyboard=True)
    for league in FOOTBALL_LEAGUES.keys():
        m.row(league)
    m.row("⬅️ رجوع")
    return m

def clean_html(text):
    if not text:
        return ""
    soup=BeautifulSoup(text,"html.parser")
    for tag in soup.find_all(['cite','script','style']):
        tag.decompose()
    return soup.get_text(strip=True)

def get_rss_news(rss_url,limit=20):
    try:
        feed=feedparser.parse(rss_url)
        items=[]
        for e in feed.entries[:limit]:
            title=e.get("title","").strip()
            link=e.get("link","").strip()
            summary=clean_html(e.get("summary","") or e.get("description",""))
            items.append({"title":title,"summary":summary,"link":link})
        return items
    except:
        return []

def arabic_prayer_name(key):
    return {"Fajr":"الفجر","Sunrise":"الشروق","Dhuhr":"الظهر","Asr":"العصر","Maghrib":"المغرب","Isha":"العشاء"}.get(key,key)

def check_and_send_notifications_loop():
    while True:
        try:
            now=datetime.now()
            today_str=now.date().isoformat()
            for chat_id,info in list(users.items()):
                if not info.get("notify_enabled"):
                    continue
                country=info.get("country")
                city=info.get("city")
                if not city or not country:
                    continue
                times=get_prayer_times(city,country)
                if not times:
                    continue
                notified=info.get("notified_for_date",{})
                if today_str not in notified:
                    notified[today_str]=[]
                for key in ["Fajr","Dhuhr","Asr","Maghrib","Isha"]:
                    if key in notified[today_str]:
                        continue
                    tstr=times.get(key)
                    if not tstr:
                        continue
                    try:
                        hh_mm=tstr.split(":")
                        prayer_dt=datetime(now.year,now.month,now.day,int(hh_mm[0]),int(hh_mm[1]))
                        delta=(now-prayer_dt).total_seconds()
                        if 0<=delta<60:
                            bot.send_message(chat_id,f"🔔 الآن وقت {arabic_prayer_name(key)} في {city} — {tstr}")
                            notified[today_str].append(key)
                    except:
                        continue
                keys_to_keep=set([(date.today()-timedelta(days=i)).isoformat() for i in range(4)])
                info["notified_for_date"]={k:v for k,v in info.get("notified_for_date",{}).items() if k in keys_to_keep}
                info["notified_for_date"].update(notified)
                users[chat_id]=info
            save_users()
        except:
            pass
        time.sleep(30)

notif_thread=threading.Thread(target=check_and_send_notifications_loop,daemon=True)
notif_thread.start()

@bot.message_handler(commands=["start"])
def cmd_start(message):
    chat_id=message.chat.id
    ensure_user(chat_id)
    bot.send_message(chat_id,"أهلاً! استخدم الأزرار للتنقل.",reply_markup=main_menu())

@bot.message_handler(content_types=["text"])
def handle_all_text(message):
    chat_id=message.chat.id
    text=message.text.strip()
    ensure_user(chat_id)
    state=users[chat_id].get("state")
    if text=="🔔 التنبيهات":
        bot.send_message(chat_id,"إدارة التنبيهات:",reply_markup=notify_menu(chat_id))
        return
    if text=="✅ تفعيل التنبيهات":
        users[chat_id]["state"]=STATE_WAIT_COUNTRY
        bot.send_message(chat_id,"اختر دولتك:",reply_markup=country_menu())
        save_users()
        return
    if text=="⛔ إيقاف التنبيهات":
        users[chat_id].update({"notify_enabled":False,"country":"","city":"","state":None,"notified_for_date":{}})
        save_users()
        bot.send_message(chat_id,"تم إيقاف التنبيهات.",reply_markup=main_menu())
        return
    if state==STATE_WAIT_COUNTRY:
        if text not in ARAB_COUNTRIES:
            bot.send_message(chat_id,"اختر دولة صحيحة.",reply_markup=country_menu())
            return
        users[chat_id]["country"]=ARAB_COUNTRIES[text]
        users[chat_id]["state"]=STATE_WAIT_CITY
        bot.send_message(chat_id,f"اخترت {text}. اكتب اسم المدينة بالعربية:",reply_markup=types.ReplyKeyboardRemove())
        save_users()
        return
    if state==STATE_WAIT_CITY:
        city=text
        country=users[chat_id]["country"]
        times=get_prayer_times(city,country)
        if not times:
            bot.send_message(chat_id,"فشل جلب أوقات الصلاة.",reply_markup=types.ReplyKeyboardRemove())
            return
        users[chat_id].update({"city":city,"notify_enabled":True,"state":None,"notified_for_date":{}})
        save_users()
        msg=f"تم تفعيل التنبيهات لمدينة {city} في {country}.\nأوقات الصلاة اليوم:\n"
        for k,v in times.items():
            msg+=f"{k}: {v}\n"
        bot.send_message(chat_id,msg,reply_markup=main_menu())
        return
    if text=="🕌 أوقات الصلاة":
        city=users[chat_id].get("city")
        country=users[chat_id].get("country")
        if city and country:
            times=get_prayer_times(city,country)
            if not times:
                bot.send_message(chat_id,"فشل جلب أوقات الصلاة.",reply_markup=main_menu())
                return
            msg=f"أوقات الصلاة في {city}:\n"
            for k,v in times.items():
                msg+=f"{k}: {v}\n"
            bot.send_message(chat_id,msg,reply_markup=main_menu())
        else:
            users[chat_id]["state"]=STATE_WAIT_CITY
            bot.send_message(chat_id,"أرسل اسم المدينة لمعرفة أوقات الصلاة.",reply_markup=types.ReplyKeyboardRemove())
        return
    if text=="🎧 تحويل نص لصوت":
        users[chat_id]["state"]=STATE_TTS_WAIT
        bot.send_message(chat_id,"أرسل النص الذي تريد تحويله إلى صوت.",reply_markup=types.ReplyKeyboardRemove())
        save_users()
        return
    if state==STATE_TTS_WAIT:
        users[chat_id]["state"]=None
        fname=text_to_speech_ar(text,lang="ar",filename=f"tts_{chat_id}.mp3")
        if fname:
            with open(fname,"rb") as audio:
                bot.send_audio(chat_id,audio,caption="هذا الصوت المحول من النص الذي أرسلته.")
            os.remove(fname)
        bot.send_message(chat_id,"انتهى التحويل.",reply_markup=main_menu())
        save_users()
        return
    if text=="🌐 ترجمة":
        users[chat_id]["state"]=STATE_TRANSLATE_WAIT
        bot.send_message(chat_id,"أرسل النص للترجمة.",reply_markup=types.ReplyKeyboardRemove())
        save_users()
        return
    if state==STATE_TRANSLATE_WAIT:
        users[chat_id]["state"]=None
        translated=translate_text(text,"ar")
        bot.send_message(chat_id,f"الترجمة:\n{translated}",reply_markup=main_menu())
        save_users()
        return
    if text=="📰 أخبار الأنمي":
        bot.send_message(chat_id,"جاري جلب أخبار الأنمي...")
        news=get_rss_news("https://www.animenewsnetwork.com/all/rss.xml")
        if not news:
            bot.send_message(chat_id,"لا توجد أخبار الآن.",reply_markup=main_menu())
            return
        msg="أخبار الأنمي:\n"
        for it in news:
            msg+=f"• {it['title']} — {it['summary']}\n{it['link']}\n"
        bot.send_message(chat_id,msg,reply_markup=main_menu())
        return
    if text=="⚽ أخبار كرة القدم":
        users[chat_id]["state"]=STATE_FOOTBALL_WAIT
        bot.send_message(chat_id,"اختر الدوري:",reply_markup=football_league_menu())
        save_users()
        return
    if state==STATE_FOOTBALL_WAIT:
        users[chat_id]["state"]=None
        rss_url=FOOTBALL_LEAGUES.get(text)
        if not rss_url:
            bot.send_message(chat_id,"اختر دوري صحيح.",reply_markup=football_league_menu())
            return
        news=get_rss_news(rss_url)
        if not news:
            bot.send_message(chat_id,"لا توجد أخبار الآن.",reply_markup=main_menu())
            return
        msg=f"أخبار {text}:\n"
        for it in news:
            msg+=f"• {it['title']} — {it['summary']}\n{it['link']}\n"
        bot.send_message(chat_id,msg,reply_markup=main_menu())
        return
    if text=="🎥 استخراج صوت من فيديو":
        users[chat_id]["state"]=STATE_VIDEO_WAIT
        bot.send_message(chat_id,"أرسل الفيديو.",reply_markup=types.ReplyKeyboardRemove())
        save_users()
        return
    if text=="🔊 تحويل صوت لنص":
        users[chat_id]["state"]=STATE_STT_WAIT
        bot.send_message(chat_id,"أرسل الرسالة الصوتية.",reply_markup=types.ReplyKeyboardRemove())
        save_users()
        return
    if text=="🔍 بحث عن أنمي":
        users[chat_id]["state"]=STATE_ANIME_SEARCH
        bot.send_message(chat_id,"أرسل اسم الأنمي للبحث عنه.",reply_markup=types.ReplyKeyboardRemove())
        save_users()
        return
    if state==STATE_ANIME_SEARCH:
        users[chat_id]["state"]=None
        query=text
        url=f"https://api.jikan.moe/v4/anime?q={query}&limit=5"
        try:
            r=requests.get(url,timeout=10,headers=HEADERS).json()
            results=r.get("data",[])
            if not results:
                bot.send_message(chat_id,"لا توجد نتائج.",reply_markup=main_menu())
                return
            msg="نتائج البحث عن الأنمي:\n"
            for a in results:
                title=a.get("title","")
                url=a.get("url","")
                synopsis=a.get("synopsis","").strip()[:500]
                msg+=f"• {title}\n{synopsis}\n{url}\n\n"
            bot.send_message(chat_id,msg,reply_markup=main_menu())
        except:
            bot.send_message(chat_id,"فشل البحث.",reply_markup=main_menu())
        return
    if text=="🖼️ بحث أنمي بالصورة":
        users[chat_id]["state"]=STATE_ANIME_IMAGE_SEARCH
        bot.send_message(chat_id,"أرسل صورة الأنمي للبحث.",reply_markup=types.ReplyKeyboardRemove())
        save_users()
        return
    if state==STATE_ANIME_IMAGE_SEARCH:
        bot.send_message(chat_id,"خاصية البحث بالصور لم تُفعل بعد.",reply_markup=main_menu())
        users[chat_id]["state"]=None
        save_users()
        return
    if text=="🔎 بحث عام":
        users[chat_id]["state"]=STATE_GENERAL_SEARCH
        bot.send_message(chat_id,"أرسل ما تريد البحث عنه.",reply_markup=types.ReplyKeyboardRemove())
        save_users()
        return
    if state==STATE_GENERAL_SEARCH:
        users[chat_id]["state"]=None
        try:
            query=text
            url=f"https://www.google.com/search?q={query}"
            bot.send_message(chat_id,f"رابط البحث العام: {url}",reply_markup=main_menu())
        except:
            bot.send_message(chat_id,"فشل البحث.",reply_markup=main_menu())
        save_users()
        return
    bot.send_message(chat_id,"اختر خياراً من القائمة.",reply_markup=main_menu())

@bot.message_handler(content_types=["audio","voice","video","document"])
def handle_media(message):
    chat_id=message.chat.id
    ensure_user(chat_id)
    state=users[chat_id].get("state")
    if state==STATE_VIDEO_WAIT:
        file_info=bot.get_file(message.video.file_id if hasattr(message,"video") else message.document.file_id)
        downloaded_file=bot.download_file(file_info.file_path)
        video_path=f"video_{chat_id}.mp4"
        with open(video_path,"wb") as f:
            f.write(downloaded_file)
        audio_file=extract_audio_from_video(video_path,audio_path=f"audio_{chat_id}.mp3")
        if audio_file:
            with open(audio_file,"rb") as a:
                bot.send_audio(chat_id,a,caption="تم استخراج الصوت من الفيديو.")
            os.remove(audio_file)
        os.remove(video_path)
        users[chat_id]["state"]=None
        save_users()
        return
    if state==STATE_STT_WAIT:
        file_info=bot.get_file(message.voice.file_id if hasattr(message,"voice") else message.audio.file_id)
        downloaded_file=bot.download_file(file_info.file_path)
        audio_path=f"stt_{chat_id}.ogg"
        with open(audio_path,"wb") as f:
            f.write(downloaded_file)
        text_result=speech_to_text(audio_path)
        if text_result:
            bot.send_message(chat_id,f"النص المستخرج:\n{text_result}")
        else:
            bot.send_message(chat_id,"فشل تحويل الصوت إلى نص.")
        os.remove(audio_path)
        users[chat_id]["state"]=None
        save_users()
        return
# ================= Keep Alive Server =================
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

t = Thread(target=run)
t.start()
# =====================================================
if __name__=="__main__":
    bot.polling(none_stop=True,timeout=60,long_polling_timeout=60)