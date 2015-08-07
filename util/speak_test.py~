import speechd
client = speechd.SSIPClient('test')
client.set_output_module('festival')
client.set_language('en')
client.set_punctuation(speechd.PunctuationMode.SOME)
client.speak("Hello World!")
client.close()
