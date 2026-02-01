"""
Smart Backup - Yedekleme İşlemleri Mixin
Tarih: 3 Ocak 2026
Yazar: Dr. Mustafa Afyonluoğlu

Bu modül SmartBackupApp sınıfı için yedekleme işlemlerini içerir.
"""

import os
import time
import threading
from sm_backup_engine import BackupEngine
from sm_ui_components import (ProgressDialog, ConfirmDialog, 
                               BackupSelectionDialog, AnalysisSelectionDialog)
from sm_deleted_files_dialog import DeletedFilesConfirmDialog
from sm_history_window import HistoryWindow


class BackupMixin:
    """Yedekleme işlemleri için mixin sınıfı"""
    
    # ==================== YEDEKLEME İŞLEMLERİ ====================
    
    def _calculate(self):
        """Toplam dosya sayısı ve boyutunu hesapla"""
        if not self.current_project_id:
            return
        
        mappings = self.db.get_mappings_by_project(self.current_project_id)
        
        if not mappings:
            ConfirmDialog.show_warning(self, "Uyarı", "Bu projede eşleşme bulunmuyor!")
            return
        
        # Log temizle ve başlat
        self._log_clear()
        self._log_write("=" * 80, "#00A0E9")
        self._log_write("TÜM EŞLEŞTİRMELERDEKİ KAYNAK KLASÖRLER İÇİN HESAPLAMA İŞLEMİ", "#A9E4FF")
        self._log_write("=" * 80, "#00A0E9")
        self.update_idletasks()
        # self.log_textbox.update_idletasks()

        total_files = 0
        total_size = 0
        total_excluded = 0
        total_excluded_size = 0
        
        for idx, mapping in enumerate(mappings, 1):
            # Log'a eşleşme bilgisi yaz
            self._log_write(f"\n[{idx}] {mapping['source_path']}", "#FFAE35")
            self._log_write(f"    Filtre: {mapping['file_filter']}", "#ADADAD")
            if mapping.get('exclude_filter'):
                self._log_write(f"    Hariç: {mapping.get('exclude_filter')}", "#ADADAD")
            
            file_count, size, excluded_count, excluded_size = self.backup_engine.calculate_mapping_stats(
                mapping['source_path'],
                mapping['file_filter'],
                mapping.get('exclude_filter', ''),
                bool(mapping['include_subdirs'])
            )
            
            # Eşleşme sonuçlarını logla
            if file_count == 0 and excluded_count == 0:
                self._log_write(f"    → Dosya bulunamadı!", "#FF0000")
            else:
                self._log_write(f"    → {file_count} dosya ({BackupEngine.format_size(size)})", "#01F001")
                if excluded_count > 0:
                    self._log_write(f"    → Hariç: {excluded_count} dosya ({BackupEngine.format_size(excluded_size)})", "#FFA500")
            
            total_files += file_count
            total_size += size
            total_excluded += excluded_count
            total_excluded_size += excluded_size
        
        # Özet
        self._log_write("\n" + "=" * 80, "#00A0E9")
        self._log_write(f"TOPLAM: {total_files} dosya ({BackupEngine.format_size(total_size)})", "#01F001")
        if total_excluded > 0:
            self._log_write(f"HARİÇ: {total_excluded} dosya ({BackupEngine.format_size(total_excluded_size)})", "#FFA500")
        self._log_write("=" * 80, "#00A0E9")
        self.log_textbox.see("1.0")

        size_str = BackupEngine.format_size(total_size)
        excluded_str = BackupEngine.format_size(total_excluded_size)
        self.stats_label.configure(
            text=f"Toplam: {total_files} dosya ({size_str}) | Hariç tutulan: {total_excluded} dosya ({excluded_str})"
        )
    
    def _analyze(self):
        """Yedeklenecek dosyaları analiz et"""
        if not self.current_project_id:
            return
        
        mappings = self.db.get_mappings_by_project(self.current_project_id)
        
        if not mappings:
            ConfirmDialog.show_warning(self, "Uyarı", "Bu projede eşleşme bulunmuyor!")
            return
        
        # Detayları Kaydet butonunu gizle (yeni analiz yapılıyor)
        self._hide_save_details_button()
        
        # Analiz seçim dialogunu göster
        mapping_list = [(m['id'], m['source_path'], m.get('exclude_filter', '')) for m in mappings]
        # Veritabanından son seçimleri al
        saved_selections = self.db.get_analysis_selections(self.current_project_id)
        selection_dialog = AnalysisSelectionDialog(self, mapping_list, saved_selections)
        result = selection_dialog.show()
        
        if not result:
            # Kullanıcı iptal etti
            return
        
        # Seçimleri al
        selected_mapping_ids = result['mappings']
        show_backup_files = result.get('show_backup_files', True)
        show_user_excluded_files = result.get('show_user_excluded_files', True)
        show_hidden_excluded_files = result.get('show_hidden_excluded_files', True)
        show_skipped_files = result.get('show_skipped_files', True)
        show_revision_files = result.get('show_revision_files', True)
        show_deleted_files = result.get('show_deleted_files', True)
        max_files_to_show = result.get('max_files_to_show', 50)
        
        # -1 ise tümünü göster (çok büyük sayı)
        if max_files_to_show == -1:
            max_files_to_show = 999999
        
        # Seçili mapping'leri filtrele
        selected_mappings = [m for m in mappings if m['id'] in selected_mapping_ids]
        
        # Hedef disklerin erişilebilir olup olmadığını kontrol et (klasör değil, disk!)
        inaccessible_drives = []
        for mapping in selected_mappings:
            target_path = mapping['target_path']
            # Hedef yolun bulunduğu diski al (örn: C:\, D:\, E:\)
            drive = os.path.splitdrive(target_path)[0] + "\\"
            
            # Diske erişilebilir mi kontrol et
            if not os.path.exists(drive):
                if drive not in inaccessible_drives:
                    inaccessible_drives.append(drive)
        
        if inaccessible_drives:
            # Erişilemeyen diskler var (USB çıkarılmış olabilir)
            error_message = "Aşağıdaki disklere erişilemiyor:\n\n"
            for drive in inaccessible_drives:
                error_message += f"  • {drive}\n"
            error_message += "\nLütfen harici disklerin bağlı olduğundan emin olun ve tekrar deneyin."
            ConfirmDialog.show_warning(self, "Hedef Disklere Erişilemiyor", error_message)
            return
        
        # Status callback ayarla - backup_engine'den log paneline mesaj göndermek için
        def status_callback(message: str):
            self.after(0, lambda msg=message: self._log_write(msg, "#FBFF2C"))
        
        self.backup_engine.set_status_callback(status_callback)
        
        # Log temizle ve başlat
        self._log_clear()
        self._log_write("=" * 80, "#00A0E9")
        self._log_write("ANALİZ İŞLEMİ", "#A9E4FF")
        self._log_write("=" * 80, "#00A0E9")
        
        # Analiz süresini ölç
        analysis_start_time = time.time()

        self.stats_label.configure(text="Hesaplanıyor...")                    
        self.update_idletasks()
        
        total_files = 0
        total_size = 0
        total_excluded = 0
        total_excluded_size = 0
        total_skipped = 0
        total_skipped_size = 0
        
        # Analiz sonuçlarını sakla - yedekleme için kullanılacak
        # Önceki analiz sonuçlarını temizle
        self.analysis_results = {}
        
        for idx, mapping in enumerate(selected_mappings, 1):
            self.stats_label.configure(text=f"Hesaplanıyor: {mapping['source_path']}")  
            self.update_idletasks()
            # Log'a eşleşme bilgisi yaz
            self._log_write(f"\n[{idx}/{len(selected_mappings)}] {mapping['source_path']}", "#FFAE35")
            self._log_write(f"    Hedef: {mapping['target_path']}", "#ADADAD")
            self._log_write(f"    Filtre: {mapping['file_filter']}", "#ADADAD")
            if mapping.get('exclude_filter'):
                self._log_write(f"    Hariç: {mapping.get('exclude_filter')}", "#ADADAD")
            
            # Detaylı analiz yap
            # print(f"Gösterilecek dosya sayısı: {max_files_to_show}")

            print(f"✨Analiz yapılıyor: {mapping['source_path']}")
            result = self.backup_engine.analyze_mapping_detailed(
                mapping['source_path'],
                mapping['file_filter'],
                mapping.get('exclude_filter', ''),
                bool(mapping['include_subdirs']),
                mapping['target_path'],
                max_files_to_show
            )
            toplam_ncelenen_dosya = (len(result['files_to_backup']) + 
                                    result.get('total_excluded_count', 0) + 
                                    result['skipped_count'])
            print(f"✅{toplam_ncelenen_dosya} dosya için Analiz tamamlandı: {mapping['source_path']}")
            

            files_to_backup = result['files_to_backup']
            user_excluded_count = result.get('user_excluded_count', 0)
            hidden_excluded_count = result.get('hidden_excluded_count', 0)
            mapping_excluded_count = result.get('total_excluded_count', 0)
            skipped_count = result['skipped_count']
            size = result['total_size']
            user_excluded_size = result.get('user_excluded_size', 0)
            hidden_excluded_size = result.get('hidden_excluded_size', 0)
            mapping_excluded_size = result.get('total_excluded_size', 0)
            skipped_size = result['skipped_size']
            revision_count = result.get('revision_count', 0)
            revision_size = result.get('revision_size', 0)
            deleted_count = result.get('deleted_count', 0)
            deleted_size = result.get('deleted_size', 0)
            
            # Analiz sonuçlarını sakla
            self.analysis_results[mapping['id']] = result
            
            # Toplam sayıları güncelle
            total_files += len(files_to_backup)
            total_size += size
            total_excluded += mapping_excluded_count
            total_excluded_size += mapping_excluded_size
            total_skipped += skipped_count
            total_skipped_size += skipped_size
            
            # Analiz sonuçlarını logla
            if len(files_to_backup) == 0 and mapping_excluded_count == 0 and skipped_count == 0:
                self._log_write(f"    → Yedeklenecek dosya bulunamadı!", "#FFA0A0")
            else:
                toplam_dosya = len(files_to_backup) + mapping_excluded_count + skipped_count
                toplam_dosya_boyutu = size + mapping_excluded_size + skipped_size
                self._log_write(f"    → Toplam incelenen dosya: {toplam_dosya:,}  ({BackupEngine.format_size(toplam_dosya_boyutu)})", "#60C2FF")
                if len(files_to_backup) > 0:
                    self._log_write(f"    → Yedeklenecek: {len(files_to_backup):,} dosya ({BackupEngine.format_size(size)})", "#01F001")
                else:
                    self._log_write(f"    → Yedeklenecek: 0 dosya", "#65FE65")
                
                if skipped_count > 0:
                    self._log_write(f"    → Atlanan (güncel): {skipped_count:,} dosya ({BackupEngine.format_size(skipped_size)})", "#FFCC6C")
                
                if user_excluded_count > 0:
                    self._log_write(f"    → Hariç (filtre): {user_excluded_count:,} dosya ({BackupEngine.format_size(user_excluded_size)})", "#FFA500")
                
                if hidden_excluded_count > 0:
                    self._log_write(f"    → Hariç (gizli): {hidden_excluded_count:,} dosya ({BackupEngine.format_size(hidden_excluded_size)})", "#FFA500")
                
                if deleted_count > 0:
                    self._log_write(f"    → Silinmiş (kaynakta yok): {deleted_count:,} dosya ({BackupEngine.format_size(deleted_size)})", "#FF6B6B")
            
                if revision_count > 0:
                    self._log_write(f"    → Arşivlenmiş (_REVISIONS): {revision_count:,} dosya ({BackupEngine.format_size(revision_size)})", "#D896FF")
                
            # Ekranı güncelle - büyük analizlerde donma olmasın
            self.update_idletasks()
        
        # Özet
        self._log_write("\n" + "=" * 80, "#00A0E9")
        if total_files > 0:
            self._log_write(f"YEDEKLENECEK TOPLAM: {total_files:,} dosya ({BackupEngine.format_size(total_size)})", "#01F001")
        else:
            self._log_write(f"YEDEKLENECEK TOPLAM: 0 dosya (tüm dosyalar güncel)", "#65FE65")
        
        if total_excluded > 0:
            self._log_write(f"HARİÇ TUTULAN: {total_excluded:,} dosya ({BackupEngine.format_size(total_excluded_size)})", "#FFCC6C")
        
        # Silinen dosya sayısını göster
        total_deleted = sum(r.get('deleted_count', 0) for r in self.analysis_results.values())
        total_deleted_size = sum(r.get('deleted_size', 0) for r in self.analysis_results.values())
        if total_deleted > 0:
            self._log_write(f"SİLİNECEK DOSYALAR: {total_deleted:,} dosya ({BackupEngine.format_size(total_deleted_size)})", "#FF6B6B")
        
        # Toplam incelenen (kaynak dosyalar): yedeklenecek + atlanan + hariç tutulan
        grand_total_files = total_files + total_skipped + total_excluded
        grand_total_size = total_size + total_skipped_size + total_excluded_size
        self._log_write(f"TOPLAM İNCELENEN: {grand_total_files:,} dosya ({BackupEngine.format_size(grand_total_size)})", "#F9AAAA")
        
        self._log_write("=" * 80, "#00A0E9")
        
        # Yedeklenecek dosyaların ilk N'ini listele (eğer checkbox işaretliyse)
        if show_backup_files:
            all_files_to_backup = []
            for mapping_id, result in self.analysis_results.items():
                all_files_to_backup.extend(result['files_to_backup'])
            
            if all_files_to_backup:
                self._log_write("\n" + "=" * 80, "#00A0E9")
                self._log_write(f"YEDEKLENECEK DOSYALAR (İlk {min(max_files_to_show, len(all_files_to_backup))} / {len(all_files_to_backup)})", "#A9E4FF")
                self._log_write("=" * 80, "#00A0E9")
                
                for i, file_info in enumerate(all_files_to_backup[:max_files_to_show], 1):
                    # Yeni format: dict veya eski format: string
                    if isinstance(file_info, dict):
                        file_path = file_info['path']
                        reason = file_info.get('reason', '')
                        
                        # Neden bilgisini formatla
                        reason_text = ""
                        if reason == 'yeni dosya':
                            reason_text = " (yeni dosya)"
                        elif reason == 'daha yeni':
                            source_date = file_info.get('source_date', '')
                            target_date = file_info.get('target_date', '')
                            reason_text = f" (daha yeni - kaynak: {source_date}, hedef: {target_date})"
                        
                        file_size = file_info.get('size', 0)
                        self._log_write(
                            f"{i}. {file_path} ({BackupEngine.format_size(file_size)}){reason_text}", 
                            "#ADADAD"
                        )
                    else:
                        # Eski format uyumluluğu
                        file_path = file_info
                        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                        self._log_write(f"{i}. {file_path} ({BackupEngine.format_size(file_size)})", "#ADADAD")
                
                if len(all_files_to_backup) > max_files_to_show:
                    self._log_write(f"\n... ve {len(all_files_to_backup) - max_files_to_show} dosya daha", "#FFAE35")
        
        # Kullanıcı tanımlı filtre ile hariç tutulan dosyaları listele
        if show_user_excluded_files:
            all_user_excluded_files = []
            total_user_excluded = 0
            total_user_excluded_size = 0
            
            for mapping_id, result in self.analysis_results.items():
                all_user_excluded_files.extend(result.get('user_excluded_files', []))
                total_user_excluded += result.get('user_excluded_count', 0)
                total_user_excluded_size += result.get('user_excluded_size', 0)
            
            if all_user_excluded_files:
                self._log_write("\n" + "=" * 80, "#00A0E9")
                self._log_write(f"HARİÇ TUTULAN DOSYALAR - FİLTRE (İlk {min(max_files_to_show, len(all_user_excluded_files))} / {total_user_excluded})", "#A9E4FF")
                self._log_write("=" * 80, "#00A0E9")
                
                for i, file_path in enumerate(all_user_excluded_files[:max_files_to_show], 1):
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    self._log_write(f"{i}. {file_path} ({BackupEngine.format_size(file_size)})", "#ADADAD")
                
                if total_user_excluded > max_files_to_show:
                    self._log_write(f"\n... ve {total_user_excluded - max_files_to_show} dosya daha", "#FFAE35")
        
        # Gizli klasör dosyalarını listele
        if show_hidden_excluded_files:
            all_hidden_excluded_files = []
            total_hidden_excluded = 0
            total_hidden_excluded_size = 0
            
            for mapping_id, result in self.analysis_results.items():
                all_hidden_excluded_files.extend(result.get('hidden_excluded_files', []))
                total_hidden_excluded += result.get('hidden_excluded_count', 0)
                total_hidden_excluded_size += result.get('hidden_excluded_size', 0)
            
            if all_hidden_excluded_files:
                self._log_write("\n" + "=" * 80, "#00A0E9")
                self._log_write(f"HARİÇ TUTULAN DOSYALAR - GİZLİ KLASÖRLER (İlk {min(max_files_to_show, len(all_hidden_excluded_files))} / {total_hidden_excluded})", "#A9E4FF")
                self._log_write("=" * 80, "#00A0E9")
                
                for i, file_path in enumerate(all_hidden_excluded_files[:max_files_to_show], 1):
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    self._log_write(f"{i}. {file_path} ({BackupEngine.format_size(file_size)})", "#ADADAD")
                
                if total_hidden_excluded > max_files_to_show:
                    self._log_write(f"\n... ve {total_hidden_excluded - max_files_to_show} dosya daha", "#FFAE35")
        
        # Atlanan dosyaların ilk N'ini listele (eğer checkbox işaretliyse)
        if show_skipped_files:
            all_skipped_files = []
            total_skipped = 0
            total_skipped_size = 0
            
            for mapping_id, result in self.analysis_results.items():
                all_skipped_files.extend(result.get('skipped_files', []))
                total_skipped += result.get('skipped_count', 0)
                total_skipped_size += result.get('skipped_size', 0)
            
            if all_skipped_files:
                self._log_write("\n" + "=" * 80, "#00A0E9")
                self._log_write(f"ATLANAN DOSYALAR (Güncel) (İlk {min(max_files_to_show, len(all_skipped_files))} / {total_skipped})", "#A9E4FF")
                self._log_write("=" * 80, "#00A0E9")
                
                for i, file_path in enumerate(all_skipped_files[:max_files_to_show], 1):
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    self._log_write(f"{i}. {file_path} ({BackupEngine.format_size(file_size)})", "#ADADAD")
                
                if total_skipped > max_files_to_show:
                    self._log_write(f"\n... ve {total_skipped - max_files_to_show} dosya daha", "#FFAE35")
        
        total_revision_count = 0
        # Revision dosyalarını listele (eğer checkbox işaretliyse)
        if show_revision_files:
            all_revision_files = []
            # total_revision_count = 0
            total_revision_size = 0
            
            for mapping_id, result in self.analysis_results.items():
                revision_files = result.get('revision_files', [])
                all_revision_files.extend(revision_files)
                total_revision_count += result.get('revision_count', 0)
                total_revision_size += result.get('revision_size', 0)
            
            if all_revision_files:
                self._log_write("\n" + "=" * 80, "#00A0E9")
                self._log_write(f"REVISIONS (Arşivlenmiş Dosyalar) (İlk {min(max_files_to_show, len(all_revision_files))} / {total_revision_count})", "#A9E4FF")
                self._log_write("=" * 80, "#00A0E9")
                
                for i, file_info in enumerate(all_revision_files[:max_files_to_show], 1):
                    file_path = file_info['path']
                    file_size = file_info['size']
                    timestamp_folder = file_info['timestamp_folder']
                    
                    # Timestamp'i daha okunabilir formata çevir (20251122_143020 -> 22-11-2025 14:30:20)
                    try:
                        if len(timestamp_folder) == 15 and '_' in timestamp_folder:
                            date_part = timestamp_folder[:8]
                            time_part = timestamp_folder[9:]
                            formatted_time = f"{date_part[6:8]}-{date_part[4:6]}-{date_part[:4]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                            # formatted_time = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                        else:
                            formatted_time = timestamp_folder
                    except:
                        formatted_time = timestamp_folder
                    
                    self._log_write(
                        f"{i}. Arşiv: {formatted_time} - {file_path} ({BackupEngine.format_size(file_size)})", 
                        "#ADADAD"
                    )
                
                if total_revision_count > max_files_to_show:
                    self._log_write(f"\n... ve {total_revision_count - max_files_to_show} dosya daha", "#FFAE35")
        
        # Silinen dosyaları listele (eğer checkbox işaretliyse)
        if show_deleted_files:
            all_deleted_files = []
            total_deleted_count = 0
            total_deleted_size = 0
            
            for mapping_id, result in self.analysis_results.items():
                deleted_files = result.get('deleted_files', [])
                all_deleted_files.extend(deleted_files)
                total_deleted_count += result.get('deleted_count', 0)
                total_deleted_size += result.get('deleted_size', 0)
            
            if all_deleted_files:
                self._log_write("\n" + "=" * 80, "#00A0E9")
                self._log_write(f"SİLİNMİŞ DOSYALAR (Kaynakta olmayan) (İlk {min(max_files_to_show, len(all_deleted_files))} / {total_deleted_count})", "#A9E4FF")
                self._log_write("=" * 80, "#00A0E9")
                
                for i, file_info in enumerate(all_deleted_files[:max_files_to_show], 1):
                    file_path = file_info['path']
                    file_size = file_info['size']
                    self._log_write(
                        f"{i}. {file_path} ({BackupEngine.format_size(file_size)})", 
                        "#ADADAD"
                    )
                
                if total_deleted_count > max_files_to_show:
                    self._log_write(f"\n... ve {total_deleted_count - max_files_to_show} dosya daha", "#FFAE35")
        
        # Analiz süresini hesapla ve kaydet
        analysis_duration = time.time() - analysis_start_time
        self.analysis_duration = analysis_duration  # Yedekleme için sakla
        
        # Analiz başarıyla tamamlandı - seçimleri kaydet
        self.db.set_analysis_selections(
            self.current_project_id, 
            selected_mapping_ids,
            show_backup_files=show_backup_files,
            show_user_excluded_files=show_user_excluded_files,
            show_hidden_excluded_files=show_hidden_excluded_files,
            show_skipped_files=show_skipped_files,
            show_revision_files=show_revision_files,
            show_deleted_files=show_deleted_files,
            max_files_to_show=max_files_to_show if max_files_to_show != 999999 else -1
        )
        
        # Analiz süresini log'a yaz
        self._log_write(f"\nAnaliz Süresi: {analysis_duration:.2f} saniye", "#A9E4FF")
        self.log_textbox.see("1.0")

        size_str = BackupEngine.format_size(total_size)
        excluded_str = BackupEngine.format_size(total_excluded_size)

        # Toplam dosya sayısı: yedeklenecek + atlanan + hariç tutulan
        grand_total = total_files + total_skipped + total_excluded
        summary = f"Toplam dosya: {grand_total:,}  | Yedeklenecek: {total_files:,}  | Atlanan: {total_skipped:,} | Hariç tutulan: {total_excluded:,}  | Silinen: {total_deleted:,} | Arşivlenen: {total_revision_count:,}"

        self.stats_label.configure(text=summary)

    
    def _backup(self):
        """Yedekleme yap"""
        if not self.current_project_id:
            return
        
        mappings = self.db.get_mappings_by_project(self.current_project_id)
        
        if not mappings:
            ConfirmDialog.show_warning(self, "Uyarı", "Bu projede eşleşme bulunmuyor!")
            return
        
        # Analiz yapılmış mı kontrol et
        if not self.analysis_results:
            ConfirmDialog.show_warning(self, "Uyarı", 
                                      "Lütfen önce 'Analiz' butonuna basarak yedeklenecek dosyaları analiz edin!")
            return
        
        # Mapping seçim dialogunu göster
        mapping_list = [(m['id'], m['source_path'], m.get('exclude_filter', '')) for m in mappings]
        analyzed_ids = set(self.analysis_results.keys())
        selection_dialog = BackupSelectionDialog(self, mapping_list, analyzed_ids, self.analysis_results)
        result = selection_dialog.show()
        
        if not result:
            # Kullanıcı iptal etti
            return
        
        # Seçimleri al
        selected_mapping_ids = result['mappings']
        backup_hidden_files = result.get('backup_hidden_files', False)
        mirror_deletions = result.get('mirror_deletions', False)
        auto_save_details = result.get('auto_save_details', False)
        
        # Seçili mapping'leri filtrele
        selected_mappings = [m for m in mappings if m['id'] in selected_mapping_ids]
        
        # if not ConfirmDialog.ask(self, "Onay",
        #                         f"{len(selected_mappings)} eşleşme için yedekleme işlemini başlatmak istediğinizden emin misiniz?"):
        #     return
        
        # Silinenleri yansıt seçiliyse, silinen dosyalar için onay dialogu göster
        if mirror_deletions:
            # Silinen dosyaları topla
            deleted_files_data = {}
            total_deleted_files_count = 0
            
            for mapping in selected_mappings:
                mapping_id = mapping['id']
                if mapping_id in self.analysis_results:
                    analysis_result = self.analysis_results[mapping_id]
                    deleted_files = analysis_result.get('deleted_files_all', [])
                    
                    if deleted_files:
                        deleted_files_data[mapping_id] = {
                            'deleted_files': deleted_files,
                            'mapping_name': f"{mapping['source_path']} → {mapping['target_path']}"
                        }
                        total_deleted_files_count += len(deleted_files)
            
            # Silinen dosya varsa onay dialogunu göster
            if total_deleted_files_count > 0:
                dialog = DeletedFilesConfirmDialog(self, deleted_files_data)
                selected_deleted_files = dialog.show()
                
                # Kullanıcı iptal ettiyse yedeklemeyi durdur
                if selected_deleted_files is None:
                    return
                
                # Seçilen dosyaları analiz sonuçlarında güncelle
                for mapping_id, selected_files in selected_deleted_files.items():
                    if mapping_id in self.analysis_results:
                        self.analysis_results[mapping_id]['deleted_files_all'] = selected_files
        
        # Log alanını temizle
        # self._log_clear()
        self._log_write("=" * 80, "#00A0E9")
        self._log_write("YEDEKLEME İŞLEMİ BAŞLADI", "#A9E4FF")
        if mirror_deletions:
            self._log_write("ℹ️  Silinenleri Yansıt: AÇIK (Kaynakta olmayan dosyalar arşivlenecek)", "#FF6B6B")
        self._log_write("=" * 80, "#00A0E9")
  
        # Progress dialog aç
        progress_dialog = ProgressDialog(self, "Yedekleme İşlemi")
        
        # Thread'de yedekleme yap
        def backup_thread():
            self.backup_engine.reset_cancel()
            
            # Dialog iptal edilirse engine'i de iptal et
            def check_dialog_cancelled():
                if progress_dialog.cancelled:
                    self.backup_engine.cancel()
                if not progress_dialog.is_closed and not self.backup_engine.cancelled:
                    self.after(100, check_dialog_cancelled)
            
            self.after(100, check_dialog_cancelled)
            start_time = time.time()
            
            total_copied = 0
            total_moved = 0
            total_skipped = 0
            total_deleted = 0
            total_excluded = 0  # Hariç tutulan dosyalar (filtre + gizli)
            size_copied = 0
            size_moved = 0
            size_skipped = 0
            size_deleted = 0
            size_excluded = 0  # Hariç tutulan dosyaların boyutu
            
            # Her eşleşme için istatistikleri sakla
            mapping_stats = []
            
            mapping_count = len(selected_mappings)  # Seçili mapping sayısı
            
            for idx, mapping in enumerate(selected_mappings):  # Sadece seçili mapping'leri işle
                if self.backup_engine.cancelled:
                    break
                
                mapping_id = mapping['id']
                
                # Analiz sonuçlarını kontrol et
                if mapping_id not in self.analysis_results:
                    self.after(0, lambda m=mapping: self._log_write(
                        f"\n⚠️ Eşleşme {m['source_path']} için analiz sonucu bulunamadı, atlanıyor...", "#FF0000"
                    ))
                    continue
                
                analysis_result = self.analysis_results[mapping_id]
                files_to_backup = analysis_result['files_to_backup'].copy()
                deleted_files = analysis_result.get('deleted_files_all', [])  # Tüm silinen dosyaları al
                deleted_count_in_analysis = analysis_result.get('deleted_count', 0)
                
                # Debug: Silinen dosya bilgilerini log'a yaz
                if mirror_deletions and deleted_count_in_analysis > 0:
                    self.after(0, lambda count=deleted_count_in_analysis, dfiles=len(deleted_files): self._log_write(
                        f"  ℹ️  Silinen dosya sayısı: {count} (liste: {dfiles} dosya)", "#FFAE35"
                    ))
                
                # Gizli dosyaları yedekleme seçeneği işaretliyse, gizli dosyaları da ekle
                if backup_hidden_files:
                    hidden_files = analysis_result.get('hidden_excluded_files', [])
                    # Gizli dosyaların tam listesini almak için tüm gizli dosyaları topla
                    # (hidden_excluded_files sadece ilk N tanesi olabilir)
                    # Şimdilik mevcut listeyi kullanıyoruz
                    self.after(0, lambda count=len(hidden_files): self._log_write(
                        f"  ℹ️ Gizli dosyalar yedeklemeye dahil edildi: {count} dosya", "#FFAE35"
                    ))
                    files_to_backup.extend(hidden_files)
                
                skipped_count_from_analysis = analysis_result['skipped_count']
                skipped_size_from_analysis = analysis_result['skipped_size']
                
                # Yedekleme/silme bilgisi log'a yaz
                if mirror_deletions and deleted_count_in_analysis > 0:
                    self.after(0, lambda count=deleted_count_in_analysis: self._log_write(
                        f"  ℹ️  Silinecek dosya: {count} dosya", "#FF6B6B"
                    ))
                
                # Yedeklenecek dosya yoksa atla
                if not files_to_backup and (not mirror_deletions or not deleted_files):
                    self.after(0, lambda m=mapping, i=idx, mc=mapping_count: self._log_write(
                        f"\n[Eşleşme {i + 1}/{mc}] {m['source_path']} → {m['target_path']}", "#FFAE35"
                    ))
                    self.after(0, lambda: self._log_write(
                        f"  → Yedeklenecek/silinecek dosya yok, atlanıyor...", "#65FE65"
                    ))
                    
                    # Hariç tutulan dosyaları analiz sonuçlarından al (bu eşleşme için)
                    excluded_count_from_analysis = analysis_result.get('total_excluded_count', 0)
                    excluded_size_from_analysis = analysis_result.get('total_excluded_size', 0)
                    total_excluded += excluded_count_from_analysis
                    size_excluded += excluded_size_from_analysis
                    
                    # Sadece skipped dosyalar varsa bunları da istatistiklere ekle
                    if skipped_count_from_analysis > 0:
                        total_skipped += skipped_count_from_analysis
                        size_skipped += skipped_size_from_analysis
                        
                        # Mapping istatistiklerini sakla (sadece skipped)
                        mapping_stats.append({
                            'mapping_id': mapping['id'],
                            'stats': {
                                'files_copied': 0,
                                'files_moved_to_revisions': 0,
                                'files_skipped': skipped_count_from_analysis,
                                'files_deleted': 0,
                                'size_copied': 0,
                                'size_moved': 0,
                                'size_skipped': skipped_size_from_analysis,
                                'size_deleted': 0
                            }
                        })
                    
                    continue
                
                # Log'a eşleşme başlangıcı yaz
                self.after(0, lambda i=idx, m=mapping, count=len(files_to_backup): self._log_write(
                    f"\n[Eşleşme {i + 1}/{mapping_count}] {m['source_path']} → {m['target_path']} ({count} dosya)", "#FFAE35"
                ))
                
                # İlerlemeyi güncelle
                progress = idx / mapping_count
                progress_dialog.update_progress(progress)
                progress_dialog.update_status(
                    f"Eşleşme {idx + 1}/{mapping_count} işleniyor..."
                )
                
                # Analiz sonuçlarını kullanarak (dosyaları tekrar taramadan) yedekleme yap
                stats = self.backup_engine.backup_from_analysis(
                    mapping['source_path'],
                    mapping['target_path'],
                    files_to_backup,
                    mirror_deletions,
                    deleted_files
                )
                
                # Analizdeki skipped sayısını ekle (backup_from_analysis bu dosyalara bakmadı)
                stats['files_skipped'] += skipped_count_from_analysis
                stats['size_skipped'] += skipped_size_from_analysis
                
                # Hariç tutulan dosyaları analiz sonuçlarından al
                excluded_count_from_analysis = analysis_result.get('total_excluded_count', 0)
                excluded_size_from_analysis = analysis_result.get('total_excluded_size', 0)
                
                # İstatistikleri topla
                total_copied += stats['files_copied']
                total_moved += stats['files_moved_to_revisions']
                total_skipped += stats['files_skipped']
                total_deleted += stats.get('files_deleted', 0)
                total_excluded += excluded_count_from_analysis
                size_copied += stats['size_copied']
                size_moved += stats['size_moved']
                size_skipped += stats['size_skipped']
                size_deleted += stats.get('size_deleted', 0)
                size_excluded += excluded_size_from_analysis
                
                # Eşleşme özeti log'a yaz
                log_msg = f"  → Kopyalanan: {stats['files_copied']}, Arşivlenen: {stats['files_moved_to_revisions']}, Atlanan: {stats['files_skipped']}"
                if mirror_deletions and stats.get('files_deleted', 0) > 0:
                    log_msg += f", Silinen: {stats['files_deleted']}"
                self.after(0, lambda msg=log_msg: self._log_write(msg, "#ADADAD"))
                
                # Her eşleşme için istatistikleri sakla (excluded bilgisi dahil)
                mapping_stats.append({
                    'mapping_id': mapping['id'],
                    'stats': stats,
                    'excluded_count': excluded_count_from_analysis,
                    'excluded_size': excluded_size_from_analysis
                })
            
            # Tamamlandı
            progress_dialog.update_progress(1.0)
            
            duration = time.time() - start_time
            status = "İptal Edildi" if self.backup_engine.cancelled else "Tamamlandı"
            
            # Analiz süresini al (yoksa 0)
            analysis_duration = getattr(self, 'analysis_duration', 0)
            
            # Veritabanına kaydet
            backup_id = self.db.add_backup_history(
                self.current_project_id,
                analysis_duration,
                duration,
                total_copied,
                total_moved,
                total_skipped,
                total_deleted,
                total_excluded,
                size_copied,
                size_moved,
                size_skipped,
                size_deleted,
                size_excluded,
                status
            )
            
            # DEBUG: Veritabanına kaydedilen değerleri kontrol et
            
            # print(f"DEBUG: Veritabanına kaydedilen değerler:")
            # print(f"  total_copied: {total_copied}, size_copied: {size_copied}")
            # print(f"  total_moved: {total_moved}, size_moved: {size_moved}")
            # print(f"  total_skipped: {total_skipped}, size_skipped: {size_skipped}")
            # print(f"  total_deleted: {total_deleted}, size_deleted: {size_deleted}")
            # print(f"  total_excluded: {total_excluded}, size_excluded: {size_excluded}")
            # total_size_for_db = size_copied + size_moved + size_skipped + size_deleted + size_excluded
            # print(f"  TOPLAM BOYUT: {total_size_for_db} ({BackupEngine.format_size(total_size_for_db)})")
            
            # Her eşleşme için detayları kaydet
            for mapping_stat in mapping_stats:
                stats = mapping_stat['stats']
                self.db.add_backup_detail(
                    backup_id,
                    mapping_stat['mapping_id'],
                    stats['files_copied'],
                    stats['files_moved_to_revisions'],
                    stats['files_skipped'],
                    stats.get('files_deleted', 0),
                    mapping_stat.get('excluded_count', 0),
                    stats['size_copied'],
                    stats['size_moved'],
                    stats['size_skipped'],
                    stats.get('size_deleted', 0),
                    mapping_stat.get('excluded_size', 0)
                )
            
            # Dialog'u kapat
            if not progress_dialog.is_closed:
                self.after(0, progress_dialog.destroy)
            
            # Log'a özet yaz
            self.after(0, lambda: self._log_write("=" * 80, "#00A0E9"))
            self.after(0, lambda: self._log_write("YEDEKLEME İŞLEMİ TAMAMLANDI", "#A9E4FF"))
            self.after(0, lambda: self._log_write("=" * 80, "#00A0E9"))
            self.after(0, lambda: self._log_write(f"Durum: {status}", "#01F001" if status == "Tamamlandı" else "#FF0000"))
            self.after(0, lambda: self._log_write(f"Süre: {duration:.2f} saniye"))
            self.after(0, lambda: self._log_write(f"Yedeklenen Dosyalar: {total_copied} dosya ({BackupEngine.format_size(size_copied)})", "#65FE65"))
            self.after(0, lambda: self._log_write(f"Arşivlenen Dosyalar: {total_moved} dosya ({BackupEngine.format_size(size_moved)})", "#FFA500"))
            self.after(0, lambda: self._log_write(f"Atlanan Dosyalar: {total_skipped} dosya ({BackupEngine.format_size(size_skipped)})", "#B5B4B4"))
            if mirror_deletions and total_deleted > 0:
                self.after(0, lambda: self._log_write(f"Silinen Dosyalar: {total_deleted} dosya ({BackupEngine.format_size(size_deleted)})", "#FF6B6B"))
            if total_excluded > 0:
                self.after(0, lambda: self._log_write(f"Hariç Tutulan: {total_excluded} dosya ({BackupEngine.format_size(size_excluded)})", "#FFCC6C"))
            total_all = total_copied + total_moved + total_skipped + total_deleted + total_excluded
            total_size_all = size_copied + size_moved + size_skipped + size_deleted + size_excluded
            self.after(0, lambda: self._log_write(f"Toplam İncelenen: {total_all} dosya ({BackupEngine.format_size(total_size_all)})", "#F9AAAA"))
            self.after(0, lambda: self._log_write("=" * 80, "#00A0E9"))
            
            # Sonuç mesajı - ana thread'de göster
            if not self.backup_engine.cancelled:
                msg = (f"Yedekleme tamamlandı!\n\n"
                      f"Kopyalanan: {total_copied} dosya ({BackupEngine.format_size(size_copied)})\n"
                      f"Arşivlenen: {total_moved} dosya ({BackupEngine.format_size(size_moved)})\n"
                      f"Atlanan: {total_skipped} dosya ({BackupEngine.format_size(size_skipped)})\n"
                      f"Süre: {duration:.1f} saniye")
                self.after(0, lambda: ConfirmDialog.show_info(self, "Başarılı", msg))
                
                # Yedekleme başarılı --> detay kaydetme butonunu göster veya otomatik kaydet
                if auto_save_details:
                    # Otomatik detay kaydetme
                    self.after(0, lambda bid=backup_id: self._auto_save_backup_details(bid))
                else:
                    # Manuel kaydetme için butonu göster
                    self.after(0, lambda bid=backup_id: self._show_save_details_button(bid))
            else:
                # İptal edildiğinde de bilgi göster
                self.after(0, lambda: ConfirmDialog.show_info(self, "İptal Edildi", "Yedekleme işlemi kullanıcı tarafından iptal edildi."))
        
        # Callback'leri ayarla - hem progress dialog hem log için
        def status_callback(msg):
            progress_dialog.update_detail(msg)
            # Log'a da yaz (ana thread'de)
            self.after(0, lambda m=msg: self._log_write(m, "#CCA9FD"))
        
        self.backup_engine.set_status_callback(status_callback)
        
        # Thread'i başlat
        thread = threading.Thread(target=backup_thread, daemon=True)
        thread.start()
        
        # Progress dialog'u göster
        self.wait_window(progress_dialog)
        
        # İptal edildiyse engine'e bildir
        if progress_dialog.cancelled:
            self.backup_engine.cancel()
    
    def _show_save_details_button(self, backup_id: int):
        """Detayları Kaydet butonunu göster"""
        self.last_backup_id = backup_id
        # Butonu göster (Geçmiş butonunun yanına)
        self.save_details_btn.pack(side="left", padx=(0, 5))
    
    def _hide_save_details_button(self):
        """Detayları Kaydet butonunu gizle"""
        self.last_backup_id = None
        self.last_backup_files = None
        try:
            self.save_details_btn.pack_forget()
        except:
            pass  # Buton henüz oluşturulmamış olabilir
    
    def _save_backup_file_details(self):
        """Yedeklenen dosyaların detaylarını veritabanına kaydet"""
        if not self.last_backup_id:
            ConfirmDialog.show_warning(self, "Uyarı", "Kaydedilecek yedekleme bilgisi bulunamadı!")
            return
        
        if not self.analysis_results:
            ConfirmDialog.show_warning(self, "Uyarı", "Analiz sonuçları bulunamadı!")
            return
        
        # Tüm yedeklenen dosyaları topla
        file_details = []
        for mapping_id, result in self.analysis_results.items():
            files_to_backup = result.get('files_to_backup', [])
            for file_info in files_to_backup:
                if isinstance(file_info, dict):
                    file_path = file_info.get('path', '')
                    file_size = file_info.get('size', 0)
                    reason = file_info.get('reason', 'bilinmiyor')
                else:
                    # Eski format uyumluluğu
                    file_path = file_info
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    reason = 'bilinmiyor'
                
                # Dosya adını yoldan ayır
                file_name = os.path.basename(file_path)
                file_dir = os.path.dirname(file_path)
                
                # Önceki yedeklerdeki boyutu bul
                previous_size = self.db.get_previous_file_size(file_dir, file_name, self.last_backup_id)
                
                file_details.append({
                    'mapping_id': mapping_id,
                    'file_path': file_dir,
                    'file_name': file_name,
                    'file_size': file_size,
                    'previous_size': previous_size,
                    'backup_reason': reason
                })
        
        if not file_details:
            ConfirmDialog.show_warning(self, "Uyarı", "Kaydedilecek dosya detayı bulunamadı!")
            return
        
        try:
            # Veritabanına kaydet
            self.db.add_backup_file_details(self.last_backup_id, file_details)
            
            # Butonu gizle (detaylar kaydedildi)
            self._hide_save_details_button()
            
            ConfirmDialog.show_info(self, "Başarılı", 
                                   f"{len(file_details)} dosyanın detayları başarıyla kaydedildi.")
        except Exception as e:
            ConfirmDialog.show_error(self, "Hata", f"Detaylar kaydedilemedi: {str(e)}")
    
    def _auto_save_backup_details(self, backup_id: int):
        """Yedekleme tamamlandığında dosya detaylarını otomatik kaydet"""
        self.last_backup_id = backup_id
        
        if not self.analysis_results:
            self._log_write("⚠️ Otomatik detay kaydetme: Analiz sonuçları bulunamadı!", "#FFA500")
            return
        
        # Tüm yedeklenen dosyaları topla
        file_details = []
        for mapping_id, result in self.analysis_results.items():
            files_to_backup = result.get('files_to_backup', [])
            for file_info in files_to_backup:
                if isinstance(file_info, dict):
                    file_path = file_info.get('path', '')
                    file_size = file_info.get('size', 0)
                    reason = file_info.get('reason', 'bilinmiyor')
                else:
                    # Eski format uyumluluğu
                    file_path = file_info
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    reason = 'bilinmiyor'
                
                # Dosya adını yoldan ayır
                file_name = os.path.basename(file_path)
                file_dir = os.path.dirname(file_path)
                
                # Önceki yedeklerdeki boyutu bul
                previous_size = self.db.get_previous_file_size(file_dir, file_name, backup_id)
                
                file_details.append({
                    'mapping_id': mapping_id,
                    'file_path': file_dir,
                    'file_name': file_name,
                    'file_size': file_size,
                    'previous_size': previous_size,
                    'backup_reason': reason
                })
        
        if not file_details:
            self._log_write("⚠️ Otomatik detay kaydetme: Kaydedilecek dosya detayı bulunamadı!", "#FFA500")
            return
        
        try:
            # Veritabanına kaydet
            self.db.add_backup_file_details(backup_id, file_details)
            
            # Log'a bilgi yaz
            self._log_write(f"✅ Dosya detayları otomatik olarak kaydedildi ({len(file_details)} dosya)", "#65FE65")
            
            # Butonu göstermeye gerek yok (zaten kaydedildi)
            self.last_backup_id = None
            self.last_backup_files = None
        except Exception as e:
            self._log_write(f"❌ Otomatik detay kaydetme hatası: {str(e)}", "#FF0000")
    
    def _show_history(self):
        """Geçmiş penceresini göster"""
        HistoryWindow(self, self.db)
