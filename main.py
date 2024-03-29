import speech_recognition as sr
import openai
import psycopg2
import nltk


# İndirme yöneticisini çalıştırarak NLTK için gereken veri kümelerini indiriyoruz
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

hostname = "*"
port = "*"
database = "*"
username = "*"
password = "*"

# OpenAI API anahtarınızı belirtin
openai.api_key = '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'

# Ses tanıma için Recognizer objesi oluşturun
r = sr.Recognizer()

conn = psycopg2.connect(
    host=hostname,
    port=port,
    database=database,
    user=username,
    password=password
)

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
            [kelime for kelime in anahtar_kelimeler if
             kelime.lower() not in ['merhaba', 'selam', 'ismim', 'adım', 'ben']])

        masa_no = None
        for i, kelime_ozniteligi in enumerate(kelime_oznitelikleri):
            kelime, oznitelik = kelime_ozniteligi
            if oznitelik == 'CD' and i < len(kelime_oznitelikleri) - 2 and kelime_oznitelikleri[i + 1][
                0] == 'numaralı' and kelime_oznitelikleri[i + 2][0] == 'masaya':
                masa_no = int(kelime)
                break

        print("Musteri adi:", musteri_adi)
        print("Masa no:", masa_no)
        print(command)

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

        # GPT-3 API'den gelen cevabı alın
        if 'choices' in response and len(response.choices) > 0:
            answer = response.choices[0].text.strip()
            print("GPT-3 API Cevabı:", answer)
        else:
            print("GPT-3 API'den cevap alınamadı.")

    except Exception as e:
        print("Bağlantı hatası:", e)

    cur = conn.cursor()
    cümle = command

    # Cümleyi kelimelere ayırın ve her kelimenin özniteliklerini bulun
    kelimeler = nltk.word_tokenize(cümle)
    kelime_oznitelikleri = nltk.pos_tag(kelimeler)

    # Boş bir sözlük oluşturun
    urunler = []

    # Değişkenleri tanımlayın
    adet = None
    urun_adi = None

    # Kelime öznitelikleri listesinde dolaşın
    for kelime, oznitelik in kelime_oznitelikleri:
        # Sayısal bir değer bulunursa, adet değerini kaydedin
        if oznitelik == 'CD':
            adet = int(kelime)
        # İsim veya isim öbeği bulunursa, ürün adını kaydedin
        elif oznitelik.startswith('NN'):
            urun_adi = kelime
        # Her iki değişken de doluysa, ürünü listeye ekleyin ve değişkenleri sıfırlayın
        if adet is not None and urun_adi is not None:
            urunler.append((adet, urun_adi))
            adet = None
            urun_adi = None

    # Ürünleri yazdırın
    for i, (adet, urun_adi) in enumerate(urunler, start=1):
        print(f"Ürün {i}: {adet} adet {urun_adi}")

    sorgu = "INSERT INTO urunler (urun_adi, adet, musteri_adi, masa_no) VALUES (%s, %s, %s, %s)"

    for i, (adet, urun_adi) in enumerate(urunler, start=1):
        veriler = (urun_adi, adet, musteri_adi, masa_no)
        cur.execute(sorgu, veriler)

    conn.commit()

    print(urun_adi)
    print(adet)

    cur.close()
    conn.close()

    print("Sipariş verildi!")
