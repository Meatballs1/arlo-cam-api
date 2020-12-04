import vlc
import threading
import time

class Recorder:
    def __init__(self, ip, file_path, timeout):
        self.ip = ip
        self.file_path = file_path
        self.stopped = False
        self.thread = None
        self.timeout = timeout

    def record_thread(self):
        args = f"sout=file/ts:{self.file_path}"
        url = f"rtsp://{self.ip}/live"
        instance = vlc.Instance()
        media = instance.media_new(url)
        media.add_option(args)
        player = instance.media_player_new()
        player.set_media(media)
        player.play()

        start_time = time.time()
        while not self.stopped:
            if (timeout > 0):
                if ((time.time()-start_time)>=timeout):
                    self.stopped = True
            time.sleep(0.1)
            continue

        player.stop()
        media.release()

    def run(self):
        self.thread = threading.Thread(target=self.record_thread, args=())
        self.thread.start()

    def stop(self):
        self.stopped = True
        self.thread.join()
