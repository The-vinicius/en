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
from docx import Document
from docx.shared import Inches
import os
import math

# id do video
id = sys.argv[1]


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



def separa(dados, n):
    table = []
    base = []
    
    for i, palavra in enumerate(dados):
        base.append(palavra)
        if (i+1) % n == 0:
            table.append(base)
            base = []

    return table




def salva_palavras(palavras, file):
    n = math.floor(math.sqrt(len(set(palavras))))

    if n > 8:
        n = 8

    data = separa(set(palavras), n)

    if os.path.isfile(file):
        doc = Document(file)
    else:
        doc = Document()
    # Adicionar uma tabela ao documento
    table = doc.add_table(rows=1, cols=n)
    for row_data in data:
        row_cells = table.add_row().cells
        for i, cell_data in enumerate(row_data):
            row_cells[i].text = cell_data
    doc.save(file)



salva_palavras(verbs, 'verbs.docx')
salva_palavras(adjectives, 'adjectives.docx')
salva_palavras(pronouns, 'pronouns.docx')
salva_palavras(noun, 'noun.docx')


