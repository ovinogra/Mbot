class QueuedVCContactUpdate:
    def __init__(self, voice_channel, to_add):
        self.voice_channel = voice_channel
        self.to_add = [to_add]

    def add_another(self, to_add):
        self.to_add.append(to_add)

    def get_channel(self):
        return self.voice_channel

    def get_to_add(self):
        return self.to_add
