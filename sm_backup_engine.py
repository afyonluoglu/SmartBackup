"""
Smart Backup - Backup Engine
Tarih: 19 Kasım 2025
Yazar: Dr. Mustafa Afyonluoğlu

Gerekli Kütüphaneler:
    - os (standart kütüphane)
    - shutil (standart kütüphane)
    - glob (standart kütüphane)
    - datetime (standart kütüphane)
    - pathlib (standart kütüphane)
"""

import os
import shutil
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Callable, Optional


class BackupEngine:
    """Yedekleme işlemlerini gerçekleştiren motor sınıfı"""
    
    def __init__(self):
        self.cancelled = False
        self.progress_callback = None
        self.status_callback = None
    
    def set_progress_callback(self, callback: Callable[[float], None]):
        """İlerleme callback'ini ayarla
        
        Args:
            callback: İlerleme yüzdesi alan fonksiyon (0.0 - 1.0)
        """
        self.progress_callback = callback
    
    def set_status_callback(self, callback: Callable[[str], None]):
        """Durum mesajı callback'ini ayarla
        
        Args:
            callback: Durum mesajı alan fonksiyon
        """
        self.status_callback = callback
    
    def cancel(self):
        """İşlemi iptal et"""
        self.cancelled = True
    
    def reset_cancel(self):
        """İptal bayrağını sıfırla"""
        self.cancelled = False
    
    def get_files_from_mapping(self, source_path: str, file_filter: str, 
                               exclude_filter: str, include_subdirs: bool) -> List[str]:
        """Eşleşmeye göre dosya listesi oluştur
        
        Args:
            source_path: Kaynak klasör
            file_filter: Dosya filtresi (örn: *.*, *.doc*, abc*.txt veya virgülle ayrılmış: *.py, *.txt)
            exclude_filter: Hariç tutulacak dosya filtresi (örn: *.db, temp\\*.* )
            include_subdirs: Alt klasörleri dahil et
            
        Returns:
            Dosya yollarının listesi
        """
        files = []
        
        # Yolu normalize et ve kontrol et
        source_path = os.path.normpath(source_path)
        
        if not os.path.exists(source_path):
            if self.status_callback:
                self.status_callback(f"UYARI: Kaynak klasör bulunamadı: {source_path}")
            return files
        
        if not os.path.isdir(source_path):
            if self.status_callback:
                self.status_callback(f"UYARI: Kaynak yol bir klasör değil: {source_path}")
            return files
        
        # File filter'ı virgülle ayır (birden fazla pattern destekle)
        filter_patterns = [p.strip() for p in file_filter.split(',') if p.strip()]
        if not filter_patterns:
            filter_patterns = ['*.*']  # Varsayılan: tüm dosyalar
        
        # Her pattern için dosyaları topla
        all_files = set()  # Tekrar etmemeleri için set kullan
        for pattern in filter_patterns:
            if include_subdirs:
                # Alt klasörler dahil
                full_pattern = os.path.join(source_path, '**', pattern)
                matched = glob.glob(full_pattern, recursive=True)
            else:
                # Sadece ana klasör
                full_pattern = os.path.join(source_path, pattern)
                matched = glob.glob(full_pattern, recursive=False)
            
            all_files.update(matched)
        
        # Sadece dosyaları al (klasörleri değil)
        files = [f for f in all_files if os.path.isfile(f)]
        
        # Exclude filter uygula
        if exclude_filter:
            files = self._apply_exclude_filter(files, source_path, exclude_filter, include_subdirs)
        
        return files
    
    def _apply_exclude_filter(self, files: List[str], source_path: str, 
                              exclude_filter: str, include_subdirs: bool) -> List[str]:
        """Exclude filter uygula
        
        Args:
            files: Dosya listesi
            source_path: Kaynak klasör
            exclude_filter: Hariç tutulacak dosya filtresi (virgülle ayrılmış)
                          Pattern örnekleri:
                          - "*.zip" -> tüm zip dosyaları  
                          - "__pycache__\\*.*" -> her seviyedeki __pycache__ klasörü (recursive modda)
                          - "temp\\*.*" -> temp klasöründeki tüm dosyalar (relative)
                          - "**\\*.log" -> tüm alt klasörlerdeki log dosyaları (explicit)
                          - "SmartBackup\\TEST_MAIN\\*.*" -> belirli klasördeki dosyalar
            include_subdirs: Alt klasörleri dahil et
            
        Returns:
            Filtrelenmiş dosya listesi
        """
        if not exclude_filter:
            return files
        
        # Virgülle ayrılmış filtreleri ayır
        exclude_patterns = [p.strip() for p in exclude_filter.split(',') if p.strip()]
        
        excluded_files = set()
        
        for pattern in exclude_patterns:
            # Tam yol mu yoksa relative pattern mı kontrol et
            if os.path.isabs(pattern) or ':' in pattern:
                # Tam yol - direkt glob kullan
                matched = glob.glob(pattern, recursive=True)
            else:
                # Relative pattern - source_path'e ekle
                if '**' in pattern:
                    # Zaten ** var, direkt ekle
                    full_pattern = os.path.join(source_path, pattern)
                    matched = glob.glob(full_pattern, recursive=True)
                else:
                    # ** yok
                    if include_subdirs:
                        # Alt klasörlerde ara - ** ekle
                        # Örnek: "__pycache__\*.*" -> "source_path\**\__pycache__\*.*"
                        # Bu her seviyedeki __pycache__ klasörlerini bulur
                        full_pattern = os.path.join(source_path, '**', pattern)
                        matched = glob.glob(full_pattern, recursive=True)
                    else:
                        # Sadece direkt alt klasörde
                        full_pattern = os.path.join(source_path, pattern)
                        matched = glob.glob(full_pattern, recursive=False)
            
            excluded_files.update(matched)
        
        # Hariç tutulanları çıkar
        return [f for f in files if f not in excluded_files]
    
    def calculate_mapping_stats(self, source_path: str, file_filter: str,
                                exclude_filter: str, include_subdirs: bool) -> Tuple[int, int, int, int]:
        """Eşleşme istatistiklerini hesapla
        
        Args:
            source_path: Kaynak klasör
            file_filter: Dosya filtresi
            exclude_filter: Hariç tutulacak dosya filtresi
            include_subdirs: Alt klasörleri dahil et
            
        Returns:
            (dosya_sayısı, toplam_boyut, hariç_tutulan_sayı, hariç_tutulan_boyut) tuple'ı
        """
        if self.status_callback:
            self.status_callback(f"Analiz ediliyor: {source_path}")
        
        # Yolu normalize et
        source_path = os.path.normpath(source_path)
        
        # Önce tüm dosyaları al (exclude olmadan) - get_files_from_mapping ile aynı mantıkla
        filter_patterns = [p.strip() for p in file_filter.split(',') if p.strip()]
        if not filter_patterns:
            filter_patterns = ['*.*']
        
        all_files_set = set()
        for pattern in filter_patterns:
            if include_subdirs:
                full_pattern = os.path.join(source_path, '**', pattern)
                matched = glob.glob(full_pattern, recursive=True)
            else:
                full_pattern = os.path.join(source_path, pattern)
                matched = glob.glob(full_pattern, recursive=False)
            all_files_set.update(matched)
        
        all_files = [f for f in all_files_set if os.path.isfile(f)]
        
        # Gizli klasörlerdeki dosyaları da say
        hidden_files_count = 0
        hidden_files_size = 0
        
        if include_subdirs:
            for root, dirs, filenames in os.walk(source_path):
                for dirname in dirs[:]:
                    if dirname.startswith('.'):
                        hidden_dir_path = os.path.join(root, dirname)
                        for hidden_root, _, hidden_filenames in os.walk(hidden_dir_path):
                            for hidden_file in hidden_filenames:
                                hidden_file_path = os.path.join(hidden_root, hidden_file)
                                if os.path.isfile(hidden_file_path):
                                    hidden_files_count += 1
                                    try:
                                        hidden_files_size += os.path.getsize(hidden_file_path)
                                    except:
                                        pass
                        dirs.remove(dirname)
        
        # Sonra exclude'lu dosyaları al
        files = self.get_files_from_mapping(source_path, file_filter, exclude_filter, include_subdirs)
        
        # Hariç tutulanları bul
        excluded_files = [f for f in all_files if f not in files]
        
        total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
        excluded_size = sum(os.path.getsize(f) for f in excluded_files if os.path.exists(f)) + hidden_files_size
        
        return len(files), total_size, len(excluded_files) + hidden_files_count, excluded_size
    
    def analyze_mapping(self, source_path: str, file_filter: str,
                       exclude_filter: str, include_subdirs: bool, target_path: str) -> Tuple[int, int, int, int]:
        """Eşleşme için yedeklenecek dosyaları analiz et
        
        Args:
            source_path: Kaynak klasör
            file_filter: Dosya filtresi
            exclude_filter: Hariç tutulacak dosya filtresi
            include_subdirs: Alt klasörleri dahil et
            target_path: Hedef klasör
            
        Returns:
            (yedeklenecek_dosya_sayısı, yedeklenecek_toplam_boyut, hariç_tutulan_sayı, hariç_tutulan_boyut) tuple'ı
        """
        # Yolu normalize et
        source_path = os.path.normpath(source_path)
        target_path = os.path.normpath(target_path)
        
        # Önce tüm dosyaları al (exclude olmadan) - get_files_from_mapping ile aynı mantıkla
        filter_patterns = [p.strip() for p in file_filter.split(',') if p.strip()]
        if not filter_patterns:
            filter_patterns = ['*.*']
        
        all_files_set = set()
        for pattern in filter_patterns:
            if include_subdirs:
                full_pattern = os.path.join(source_path, '**', pattern)
                matched = glob.glob(full_pattern, recursive=True)
            else:
                full_pattern = os.path.join(source_path, pattern)
                matched = glob.glob(full_pattern, recursive=False)
            all_files_set.update(matched)
        
        all_files = [f for f in all_files_set if os.path.isfile(f)]
        
        # Sonra exclude'lu dosyaları al
        files = self.get_files_from_mapping(source_path, file_filter, exclude_filter, include_subdirs)
        
        # Hariç tutulanları bul
        excluded_files = [f for f in all_files if f not in files]
        excluded_size = sum(os.path.getsize(f) for f in excluded_files if os.path.exists(f))
        
        files_to_backup = []
        total_size = 0
        
        for source_file in files:
            if not os.path.exists(source_file):
                continue
            
            # Hedef dosya yolunu oluştur
            rel_path = os.path.relpath(source_file, source_path)
            target_file = os.path.join(target_path, rel_path)
            
            # Hedefte yoksa veya daha yeni ise yedekle
            if not os.path.exists(target_file):
                files_to_backup.append(source_file)
                total_size += os.path.getsize(source_file)
            else:
                # Tarih karşılaştırması
                source_mtime = os.path.getmtime(source_file)
                target_mtime = os.path.getmtime(target_file)
                if source_mtime > target_mtime:
                    files_to_backup.append(source_file)
                    total_size += os.path.getsize(source_file)
        
        return len(files_to_backup), total_size, len(excluded_files), excluded_size
    
    def analyze_mapping_detailed(self, source_path: str, file_filter: str,
                                 exclude_filter: str, include_subdirs: bool, target_path: str, max_files_to_show) -> Dict:
        """Eşleşme için yedeklenecek dosyaları detaylı analiz et
        
        Args:
            source_path: Kaynak klasör
            file_filter: Dosya filtresi
            exclude_filter: Hariç tutulacak dosya filtresi
            include_subdirs: Alt klasörleri dahil et
            target_path: Hedef klasör
            
        Returns:
            {
                'files_to_backup': [dosya_listesi],
                'files_to_skip': [dosya_listesi],
                'excluded_count': hariç_tutulan_dosya_sayısı,
                'skipped_count': atlanan_dosya_sayısı,
                'total_size': toplam_boyut,
                'excluded_size': hariç_tutulan_boyut,
                'skipped_size': atlanan_dosya_boyutu
            }
        """

        # Yolu normalize et
        source_path = os.path.normpath(source_path)
        target_path = os.path.normpath(target_path)
        
        # Önce glob ile bulunan dosyaları al (exclude olmadan)
        filter_patterns = [p.strip() for p in file_filter.split(',') if p.strip()]
        if not filter_patterns:
            filter_patterns = ['*.*']
        
        all_files_set = set()
        for pattern in filter_patterns:
            if include_subdirs:
                full_pattern = os.path.join(source_path, '**', pattern)
                matched = glob.glob(full_pattern, recursive=True)
            else:
                full_pattern = os.path.join(source_path, pattern)
                matched = glob.glob(full_pattern, recursive=False)
            all_files_set.update(matched)
        
        all_files = [f for f in all_files_set if os.path.isfile(f)]
        
        # Gizli klasörlerdeki dosyaları da say (glob bunları atlar)
        # .git, .vscode gibi klasörler glob tarafından görmezden gelinir
        hidden_files_count = 0
        hidden_files_size = 0
        hidden_files_list = []  # Gizli dosyaların listesi
        
        if include_subdirs:
            # os.walk ile tüm dosyaları tara (gizli klasörler dahil)
            for root, dirs, filenames in os.walk(source_path):
                # Gizli klasörleri kontrol et
                for dirname in dirs[:]:  # [:] ile kopya oluştur, güvenli silme için
                    if dirname.startswith('.'):
                        # Gizli klasör - dosyalarını say
                        hidden_dir_path = os.path.join(root, dirname)
                        for hidden_root, _, hidden_filenames in os.walk(hidden_dir_path):
                            for hidden_file in hidden_filenames:
                                hidden_file_path = os.path.join(hidden_root, hidden_file)
                                if os.path.isfile(hidden_file_path):
                                    hidden_files_count += 1
                                    hidden_files_list.append(hidden_file_path)  # Listeye ekle
                                    try:
                                        hidden_files_size += os.path.getsize(hidden_file_path)
                                    except:
                                        pass
                        # Bu klasöre girme (zaten saydık)
                        dirs.remove(dirname)
        
        # Sonra exclude'lu dosyaları al
        files = self.get_files_from_mapping(source_path, file_filter, exclude_filter, include_subdirs)
        
        # Hariç tutulanları 2 gruba ayır:
        # 1. Kullanıcı tanımlı exclude filtresi ile hariç tutulanlar
        # 2. Gizli klasörlerde olduğu için hariç tutulanlar
        
        # Kullanıcı tanımlı exclude ile hariç tutulanlar
        user_excluded_files_set = set(all_files) - set(files)
        user_excluded_files_list = list(user_excluded_files_set)[:max_files_to_show]
        user_excluded_count = len(user_excluded_files_set)
        user_excluded_size = sum(os.path.getsize(f) for f in user_excluded_files_set if os.path.exists(f))
        
        # Gizli klasör dosyalarının listesi (ilk N tanesi)
        hidden_excluded_files_list = hidden_files_list[:max_files_to_show]
        
        # Toplam hariç tutulanlar
        total_excluded_count = user_excluded_count + hidden_files_count
        total_excluded_size = user_excluded_size + hidden_files_size
        
        # _REVISIONS klasöründeki dosyaları say ve listele
        revision_count = 0
        revision_size = 0
        revision_files_list = []  # Revision dosyalarının detaylı listesi
        revisions_path = os.path.join(target_path, '_REVISIONS')
        
        if os.path.exists(revisions_path):
            try:
                for root, dirs, filenames in os.walk(revisions_path):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        if os.path.isfile(file_path):
                            revision_count += 1
                            try:
                                file_size = os.path.getsize(file_path)
                                revision_size += file_size
                                
                                # Tarih-saat klasörünü bul (_REVISIONS\20251122_143020 gibi)
                                # file_path örnek: D:\Backup\_REVISIONS\20251122_143020\project\file.txt
                                # revisions_path örnek: D:\Backup\_REVISIONS
                                rel_to_revisions = os.path.relpath(file_path, revisions_path)
                                # rel_to_revisions: 20251122_143020\project\file.txt
                                parts = rel_to_revisions.split(os.sep)
                                timestamp_folder = parts[0] if parts else "Unknown"
                                
                                # İlk 50 dosyayı sakla
                                if len(revision_files_list) < max_files_to_show:
                                    revision_files_list.append({
                                        'path': file_path,
                                        'size': file_size,
                                        'timestamp_folder': timestamp_folder
                                    })
                            except:
                                pass
            except Exception as e:
                # Erişim hatası durumunda sessizce devam et
                pass
        
        # Hedefte olup kaynakta olmayan dosyaları tespit et (silinmiş dosyalar)
        deleted_files_list = []  # Görüntülemek için (ilk N tane)
        deleted_files_all = []   # Yedekleme işlemi için (tümü)
        deleted_count = 0
        deleted_size = 0
        
        if os.path.exists(target_path):
            try:
                # DEBUG: Log dosyası oluştur
                debug_log_path = os.path.join(os.path.dirname(__file__), 'debug_deleted_files.txt')
               
                # Hedef klasördeki dosyaları tara (exclude _REVISIONS klasörü)
                for root, dirs, filenames in os.walk(target_path):

                    
                    # ÖNCELİKLE: root path'ini klasör isimlerine ayırarak _REVISIONS kontrolü yap
                    path_parts = root.split(os.sep)
                    
                    if '_REVISIONS' in path_parts:
                        continue  # Bu klasör _REVISIONS altındaysa atla
                    
                    # İKİNCİL: Alt klasörlerden _REVISIONS'ı çıkar
                    if '_REVISIONS' in dirs:
                        dirs.remove('_REVISIONS')
                    
                    for filename in filenames:
                        target_file = os.path.join(root, filename)
                        
                        # ÜÇÜNCÜL: Güvenlik kontrolü - path component olarak kontrol
                        target_parts = target_file.split(os.sep)
                        if '_REVISIONS' in target_parts:
                            continue
                        
                        # Hedef dosyanın kaynak karşılığını bul
                        rel_path = os.path.relpath(target_file, target_path)
                        source_file = os.path.join(source_path, rel_path)
                        
                        # Kaynakta yoksa, silinmiş demektir
                        if not os.path.exists(source_file):
                            deleted_count += 1
                            try:
                                file_size = os.path.getsize(target_file)
                                deleted_size += file_size
                                
                                file_info = {
                                    'path': target_file,
                                    'size': file_size
                                }
                                
                                # Tüm silinen dosyaları kaydet (yedekleme için)
                                deleted_files_all.append(file_info)
                                
                                # İlk N tanesini görüntüleme listesine ekle
                                if len(deleted_files_list) < max_files_to_show:
                                    deleted_files_list.append(file_info)
                            except:
                                pass
                                    
                # print(f"[DEBUG] Log dosyası kaydedildi: {debug_log_path}")
            except Exception as e:
                # Erişim hatası durumunda sessizce devam et
                pass
        
        files_to_backup = []
        files_to_skip = []
        skipped_files_list = []  
        total_size = 0
        skipped_count = 0
        skipped_size = 0
        
        # İlerleme mesajı
        # if self.status_callback:
        #    self.status_callback(f"🟢 : {source_path} : {len(files)} dosya kontrol ediliyor...")

        for source_file in files:
            if not os.path.exists(source_file):
                continue
            
            file_size = os.path.getsize(source_file)
            
            # Hedef dosya yolunu oluştur
            rel_path = os.path.relpath(source_file, source_path)
            target_file = os.path.join(target_path, rel_path)
            
            # Hedefte yoksa veya daha yeni ise yedekle
            if not os.path.exists(target_file):
                # YENİ: Neden bilgisi ekle
                file_info = {
                    'path': source_file,
                    'size': file_size,
                    'reason': 'yeni dosya',
                    'source_mtime': os.path.getmtime(source_file),
                    'target_mtime': None
                }
                files_to_backup.append(file_info)
                total_size += file_size
            else:
                # Tarih karşılaştırması
                source_mtime = os.path.getmtime(source_file)
                target_mtime = os.path.getmtime(target_file)
                if source_mtime > target_mtime:
                    # YENİ: Tarih farkı bilgisi ekle
                    from datetime import datetime
                    source_dt = datetime.fromtimestamp(source_mtime)
                    target_dt = datetime.fromtimestamp(target_mtime)
                    
                    file_info = {
                        'path': source_file,
                        'size': file_size,
                        'reason': 'daha yeni',
                        'source_mtime': source_mtime,
                        'target_mtime': target_mtime,
                        'source_date': source_dt.strftime('%Y-%m-%d %H:%M:%S'),
                        'target_date': target_dt.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    files_to_backup.append(file_info)
                    total_size += file_size
                else:
                    # Dosya güncel, atlandı
                    files_to_skip.append(source_file)
                    if len(skipped_files_list) < max_files_to_show: 
                        skipped_files_list.append(source_file)
                    skipped_count += 1
                    skipped_size += file_size
        
        return {
            'files_to_backup': files_to_backup,
            'files_to_skip': files_to_skip,
            'skipped_files': skipped_files_list,
            # Kullanıcı tanımlı exclude ile hariç tutulanlar
            'user_excluded_files': user_excluded_files_list,
            'user_excluded_count': user_excluded_count,
            'user_excluded_size': user_excluded_size,
            # Gizli klasör dosyaları
            'hidden_excluded_files': hidden_excluded_files_list,
            'hidden_excluded_count': hidden_files_count,
            'hidden_excluded_size': hidden_files_size,
            # Toplam hariç tutulanlar
            'total_excluded_count': total_excluded_count,
            'total_excluded_size': total_excluded_size,
            'skipped_count': skipped_count,
            'total_size': total_size,
            'skipped_size': skipped_size,
            'revision_count': revision_count,
            'revision_size': revision_size,
            'revision_files': revision_files_list,
            # Silinmiş dosyalar
            'deleted_files': deleted_files_list,        # Görüntüleme için (ilk N tane)
            'deleted_files_all': deleted_files_all,     # Yedekleme için (tümü)
            'deleted_count': deleted_count,
            'deleted_size': deleted_size
        }
    
    def backup_mapping(self, source_path: str, file_filter: str,
                      exclude_filter: str, include_subdirs: bool, target_path: str) -> Dict:
        """Tek bir eşleşme için yedekleme yap
        
        Args:
            source_path: Kaynak klasör
            file_filter: Dosya filtresi
            exclude_filter: Hariç tutulacak dosya filtresi
            include_subdirs: Alt klasörleri dahil et
            target_path: Hedef klasör
            
        Returns:
            {
                'files_copied': int,
                'files_moved_to_revisions': int,
                'files_skipped': int,
                'size_copied': int,
                'size_moved': int,
                'size_skipped': int
            }
        """
        stats = {
            'files_copied': 0,
            'files_moved_to_revisions': 0,
            'files_skipped': 0,
            'size_copied': 0,
            'size_moved': 0,
            'size_skipped': 0
        }
        
        files = self.get_files_from_mapping(source_path, file_filter, exclude_filter, include_subdirs)
        
        for source_file in files:
            if self.cancelled:
                break
            
            if not os.path.exists(source_file):
                continue
            
            # Hedef dosya yolunu oluştur
            rel_path = os.path.relpath(source_file, source_path)
            target_file = os.path.join(target_path, rel_path)
            
            # Dosya boyutu
            file_size = os.path.getsize(source_file)
            
            # Hedef klasörü oluştur
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # Hedefte dosya var mı kontrol et
            if os.path.exists(target_file):
                source_mtime = os.path.getmtime(source_file)
                target_mtime = os.path.getmtime(target_file)
                
                if source_mtime > target_mtime:
                    # Hedef dosya daha eski, REVISIONS'a taşı
                    revision_folder = self._create_revision_folder(target_path)
                    revision_file = os.path.join(revision_folder, rel_path)
                    
                    # Revision klasörünü oluştur
                    print(f"Creating revision folder: {os.path.dirname(revision_file)}")
                    os.makedirs(os.path.dirname(revision_file), exist_ok=True)
                    
                    # Eski dosyayı taşı
                    shutil.move(target_file, revision_file)
                    stats['files_moved_to_revisions'] += 1
                    stats['size_moved'] += file_size
                    
                    # Yeni dosyayı kopyala
                    shutil.copy2(source_file, target_file)
                    stats['files_copied'] += 1
                    stats['size_copied'] += file_size
                    
                    if self.status_callback:
                        size_str = self.format_size(file_size)
                        self.status_callback(f"✓ Kopyalandı (eski sürüm arşivlendi): {os.path.basename(source_file)} ({size_str})")
                else:
                    # Dosyalar aynı veya hedef daha yeni, atla
                    stats['files_skipped'] += 1
                    stats['size_skipped'] += file_size
                    
                    if self.status_callback:
                        size_str = self.format_size(file_size)
                        # Mustafa self.status_callback(f"○ Atlandı (değişiklik yok): {os.path.basename(source_file)} ({size_str})")
            else:
                # Hedefte dosya yok, direkt kopyala
                shutil.copy2(source_file, target_file)
                stats['files_copied'] += 1
                stats['size_copied'] += file_size
                
                if self.status_callback:
                    size_str = self.format_size(file_size)
                    self.status_callback(f"✓ Kopyalandı (yeni): {os.path.basename(source_file)} ({size_str})")
        
        return stats
    
    def backup_from_analysis(self, source_path: str, target_path: str, 
                            files_to_backup: List, mirror_deletions: bool = False,
                            deleted_files: List[Dict] = None) -> Dict:
        """Analiz sonuçlarına göre yedekleme yap (dosyaları tekrar taramadan)
        
        Args:
            source_path: Kaynak klasör
            target_path: Hedef klasör
            files_to_backup: Yedeklenecek dosya listesi - artık dict formatında (path, reason, vb.)
            mirror_deletions: Silinenleri yansıt (kaynakta olmayan dosyaları hedefte de sil/arşivle)
            deleted_files: Silinmiş dosyalar listesi (analiz sonucundan)
            
        Returns:
            {
                'files_copied': int,
                'files_moved_to_revisions': int,
                'files_skipped': int,
                'files_deleted': int,
                'size_copied': int,
                'size_moved': int,
                'size_skipped': int,
                'size_deleted': int
            }
        """
        stats = {
            'files_copied': 0,
            'files_moved_to_revisions': 0,
            'files_skipped': 0,
            'files_deleted': 0,
            'size_copied': 0,
            'size_moved': 0,
            'size_skipped': 0,
            'size_deleted': 0
        }
        
        for file_info in files_to_backup:
            if self.cancelled:
                break
            
            # Yeni format: dict ile gelebilir veya eski format: string
            if isinstance(file_info, dict):
                source_file = file_info['path']
            else:
                source_file = file_info  # Eski format uyumluluğu
            
            if not os.path.exists(source_file):
                continue
            
            # Hedef dosya yolunu oluştur
            rel_path = os.path.relpath(source_file, source_path)
            target_file = os.path.join(target_path, rel_path)
            
            # Dosya boyutu
            file_size = os.path.getsize(source_file)
            
            # Hedef klasörü oluştur
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # Hedefte dosya var mı kontrol et
            if os.path.exists(target_file):
                source_mtime = os.path.getmtime(source_file)
                target_mtime = os.path.getmtime(target_file)
                
                if source_mtime > target_mtime:
                    # Hedef dosya daha eski, REVISIONS'a taşı
                    revision_folder = self._create_revision_folder(target_path)
                    revision_file = os.path.join(revision_folder, rel_path)
                    
                    # Revision klasörünü oluştur
                    os.makedirs(os.path.dirname(revision_file), exist_ok=True)
                    
                    # Eski dosyayı taşı
                    shutil.move(target_file, revision_file)
                    stats['files_moved_to_revisions'] += 1
                    stats['size_moved'] += file_size
                    
                    # Yeni dosyayı kopyala
                    shutil.copy2(source_file, target_file)
                    stats['files_copied'] += 1
                    stats['size_copied'] += file_size
                    
                    if self.status_callback:
                        size_str = self.format_size(file_size)
                        self.status_callback(f"✓ Kopyalandı (eski sürüm arşivlendi): {os.path.basename(source_file)} ({size_str})")
                else:
                    # Dosyalar aynı veya hedef daha yeni, atla
                    stats['files_skipped'] += 1
                    stats['size_skipped'] += file_size
            else:
                # Hedefte dosya yok, direkt kopyala
                shutil.copy2(source_file, target_file)
                stats['files_copied'] += 1
                stats['size_copied'] += file_size
                
                if self.status_callback:
                    size_str = self.format_size(file_size)
                    self.status_callback(f"✓ Kopyalandı (yeni): {os.path.basename(source_file)} ({size_str})")
        
        # Mirror deletions: Silinenleri yansıt
        if mirror_deletions and deleted_files:
            revision_folder = self._create_revision_folder(target_path)
            
            for deleted_file_info in deleted_files:
                if self.cancelled:
                    break
                
                target_file = deleted_file_info['path']
                
                if not os.path.exists(target_file):
                    continue
                
                try:
                    file_size = os.path.getsize(target_file)
                    
                    # Hedef dosyanın relative path'ini bul
                    rel_path = os.path.relpath(target_file, target_path)
                    
                    # _REVISIONS'a "sil_" prefix'i ile taşı
                    revision_file = os.path.join(revision_folder, f"sil_{rel_path}")
                    
                    # Revision klasörünü oluştur
                    os.makedirs(os.path.dirname(revision_file), exist_ok=True)
                    
                    # Dosyayı taşı
                    shutil.move(target_file, revision_file)
                    stats['files_deleted'] += 1
                    stats['size_deleted'] += file_size
                    
                    if self.status_callback:
                        size_str = self.format_size(file_size)
                        self.status_callback(f"🗑 Silindi (arşivlendi): {os.path.basename(target_file)} ({size_str})")
                except Exception as e:
                    if self.status_callback:
                        self.status_callback(f"⚠ Silme hatası: {os.path.basename(target_file)} - {str(e)}")
        
        return stats
    
    def _create_revision_folder(self, target_path: str) -> str:
        """_REVISIONS klasörü oluştur
        
        Args:
            target_path: Hedef klasör
            
        Returns:
            Revision klasörünün yolu
        """
        now = datetime.now().strftime('%Y-%m-%d %H-%M')
        revision_folder = os.path.join(target_path, '_REVISIONS', now)
        os.makedirs(revision_folder, exist_ok=True)
        return revision_folder
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Boyutu okunabilir formata çevir
        
        Args:
            size_bytes: Byte cinsinden boyut
            
        Returns:
            Formatlanmış string (örn: "1.5 GB", "234 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
