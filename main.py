import speech_recognition as sr
import openai
import psycopg2

hostname = "localhost"
port = "5432"
database = "db"
username = "yunusemre"
password = "1950"

# OpenAI API anahtarınızı belirtin
openai.api_key = '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'

# Ses tanıma için Recognizer objesi oluşturun
r = sr.Recognizer()

# Mikrofonu kullanarak ses alın ve süreyi 30 saniye olarak ayarlayın
with sr.Microphone() as source:
    print("Komut bekleniyor...")
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


        conn = psycopg2.connect(
            host=hostname,
            port=port,
            database=database,
            user=username,
            password=password
        )

        # Veritabanı bağlantısı üzerinde bir cursor oluşturma
        cursor = conn.cursor()

        query2 = "INSERT INTO genel_tablo (column1,column2) VALUES (%s,%s)"
        data = (text, answer)
        cursor.execute(query2, data)
        print("Sesli komut ve mantıklı cevap  başarıyla veritabanına eklendi.")

        # Değişiklikleri veritabanına kaydetme
        conn.commit()

        # Veritabanı bağlantısını kapatma
        cursor.close()
        conn.close()


    except sr.UnknownValueError:
        print("Anlaşılamayan komut")
    except sr.RequestError:
        print("Google Speech Recognition servisi çalışmıyor")
