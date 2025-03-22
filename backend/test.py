import jiwer
from gruut import sentences
# reference = 'hɛloʊ wɚld'
# hypothesis = 'hɛlo ɜld'

# output = jiwer.process_words(reference, hypothesis)
# cer = jiwer.cer(reference, hypothesis)
# print(cer)

# Reference and hypothesis in IPA

ref_ipa = 'h aɪ w ɚ l d'
hyp_ipa = 'h ɛ l o ɜ l d'

# Convert IPA transcriptions into lists
# ref = ref_ipa.split()
# hyp = hyp_ipa.split()

# Calculate PER
phoneme_error_rate = jiwer.wer(hyp_ipa, ref_ipa)
print("Phoneme Error Rate:", phoneme_error_rate)

text = "shore"
output = []
output2 = []
  # using phonemizer
  # output = phonemize(text, 'en-us')
  # output = output.replace("ː", "") 
  
  #using gruut

for sent in sentences(text, lang="en-us", minor_breaks=False, major_breaks=False, punctuations=False, espeak=True):
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
          
print(output2)