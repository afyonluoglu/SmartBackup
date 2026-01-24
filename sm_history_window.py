"""
Smart Backup - History Window
Tarih: 19 Kasım 2025
Yazar: Dr. Mustafa Afyonluoğlu

Gerekli Kütüphaneler:
    - customtkinter (pip install customtkinter)
    - tkinter (standart kütüphane)
"""

import customtkinter as ctk
from tkinter import ttk, Menu
from typing import List, Dict
from datetime import datetime
import os
import subprocess
import fnmatch
from sm_database import DatabaseManager
from sm_backup_engine import BackupEngine
from sm_ui_components import ConfirmDialog


class HistoryWindow(ctk.CTkToplevel):
    """Yedekleme geçmişi penceresi"""
    
    def __init__(self, parent, db_manager: DatabaseManager):
        super().__init__(parent)
        
        self.db = db_manager
        self.title("Yedekleme Geçmişi")
        self.geometry("1200x800+100+10")
        # self._center_window()
        
        # Ana pencerenin üzerinde görünmesini sağla
        self.transient(parent)
        self.lift()
        self.focus_force()
        
        # ESC tuşu ile kapat
        self.bind('<Escape>', lambda e: self.destroy())
        
        self._create_widgets()
        self._load_history()
    
    def _center_window(self):
        """Pencereyi ekranda ortala"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """Widget'ları oluştur"""
        # Ana frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ctk.CTkLabel(main_frame, text="Yedekleme Geçmişi",
                                   font=("", 18, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Treeview için frame
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Scrollbar'lar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ("Proje", "Tarih", "Analiz Süresi", "Yedekleme Süresi", "Kopyalanan", "Arşivlenen", 
                   "Atlanan", "Silinen", "Hariç Tutulan", "Toplam Boyut", "Kopyalanan Boyut", "Arşiv Boyut", 
                    "Atlanan Boyut", "Silinen Boyut", "Hariç Tutulan Boyut", "Durum", "_id")  # _id gizli kolon
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                 displaycolumns=("Proje", "Tarih", "Analiz Süresi", "Yedekleme Süresi", "Kopyalanan", "Arşivlenen", 
                                                "Atlanan", "Silinen", "Hariç Tutulan", "Toplam Boyut", "Kopyalanan Boyut", "Arşiv Boyut", 
                                                "Atlanan Boyut", "Silinen Boyut", "Hariç Tutulan Boyut", "Durum"))  # _id gösterilmez
        
        # Sütün başlıkları
        self.tree.heading("Proje", text="Proje")
        self.tree.heading("Tarih", text="Tarih")
        self.tree.heading("Analiz Süresi", text="Analiz (sn)")
        self.tree.heading("Yedekleme Süresi", text="Yedekleme (sn)")
        self.tree.heading("Kopyalanan", text="Kopyalanan")
        self.tree.heading("Arşivlenen", text="Arşivlenen")
        self.tree.heading("Atlanan", text="Atlanan")
        self.tree.heading("Silinen", text="Silinen")
        self.tree.heading("Hariç Tutulan", text="Hariç Tutulan")
        self.tree.heading("Toplam Boyut", text="Toplam Boyut")
        self.tree.heading("Kopyalanan Boyut", text="Kopyalanan Boyut")
        self.tree.heading("Arşiv Boyut", text="Arşiv Boyut")
        self.tree.heading("Atlanan Boyut", text="Atlanan Boyut")
        self.tree.heading("Silinen Boyut", text="Silinen Boyut")
        self.tree.heading("Hariç Tutulan Boyut", text="Hariç Tutulan Boyut")
        self.tree.heading("Durum", text="Durum")
        
        # Sütün genişlikleri
        self.tree.column("Proje", width=170, stretch=False)
        self.tree.column("Tarih", width=220, stretch=False)
        self.tree.column("Analiz Süresi", width=140, anchor="center", stretch=False)
        self.tree.column("Yedekleme Süresi", width=180, anchor="center", stretch=False)
        self.tree.column("Kopyalanan", width=145, anchor="center", stretch=False)
        self.tree.column("Arşivlenen", width=145, anchor="center", stretch=False)
        self.tree.column("Atlanan", width=140, anchor="center", stretch=False)
        self.tree.column("Silinen", width=140, anchor="center", stretch=False)
        self.tree.column("Hariç Tutulan", width=140, anchor="center", stretch=False)
        self.tree.column("Toplam Boyut", width=220, anchor="center", stretch=False)
        self.tree.column("Kopyalanan Boyut", width=220, anchor="center", stretch=False)
        self.tree.column("Arşiv Boyut", width=220, anchor="center", stretch=False)
        self.tree.column("Atlanan Boyut", width=220, anchor="center", stretch=False)
        self.tree.column("Silinen Boyut", width=220, anchor="center", stretch=False)
        self.tree.column("Hariç Tutulan Boyut", width=220, anchor="center", stretch=False)
        self.tree.column("Durum", width=150, anchor="center", stretch=False)
        self.tree.column("_id", width=0, stretch=False)  # Gizli kolon
        
        # Scrollbar yapılandırması
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Grid yerleşimi
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Çift tıklama ile detay göster
        self.tree.bind('<Double-Button-1>', lambda e: self._show_details())
        
        # Sağ tık context menü oluştur
        self._create_context_menu()
        self.tree.bind('<Button-3>', self._show_context_menu)
        
        # Butonlar
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="Detayları Göster",
                     command=self._show_details, width=130).pack(side="left", padx=(0, 5))
        ctk.CTkButton(button_frame, text="Seçili Kaydı Sil",
                     command=self._delete_selected, width=130,
                     fg_color="red", hover_color="darkred").pack(side="left", padx=(0, 5))
        ctk.CTkButton(button_frame, text="🔍 Ara",
                     command=self._show_file_search, width=100,
                     fg_color="#2D7D46", hover_color="#236835").pack(side="left")
        
        ctk.CTkButton(button_frame, text="Kapat", command=self.destroy,
                     width=100).pack(side="right")
    
    def _load_history(self):
        """Geçmişi yükle"""
        # Mevcut verileri temizle
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Veritabanından geçmişi al
        history = self.db.get_all_backup_history()
        
        for record in history:
            total_size = (record['total_size_copied'] + 
                         record['total_size_moved'] + 
                         record['total_size_skipped'] +
                         record.get('total_size_deleted', 0) +
                         record.get('total_size_excluded', 0))
            
            # DEBUG: Geçmiş tablosundaki değerleri kontrol et
            # print(f"DEBUG Geçmiş: id={record['id']}")
            # print(f"  size_copied: {record['total_size_copied']}")
            # print(f"  size_moved: {record['total_size_moved']}")
            # print(f"  size_skipped: {record['total_size_skipped']}")
            # print(f"  size_deleted: {record.get('total_size_deleted', 0)}")
            # print(f"  size_excluded: {record.get('total_size_excluded', 0)}")
            # print(f"  TOPLAM: {total_size} ({BackupEngine.format_size(total_size)})")
            
            # Analiz süresini al (eski kayıtlar için 0 olabilir)
            analysis_duration = record.get('analysis_duration_seconds', 0)
            
            # Tarihi formatla: YYYY-MM-DD HH:MM:SS -> DD-MM-YYYY HH:MM:SS
            backup_date = record['backup_date']
            try:
                from datetime import datetime
                dt = datetime.strptime(backup_date, '%Y-%m-%d %H:%M:%S')
                formatted_date = dt.strftime('%d-%m-%Y %H:%M:%S')
            except:
                formatted_date = backup_date  # Hata durumunda orijinali kullan
            
            self.tree.insert("", "end", values=(
                record['project_name'],
                formatted_date,
                f"{analysis_duration:.1f}",
                f"{record['duration_seconds']:.1f}",
                f"{record['total_files_copied']:,}",
                f"{record['total_files_moved_to_revisions']:,}",
                f"{record['total_files_skipped']:,}",
                f"{record.get('total_files_deleted_to_revisions', 0):,}",
                f"{record.get('total_files_excluded', 0):,}",
                BackupEngine.format_size(total_size),
                BackupEngine.format_size(record['total_size_copied']),
                BackupEngine.format_size(record['total_size_moved']),
                BackupEngine.format_size(record.get('total_size_skipped', 0)),
                BackupEngine.format_size(record.get('total_size_deleted', 0)),
                BackupEngine.format_size(record.get('total_size_excluded', 0)),
                record['status'],
                record['id']  # Gizli kolon - detay gösterme için gerekli
            ))
    
    def _show_details(self):
        """Seçili kaydın detaylarını göster"""
        selection = self.tree.selection()
        if not selection:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir kayıt seçin!")
            return
        
        item = self.tree.item(selection[0])
        backup_id = item['values'][-1]  # Son kolon (_id) backup_id'yi içerir
        
        # Detay penceresi aç
        DetailWindow(self, self.db, backup_id)
    
    def _delete_selected(self):
        """Seçili kayıtları sil (çoklu seçim destekler)"""
        selection = self.tree.selection()
        if not selection:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen en az bir kayıt seçin!")
            return
        
        # Seçili kayıt sayısını al
        count = len(selection)
        
        # Onay mesajını oluştur
        if count == 1:
            item = self.tree.item(selection[0])
            project_name = item['values'][0]  # Proje artık ilk kolon
            backup_date = item['values'][1]   # Tarih ikinci kolon
            confirm_msg = f"'{project_name}' projesinin {backup_date} tarihli yedekleme kaydını silmek istediğinizden emin misiniz?"
        else:
            confirm_msg = f"{count} adet yedekleme kaydını silmek istediğinizden emin misiniz?"
        
        # Onay al
        if not ConfirmDialog.ask(self, "Onay", confirm_msg):
            return
        
        # Tüm seçili kayıtları sil
        for item_id in selection:
            item = self.tree.item(item_id)
            backup_id = item['values'][-1]  # Son kolon (_id) backup_id'yi içerir
            self.db.delete_backup_history(backup_id)
        
        # Listeyi yenile
        self._load_history()
        
        if count == 1:
            ConfirmDialog.show_info(self, "Başarılı", "Kayıt başarıyla silindi.")
        else:
            ConfirmDialog.show_info(self, "Başarılı", f"{count} adet kayıt başarıyla silindi.")
    
    def _create_context_menu(self):
        """Sağ tık context menüsü oluştur"""
        list_font = ("Segoe UI", 11)
        self.context_menu = Menu(self, tearoff=0,
                                 background="#333333",
                                 foreground="white",
                                 activebackground="#1F6AA5",
                                 activeforeground="white",
                                 font=list_font)
        
        self.context_menu.add_command(label="📄 Kayıt Sayfası", command=self._show_record_page)
        self.context_menu.add_command(label="📋 Detayları Göster", command=self._show_details)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="� Dosya Ara", command=self._show_file_search)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Sil", command=self._delete_selected)

        list_font = ("Segoe UI", 13) 
        self.context_menu.config(font=list_font)   
    
    def _show_context_menu(self, event):
        """Context menüyü göster"""
        # Tıklanan satırı seç
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def _show_file_search(self):
        """Dosya arama penceresini göster"""
        FileSearchWindow(self, self.db)
    
    def _show_record_page(self):
        """Seçili kaydın özet sayfasını göster"""
        selection = self.tree.selection()
        if not selection:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir kayıt seçin!")
            return
        
        item = self.tree.item(selection[0])
        backup_id = item['values'][-1]  # Son kolon (_id) backup_id'yi içerir
        
        # Kayıt sayfası penceresini aç
        RecordPageWindow(self, self.db, backup_id)


class RecordPageWindow(ctk.CTkToplevel):
    """Yedekleme kaydı özet sayfası - Log ekranına benzer renkli görünüm"""
    
    # Renk sabitleri (log ekranındaki ile aynı)
    COLORS = {
        'header': "#00A0E9",       # Mavi çizgi
        'main_title': "#024FD3",   # Koyu mavi ana başlık
        'title': "#9ED9FA",        # Açık mavi başlık
        'label': "#FFAE35",        # Turuncu etiket
        'value_green': "#01F001",  # Yeşil (yedeklenen)
        'value_yellow': "#FFCC6C", # Sarı (atlanan)
        'value_orange': "#FFA500", # Turuncu (hariç tutulan)
        'value_red': "#FF6B6B",    # Kırmızı (silinen)
        'value_purple': "#D896FF", # Mor (arşivlenen)
        'info': "#60C2FF",         # Açık mavi (bilgi)
        'gray': "#ADADAD",         # Gri (detay)
        'white': "#FFFFFF",        # Beyaz
        'success': "#65FE65",      # Açık yeşil (başarılı)
    }
    
    def __init__(self, parent, db_manager: DatabaseManager, backup_id: int):
        super().__init__(parent)
        
        self.db = db_manager
        self.backup_id = backup_id
        
        self.title("Kayıt Sayfası")
        self.geometry("750x700+150+50")
        
        # ESC tuşu ile kapat
        self.bind('<Escape>', lambda e: self.destroy())
        
        # Ana pencerenin üzerinde görünmesini sağla
        self.transient(parent)
        self.lift()
        self.focus_force()
        
        self._create_widgets()
        self._load_record()
    
    def _create_widgets(self):
        """Widget'ları oluştur"""
        # Ana frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Başlık
        title_label = ctk.CTkLabel(main_frame, text="📋 YEDEKLEME KAYIT SAYFASI",
                                   font=("Segoe UI", 18, "bold"),
                                   text_color=self.COLORS['main_title'])
        title_label.pack(pady=(0, 10))
        
        # Metin alanı (log görünümü)
        self.text_box = ctk.CTkTextbox(main_frame, 
                                        font=("Consolas", 12),
                                        wrap="word",
                                        fg_color="#000000"                                        
                                        )
        self.text_box.pack(fill="both", expand=True, pady=(0, 10))
        
        # Alt butonlar
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="Detayları Göster",
                     command=self._show_details, width=130).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(button_frame, text="Kapat (ESC)", 
                     command=self.destroy,
                     width=100).pack(side="right")
    
    def _write_line(self, text: str, color: str = None):
        """Metin alanına satır yaz"""
        if color:
            tag_name = f"color_{color.replace('#', '')}"
            self.text_box.tag_config(tag_name, foreground=color)
            self.text_box.insert("end", text + "\n", tag_name)
        else:
            self.text_box.insert("end", text + "\n")
    
    def _write_separator(self):
        """Ayırıcı çizgi yaz"""
        self._write_line("═" * 70, self.COLORS['header'])
    
    def _write_item(self, label: str, value: str, label_color: str = None, value_color: str = None):
        """Etiket-değer çifti yaz"""
        label_col = label_color or self.COLORS['label']
        label_col = "#B0E7FF"

        value_col = value_color or self.COLORS['white']
        
        # Etiket
        tag_label = f"color_{label_col.replace('#', '')}"
        self.text_box.tag_config(tag_label, foreground=label_col)
        self.text_box.insert("end", f"  → {label}: ", tag_label)
        
        # Değer
        tag_value = f"color_{value_col.replace('#', '')}"
        self.text_box.tag_config(tag_value, foreground=value_col)
        self.text_box.insert("end", value + "\n", tag_value)
    
    def _load_record(self):
        """Kayıt bilgilerini yükle ve göster"""
        # Backup history kaydını al
        history_records = self.db.get_all_backup_history()
        record = None
        for r in history_records:
            if r['id'] == self.backup_id:
                record = r
                break
        
        if not record:
            self._write_line("Kayıt bulunamadı!", self.COLORS['value_red'])
            return
        
        # Tarihi formatla
        backup_date = record['backup_date']
        try:
            dt = datetime.strptime(backup_date, '%Y-%m-%d %H:%M:%S')
            formatted_date = dt.strftime('%d %B %Y, %H:%M:%S')
            day_name = dt.strftime('%A')
            # Türkçe gün ve ay isimleri
            day_names = {'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
                        'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'}
            month_names = {'January': 'Ocak', 'February': 'Şubat', 'March': 'Mart', 'April': 'Nisan',
                          'May': 'Mayıs', 'June': 'Haziran', 'July': 'Temmuz', 'August': 'Ağustos',
                          'September': 'Eylül', 'October': 'Ekim', 'November': 'Kasım', 'December': 'Aralık'}
            
            for eng, tr in month_names.items():
                formatted_date = formatted_date.replace(eng, tr)
            day_name = day_names.get(day_name, day_name)
        except:
            formatted_date = backup_date
            day_name = ""
        
        # Hesaplamalar
        total_size = (record['total_size_copied'] + 
                     record['total_size_moved'] + 
                     record['total_size_skipped'] +
                     record.get('total_size_deleted', 0) +
                     record.get('total_size_excluded', 0))
        
        total_files = (record['total_files_copied'] + 
                      record['total_files_moved_to_revisions'] + 
                      record['total_files_skipped'] +
                      record.get('total_files_deleted_to_revisions', 0) +
                      record.get('total_files_excluded', 0))
        
        analysis_duration = record.get('analysis_duration_seconds', 0)
        backup_duration = record['duration_seconds']
        total_duration = analysis_duration + backup_duration
        
        # ============ BAŞLIK ============
        self._write_separator()
        self._write_line(f"  {record['project_name'].upper()} - YEDEKLEME RAPORU", self.COLORS['title'])
        self._write_separator()
        
        # ============ GENEL BİLGİLER ============
        self._write_line("\n📅 GENEL BİLGİLER", self.COLORS['info'])
        self._write_line("─" * 50, self.COLORS['gray'])
        
        self._write_item("Proje Adı", record['project_name'], value_color=self.COLORS['white'])
        self._write_item("Tarih", f"{formatted_date} ({day_name})", value_color=self.COLORS['white'])
        
        status_color = self.COLORS['success'] if record['status'] == 'Tamamlandı' else self.COLORS['value_red']
        # print(f"DEBUG: Kayıt durumu = {record['status']}, renk = {status_color}")
        status_text = "✓ Tamamlandı" if record['status'] == 'Tamamlandı' else f"✗ {record['status']}"
        self._write_item("Durum", status_text, value_color=status_color)
        
        # ============ SÜRE BİLGİLERİ ============
        self._write_line("\n⏱️ SÜRE BİLGİLERİ", self.COLORS['info'])
        self._write_line("─" * 50, self.COLORS['gray'])
        
        self._write_item("Analiz Süresi", f"{analysis_duration:.1f} saniye", value_color=self.COLORS['gray'])
        self._write_item("Yedekleme Süresi", f"{backup_duration:.1f} saniye", value_color=self.COLORS['gray'])
        self._write_item("Toplam Süre", f"{total_duration:.1f} saniye ({total_duration/60:.1f} dakika)", value_color=self.COLORS['white'])
        
        # ============ DOSYA İSTATİSTİKLERİ ============
        self._write_line("\n📊 DOSYA İSTATİSTİKLERİ", self.COLORS['info'])
        self._write_line("─" * 50, self.COLORS['gray'])
        
        self._write_item("Toplam İncelenen Dosya", f"{total_files:,} adet ({BackupEngine.format_size(total_size)})", 
                        value_color=self.COLORS['info'])
        
        # Yedeklenen dosyalar
        if record['total_files_copied'] > 0:
            self._write_item("Yedeklenen Dosya", 
                           f"{record['total_files_copied']:,} adet ({BackupEngine.format_size(record['total_size_copied'])})",
                           value_color=self.COLORS['value_green'])
        
        # Atlanan dosyalar (güncel)
        if record['total_files_skipped'] > 0:
            self._write_item("Atlanan Dosya (güncel)", 
                           f"{record['total_files_skipped']:,} adet ({BackupEngine.format_size(record.get('total_size_skipped', 0))})",
                           value_color=self.COLORS['value_yellow'])
        
        # Hariç tutulan dosyalar
        excluded_files = record.get('total_files_excluded', 0)
        if excluded_files > 0:
            self._write_item("Hariç Tutulan (filtre)", 
                           f"{excluded_files:,} adet ({BackupEngine.format_size(record.get('total_size_excluded', 0))})",
                           value_color=self.COLORS['value_orange'])
        
        # Arşivlenen dosyalar (_REVISIONS)
        if record['total_files_moved_to_revisions'] > 0:
            self._write_item("Arşivlenen (_REVISIONS)", 
                           f"{record['total_files_moved_to_revisions']:,} adet ({BackupEngine.format_size(record['total_size_moved'])})",
                           value_color=self.COLORS['value_purple'])
        
        # Silinen dosyalar (kaynakta yok)
        deleted_files = record.get('total_files_deleted_to_revisions', 0)
        if deleted_files > 0:
            self._write_item("Silinen (kaynakta yok)", 
                           f"{deleted_files:,} adet ({BackupEngine.format_size(record.get('total_size_deleted', 0))})",
                           value_color=self.COLORS['value_red'])
        
        # ============ ÖZET ============
        self._write_line("\n" + "═" * 70, self.COLORS['header'])
        self._write_line("  📋 ÖZET", self.COLORS['title'])
        self._write_separator()
        
        # Özet satırları
        summary_lines = []
        if record['total_files_copied'] > 0:
            summary_lines.append(f"• Yedeklenen: {record['total_files_copied']:,} dosya ({BackupEngine.format_size(record['total_size_copied'])})")
        if record['total_files_skipped'] > 0:
            summary_lines.append(f"• Atlanan: {record['total_files_skipped']:,} dosya")
        if excluded_files > 0:
            summary_lines.append(f"• Hariç Tutulan: {excluded_files:,} dosya")
        if record['total_files_moved_to_revisions'] > 0:
            summary_lines.append(f"• Arşivlenen: {record['total_files_moved_to_revisions']:,} dosya")
        if deleted_files > 0:
            summary_lines.append(f"• Silinen: {deleted_files:,} dosya")
        
        for line in summary_lines:
            self._write_line("  " + line, self.COLORS['gray'])
        
        self._write_line("", None)
        self._write_line(f"  ⏱️ İşlem Süresi: {total_duration:.1f} saniye", self.COLORS['gray'])
        self._write_separator()
        
        # ============ EK BİLGİLER ============
        # Dosya detayları var mı kontrol et
        has_file_details = self.db.has_backup_file_details(self.backup_id)
        
        self._write_line("\n💡 EK BİLGİLER", self.COLORS['info'])
        self._write_line("─" * 50, self.COLORS['gray'])
        
        if has_file_details:
            file_details = self.db.get_backup_file_details(self.backup_id)
            self._write_line(f"  • Dosya detay kaydı: {len(file_details)} adet dosya", self.COLORS['gray'])
        else:
            self._write_line("  • Dosya detay kaydı: Mevcut değil", self.COLORS['gray'])
        
        # Backup detayları (mapping bazlı)
        backup_details = self.db.get_backup_details(self.backup_id)
        if backup_details:
            self._write_line(f"  • Eşleşme sayısı: {len(backup_details)} adet", self.COLORS['gray'])
        
        # Pencere başlığını güncelle
        self.title(f"Kayıt Sayfası - {record['project_name']}")
        
        # Scroll'u en başa al
        self.text_box.see("1.0")
        
        # Metin alanını salt okunur yap
        self.text_box.configure(state="disabled")
    
    def _show_details(self):
        """Detay penceresini aç"""
        DetailWindow(self, self.db, self.backup_id)


class DetailWindow(ctk.CTkToplevel):
    """Yedekleme detay penceresi"""
    
    def __init__(self, parent, db_manager: DatabaseManager, backup_id: int):
        super().__init__(parent)
        
        self.db = db_manager
        self.backup_id = backup_id
        
        self.title("Yedekleme Detayları")
        self.geometry("1200x700+100+10")
        # self._center_window()
        
        # ESC tuşu ile kapat
        self.bind('<Escape>', lambda e: self.destroy())
        
        # Renk paleti - farklı eşleşme grupları için
        self.bg_colors = [
            '#2b3e50',  # Koyu mavi-gri
            "#2c4b6b",  # Koyu gri
            "#335F5B",  # Orta koyu gri
            "#6b552e",  # Açık koyu gri
            "#742F28",  # Alternatif koyu ton
            "#234a46",  # Çok koyu ton
        ]
        
        self._create_widgets()
        self._load_details()
    
    def _setup_treeview_styles(self):
        """Treeview için stilleri tanımla"""
        style = ttk.Style()
        
        # Her eşleşme grubu için farklı tag'ler oluştur
        for i, color in enumerate(self.bg_colors):
            tag_name = f'match_group_{i}'
            style.map('Treeview',
                     background=[('selected', '#1f538d')],
                     foreground=[('selected', 'white')])
        
        # "Daha yeni" için parlak yeşil renk
        style.configure('newer.Treeview', foreground='#00ff00')
        style.configure('new.Treeview', foreground="#00d5ff")
    
    def _center_window(self):
        """Pencereyi ekranda ortala"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """Widget'ları oluştur"""
        # Ana frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Treeview stilleri için renk paleti tanımla
        self._setup_treeview_styles()
        
        # Başlık - Eşleşme Detayları
        title_label = ctk.CTkLabel(main_frame, text="Eşleşme Detayları",
                                   font=("", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Treeview için frame (Eşleşme detayları)
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.pack(fill="x", pady=(0, 15))
        
        # Scrollbar'lar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ("Kaynak", "Hedef", "Kopyalanan", "Arşivlenen", 
                   "Atlanan", "Silinen", "Hariç Tutulan", "Boyut")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                height=5)
        
        # Sütün başlıkları
        self.tree.heading("Kaynak", text="Kaynak Klasör")
        self.tree.heading("Hedef", text="Hedef Klasör")
        self.tree.heading("Kopyalanan", text="Kopyalanan")
        self.tree.heading("Arşivlenen", text="Arşivlenen")
        self.tree.heading("Atlanan", text="Atlanan")
        self.tree.heading("Silinen", text="Silinen")
        self.tree.heading("Hariç Tutulan", text="Hariç Tutulan")
        self.tree.heading("Boyut", text="Toplam Boyut")
        
        # Sütün genişlikleri
        self.tree.column("Kaynak", width=250)
        self.tree.column("Hedef", width=250)
        self.tree.column("Kopyalanan", width=90, anchor="center")
        self.tree.column("Arşivlenen", width=90, anchor="center")
        self.tree.column("Atlanan", width=80, anchor="center")
        self.tree.column("Silinen", width=80, anchor="center")
        self.tree.column("Hariç Tutulan", width=140, anchor="center")
        self.tree.column("Boyut", width=120, anchor="center")
        
        # Scrollbar yapılandırması
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Grid yerleşimi
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Dosya Detayları başlık
        self.file_details_label = ctk.CTkLabel(main_frame, text="Dosya Detayları",
                                               font=("", 16, "bold"))
        self.file_details_label.pack(pady=(10, 10))
        
        # Dosya Detayları için Treeview frame
        file_tree_frame = ctk.CTkFrame(main_frame)
        file_tree_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Scrollbar'lar
        file_vsb = ttk.Scrollbar(file_tree_frame, orient="vertical")
        file_hsb = ttk.Scrollbar(file_tree_frame, orient="horizontal")
        
        # Dosya Detayları Treeview
        file_columns = ("Dizin", "Dosya Adı", "Boyut", "Önceki Boyut", "Yedekleme Sebebi")
        self.file_tree = ttk.Treeview(file_tree_frame, columns=file_columns, 
                                      show="headings",
                                      yscrollcommand=file_vsb.set, 
                                      xscrollcommand=file_hsb.set)
        
        # Sütün başlıkları
        self.file_tree.heading("Dizin", text="Dosya Dizini")
        self.file_tree.heading("Dosya Adı", text="Dosya Adı")
        self.file_tree.heading("Boyut", text="Boyut")
        self.file_tree.heading("Önceki Boyut", text="Önceki Boyut")
        self.file_tree.heading("Yedekleme Sebebi", text="Yedekleme Sebebi")
        
        # Sütün genişlikleri
        self.file_tree.column("Dizin", width=400)
        self.file_tree.column("Dosya Adı", width=250)
        self.file_tree.column("Boyut", width=100, anchor="center")
        self.file_tree.column("Önceki Boyut", width=100, anchor="center")
        self.file_tree.column("Yedekleme Sebebi", width=150, anchor="center")
        
        # Scrollbar yapılandırması
        file_vsb.config(command=self.file_tree.yview)
        file_hsb.config(command=self.file_tree.xview)
        
        # Grid yerleşimi
        self.file_tree.grid(row=0, column=0, sticky="nsew")
        file_vsb.grid(row=0, column=1, sticky="ns")
        file_hsb.grid(row=1, column=0, sticky="ew")
        
        file_tree_frame.grid_rowconfigure(0, weight=1)
        file_tree_frame.grid_columnconfigure(0, weight=1)
        
        # Dosya tablosu için context menü oluştur
        self._create_file_context_menu()
        self.file_tree.bind('<Button-3>', self._show_file_context_menu)
        
        # Kapat butonu
        ctk.CTkButton(main_frame, text="Kapat", command=self.destroy,
                     width=100).pack()
    
    def _load_details(self):
        """Detayları yükle"""
        # Eşleşme detaylarını yükle
        details = self.db.get_backup_details(self.backup_id)
        
        for detail in details:
            total_size = (detail['size_copied'] + 
                         detail['size_moved'] + 
                         detail['size_skipped'] +
                         detail.get('size_deleted', 0) +
                         detail.get('size_excluded', 0))
            
            # DEBUG: Detay penceresindeki değerleri kontrol et
            # print(f"DEBUG Detay: mapping_id={detail['mapping_id']}")
            # print(f"  size_copied: {detail['size_copied']}")
            # print(f"  size_moved: {detail['size_moved']}")
            # print(f"  size_skipped: {detail['size_skipped']}")
            # print(f"  size_deleted: {detail.get('size_deleted', 0)}")
            # print(f"  size_excluded: {detail.get('size_excluded', 0)}")
            # print(f"  TOPLAM: {total_size} ({BackupEngine.format_size(total_size)})")
            
            self.tree.insert("", "end", values=(
                detail['source_path'],
                detail['target_path'],
                detail['files_copied'],
                detail['files_moved'],
                detail['files_skipped'],
                detail.get('files_deleted', 0),
                detail.get('files_excluded', 0),
                BackupEngine.format_size(total_size)
            ))
        
        # Dosya detaylarını yükle
        file_details = self.db.get_backup_file_details(self.backup_id)
        
        # DEBUG: Dosya detayları kontrolü
        # print(f"\n========== DOSYA DETAYLARI DEBUG ==========")
        # print(f"Backup ID: {self.backup_id}")
        # print(f"Dönen kayıt sayısı: {len(file_details) if file_details else 0}")
        # if file_details:
        #     print(f"İlk kayıt örneği: {file_details[0]}")
        #     print(f"Toplam kayıt: {len(file_details)}")
        # else:
        #     print("HİÇ KAYIT DÖNMÜYOR!")
        #     # Veritabanında bu backup_id ile kayıt var mı kontrol et
        #     has_details = self.db.has_backup_file_details(self.backup_id)
        #     print(f"Veritabanında kayıt var mı? {has_details}")
        # print(f"===========================================\n")
        
        if file_details:
            self.file_details_label.configure(text=f"Dosya Detayları ({len(file_details)} dosya)")
            
            # mapping_id'ye göre grupla - her grup farklı renk alacak
            mapping_groups = {}
            for file_detail in file_details:
                mapping_id = file_detail.get('mapping_id', 0)
                if mapping_id not in mapping_groups:
                    mapping_groups[mapping_id] = []
                mapping_groups[mapping_id].append(file_detail)
            
            # print(f"DEBUG: Mapping grupları: {list(mapping_groups.keys())}")
            # print(f"DEBUG: Grup sayısı: {len(mapping_groups)}")
            
            # Her mapping grubu için farklı renk ata
            for group_index, (mapping_id, files) in enumerate(sorted(mapping_groups.items())):
                color_index = group_index % len(self.bg_colors)
                bg_color = self.bg_colors[color_index]
                tag_name = f'match_group_{group_index}'
                
                # print(f"DEBUG: Grup {group_index} - mapping_id={mapping_id}, dosya sayısı={len(files)}, renk={bg_color}")
                
                # Bu grup için tag yapılandır
                self.file_tree.tag_configure(tag_name, background=bg_color)
                
                # Dosyaları ekle
                for file_detail in files:
                    # Önceki boyutu formatla (varsa)
                    previous_size = file_detail.get('previous_size')
                    previous_size_str = BackupEngine.format_size(previous_size) if previous_size is not None else "-"
                    
                    backup_reason = file_detail['backup_reason']
                    
                    # Satırı ekle
                    item_id = self.file_tree.insert("", "end", values=(
                        file_detail['file_path'],
                        file_detail['file_name'],
                        BackupEngine.format_size(file_detail['file_size']),
                        previous_size_str,
                        backup_reason
                    ), tags=(tag_name,))
                    
                    # "daha yeni" ise özel renklendirme yap
                    if backup_reason.lower() == "daha yeni":
                        # Parlak yeşil renk için özel tag ekle
                        newer_tag = f'{tag_name}_newer'
                        self.file_tree.tag_configure(newer_tag, background=bg_color, foreground='#00ff00')
                        self.file_tree.item(item_id, tags=(newer_tag,))

                    if backup_reason.lower() == "yeni dosya":
                        new_tag = f'{tag_name}_new'
                        self.file_tree.tag_configure(new_tag, background=bg_color, foreground="#ffea00")
                        self.file_tree.item(item_id, tags=(new_tag,))

            # Dosya detaylarını sakla (context menü için)
            self.file_details_data = file_details

            # print(f"DEBUG: Toplam {len(file_details)} dosya Treeview'e eklendi.\n")
        else:
            self.file_details_data = []
            self.file_details_label.configure(text="Dosya Detayları (Kayıt yok)")
    
    def _create_file_context_menu(self):
        """Dosya tablosu için context menü oluştur"""
        list_font = ("Segoe UI", 13)
        self.file_context_menu = Menu(self, tearoff=0,
                                      background="#333333",
                                      foreground="white",
                                      activebackground="#1F6AA5",
                                      activeforeground="white",
                                      font=list_font)
        
        self.file_context_menu.add_command(label="📜 Geçmişini Göster", command=self._show_file_history)
        self.file_context_menu.add_separator()
        self.file_context_menu.add_command(label="📂 Dosya Konumunu Aç", command=self._open_file_location)
    
    def _show_file_context_menu(self, event):
        """Dosya tablosu context menüsünü göster"""
        # Tıklanan satırı seç
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            try:
                self.file_context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.file_context_menu.grab_release()
    
    def _get_selected_file_data(self):
        """Seçili dosyanın verilerini al"""
        selection = self.file_tree.selection()
        if not selection:
            return None
        
        item = self.file_tree.item(selection[0])
        values = item['values']
        
        # file_path (dizin) ve file_name değerlerini al
        file_path = values[0]
        file_name = values[1]
        
        # file_details_data içinden eşleşen kaydı bul
        if hasattr(self, 'file_details_data'):
            for detail in self.file_details_data:
                if detail['file_path'] == file_path and detail['file_name'] == file_name:
                    return detail
        
        # Eğer detay bulunamazsa basit bir dict döndür
        return {
            'file_path': file_path,
            'file_name': file_name
        }
    
    def _show_file_history(self):
        """Seçili dosyanın revision geçmişini göster"""
        file_data = self._get_selected_file_data()
        if not file_data:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir dosya seçin!")
            return
        
        # Backup details'dan hedef klasörü al
        details = self.db.get_backup_details(self.backup_id)
        if not details:
            ConfirmDialog.show_warning(self, "Uyarı", "Hedef klasör bilgisi bulunamadı!")
            return
        
        # mapping_id'ye göre hedef klasörü bul
        target_path = None
        mapping_id = file_data.get('mapping_id')
        
        if mapping_id:
            for detail in details:
                if detail['mapping_id'] == mapping_id:
                    target_path = detail['target_path']
                    break
        
        # Eğer mapping_id yoksa veya bulunamazsa, ilk detayı kullan
        if not target_path and details:
            target_path = details[0]['target_path']
        
        if not target_path:
            ConfirmDialog.show_warning(self, "Uyarı", "Hedef klasör bilgisi bulunamadı!")
            return
        
        # FileHistoryWindow aç
        FileHistoryWindow(self, self.db, file_data['file_path'], file_data['file_name'], target_path)
    
    def _open_file_location(self):
        """Seçili dosyanın konumunu Windows Explorer'da aç"""
        file_data = self._get_selected_file_data()
        if not file_data:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir dosya seçin!")
            return
        
        # Tam dosya yolunu oluştur
        full_path = os.path.join(file_data['file_path'], file_data['file_name'])
        
        if os.path.exists(full_path):
            # Windows Explorer'da dosyayı seçili olarak aç
            subprocess.run(['explorer', '/select,', os.path.normpath(full_path)])
        else:
            ConfirmDialog.show_warning(self, "Uyarı", f"Dosya bulunamadı:\n{full_path}")


class FileHistoryWindow(ctk.CTkToplevel):
    """Dosya revision geçmişi penceresi"""
    
    def __init__(self, parent, db_manager: DatabaseManager, file_path: str, file_name: str, target_path: str):
        super().__init__(parent)
        
        self.db = db_manager
        self.file_path = file_path
        self.file_name = file_name
        self.target_path = target_path
        
        self.title(f"Dosya Geçmişi - {file_name}")
        self.geometry("1200x750+150+100")
        
        # ESC tuşu ile kapat
        self.bind('<Escape>', lambda e: self.destroy())
        
        # Ana pencerenin üzerinde görünmesini sağla
        self.transient(parent)
        self.lift()
        self.focus_force()
        
        self._create_widgets()
        self._load_file_history()
    
    def _create_widgets(self):
        """Widget'ları oluştur"""
        # Ana frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ctk.CTkLabel(main_frame, text=f"📜 {self.file_name} - Revision Geçmişi",
                                   font=("", 16, "bold"))
        title_label.pack(pady=(0, 5))
        
        # Dosya yolu bilgisi
        path_label = ctk.CTkLabel(main_frame, text=f"Dizin: {self.file_path}",
                                  font=("", 11), text_color="gray")
        path_label.pack(pady=(0, 15))
        
        # Treeview frame
        tree_frame = ctk.CTkFrame(main_frame, height = 400)
        tree_frame.pack(fill="x", expand=False, pady=(0, 15))
        tree_frame.pack_propagate(False)
        
        # Scrollbar'lar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ("Tarih", "Boyut", "Sebep", "Durum", "Tam Yol")
        self.tree = ttk.Treeview(tree_frame, columns=columns, 
                                 show="headings", height=21,
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Sütun başlıkları
        self.tree.heading("Tarih", text="Yedekleme Tarihi")
        self.tree.heading("Boyut", text="Dosya Boyutu")
        self.tree.heading("Sebep", text="Y.Sebebi")
        self.tree.heading("Durum", text="Dosya Durumu")
        self.tree.heading("Tam Yol", text="Dosya Konumu")
        
        # Sütun genişlikleri
        self.tree.column("Tarih", width=200, stretch=False, anchor="center")
        self.tree.column("Boyut", width=140, stretch=False, anchor="center")
        self.tree.column("Sebep", width=140, stretch=False, anchor="center")
        self.tree.column("Durum", width=170, stretch=False, anchor="center")
        self.tree.column("Tam Yol", width=900, stretch=False)
        
        # Scrollbar yapılandırması
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Grid yerleşimi
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Context menü oluştur
        self._create_context_menu()
        self.tree.bind('<Button-3>', self._show_context_menu)
        self.tree.bind('<Double-Button-1>', lambda e: self._show_in_explorer())
        
        # Butonlar
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="📂 Göster",
                     command=self._show_in_explorer, width=100).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(button_frame, text="Kapat (ESC)",
                     command=self.destroy, width=100).pack(side="right")
    
    def _create_context_menu(self):
        """Context menü oluştur"""
        list_font = ("Segoe UI", 13)
        self.context_menu = Menu(self, tearoff=0,
                                 background="#333333",
                                 foreground="white",
                                 activebackground="#1F6AA5",
                                 activeforeground="white",
                                 font=list_font)
        
        self.context_menu.add_command(label="📂 Göster", command=self._show_in_explorer)
    
    def _show_context_menu(self, event):
        """Context menüyü göster"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def _load_file_history(self):
        """Dosyanın revision geçmişini veritabanından yükle"""
        # Veritabanından dosya geçmişini al
        history = self.db.get_file_revision_history(self.file_path, self.file_name)
        
        if not history:
            self.tree.insert("", "end", values=("", "", "Veritabanında kayıt bulunamadı", "", ""))
            return
        
        # Tag'leri yapılandır
        self.tree.tag_configure('missing', background='#FF6B6B', foreground='white')
        self.tree.tag_configure('exists', background='', foreground='')
        
        for record in history:
            # Tarihi formatla
            try:
                dt = datetime.strptime(record['backup_date'], '%Y-%m-%d %H:%M:%S')
                formatted_date = dt.strftime('%d.%m.%Y %H:%M')
                date_folder = dt.strftime('%Y-%m-%d %H-%M')
            except (ValueError, TypeError):
                formatted_date = record['backup_date']
                date_folder = record['backup_date']
            
            # Hedef yol - kayıttaki target_path veya varsayılan target_path kullan
            target_path = record.get('target_path') or self.target_path
            
            # Dosyanın hedef klasöre göre göreli yolunu hesapla
            relative_path = ""
            if self.file_path.startswith(target_path):
                relative_path = os.path.relpath(self.file_path, target_path)
                if relative_path == ".":
                    relative_path = ""
            
            # _REVISIONS klasöründeki dosya yolunu oluştur
            revisions_base = os.path.join(target_path, '_REVISIONS')
            if relative_path:
                expected_path = os.path.join(revisions_base, date_folder, relative_path, self.file_name)
            else:
                expected_path = os.path.join(revisions_base, date_folder, self.file_name)
            
            # Dosyanın fiziksel olarak var olup olmadığını kontrol et
            file_exists = os.path.exists(expected_path)
            
            # Durum ve tag belirleme
            if file_exists:
                status = "✓ Mevcut"
                tag = 'exists'
            else:
                status = "✗ Bulunamadı"
                tag = 'missing'
            
            # Treeview'e ekle
            self.tree.insert("", "end", values=(
                formatted_date,
                BackupEngine.format_size(record['file_size']),
                record['backup_reason'],
                status,
                expected_path
            ), tags=(tag,))
    
    def _show_in_explorer(self):
        """Seçili revision'u Windows Explorer'da göster"""
        selection = self.tree.selection()
        if not selection:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir revision seçin!")
            return
        
        item = self.tree.item(selection[0])
        full_path = item['values'][4]
        
        # print(f"DEBUG: Dosya yolu = {full_path}")
        if full_path and os.path.exists(full_path):
            # Windows Explorer'da dosyayı seçili olarak aç
            subprocess.run(['explorer', '/select,', os.path.normpath(full_path)])
        else:
            ConfirmDialog.show_warning(self, "Uyarı", "Dosya bulunamadı!")


class FileSearchWindow(ctk.CTkToplevel):
    """Yedekleme veritabanında dosya arama penceresi"""
    
    MAX_DISPLAY_RESULTS = 200  # Maksimum gösterilecek satır sayısı
    
    def __init__(self, parent, db_manager: DatabaseManager):
        super().__init__(parent)
        
        self.db = db_manager
        self.search_results = []  # Arama sonuçlarını sakla
        
        self.title("Dosya Arama")
        self.geometry("1100x700+150+50")
        
        # ESC tuşu ile kapat
        self.bind('<Escape>', lambda e: self.destroy())
        
        # Ana pencerenin üzerinde görünmesini sağla
        self.transient(parent)
        self.lift()
        self.focus_force()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Widget'ları oluştur"""
        # Ana frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ctk.CTkLabel(main_frame, text="🔍 Arşivde Dosya Arama",
                                   font=("", 18, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Arama frame
        search_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        
        # Arama etiket
        search_label = ctk.CTkLabel(search_frame, text="Aranacak kelime:",
                                    font=("", 12))
        search_label.pack(side="left", padx=(0, 10))
        
        # Arama alanı
        self.search_entry = ctk.CTkEntry(search_frame, width=400, 
                                         placeholder_text="Dosya adı veya wildcard (örn: *.py, test*.txt)")
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind('<Return>', lambda e: self._perform_search())
        
        # Arama butonu
        self.search_btn = ctk.CTkButton(search_frame, text="Ara",
                                        command=self._perform_search, width=80)
        self.search_btn.pack(side="left", padx=(0, 10))
        
        # Temizle butonu
        ctk.CTkButton(search_frame, text="Temizle",
                     command=self._clear_search, width=80,
                     fg_color="gray", hover_color="darkgray").pack(side="left")
        
        # Bilgi frame
        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 10))
        
        # Sonuç sayısı etiketi
        self.result_label = ctk.CTkLabel(info_frame, text="",
                                         font=("", 11), text_color="#60C2FF")
        self.result_label.pack(side="left")
        
        # Bilgi etiketi
        info_text = "💡 İpucu: Wildcard kullanmak için * veya ? kullanın. Örn: *.py, test*.txt, dosya?.doc"
        self.info_label = ctk.CTkLabel(info_frame, text=info_text,
                                       font=("", 10), text_color="gray")
        self.info_label.pack(side="right")
        
        # Treeview frame
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Scrollbar'lar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ("Tarih", "Dosya Adı", "Boyut", "Dizin", "İşlem")
        self.tree = ttk.Treeview(tree_frame, columns=columns, 
                                 show="headings",
                                 yscrollcommand=vsb.set, 
                                 xscrollcommand=hsb.set)
        
        # Sütun başlıkları
        self.tree.heading("Tarih", text="Yedekleme Tarihi", command=lambda: self._sort_column("Tarih"))
        self.tree.heading("Dosya Adı", text="Dosya Adı", command=lambda: self._sort_column("Dosya Adı"))
        self.tree.heading("Boyut", text="Boyut", command=lambda: self._sort_column("Boyut"))
        self.tree.heading("Dizin", text="Dosya Dizini", command=lambda: self._sort_column("Dizin"))
        self.tree.heading("İşlem", text="İşlem Türü", command=lambda: self._sort_column("İşlem"))
        
        # Sütun genişlikleri
        self.tree.column("Tarih", width=160, stretch=False, anchor="center")
        self.tree.column("Dosya Adı", width=250, stretch=False)
        self.tree.column("Boyut", width=100, stretch=False, anchor="center")
        self.tree.column("Dizin", width=450, stretch=True)
        self.tree.column("İşlem", width=120, stretch=False, anchor="center")
        
        # Scrollbar yapılandırması
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Grid yerleşimi
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Çift tıklama ile klasörü aç
        self.tree.bind('<Double-Button-1>', lambda e: self._open_folder())
        
        # Context menü oluştur
        self._create_context_menu()
        self.tree.bind('<Button-3>', self._show_context_menu)
        
        # Alt butonlar
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="📂 Klasörü Aç",
                     command=self._open_folder, width=120).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(button_frame, text="📜 Dosya Geçmişi",
                     command=self._show_file_history, width=120).pack(side="left")
        
        ctk.CTkButton(button_frame, text="Kapat (ESC)",
                     command=self.destroy, width=100).pack(side="right")
        
        # Sıralama durumu
        self.sort_column = None
        self.sort_reverse = False
        
        # Arama alanına odaklan
        self.search_entry.focus_set()
    
    def _create_context_menu(self):
        """Context menü oluştur"""
        list_font = ("Segoe UI", 13)
        self.context_menu = Menu(self, tearoff=0,
                                 background="#333333",
                                 foreground="white",
                                 activebackground="#1F6AA5",
                                 activeforeground="white",
                                 font=list_font)
        
        self.context_menu.add_command(label="📂 Klasörü Aç", command=self._open_folder)
        self.context_menu.add_command(label="📜 Dosya Geçmişi", command=self._show_file_history)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 Yolu Kopyala", command=self._copy_path)
    
    def _show_context_menu(self, event):
        """Context menüyü göster"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def _perform_search(self):
        """Arama işlemini gerçekleştir"""
        search_term = self.search_entry.get().strip()
        
        if not search_term:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen aranacak bir kelime girin!")
            return
        
        # Mevcut sonuçları temizle
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Wildcard kontrolü
        has_wildcard = '*' in search_term or '?' in search_term
        
        # Veritabanından arama yap
        self.search_results = self.db.search_files_in_backup(search_term, has_wildcard)
        
        # Her sonuç için revision klasör yolunu hesapla
        for result in self.search_results:
            result['display_path'] = self._calculate_revision_path(result)
        
        total_count = len(self.search_results)
        display_count = min(total_count, self.MAX_DISPLAY_RESULTS)
        
        # Sonuç etiketini güncelle
        if total_count == 0:
            self.result_label.configure(text="Sonuç bulunamadı.", text_color="#FF6B6B")
        elif total_count > self.MAX_DISPLAY_RESULTS:
            self.result_label.configure(
                text=f"Toplam {total_count:,} dosya bulundu. İlk {self.MAX_DISPLAY_RESULTS} sonuç gösteriliyor.",
                text_color="#FFA500"
            )
        else:
            self.result_label.configure(
                text=f"Toplam {total_count:,} dosya bulundu.",
                text_color="#60C2FF"
            )
        
        # Sonuçları tabloya ekle
        for i, result in enumerate(self.search_results[:display_count]):
            # DEBUG: İlk 5 sonuç için bilgileri yazdır
            if i < 5:
                print(f"DEBUG Sonuç {i+1}: {result['file_name']} ({result['backup_date']})")
                print(f"  display_path: {result.get('display_path')}")
            
            # Tarihi formatla
            try:
                dt = datetime.strptime(result['backup_date'], '%Y-%m-%d %H:%M:%S')
                formatted_date = dt.strftime('%d.%m.%Y %H:%M')
            except (ValueError, TypeError):
                formatted_date = result['backup_date']
            
            self.tree.insert("", "end", values=(
                formatted_date,
                result['file_name'],
                BackupEngine.format_size(result['file_size']),
                result['display_path'],  # Revision veya hedef klasör yolu
                result['backup_reason']
            ))
    
    def _calculate_revision_path(self, result: dict) -> str:
        """Dosyanın o tarihteki revision klasöründeki tam yolunu hesapla
        
        backup_reason'a göre:
        - "yeni dosya" veya "daha yeni": Dosya hedef klasörde veya _REVISIONS altında olabilir
        - Tarih bilgisine göre _REVISIONS klasör yapısını oluştur
        
        Args:
            result: Arama sonucu dict
        
        Returns:
            Dosyanın tam yolu (ya hedef klasörde ya da _REVISIONS altında)
        """
        source_path = result.get('source_path', '') or ''
        target_path = result.get('target_path', '') or ''
        file_path = result.get('file_path', '') or ''
        file_name = result.get('file_name', '')
        backup_date = result.get('backup_date', '')
        backup_reason = result.get('backup_reason', '').lower()
        
        if not source_path or not target_path or source_path == 'None' or target_path == 'None':
            return file_path
        
        # Yolları normalleştir
        source_path_norm = os.path.normpath(source_path)
        target_path_norm = os.path.normpath(target_path)
        file_path_norm = os.path.normpath(file_path)
        
        # Göreli yolu hesapla (source_path'ten sonraki kısım)
        relative_path = ""
        if file_path_norm.lower().startswith(source_path_norm.lower()):
            relative_path = file_path_norm[len(source_path_norm):].lstrip('\\/')
        
        # Hedef klasördeki dosyanın dizini
        if relative_path:
            target_file_dir = os.path.join(target_path_norm, relative_path)
        else:
            target_file_dir = target_path_norm
        
        # Tarihi _REVISIONS klasör formatına çevir
        try:
            dt = datetime.strptime(backup_date, '%Y-%m-%d %H:%M:%S')
            date_folder = dt.strftime('%Y-%m-%d %H-%M')
        except (ValueError, TypeError):
            date_folder = backup_date.replace(':', '-').replace(' ', '_') if backup_date else ''
        
        # _REVISIONS klasöründeki yol
        # Yapı: hedef_klasör/_REVISIONS/YYYY-MM-DD HH-MM/göreli_yol/dosya
        if relative_path:
            revision_file_path = os.path.join(target_path_norm, '_REVISIONS', date_folder, relative_path, file_name)
        else:
            revision_file_path = os.path.join(target_path_norm, '_REVISIONS', date_folder, file_name)
        
        # Hedef klasördeki dosya yolu
        target_file_path = os.path.join(target_file_dir, file_name)
        
        # Önce _REVISIONS'da ara, sonra hedef klasörde
        if os.path.exists(revision_file_path):
            # Dosya _REVISIONS klasöründe - dizin yolunu döndür
            return os.path.dirname(revision_file_path)
        elif os.path.exists(target_file_path):
            # Dosya hedef klasörde (güncel dosya) - dizin yolunu döndür
            return target_file_dir
        else:
            # Dosya bulunamadı - _REVISIONS yolunu göster (disk takılı olmayabilir)
            return os.path.dirname(revision_file_path)
    
    def _calculate_target_folder(self, result: dict) -> str:
        """Dosyanın hedef klasördeki yolunu hesapla (eski metod - geriye uyumluluk için)
        
        Args:
            result: Arama sonucu dict (source_path, target_path, file_path içermeli)
        
        Returns:
            Hedef klasördeki dosya dizini yolu
        """
        source_path = result.get('source_path', '') or ''
        target_path = result.get('target_path', '') or ''
        file_path = result.get('file_path', '') or ''
        
        if not source_path or not target_path or source_path == 'None' or target_path == 'None':
            # Mapping bilgisi yoksa file_path'i olduğu gibi döndür
            return file_path
        
        # Yolları normalleştir - hem / hem \ karakterlerini aynı hale getir
        source_path_norm = os.path.normpath(source_path)
        target_path_norm = os.path.normpath(target_path)
        file_path_norm = os.path.normpath(file_path)
        
        # file_path'in source_path'e göre göreli kısmını bul
        # Örnek: source_path = "C:\D\1\LIBRARY", file_path = "C:\D\1\LIBRARY\DOCS"
        # relative = "DOCS"
        if file_path_norm.lower().startswith(source_path_norm.lower()):
            # Kaynak yoldan göreli yolu çıkar
            relative_path = file_path_norm[len(source_path_norm):].lstrip('\\/')
            # Hedef yola ekle
            if relative_path:
                return os.path.join(target_path_norm, relative_path)
            else:
                return target_path_norm
        else:
            # file_path kaynak yolu içermiyorsa olduğu gibi döndür
            return file_path
    
    def _clear_search(self):
        """Arama alanını ve sonuçları temizle"""
        self.search_entry.delete(0, 'end')
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.result_label.configure(text="")
        self.search_results = []
        self.search_entry.focus_set()
    
    def _sort_column(self, col):
        """Sütuna göre sırala"""
        # Aynı sütuna tıklanırsa sıralamayı tersine çevir
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False
        
        # Treeview'deki verileri al
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        # Boyut sütunu için özel sıralama (numerik)
        if col == "Boyut":
            def get_size_bytes(size_str):
                try:
                    # "1.23 MB" gibi bir değeri byte'a çevir
                    size_str = size_str.strip()
                    if not size_str or size_str == "-":
                        return 0
                    parts = size_str.split()
                    if len(parts) != 2:
                        return 0
                    value = float(parts[0].replace(',', '.'))
                    unit = parts[1].upper()
                    multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
                    return int(value * multipliers.get(unit, 1))
                except:
                    return 0
            
            items.sort(key=lambda x: get_size_bytes(x[0]), reverse=self.sort_reverse)
        else:
            # Diğer sütunlar için alfabetik sıralama
            items.sort(key=lambda x: x[0].lower() if isinstance(x[0], str) else x[0], 
                      reverse=self.sort_reverse)
        
        # Sıralanmış verileri yeniden yerleştir
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
    
    def _get_selected_file_data(self):
        """Seçili dosyanın verilerini al"""
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = self.tree.item(selection[0])
        values = item['values']
        
        # Treeview'deki değerler: Tarih, Dosya Adı, Boyut, display_path (Dizin), İşlem Türü
        display_path = values[3]  # Revision veya hedef klasör yolu
        file_name = values[1]
        formatted_date = values[0]  # Tarihi de al (eşleşme için)
        
        # search_results'dan tam bilgiyi bul
        for result in self.search_results:
            if result.get('display_path') == display_path and result['file_name'] == file_name:
                return {
                    'display_path': display_path,  # Gösterilen yol (revision veya hedef)
                    'file_path': result['file_path'],  # Kaynak dizin  
                    'file_name': file_name,
                    'source_path': result.get('source_path', ''),
                    'target_path': result.get('target_path', ''),
                    'backup_date': result.get('backup_date', '')
                }
        
        # Eşleşme bulunamazsa basit dict döndür
        return {
            'display_path': display_path,
            'file_path': display_path,
            'file_name': file_name
        }
    
    def _open_folder(self):
        """Seçili dosyanın revision/hedef klasörünü Windows Explorer'da aç"""
        file_data = self._get_selected_file_data()
        if not file_data:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir dosya seçin!")
            return
        
        # display_path revision veya hedef klasör yolunu içerir
        display_path = file_data['display_path']
        file_name = file_data['file_name']
        
        # Tam dosya yolu
        full_path = os.path.join(display_path, file_name)
        print(f">>> DEBUG: Açılacak dosya yolu: {full_path}")
        print(f">>> DEBUG: Dosya var mı: {os.path.exists(full_path)}")
        
        if os.path.exists(full_path):
            # Windows Explorer'da dosyayı seçili olarak aç
            subprocess.run(['explorer', '/select,', os.path.normpath(full_path)])
        elif os.path.exists(display_path):
            # Dosya bulunamadıysa sadece klasörü aç
            print(f">>> DEBUG: Dosya yok, klasör açılıyor: {display_path}")
            subprocess.run(['explorer', os.path.normpath(display_path)])
        else:
            ConfirmDialog.show_warning(self, "Uyarı", f"Klasör bulunamadı:\n{display_path}\n\nDisk takılı olmayabilir.")
    
    def _show_file_history(self):
        """Seçili dosyanın geçmişini göster"""
        file_data = self._get_selected_file_data()
        if not file_data:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir dosya seçin!")
            return
        
        # Hedef klasör bilgisini al
        target_path = file_data.get('target_path', file_data.get('display_path', ''))
        
        if not target_path:
            target_path = file_data['display_path']
        
        # FileHistoryWindow'u aç - kaynak dizin yolu gerekli (file_path)
        FileHistoryWindow(self, self.db, file_data['file_path'], file_data['file_name'], target_path)
    
    def _copy_path(self):
        """Gösterilen klasördeki dosya yolunu panoya kopyala"""
        file_data = self._get_selected_file_data()
        if not file_data:
            return
        
        # Gösterilen yoldaki tam dosya yolunu kopyala
        full_path = os.path.join(file_data['display_path'], file_data['file_name'])
        self.clipboard_clear()
        self.clipboard_append(full_path)
        
        # Kısa süreliğine onay mesajı göster
        self.result_label.configure(text="✓ Yol panoya kopyalandı!", text_color="#65FE65")
        self.after(2000, lambda: self._restore_result_label())
    
    def _restore_result_label(self):
        """Sonuç etiketini eski haline döndür"""
        total_count = len(self.search_results)
        if total_count == 0:
            self.result_label.configure(text="", text_color="#4138E5")
        elif total_count > self.MAX_DISPLAY_RESULTS:
            self.result_label.configure(
                text=f"Toplam {total_count:,} dosya bulundu. İlk {self.MAX_DISPLAY_RESULTS} sonuç gösteriliyor.",
                text_color="#5B0900"
            )
        else:
            self.result_label.configure(
                text=f"Toplam {total_count:,} dosya bulundu.",
                text_color="#FF9148"
            )
