from playsound import playsound
import threading

def play_buy_sound():
    threading.Thread(target=playsound, args=('bot/assets/buy_ringtone.mp3',)).start()
    return None