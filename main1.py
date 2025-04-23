import os
import json
import requests
import pyttsx3
import pyaudio
import webbrowser
from vosk import Model, KaldiRecognizer

class VoiceOutput:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170)

    def speak(self, msg):
        print(f"System: {msg}")
        self.engine.say(msg)
        self.engine.runAndWait()

class AudioInput:
    def __init__(self):
        model_path = "model_en"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Missing Vosk model at '{model_path}'")
        self.recognizer = KaldiRecognizer(Model(model_path), 16000)
        self.audio_interface = pyaudio.PyAudio()
        self.stream = self.audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000
        )
        self.stream.start_stream()

    def capture(self):
        while True:
            block = self.stream.read(4000, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(block):
                outcome = json.loads(self.recognizer.Result())
                return outcome.get("text", "").strip()

class LexiCore:
    def __init__(self):
        self.voice = VoiceOutput()
        self.listener = AudioInput()
        self.definition_data = None
        self.current_word = ""

    def fetch_info(self, term):
        try:
            endpoint = f"https://api.dictionaryapi.dev/api/v2/entries/en/{term}"
            reply = requests.get(endpoint)
            reply.raise_for_status()
            self.definition_data = reply.json()[0]
            self.current_word = term
            self.voice.speak(f"{term} loaded.")
        except Exception:
            self.voice.speak(f"Failed to find {term}.")

    def explain(self):
        if self.definition_data:
            try:
                definition = self.definition_data["meanings"][0]["definitions"][0]["definition"]
                self.voice.speak(f"{self.current_word}: {definition}")
            except:
                self.voice.speak("No definition found.")
        else:
            self.voice.speak("Load a word first.")

    def sample_usage(self):
        if self.definition_data:
            try:
                example = self.definition_data["meanings"][0]["definitions"][0].get("example", None)
                if example:
                    self.voice.speak(f"Example: {example}")
                else:
                    self.voice.speak("No example available.")
            except:
                self.voice.speak("Error fetching example.")
        else:
            self.voice.speak("No data available.")

    def web_reference(self):
        if self.current_word:
            webbrowser.open(f"https://www.dictionary.com/browse/{self.current_word}")
            self.voice.speak("Opening browser.")
        else:
            self.voice.speak("No word set.")

    def archive(self):
        if self.definition_data:
            try:
                definition = self.definition_data["meanings"][0]["definitions"][0]["definition"]
                with open("records.txt", "a", encoding="utf-8") as f:
                    f.write(f"{self.current_word}\n{definition}\n\n")
                self.voice.speak("Saved.")
            except:
                self.voice.speak("Error saving.")
        else:
            self.voice.speak("Nothing to store.")

    def launch(self):
        self.voice.speak("Ready for commands.")
        while True:
            command = self.listener.capture()
            print(f"You said: {command}")

            if command.startswith("find "):
                self.fetch_info(command.replace("find ", ""))
            elif command == "meaning":
                self.explain()
            elif command == "example":
                self.sample_usage()
            elif command == "link":
                self.web_reference()
            elif command == "save":
                self.archive()
            elif command in ["exit", "stop"]:
                self.voice.speak("Session ended.")
                break
            else:
                self.voice.speak("Unknown command.")

if __name__ == "__main__":
    LexiCore().launch()
