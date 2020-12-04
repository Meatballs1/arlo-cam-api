import vlc
import threading
import time

#TODO: This should probably be managed by a singleton RecorderManager to prevent multiple records?
class Recorder:
    def __init__(self, address, file_path, timeout):
        self.address = address
        self.file_path = file_path
        self.stopped = False
        self.thread = None
        self.timeout = timeout

    def record_thread(self):
        args = f"sout=file/ts:{self.file_path}"
        url = f"rtsp://{self.address}/live"
        instance = vlc.Instance()
        media = instance.media_new(url)
        media.add_option(args)
        player = instance.media_player_new()
        player.set_media(media)
        player.play()

        start_time = time.time()
        while not self.stopped:
            if (self.timeout > 0):
                if ((time.time()-start_time)>=self.timeout):
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

if __name__ == "__main__":
    recorder = Recorder("172.14.1.194","/tmp/test.mpg",10)
    recorder.run()
    while 1:
        continue
