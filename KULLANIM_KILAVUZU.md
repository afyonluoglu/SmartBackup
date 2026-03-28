# Smart Backup - Hızlı Başlangıç Kılavuzu

## Program Nasıl Çalıştırılır?

### Yöntem 1: Batch Dosyası ile (Önerilen)
1. `start_smartbackup.bat` dosyasına çift tıklayın
2. Gerekli kütüphane yoksa otomatik yükleme önerisi gelir
3. Program otomatik başlar

### Yöntem 2: Manuel Çalıştırma
1. Komut satırını açın
2. Klasöre gidin: `cd "c:\Users\ASUS\Desktop\Python with AI\SmartBackup"`
3. Çalıştırın: `python sm_main.py`

## 5 Dakikada Smart Backup Kullanımı

### Adım 1: İlk Projenizi Oluşturun
1. Sol üstteki **"Yeni Proje"** butonuna tıklayın
2. Proje adı girin (örn: "Belgelerim Yedekleme")
3. İsteğe bağlı açıklama ekleyin
4. **Tamam**'a tıklayın

### Adım 2: Eşleşme Ekleyin
1. Yeni oluşturduğunuz proje otomatik seçilecek
2. Sağ üstteki **"Yeni Eşleşme"** butonuna tıklayın
3. **Eşleşme İsmi**: Eşleşme için açıklayıcı bir isim verin (örn: "Belgeler", "Resimler") - Bu isim ana tabloda ve seçim diyaloglarında görünür
4. **Kaynak Klasör**: Yedeklemek istediğiniz klasörü seçin (örn: `C:\Users\YourName\Documents`)
5. **Dosya Filtresi**: (Birden fazla filtre, aralarına virgül konularak verilebilir)
   - `*.*` = Tüm dosyalar
   - `*.docx` = Sadece Word belgeleri
   - `*.pdf` = Sadece PDF dosyaları
   - `rapor*.xlsx` = "rapor" ile başlayan Excel dosyaları
6. **Alt klasörleri dahil et**: ✓ işaretleyin (alt klasörlerdeki dosyalar da dahil olur)
7. **Hedef Klasör**: Yedeklemenin kopyalanacağı yeri seçin (örn: `D:\Backups\Documents`)
8. **Yedeklenmeyecek dosyalar**: Yedeklemede hariç tutulmasını istediğiniz dosya filtresini girin. 
(Birden fazla filtre, aralarına virgül konularak verilebilir)
Örnek:
   *.db - Tüm .db uzantılı dosyaları hariç tut
   *.db, *.log - Hem .db hem .log dosyalarını hariç tut
   temp\*.* - temp klasöründeki tüm dosyaları hariç tut
   __pycache__\*.*, *.pyc - Python cache dosyalarını hariç tut
   deneme\*.* - deneme klasöründeki tüm dosyaları hariç tut
9. **Tamam**'a tıklayın

### Adım 3: Analiz Yapın
1. **"Analiz"** butonuna tıklayın
2. Kaç dosyanın yedekleneceğini ve toplam boyutu göreceksiniz
3. Bu işlem sadece bilgi verir, hiçbir şey kopyalanmaz

### Adım 4: Yedekleme Yapın
1. **"Yedekle"** butonuna tıklayın (yeşil buton)
2. Onay verin
3. İşlem sırasında:
   - İlerleme çubuğu gösterilir
   - Hangi dosyanın kopyalandığı görünür
   - İstatistikler anlık güncellenir
4. İşlem bitince özet rapor gösterilir
5. Yedeklemenin tüm aşamaları, işlem gören her dosya için ana ekrandaki takip penceresinde lisstelenir.

### Adım 5: Geçmişi Görüntüleyin
1. **"Geçmiş"** butonuna tıklayın
2. Tüm yedekleme işlemlerinizi görebilirsiniz
3. Bir kayda çift tıklayarak detayları görebilirsiniz. 

## Örnek Senaryo: Fotoğraflarım Yedekleme

**Amaç**: Telefondan bilgisayara aktardığım fotoğrafları harici diske yedeklemek

### Proje: "Fotoğraf Yedekleme"
- Açıklama: "Telefon fotoğraflarının aylık yedeği"

### Eşleşme 1: 2026 Fotoğrafları
- Kaynak: `C:\Users\User1\Pictures\2026`
- Filtre: `*.jpg` (sadece JPG fotoğraflar)
- Alt klasörler: ✓ Evet
- Hedef: `E:\Backups\Photos\2026`

### Eşleşme 2: Videolar
- Kaynak: `C:\Users\Mustafa\Videos\Phone`
- Filtre: `*.mp4` (sadece MP4 videolar)
- Alt klasörler: ✓ Evet
- Hedef: `E:\Backups\Videos\Phone`

**Sonuç**: Tek tıkla hem fotoğraflar hem videolar yedeklenir!

## Örnek Senaryo: İş Belgeleri

**Amaç**: Çalışma dosyalarımı her gün yedeklemek

### Proje: "Günlük İş Yedekleme"
- Açıklama: "Ofis bilgisayarı - günlük yedek"

### Eşleşme 1: Word Belgeleri
- Kaynak: `C:\Work\Documents`
- Filtre: `*.docx`
- Alt klasörler: ✓ Evet
- Hedef: `D:\WorkBackup\Documents`

### Eşleşme 2: Excel Tabloları
- Kaynak: `C:\Work\Spreadsheets`
- Filtre: `*.xlsx`
- Alt klasörler: ✓ Evet
- Hedef: `D:\WorkBackup\Spreadsheets`

### Eşleşme 3: Sunumlar
- Kaynak: `C:\Work\Presentations`
- Filtre: `*.pptx`
- Alt klasörler: ✓ Evet
- Hedef: `D:\WorkBackup\Presentations`

**Kullanım**: Her gün mesai sonunda "Yedekle" butonuna basmanız yeterli!

## Önemli Özellikler

### ⚡ Akıllı Kopyalama
- Sadece yeni dosyalar kopyalanır
- Değişmeyen dosyalar atlanır (zaman kazanır)
- Değişen dosyaların eski versiyonları REVISONS klasöründe tarihe göre korunur

### 📦 REVISIONS Klasörü
Bir dosyayı güncelleyip yeniden yedeklediğinizde:
- Eski versiyon `Hedef\REVISIONS\2025-11-19 14-30\` klasörüne taşınır
- Yeni versiyon normal yerine kopyalanır
- Böylece hem yeni hem eski versiyona sahip olursunuz!

### 🎨 Tema Desteği
- Sol alt köşeden Light/Dark/System seçebilirsiniz
- Tercihiniz kaydedilir

### ⌨️ Kısayollar
- **ESC**: Herhangi bir pencereyi kapatır
- **Çift Tıklama**: Eşleşmeyi düzenler

## İpuçları

### 💡 İpucu 1: Birden Fazla Proje
Farklı yedekleme senaryoları için ayrı projeler oluşturun:
- "Günlük Yedekleme"
- "Haftalık Tam Yedek"
- "Proje XYZ Arşivi"
- "Aile Fotoğrafları"

### 💡 İpucu 2: Filtreleme Gücü
Filtre örnekleri:
- `*.*` → Tüm dosyalar
- `*.doc*` → .doc ve .docx dosyaları
- `rapor*.*` → "rapor" ile başlayan tüm dosyalar
- `*2024*.*` → İsminde "2024" geçen dosyalar

Birden fazla filtre, aralarına virgül konularak verilebilir:
- `*.db, *.py` → veritabanı dosyaları ve python dosyaları 

### 💡 İpucu 3: Önce Analiz
Yedekleme yapmadan önce **Analiz** yapın:
- Kaç dosya kopyalanacağını görürsünüz
- Toplam boyutu öğrenirsiniz
- Hedefteki boş alanı kontrol edebilirsiniz

### 💡 İpucu 4: Geçmişi İnceleyin
- Geçmiş penceresinde tüm yedeklemeleriniz kayıtlı
- Her işlemin detaylarını görebilirsiniz
- Gereksiz kayıtları silebilirsiniz. (Birden fazla satırı seçerek toplu silme yapılabilir)

### 💡 İpucu 5: Düzenli Yedekleme
Smart Backup'ı favorilerinize ekleyin ve:
- Her gün aynı saatte çalıştırın
- Bir rutin oluşturun
- Veri kaybını önleyin!

## Sık Sorulan Sorular

**S: Yedekleme sırasında bilgisayar kapatılırsa ne olur?**
C: Kopyalanan dosyalar kaybolmaz. Bir sonraki yedeklemede kaldığı yerden devam eder.

**S: Aynı projeyi birden fazla kez yedekleyebilir miyim?**
C: Evet! Her yedekleme ayrı kayıt olarak tutulur ve geçmişte görünür.

**S: REVISIONS klasörü çok büyüdü, silebilir miyim?**
C: Evet, manuel olarak silebilirsiniz. Eski versiyonlara ihtiyacınız yoksa güvenle silin.

**S: İki bilgisayar arasında senkronizasyon yapabilir miyim?**
C: Smart Backup tek yönlü yedekleme yapar. İki yönlü senkronizasyon için kaynak ve hedefi ters çevirerek iki ayrı proje oluşturabilirsiniz.

**S: Veritabanı nerede?**
C: `smartbackup.db` dosyası program klasöründe. Yedeklemek isterseniz bu dosyayı kopyalayın.

## Sorun mu Yaşıyorsunuz?

### ❌ "CustomTkinter bulunamadı" hatası
```bash
pip install customtkinter
```

### ❌ "Dosya kopyalanamadı" hatası
- Hedef klasörün var olduğunu kontrol edin
- Yazma izniniz olduğundan emin olun
- Hedefte yeterli boş alan var mı?

### ❌ Program açılmıyor
- Python 3.7+ kullandığınızdan emin olun
- `python --version` ile kontrol edin

---

**Keyifli yedeklemeler!** 🎉

Dr. Mustafa Afyonluoğlu - Kasım 2025
