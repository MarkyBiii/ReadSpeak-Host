from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from transformers import AutoProcessor, AutoModelForCTC
# from datasets import load_dataset
from gruut import sentences
import numpy
import torch
import librosa

#AI model stuff
# load model and processor for phonemes
# processor = Wav2Vec2Processor.from_pretrained("./model")
# model = Wav2Vec2ForCTC.from_pretrained("./model")
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-lv-60-espeak-cv-ft")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-lv-60-espeak-cv-ft")

# # load model and processor for words
# processor2 = AutoProcessor.from_pretrained("./model2")
# model2 = AutoModelForCTC.from_pretrained("./model2")
processor2 = AutoProcessor.from_pretrained("facebook/wav2vec2-large-960h-lv60-self")
model2 = AutoModelForCTC.from_pretrained("facebook/wav2vec2-large-960h-lv60-self")
sr = processor.feature_extractor.sampling_rate

#todo
#Compare phoneme offset with word offset to group phonemes into words(could use some more improvements)
#remove stress on original phonemes and colon on transcribed phonemes
#also remove the curved lines above some chars on the ch/tch sound (good for now, search for more possible phonemes that need to be cleaned)
#Scoring?
#error handling if some words were not detected, eg. wood would a woodchuck, 'a' was not detected
#maybe compare words detected first before phonemes?
#problem: some starting phonemes get included in the previous word
def wordOffsetGet(inputs):
  # retrieve logits
  with torch.no_grad():
    #logits = model(inputs).logits
    logits = model2(inputs["input_values"]).logits
  # take argmax and decode
  predicted_ids = torch.argmax(logits, dim=-1)
  transcription = processor2.batch_decode(predicted_ids, output_word_offsets = True)
  # print(transcription.word_offsets[0])
  return transcription.word_offsets[0]

def textToPhoneme(text):
  output = []
  output2 = []
  # using phonemizer
  # output = phonemize(text, 'en-us')
  # output = output.replace("ː", "") 
  
  #using gruut
  for sent in sentences(text, lang="en-us", minor_breaks=False, major_breaks=False, punctuations=False):
    for word in sent:
        if word.phonemes:
          phones = ''.join(word.phonemes)
          phones = phones.replace("ˈ", "") #removes stress symbols could be removed if needed
          phones = phones.replace("ˌ", "")
          phones = phones.replace("t͡ʃ", "tʃ")
          phones = phones.replace("d͡ʒ", "dʒ")
          output.append(phones)
          for phonemes in word.phonemes:
            phonemes = phonemes.replace("ː", "")
            phonemes = phonemes.replace("ˈ", "") #removes stress symbols could be removed if needed
            phonemes = phonemes.replace("ˌ", "")
            phonemes = phonemes.replace("t͡ʃ", "tʃ")
            phonemes = phonemes.replace("d͡ʒ", "dʒ")
            output2.append(phonemes)
  
  return output, output2

def audioToPhoneme(inputs):
  # retrieve logits
  with torch.no_grad():
    # logits = model(inputs).logits
    logits = model(inputs["input_values"]).logits
  # take argmax and decode
  predicted_ids = torch.argmax(logits, dim=-1)
  transcription = processor.batch_decode(predicted_ids, output_char_offsets = True)
  transcriptionstr = ''.join(transcription.text)
  transcriptionstr = transcriptionstr.replace("ː", " ")
  transcriptionstr2 = transcriptionstr.split()
  transcriptionstr = transcriptionstr.replace(" ", "")
  # print(transcription.char_offsets[0])
  return transcriptionstr, transcription.char_offsets[0], transcriptionstr2

def groupPhonemes(audio_phonemes,word_offsets, char_offsets):
  #change it so that it iterates through chars in char_offsets, not in audio_phonemes
  grouped_phonemes = []
  current_word = []
  word_index = 0
  char_index = 0
  next_word_index = 1
  word_reset_offset = int(word_offsets[word_index]['start_offset'])
  char_reset_offset = int(char_offsets[char_index]['start_offset'])
  # print("Word length",len(word_offsets))
  # for i, key in enumerate(char_offsets):
  #   print(f"Index: {i}, Key: {key}, Char: {key['char']}")
  while char_index < len(char_offsets) and word_index < len(word_offsets):
      # print(char_offsets[char_index]['char'])
      if next_word_index >= len(word_offsets) and char_index < len(char_offsets):
        current_word.append(char_offsets[char_index]['char'].replace("ː",""))
        # print(current_word)
        char_index += 1
      elif word_index < len(word_offsets) and char_index < len(char_offsets):
        word_start = int(word_offsets[word_index]['start_offset']) - word_reset_offset
        word_end = int(word_offsets[word_index]['end_offset']) - word_reset_offset
        next_word_start = int(word_offsets[next_word_index]['start_offset']) - word_reset_offset
        char_start = int(char_offsets[char_index]['start_offset']) - char_reset_offset
        char_end = int(char_offsets[char_index]['end_offset']) - char_reset_offset
        # print(char_start, ' ', word_end, ' ', next_word_start)
        if char_start >= word_start and char_start < next_word_start:
            current_word.append(char_offsets[char_index]['char'].replace("ː",""))
            # print(current_word)
            char_index += 1
        elif char_index < len(char_offsets) and char_start >= word_end:
            # print('bruh2')
            if current_word:
                grouped_phonemes.append(''.join(current_word))
                current_word = []
                word_index += 1
                next_word_index += 1
            else:
              break
  if current_word:
      # print('bruh3')
      grouped_phonemes.append(''.join(current_word))
  # print(len(grouped_phonemes))
  # print(grouped_phonemes)
      
  return grouped_phonemes
