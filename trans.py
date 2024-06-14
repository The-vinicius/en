from youtube_transcript_api import YouTubeTranscriptApi
import sys
from collections import Counter
import re
# from sklearn.feature_extraction.text import TfidfVectorizer
from nltk import pos_tag, word_tokenize, download
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.probability import FreqDist
from nltk.tokenize import sent_tokenize
import requests
from datetime import datetime, timezone
import aiohttp
import asyncio

# id do video
id = sys.argv[1]
# nome do arquivo txt
file = sys.argv[2]


# Função para obter a data e hora atual no formato ISO 8601 com sufixo 'Z'
def get_iso8601_utc_now():
    now_utc = datetime.now(timezone.utc)
    iso_format_utc = now_utc.isoformat(timespec='milliseconds')
    iso_format_utc = iso_format_utc.replace('+00:00', '') + 'Z'
    return iso_format_utc

# Função assíncrona para fazer a requisição GET para uma palavra
async def fetch_example(session, word):
    base_url = "https://www.wordsapi.com/mashape/words"
    endpoint = f"{base_url}/{word}/examples"
    params = {
        "when": "2024-06-08T13:08:00.752Z",
        "encrypted": "8cfdb18ee722959bea9907beec58beb1aeb02d0937fa95b8"
    }
    async with session.get(endpoint, params=params) as response:
        if response.status == 200:
            data = await response.json()
            with open(file, "a") as f:
                f.write(f'{word}\n')
                for i, example in enumerate(data['examples']):
                    f.write(f'{i+1} - {example}\n')
                f.write('\n\n')
                f.close()
        else:
            return word, {"error": f"Failed to retrieve data: {response.status}"}

# Função principal para iterar sobre a lista de palavras e fazer as requisições
async def fetch_examples_for_words(words, tipo):
    with open(file, "a") as f:
        f.write(f'*******{tipo}*******\n')

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_example(session, word) for word in words]
        await asyncio.gather(*tasks)
                    


srt = YouTubeTranscriptApi.get_transcript(str(id), languages=['en'])

texto = ''

for text in srt:
    texto = texto + text['text'] 


def remove_special_characters(text):
    # Substituir \xa0\n e \xa0\xa0 por espaços
    cleaned_text = re.sub(r'[\xa0\n]+', ' ', text)
    return cleaned_text


#removendo caracteris especiais
texto = remove_special_characters(texto)

# Pré-processamento do texto
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalnum()]
    tokens = [token for token in tokens if token not in stop_words]
    return ' '.join(tokens)


def split_sentences(text, max_words_per_sentence):
    sentences = sent_tokenize(text)
    split_sentences = []
    
    for sentence in sentences:
        words = word_tokenize(sentence)
        for i in range(0, len(words), max_words_per_sentence):
            split_sentences.append(' '.join(words[i:i+max_words_per_sentence]))
    
    return split_sentences

#obter as sentenças mais importamtes
def find_most_important_sentences(text, max_words_per_sentence, num_sentences):
    sentences = split_sentences(text, max_words_per_sentence)
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]

    sentence_scores = {}
    for sentence in sentences:
        sentence_words = word_tokenize(sentence.lower())
        sentence_words = [word for word in sentence_words if word.isalnum() and word not in stop_words]
        sentence_word_count = len(sentence_words)
        sentence_word_freq = Counter(sentence_words)
        sentence_score = sum(sentence_word_freq[word] for word in sentence_word_freq) / sentence_word_count if sentence_word_count > 0 else 0
        sentence_scores[sentence] = sentence_score

    top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
    return top_sentences

preprocessed_text = preprocess_text(texto)

# Tokenização e extração de partes do discurso
pos_tags = pos_tag(word_tokenize(preprocessed_text))


# Inicializar listas para armazenar verbos, adjetivos e pronomes
verbs = []
adjectives = []
pronouns = []
noun = []

# Filtrar por partes do discurso desejadas (verbos, adjetivos, pronomes)
for token, pos in pos_tags:
    if pos.startswith('VB'):
        verbs.append(token)
    elif pos.startswith('JJ'):
        adjectives.append(token)
    elif pos.startswith('PRP'):
        pronouns.append(token)
    elif pos.startswith('NN'):
        noun.append(token)

# important_sentences = find_most_important_sentences(texto, 20, 20)
# sentences = sent_tokenize(texto)
# for sentence in important_sentences:
#     print(sentence)
#     print('/'*30)
# Imprimir os verbos, adjetivos e pronomes separadamente
# print("Verbos:")
# print(set(verbs))
#
# print("\nAdjetivos:")
# print(set(adjectives))
#
# print("\nPronomes:")
# print(set(pronouns))
#
# print("\nNoun:")
# print(set(noun))

# Cálculo do TF-IDF
# tfidf = TfidfVectorizer()
# tfidf_matrix = tfidf.fit_transform([preprocessed_text])

# Imprimir os tokens e seus valores TF-IDF
# feature_names = tfidf.get_feature_names_out()
# for i in range(len(feature_names)):
#     if feature_names[i] in verbs:
#         print(f"{feature_names[i]}: {tfidf_matrix[0, i]}")

# Encontrar palavras que se repetem pelo menos três vezes
# palavras = re.findall(r'\b\w+\b', texto.lower())
contagem_verbs = Counter(verbs)
contagem_adj = Counter(adjectives)
contagem_pron = Counter(pronouns)
contagem_noun = Counter(noun)




# Filtrar palavras que se repetem pelo menos três vezes
verbs_repetidas = [palavra for palavra, contagem in contagem_verbs.items() if contagem == 3]
adj_repetidas = [palavra for palavra, contagem in contagem_adj.items() if contagem == 3]
pron_repetidas = [palavra for palavra, contagem in contagem_pron.items() if contagem == 3]
noun_repetidas = [palavra for palavra, contagem in contagem_noun.items() if contagem == 3]

# Imprimir as palavras que se repetem pelo menos três vezes

asyncio.run(fetch_examples_for_words(verbs_repetidas, 'verbos'))
asyncio.run(fetch_examples_for_words(adj_repetidas, 'adjectives'))
asyncio.run(fetch_examples_for_words(pron_repetidas, 'pronouns'))
asyncio.run(fetch_examples_for_words(noun_repetidas, 'noun'))
