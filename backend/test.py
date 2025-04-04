import jiwer
from gruut import sentences
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import librosa
import numpy as np
import torch
from scipy.signal import medfilt
import noisereduce as nr
import numpy as np
import sys

processor = Wav2Vec2Processor.from_pretrained("./model")
model = Wav2Vec2ForCTC.from_pretrained("./model")
sr = processor.feature_extractor.sampling_rate
input_values, _ = librosa.load('r7znxiuw2dfii7tuok9x.wav', sr=sr)
S_full, phase = librosa.magphase(librosa.stft(input_values))
noise_power = np.mean(S_full[:, :int(sr*0.1)], axis=1)
mask = S_full > noise_power[:, None]
mask = mask.astype(float)
mask = medfilt(mask, kernel_size=(1,5))
S_clean = S_full * mask
y_clean = librosa.istft(S_clean * phase)

y_clean2 = nr.reduce_noise(y=input_values, sr=sr, stationary=True)

inputsMedfilt = processor(y_clean, return_tensors="pt", padding=True)
inputsNoFilter = processor(input_values, return_tensors="pt", padding=True)
inputsNoiseReduce = processor(y_clean2, return_tensors="pt", padding=True)
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
  print(transcriptionstr)
  print(transcriptionstr2)
  return transcriptionstr, transcription.char_offsets[0], transcriptionstr2

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
  print(transcriptionstr)
  print(transcriptionstr2)
  return transcriptionstr, transcription.char_offsets[0], transcriptionstr2

# Example usage
reference_phonemes =[
  "ð",
  "ə",
  "b",
  "ɪ",
  "ɡ",
  "d",
  "ɔ",
  "ɡ",
  "k",
  "ə",
  "n",
  "ɹ",
  "ʌ",
  "n"
]
phonem1, offset, predicted_phonemes = audioToPhoneme(inputsMedfilt)
phonem2, offset2, predicted_phonemes2 = audioToPhoneme(inputsNoFilter)
phonem3, offset3, predicted_phonemes3 = audioToPhoneme(inputsNoiseReduce)


print("reference: ",' '.join(reference_phonemes))
print("predicted 1: ",' '.join(predicted_phonemes))
print("predicted 2: ",' '.join(predicted_phonemes2))
print("predicted 3: ",' '.join(predicted_phonemes3))

score_test = jiwer.wer(' '.join(reference_phonemes), ' '.join(predicted_phonemes))
score_test2 = jiwer.wer(' '.join(reference_phonemes), ' '.join(predicted_phonemes2))
score_test3 = jiwer.wer(' '.join(reference_phonemes), ' '.join(predicted_phonemes3))
score1 = 100- round(score_test*100, 2)
score2 = 100- round(score_test2*100, 2)
score3 = 100- round(score_test3*100, 2)

print(f"Phoneme Error Rate (PER) using WER: {score1:.2f}%")

print(f"Phoneme Error Rate (PER) using WER: {score2:.2f}%")

print(f"Phoneme Error Rate (PER) using WER: {score3:.2f}%")

# Get the best score among the three noise reduction methods
best_score = max(score1, score2, score3)
best_method = None

if best_score == score1:
    best_method = "Median Filtering"
elif best_score == score2:
    best_method = "No Filter (Raw Audio)"
elif best_score == score3:
    best_method = "NoiseReduce"

# Print the best method
print(f"\nBest Noise Reduction Method: {best_method} with {best_score:.2f}% accuracy")


