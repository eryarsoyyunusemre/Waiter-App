import speech_recognition as sr
import openai
import psycopg2
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

# İndirme yöneticisini çalıştırarak NLTK için gereken veri kümelerini indiriyoruz
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

hostname = "localhost"
port = "5432"
database = "db"
username = "yunusemre"
password = "1950"

# OpenAI API anahtarınızı belirtin
openai.api_key = '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'

# Ses tanıma için Recognizer objesi oluşturun
r = sr.Recognizer()

# İlk olarak masa numarası ve müşteri adını alın ve süreyi 30 saniye olarak ayarlayın
with sr.Microphone() as source:
    print("Masa numarasını ve müşteri adını söyleyin...")
    audio = r.listen(source, timeout=30)

    try:
        # Sesli komutu tanıyın
        command = r.recognize_google(audio, language='tr-TR')
        text = command
        print("Alınan komut:", command)

        from nltk.tokenize import word_tokenize
        from nltk import pos_tag

        cumle = command
        kelimeler = word_tokenize(cumle)
        kelime_oznitelikleri = pos_tag(kelimeler)
        anahtar_kelimeler = [kelime[0] for kelime in kelime_oznitelikleri if kelime[1] == 'NNP']

        musteri_adi = ' '.join(
            [kelime for kelime in anahtar_kelimeler if kelime.lower() not in ['merhaba', 'selam', 'ismim', 'adım']])



        masa_no = None
        for i, kelime_ozniteligi in enumerate(kelime_oznitelikleri):
            kelime, oznitelik = kelime_ozniteligi
            if oznitelik == 'CD' and i < len(kelime_oznitelikleri) - 2 and kelime_oznitelikleri[i + 1][
                0] == 'numaralı' and kelime_oznitelikleri[i + 2][0] == 'masaya':
                masa_no = int(kelime)
                break

        print("Musteri adi:", musteri_adi)
        print("Masa no:", masa_no)




    except sr.UnknownValueError:
        print("Anlaşılamayan komut")
    except sr.RequestError:
        print("Google Speech Recognition servisi çalışmıyor")

# Şimdi ürün adı ve adetini alın ve süreyi 30 saniye olarak ayarlayın
with sr.Microphone() as source:
    print("Ürün adını ve adedini söyleyin...")
    audio = r.listen(source, timeout=30)

    try:
        # Sesli komutu tanıyın
        command = r.recognize_google(audio, language='tr-TR')
        text = command
        print("Alınan komut:", command)

        # GPT-3 API'sini kullanarak cevap alın
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=command,
            max_tokens=250,
            temperature=0.7,
            n=1,
            stop=None
        )
        conn = psycopg2.connect(
            host=hostname,
            port=port,
            database=database,
            user=username,
            password=password
        )


        # GPT-3 API'den gelen cevabı alın
        if 'choices' in response and len(response.choices) > 0:
            answer = response.choices[0].text.strip()
            print("GPT-3 API Cevabı:", answer)
        else:
            print("GPT-3 API'den cevap alınamadı.")

    except Exception as e:
        print("Bağlantı hatası:", e)

    cur = conn.cursor()

    cumle = command
    kelimeler = word_tokenize(cumle)
    kelime_oznitelikleri = pos_tag(kelimeler)
    anahtar_kelimeler = [kelime[0] for kelime in kelime_oznitelikleri if kelime[1] == 'NN']
    urunler = {}

    adet_indexleri = [i for i, kelime_ozniteligi in enumerate(kelime_oznitelikleri) if kelime_ozniteligi[1] == 'CD']
    for i in range(len(adet_indexleri)):
        adet_indexi = adet_indexleri[i]
        if i < len(adet_indexleri) - 1:
            sonraki_adet_indexi = adet_indexleri[i + 1]
        else:
            sonraki_adet_indexi = len(kelime_oznitelikleri)
        urun_adi = ' '.join([kelime for kelime in anahtar_kelimeler[adet_indexi + 1:sonraki_adet_indexi] if
                             kelime not in ['adet', 'istiyorum', 'tane', 'vermek', 'sipariş', 'etmek']])
        adet = int(kelime_oznitelikleri[adet_indexi][0])
        if urun_adi in urunler:
            urunler[urun_adi].append(adet)
        else:
            urunler[urun_adi] = [adet]



    query = "INSERT INTO siparisler (urun_adi, adet, musteri_adi, masa_no) VALUES (%s, %s, %s, %s)"
    data = (urun_adi,adet,musteri_adi,masa_no)
    cur.execute(query, data)


    conn.commit()
    cur.close()
    conn.close()

    print("Sipariş verildi!")