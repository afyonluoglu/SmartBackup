"""
Smart Backup - UI Components
Tarih: 19 Kasım 2025
Yazar: Dr. Mustafa Afyonluoğlu

Gerekli Kütüphaneler:
    - customtkinter (pip install customtkinter)
    - tkinter (standart kütüphane)
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog, Menu
from typing import Callable, Optional

class ProjectDialog(ctk.CTkToplevel):
    """Proje ekleme/düzenleme dialog'u"""
    
    def __init__(self, parent, title: str = "Yeni Yedekleme Paketi", 
                 project_name: str = "", project_desc: str = ""):
        super().__init__(parent)
        
        self.result = None
        self.title(title)
        self.geometry("600x300")
        # self._center_window()
        
        # Modal yap
        self.transient(parent)
        self.grab_set()
        
        # ESC tuşu ile kapat
        self.bind('<Escape>', lambda e: self.destroy())
        
        self._create_widgets(project_name, project_desc)
    
    def _center_window(self):
        """Pencereyi ekranda ortala"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self, project_name: str, project_desc: str):
        """Widget'ları oluştur"""
        # Padding frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Paket adı
        ctk.CTkLabel(main_frame, text="Paket Adı:", anchor="w").pack(fill="x", pady=(0, 5))
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="Yedekleme paketine bir ad verin")
        self.name_entry.pack(fill="x", pady=(0, 15))
        self.name_entry.insert(0, project_name)
        self.name_entry.focus()
        
        # Açıklama
        ctk.CTkLabel(main_frame, text="Paket Açıklaması:", anchor="w").pack(fill="x", pady=(0, 5))
        self.desc_entry = ctk.CTkTextbox(main_frame, height=80)
        self.desc_entry.pack(fill="both", expand=True, pady=(0, 15))
        if project_desc:
            self.desc_entry.insert("1.0", project_desc)
        
        # Butonlar
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="Tamam", command=self._on_ok,
                     width=100).pack(side="right", padx=(5, 0))
        ctk.CTkButton(button_frame, text="İptal", command=self.destroy,
                     width=100).pack(side="right")
    
    def _on_ok(self):
        """Tamam butonuna basıldı"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Uyarı", "Proje adı boş olamaz!", parent=self)
            return
        
        desc = self.desc_entry.get("1.0", "end-1c").strip()
        self.result = (name, desc)
        self.destroy()


class MappingDialog(ctk.CTkToplevel):
    """Eşleşme ekleme/düzenleme dialog'u"""
    
    def __init__(self, parent, title: str = "Yeni Eşleşme",
                 source_path: str = "", file_filter: str = "*.*",
                 exclude_filter: str = "", include_subdirs: bool = True, 
                 target_path: str = ""):
        super().__init__(parent)
        
        self.result = None
        self.title(title)
        self.geometry("700x450")
        # self._center_window()
        
        # Modal yap
        self.transient(parent)
        self.grab_set()
        
        # ESC tuşu ile kapat
        self.bind('<Escape>', lambda e: self.destroy())
        
        self._create_widgets(source_path, file_filter, exclude_filter, 
                            include_subdirs, target_path)
    
    def _center_window(self):
        """Pencereyi ekranda ortala"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self, source_path: str, file_filter: str,
                       exclude_filter: str, include_subdirs: bool, target_path: str):
        """Widget'ları oluştur"""
        # Padding frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Kaynak klasör
        ctk.CTkLabel(main_frame, text="Kaynak Klasör:", anchor="w").pack(fill="x", pady=(0, 5))
        source_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        source_frame.pack(fill="x", pady=(0, 15))
        
        self.source_entry = ctk.CTkEntry(source_frame, placeholder_text="Kaynak klasör seçin")
        self.source_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.source_entry.insert(0, source_path)
        
        ctk.CTkButton(source_frame, text="Gözat...", command=self._browse_source,
                     width=80).pack(side="right")
        
        # Dosya filtresi
        ctk.CTkLabel(main_frame, text="Dahil Edilecek Dosyalar:", anchor="w").pack(fill="x", pady=(0, 5))
        self.filter_entry = ctk.CTkEntry(main_frame, 
                                         placeholder_text="Örn: *.*, *.doc*, abc*.txt")
        self.filter_entry.pack(fill="x", pady=(0, 15))
        self.filter_entry.insert(0, file_filter)
        
        # Hariç tutulacak dosyalar
        ctk.CTkLabel(main_frame, text="Hariç Tutulacak Dosyalar (opsiyonel):", 
                    anchor="w").pack(fill="x", pady=(0, 0))
        
        # Açıklama label'ı ekle
        hint_label = ctk.CTkLabel(main_frame, 
                                 text="💡 Relatif kullanılan yollar (örnek: temp\\*.*  gibi) tüm klasörlerde eşleştirilir",
                                 font=("", 11), 
                                 text_color="gray",
                                 anchor="w")
        hint_label.pack(fill="x", pady=(0, 0))
        
        self.exclude_entry = ctk.CTkEntry(main_frame, 
                                         placeholder_text="Örn: *.db, temp\\*.*, __pycache__\\*.*")
        self.exclude_entry.pack(fill="x", pady=(0, 15))
        self.exclude_entry.insert(0, exclude_filter)
        
        # Alt klasörler
        self.subdirs_var = ctk.BooleanVar(value=include_subdirs)
        ctk.CTkCheckBox(main_frame, text="Alt klasörleri dahil et",
                       variable=self.subdirs_var).pack(fill="x", pady=(0, 15))
        
        # Hedef klasör
        ctk.CTkLabel(main_frame, text="Hedef Klasör:", anchor="w").pack(fill="x", pady=(0, 5))
        target_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        target_frame.pack(fill="x", pady=(0, 20))
        
        self.target_entry = ctk.CTkEntry(target_frame, placeholder_text="Hedef klasör seçin")
        self.target_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.target_entry.insert(0, target_path)
        
        ctk.CTkButton(target_frame, text="Gözat...", command=self._browse_target,
                     width=80).pack(side="right")
        
        # Butonlar
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="Tamam", command=self._on_ok,
                     width=100).pack(side="right", padx=(5, 0))
        ctk.CTkButton(button_frame, text="İptal", command=self.destroy,
                     width=100).pack(side="right")
    
    def _browse_source(self):
        """Kaynak klasör seç"""
        folder = filedialog.askdirectory(parent=self, title="Kaynak Klasör Seçin")
        if folder:
            self.source_entry.delete(0, "end")
            self.source_entry.insert(0, folder)
    
    def _browse_target(self):
        """Hedef klasör seç"""
        folder = filedialog.askdirectory(parent=self, title="Hedef Klasör Seçin")
        if folder:
            self.target_entry.delete(0, "end")
            self.target_entry.insert(0, folder)
    
    def _on_ok(self):
        """Tamam butonuna basıldı"""
        source = self.source_entry.get().strip()
        target = self.target_entry.get().strip()
        file_filter = self.filter_entry.get().strip()
        exclude_filter = self.exclude_entry.get().strip()
        
        if not source:
            messagebox.showwarning("Uyarı", "Kaynak klasör boş olamaz!", parent=self)
            return
        if not target:
            messagebox.showwarning("Uyarı", "Hedef klasör boş olamaz!", parent=self)
            return
        if not file_filter:
            messagebox.showwarning("Uyarı", "Dosya filtresi boş olamaz!", parent=self)
            return
        
        self.result = (source, file_filter, exclude_filter, self.subdirs_var.get(), target)
        self.destroy()


class ProgressDialog(ctk.CTkToplevel):
    """İlerleme dialog'u"""
    
    def __init__(self, parent, title: str = "İşlem Devam Ediyor"):
        super().__init__(parent)
        
        self.cancelled = False
        self.is_closed = False
        self.title(title)
        self.geometry("600x150")
        # self._center_window()
        
        # Modal yap
        self.transient(parent)
        self.grab_set()
        
        # ESC tuşu ile iptal
        self.bind('<Escape>', lambda e: self._on_cancel())
        
        # Pencere kapatma butonunu devre dışı bırak
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        self._create_widgets()
    
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
        # Padding frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Durum etiketi
        self.status_label = ctk.CTkLabel(main_frame, text="İşlem başlatılıyor...",
                                         wraplength=460)
        self.status_label.pack(fill="x", pady=(0, 15))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.pack(fill="x", pady=(0, 15))
        self.progress_bar.set(0)
        
        # Detay etiketi
        self.detail_label = ctk.CTkLabel(main_frame, text="", 
                                         font=("", 10), text_color="gray")
        self.detail_label.pack(fill="x", pady=(0, 15))
        
        # İptal butonu
        self.cancel_btn = ctk.CTkButton(main_frame, text="İptal (ESC)",
                                        command=self._on_cancel, width=100)
        self.cancel_btn.pack()
    
    def update_progress(self, value: float):
        """İlerleme çubuğunu güncelle (0.0 - 1.0)"""
        if not self.is_closed:
            try:
                self.progress_bar.set(value)
                self.update()
            except:
                pass
    
    def update_status(self, text: str):
        """Durum metnini güncelle"""
        if not self.is_closed:
            try:
                self.status_label.configure(text=text)
                self.update()
            except:
                pass
    
    def update_detail(self, text: str):
        """Detay metnini güncelle"""
        if not self.is_closed:
            try:
                self.detail_label.configure(text=text)
                self.update()
            except:
                pass
    
    def _on_cancel(self):
        """İptal butonuna basıldı"""
        # Zaten iptal edilmişse tekrar sorma
        if self.cancelled or self.is_closed:
            return
        
        if messagebox.askyesno("Onay", "İşlemi iptal etmek istediğinizden emin misiniz?",
                              parent=self):
            self.cancelled = True
            self.is_closed = True
            self.cancel_btn.configure(state="disabled", text="İptal ediliyor...")
            # Dialog'u kapat
            self.destroy()
    
    def destroy(self):
        """Dialog'u kapat"""
        self.is_closed = True
        super().destroy()


class AnalysisSelectionDialog:
    """Analiz için mapping seçim dialogu"""
    
    def __init__(self, parent, mappings: list, saved_selections: dict = None):
        """
        Args:
            parent: Ana pencere
            mappings: [(mapping_id, include_filter, exclude_filter), ...] listesi
            saved_selections: Daha önce seçilmiş ayarlar dictionary (opsiyonel)
                {
                    'mapping_ids': [int, ...],
                    'show_backup_files': bool,
                    'show_excluded_files': bool,
                    'show_skipped_files': bool,
                    'max_files_to_show': int
                }
        """
        self.result = None  # Seçilen mapping ID'leri ve ayarlar
        
        # Varsayılan değerler
        if saved_selections is None:
            saved_selections = {
                'mapping_ids': [],
                'show_backup_files': True,
                'show_excluded_files': True,
                'show_skipped_files': True,
                'max_files_to_show': 50
            }
        
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Analiz Edilecek Mapping'leri Seç")
        self.dialog.geometry("850x500+100+100")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Analiz edilecek dosya eşleştirmelerini seçin:",
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(main_frame)
        scroll_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Checkbox'lar ve mapping bilgileri
        self.checkboxes = {}
        for mapping_id, include_filter, exclude_filter in mappings:
            checkbox_frame = ctk.CTkFrame(scroll_frame)
            checkbox_frame.pack(fill="x", pady=2, padx=5)
            
            # Eğer saved_selections varsa onu kullan, yoksa hepsini seç
            saved_mapping_ids = saved_selections.get('mapping_ids', [])
            is_selected = (mapping_id in saved_mapping_ids) if saved_mapping_ids else True
            var = ctk.BooleanVar(value=is_selected)
            self.checkboxes[mapping_id] = var
            
            cb = ctk.CTkCheckBox(
                checkbox_frame,
                text="",
                variable=var,
                width=30
            )
            cb.pack(side="left", padx=(0, 10))
            
            # Mapping bilgisi
            info_text = f"Include: {include_filter}"
            if exclude_filter:
                info_text += f"  |  Exclude: {exclude_filter}"
            
            info_label = ctk.CTkLabel(
                checkbox_frame,
                text=info_text,
                anchor="w"
            )
            info_label.pack(side="left", fill="x", expand=True)
        
        # Analiz seçenekleri frame
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=(10, 0))
        
        options_label = ctk.CTkLabel(
            options_frame,
            text="Analiz Sonuçlarında Listelenecek Dosyalar:",
            font=("Arial", 11, "bold")
        )
        options_label.pack(pady=(5, 5))
        
        # Checkbox'lar için frame
        checkboxes_frame = ctk.CTkFrame(options_frame)
        checkboxes_frame.pack(pady=(0, 5))
        
        # Yedeklenecek dosyaları göster
        self.show_backup_files_var = ctk.BooleanVar(value=saved_selections.get('show_backup_files', True))
        backup_cb = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Yedeklenecekler",
            variable=self.show_backup_files_var
        )
        backup_cb.pack(side="left", padx=10)
        
        # Hariç tutulacak dosyaları göster (kullanıcı tanımlı)
        self.show_user_excluded_files_var = ctk.BooleanVar(value=saved_selections.get('show_user_excluded_files', True))
        user_excluded_cb = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Hariçler (Filtre)",
            variable=self.show_user_excluded_files_var
        )
        user_excluded_cb.pack(side="left", padx=10)
        
        # Hariç tutulacak dosyaları göster (gizli klasörler)
        self.show_hidden_excluded_files_var = ctk.BooleanVar(value=saved_selections.get('show_hidden_excluded_files', True))
        hidden_excluded_cb = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Hariçler (Gizli)",
            variable=self.show_hidden_excluded_files_var
        )
        hidden_excluded_cb.pack(side="left", padx=10)
        
        # Atlanacak dosyaları göster
        self.show_skipped_files_var = ctk.BooleanVar(value=saved_selections.get('show_skipped_files', True))
        skipped_cb = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Atlanacaklar",
            variable=self.show_skipped_files_var
        )
        skipped_cb.pack(side="left", padx=10)
        
        # Revisions dosyalarını göster
        self.show_revision_files_var = ctk.BooleanVar(value=saved_selections.get('show_revision_files', True))
        revision_cb = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Arşiv Durumu",
            variable=self.show_revision_files_var
        )
        revision_cb.pack(side="left", padx=10)
        
        # Silinmiş dosyaları göster
        self.show_deleted_files_var = ctk.BooleanVar(value=saved_selections.get('show_deleted_files', True))
        deleted_cb = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Silinenler",
            variable=self.show_deleted_files_var
        )
        deleted_cb.pack(side="left", padx=10)
        
        # Gösterilecek dosya sayısı
        count_frame = ctk.CTkFrame(options_frame)
        count_frame.pack(pady=(5, 5))
        
        count_label = ctk.CTkLabel(
            count_frame,
            text="Her Kategoride Gösterilecek Dosya Sayısı:",
            font=("Arial", 10)
        )
        count_label.pack(side="left", padx=(10, 5))
        
        self.max_files_entry = ctk.CTkEntry(
            count_frame,
            width=80,
            placeholder_text="50"
        )
        self.max_files_entry.insert(0, str(saved_selections.get('max_files_to_show', 50)))
        self.max_files_entry.pack(side="left", padx=5)
        
        count_info = ctk.CTkLabel(
            count_frame,
            text="(Örn: 25, 50, 100... Tümü için -1)",
            font=("Arial", 11),
            text_color="#888888"
        )
        count_info.pack(side="left", padx=5)
        
        # Butonlar
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        # Tümünü seç/kaldır butonları
        select_all_btn = ctk.CTkButton(
            button_frame,
            text="Tümünü Seç",
            command=self._select_all,
            width=120
        )
        select_all_btn.pack(side="left", padx=5)
        
        deselect_all_btn = ctk.CTkButton(
            button_frame,
            text="Tümünü Kaldır",
            command=self._deselect_all,
            width=120
        )
        deselect_all_btn.pack(side="left", padx=5)
        
        # Spacer
        spacer = ctk.CTkFrame(button_frame, fg_color="transparent")
        spacer.pack(side="left", fill="x", expand=True)
        
        # Başla/İptal
        start_btn = ctk.CTkButton(
            button_frame,
            text="Başla",
            command=self._on_start,
            width=100
        )
        start_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="İptal",
            command=self._on_cancel,
            width=100
        )
        cancel_btn.pack(side="left", padx=5)
        
        # ESC tuşu ile iptal
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        
        # Pencere kapatma
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
    def _select_all(self):
        """Tüm mapping'leri seç"""
        for var in self.checkboxes.values():
            var.set(True)
    
    def _deselect_all(self):
        """Tüm seçimleri kaldır"""
        for var in self.checkboxes.values():
            var.set(False)
    
    def _on_start(self):
        """Başla butonuna basıldı"""
        # Seçili mapping ID'lerini topla
        selected = [mid for mid, var in self.checkboxes.items() if var.get()]
        
        if not selected:
            messagebox.showwarning(
                "Uyarı",
                "En az bir mapping seçmelisiniz!",
                parent=self.dialog
            )
            return
        
        # Dosya sayısını al ve doğrula
        try:
            max_files = int(self.max_files_entry.get())
            if max_files < -1 or max_files == 0:
                raise ValueError()
        except:
            messagebox.showwarning(
                "Uyarı",
                "Geçerli bir dosya sayısı girin! (-1 için tümü, pozitif sayı için limit)",
                parent=self.dialog
            )
            return
        
        # Sonuçları dictionary olarak döndür
        self.result = {
            'mappings': selected,
            'show_backup_files': self.show_backup_files_var.get(),
            'show_user_excluded_files': self.show_user_excluded_files_var.get(),
            'show_hidden_excluded_files': self.show_hidden_excluded_files_var.get(),
            'show_skipped_files': self.show_skipped_files_var.get(),
            'show_revision_files': self.show_revision_files_var.get(),
            'show_deleted_files': self.show_deleted_files_var.get(),
            'max_files_to_show': max_files
        }
        self.dialog.destroy()
    
    def _on_cancel(self):
        """İptal butonuna basıldı"""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Dialog'u göster ve sonucu döndür"""
        self.dialog.wait_window()
        return self.result


class BackupSelectionDialog:
    """Yedekleme için mapping seçim dialogu"""
    
    def __init__(self, parent, mappings: list, analyzed_mapping_ids: set = None, analysis_results: dict = None):
        """
        Args:
            parent: Ana pencere
            mappings: [(mapping_id, include_filter, exclude_filter), ...] listesi
            analyzed_mapping_ids: Analiz yapılmış mapping ID'leri seti
            analysis_results: Analiz sonuçları dict {mapping_id: {...}}
        """
        self.result = None  # Seçilen mapping ID'leri
        self.analyzed_mapping_ids = analyzed_mapping_ids or set()
        self.analysis_results = analysis_results or {}
        
        # Toplam gizli ve silinen dosya sayılarını hesapla
        self.total_hidden_files = 0
        self.total_deleted_files = 0
        
        for mapping_id, result in self.analysis_results.items():
            self.total_hidden_files += result.get('hidden_excluded_count', 0)
            self.total_deleted_files += result.get('deleted_count', 0)
        
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Yedeklenecek Mapping'leri Seç")
        self.dialog.geometry("750x470+100+100")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Yedeklenecek dosya eşleştirmelerini seçin:",
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(main_frame)
        scroll_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Checkbox'lar ve mapping bilgileri
        self.checkboxes = {}
        for mapping_id, include_filter, exclude_filter in mappings:
            checkbox_frame = ctk.CTkFrame(scroll_frame)
            checkbox_frame.pack(fill="x", pady=2, padx=5)
            
            # Analiz yapılmış mı kontrol et
            is_analyzed = mapping_id in self.analyzed_mapping_ids
            
            var = ctk.BooleanVar(value=is_analyzed)  # Analiz yapılmışsa seçili
            self.checkboxes[mapping_id] = var
            
            cb = ctk.CTkCheckBox(
                checkbox_frame,
                text="",
                variable=var,
                width=30,
                state="normal" if is_analyzed else "disabled"  # Analiz yoksa disabled
            )
            cb.pack(side="left", padx=(0, 10))
            
            # Mapping bilgisi
            info_text = f"Include: {include_filter}"
            if exclude_filter:
                info_text += f"  |  Exclude: {exclude_filter}"
            if not is_analyzed:
                info_text += "  [ANALİZ YAPILMAMIŞ]"
            
            info_label = ctk.CTkLabel(
                checkbox_frame,
                text=info_text,
                anchor="w",
                text_color="gray" if not is_analyzed else None
            )
            info_label.pack(side="left", fill="x", expand=True)
        
        # Yedekleme seçenekleri frame
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=(10, 0))
        
        options_label = ctk.CTkLabel(
            options_frame,
            text="Yedekleme Seçenekleri:",
            font=("Arial", 11, "bold")
        )
        options_label.pack(pady=(5, 5))
        
        # Gizli dosyaları yedekle checkbox - sadece gizli dosya varsa göster
        self.backup_hidden_files_var = ctk.BooleanVar(value=False)
        if self.total_hidden_files > 0:
            hidden_cb = ctk.CTkCheckBox(
                options_frame,
                text=f"Gizli Dosyaları Yedekle ({self.total_hidden_files} dosya tespit edildi)",
                variable=self.backup_hidden_files_var
            )
            hidden_cb.pack(pady=5)
        
        # Silinenleri yansıt checkbox - sadece silinen dosya varsa göster
        self.mirror_deletions_var = ctk.BooleanVar(value=False)
        if self.total_deleted_files > 0:
            mirror_cb = ctk.CTkCheckBox(
                options_frame,
                text=f"Silinenleri Yansıt ({self.total_deleted_files} dosya tespit edildi)",
                variable=self.mirror_deletions_var
            )
            mirror_cb.pack(pady=5)
        
        # Detayları Kaydet checkbox - yedekleme sonrası otomatik kaydet
        self.auto_save_details_var = ctk.BooleanVar(value=True)
        auto_save_cb = ctk.CTkCheckBox(
            options_frame,
            text="Yedekleme Sonrası Detayları Kaydet",
            variable=self.auto_save_details_var
        )
        auto_save_cb.pack(pady=5)
        
        # Butonlar
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        # Tümünü seç/kaldır butonları (sadece analiz yapılmışlar için)
        select_all_btn = ctk.CTkButton(
            button_frame,
            text="Tümünü Seç",
            command=self._select_all,
            width=120
        )
        select_all_btn.pack(side="left", padx=5)
        
        deselect_all_btn = ctk.CTkButton(
            button_frame,
            text="Tümünü Kaldır",
            command=self._deselect_all,
            width=120
        )
        deselect_all_btn.pack(side="left", padx=5)
        
        # Spacer
        spacer = ctk.CTkFrame(button_frame, fg_color="transparent")
        spacer.pack(side="left", fill="x", expand=True)
        
        # Başla/İptal
        start_btn = ctk.CTkButton(
            button_frame,
            text="Başla",
            command=self._on_start,
            width=100
        )
        start_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="İptal",
            command=self._on_cancel,
            width=100
        )
        cancel_btn.pack(side="left", padx=5)
        
        # ESC tuşu ile iptal
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        
        # Pencere kapatma
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
    def _select_all(self):
        """Analiz yapılmış tüm mapping'leri seç"""
        for mapping_id, var in self.checkboxes.items():
            if mapping_id in self.analyzed_mapping_ids:
                var.set(True)
    
    def _deselect_all(self):
        """Analiz yapılmış tüm seçimleri kaldır"""
        for mapping_id, var in self.checkboxes.items():
            if mapping_id in self.analyzed_mapping_ids:
                var.set(False)
    
    def _on_start(self):
        """Başla butonuna basıldı"""
        # Seçili mapping ID'lerini topla
        selected = [mid for mid, var in self.checkboxes.items() if var.get()]
        
        if not selected:
            messagebox.showwarning(
                "Uyarı",
                "En az bir mapping seçmelisiniz!",
                parent=self.dialog
            )
            return
        
        # Sonucu dictionary olarak döndür
        self.result = {
            'mappings': selected,
            'backup_hidden_files': self.backup_hidden_files_var.get(),
            'mirror_deletions': self.mirror_deletions_var.get(),
            'auto_save_details': self.auto_save_details_var.get()
        }
        self.dialog.destroy()
    
    def _on_cancel(self):
        """İptal butonuna basıldı"""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Dialog'u göster ve sonucu döndür"""
        self.dialog.wait_window()
        return self.result


class ConfirmDialog:
    """Onay dialog'u (messagebox wrapper)"""
    
    @staticmethod
    def ask(parent, title: str, message: str) -> bool:
        """Evet/Hayır onay penceresi göster"""
        return messagebox.askyesno(title, message, parent=parent)
    
    @staticmethod
    def show_info(parent, title: str, message: str):
        """Bilgi mesajı göster"""
        messagebox.showinfo(title, message, parent=parent)
    
    @staticmethod
    def show_warning(parent, title: str, message: str):
        """Uyarı mesajı göster"""
        messagebox.showwarning(title, message, parent=parent)
    
    @staticmethod
    def show_error(parent, title: str, message: str):
        """Hata mesajı göster"""
        messagebox.showerror(title, message, parent=parent)


class SourceSearchDialog(ctk.CTkToplevel):
    """Kaynak klasörde dosya arama dialog'u"""
    
    def __init__(self, parent, source_path: str = None, include_subfolders: bool = True):
        super().__init__(parent)
        
        self.source_path = source_path
        self.include_subfolders = include_subfolders
        
        # Sıralama durumu: {'column': str, 'reverse': bool}
        self.sort_state = {'column': None, 'reverse': False}
        
        width = 1000
        height = 600
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.title("Dosya Ara")
        
        # Modal yap
        self.transient(parent)
        self.grab_set()
        
        # ESC tuşu ile kapat
        self.bind('<Escape>', lambda e: self.destroy())
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Widget'ları oluştur"""
        import os
        import glob
        from tkinter import ttk
        
        # Padding frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Klasör seçimi
        folder_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        folder_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(folder_frame, text="Klasör:", 
                    font=("", 12, "bold")).pack(side="left", padx=(0, 10))
        
        self.folder_entry = ctk.CTkEntry(folder_frame, width=700, 
                                         font=("", 12))
        self.folder_entry.pack(side="left", padx=(0, 10))
        if self.source_path:
            self.folder_entry.insert(0, self.source_path)
        
        ctk.CTkButton(folder_frame, text="Gözat...", 
                     command=self._browse_folder, width=100).pack(side="left")
        
        # Arama girişi
        search_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(search_frame, text="Arama Kelimesi:", 
                    font=("", 12)).pack(side="left", padx=(0, 10))
        
        self.search_entry = ctk.CTkEntry(search_frame, width=400, 
                                        font=("", 12))
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind('<Return>', lambda e: self._search_files())
        
        ctk.CTkButton(search_frame, text="Ara", 
                     command=self._search_files, width=100).pack(side="left")
        
        # Yardım düğmesi
        ctk.CTkButton(search_frame, text="?", 
                     command=self._show_search_help, width=30,
                     fg_color="#555555", hover_color="#666666").pack(side="left", padx=(5, 0))
        
        # Alt klasörler checkbox
        self.subfolders_var = ctk.BooleanVar(value=self.include_subfolders)
        ctk.CTkCheckBox(search_frame, text="Alt klasörleri dahil et",
                       variable=self.subfolders_var).pack(side="left", padx=(20, 0))
        
        # Sonuç sayısı
        self.result_label = ctk.CTkLabel(main_frame, text="Sonuç: 0 dosya",
                                        font=("", 11))
        self.result_label.pack(pady=(0, 5))
        
        # Treeview için style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Search.Treeview", 
                       background="#2b2b2b", 
                       foreground="white",
                       fieldbackground="#2b2b2b", 
                       borderwidth=0,
                       font=("Arial", 14),
                       rowheight=25)
        style.configure("Search.Treeview.Heading", 
                       background="#1f538d", 
                       foreground="white",
                       font=("Arial", 15, "bold"))
        style.map("Search.Treeview",
                 background=[('selected', '#1F6AA5')],
                 foreground=[('selected', 'white')])
        
        # Treeview frame
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Scrollbar'lar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ("Dosya Adı", "Klasör", "Tarih", "Boyut")
        self.results_tree = ttk.Treeview(tree_frame, 
                                        columns=columns,
                                        show="headings",
                                        style="Search.Treeview",
                                        yscrollcommand=vsb.set,
                                        xscrollcommand=hsb.set)
        
        # Sütun başlıkları (sıralama için tıklanabilir)
        for col in columns:
            self.results_tree.heading(col, text=col, 
                                     command=lambda c=col: self._sort_by_column(c))
        
        # Sütun genişlikleri
        self.results_tree.column("Dosya Adı", width=250)
        self.results_tree.column("Klasör", width=400)
        self.results_tree.column("Tarih", width=150, anchor="center")
        self.results_tree.column("Boyut", width=100, anchor="e")
        
        # Scrollbar yapılandırması
        vsb.config(command=self.results_tree.yview)
        hsb.config(command=self.results_tree.xview)
        
        # Grid yerleşimi
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Çift tıklama ile dosya aç
        self.results_tree.bind('<Double-Button-1>', self._open_file)
        
        # Sağ tık context menüsü
        self.results_tree.bind('<Button-3>', self._show_context_menu)
        

        # Context menüsü oluştur
        self.context_menu = Menu(self.results_tree, tearoff=0)
        self.context_menu.add_command(label="Aç", command=self._open_file_with_app)
        self.context_menu.add_command(label="Gezginde Göster", command=lambda: self._open_file(None))
        
        list_font = ("Segoe UI", 13) 
        self.context_menu.config(font=list_font)   
                
        # Butonlar frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Göster butonu
        ctk.CTkButton(button_frame, text="Göster", 
                     command=lambda: self._open_file(None), width=120,
                     fg_color="#1F6AA5", hover_color="#1557A0").pack(side="left", padx=(0, 10))
        
        # Kapat butonu
        ctk.CTkButton(button_frame, text="Kapat", 
                     command=self.destroy, width=100).pack(side="left")
        
        # Başlangıçta odakla
        self.search_entry.focus()
    
    def _browse_folder(self):
        """Klasör seç"""
        folder = filedialog.askdirectory(parent=self, title="Arama Yapılacak Klasörü Seçin")
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.source_path = folder
    
    def _show_search_help(self):
        """Arama yardımını göster"""
        help_text = """Gelişmiş Arama Özellikleri:

• Birden fazla kelime: Tüm kelimelerin geçtiği dosyalar bulunur.
   Örnek: rusça ders → "dünkü rusça ders özetleri.txt"
   ve "dersimiz rusça.pdf" bulunur.

• Tırnak içinde arama: Kelimeler yazılan sırayla aranır
   (aralarında başka kelimeler olabilir).
   Örnek: "muhit fatura" → "Muhit hoca fatura.pdf" bulunur
   ama "fatura muhit.pdf" bulunmaz.

• Hariç tutma (-): Belirtilen kelimeyi içermeyen dosyalar.
   Örnek: rusça -özet → "rusça" içeren ama "özet"
   içermeyen dosyalar bulunur.

• Wildcard: *.txt, test*.py gibi kalıplar kullanabilirsiniz."""
        
        ConfirmDialog.show_info(self, "Arama Yardımı", help_text)
    
    def _turkish_lower(self, text: str) -> str:
        """Türkçe karakterleri düzgün şekilde küçük harfe çevir"""
        # Türkçe özel karakterler için dönüşüm
        tr_map = str.maketrans('İIŞĞÜÖÇ', 'iışğüöç')
        return text.translate(tr_map).lower()
    
    def _parse_search_term(self, search_term: str):
        """
        Arama terimini ayrıştır.
        Returns: (exact_phrase, include_words, exclude_words, is_wildcard)
        """
        import re
        
        search_term = search_term.strip()
        
        # Wildcard kontrolü
        if '*' in search_term or '?' in search_term:
            return (None, [], [], True)
        
        # Tırnak içinde sıralı kelime araması kontrolü
        if search_term.startswith('"') and search_term.endswith('"') and len(search_term) > 2:
            phrase_content = search_term[1:-1]  # Tırnakları kaldır
            ordered_words = phrase_content.split()  # Kelimelere ayır
            return (ordered_words, [], [], False)  # ordered_words olarak döndür
        
        # Kelimeleri ayrıştır
        words = search_term.split()
        include_words = []
        exclude_words = []
        
        for word in words:
            if word.startswith('-') and len(word) > 1:
                exclude_words.append(self._turkish_lower(word[1:]))  # - işaretini kaldır
            else:
                include_words.append(self._turkish_lower(word))
        
        return (None, include_words, exclude_words, False)
    
    def _matches_search_criteria(self, filename: str, ordered_words, include_words, exclude_words) -> bool:
        """
        Dosya adının arama kriterlerine uyup uymadığını kontrol et.
        ordered_words: Tırnak içinde yazılan kelimelerin sıralı listesi (veya None)
        """
        filename_lower = self._turkish_lower(filename)
        
        # Sıralı kelime araması kontrolü (tırnak içinde yazılan)
        if ordered_words:
            # Tüm kelimelerin bu sırayla geçip geçmediğini kontrol et
            last_pos = -1
            for word in ordered_words:
                word_lower = self._turkish_lower(word)
                pos = filename_lower.find(word_lower, last_pos + 1)
                if pos == -1:
                    return False  # Kelime bulunamadı
                last_pos = pos
            return True
        
        # Hariç tutulan kelimeleri kontrol et
        for word in exclude_words:
            if word in filename_lower:
                return False
        
        # Dahil edilecek tüm kelimelerin varlığını kontrol et (AND mantığı)
        for word in include_words:
            if word not in filename_lower:
                return False
        
        return True
    
    def _search_files(self):
        """Arama yap"""
        import os
        import glob
        
        search_term = self.search_entry.get().strip()
        if not search_term:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen arama kelimesi girin!")
            return
        
        # Klasör entry'den al
        self.source_path = self.folder_entry.get().strip()
        
        if not self.source_path:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir klasör seçin veya girin!")
            return
        
        # Kaynak klasör var mı kontrol et
        if not os.path.exists(self.source_path):
            ConfirmDialog.show_error(self, "Hata", 
                                    f"Klasör bulunamadı:\n{self.source_path}")
            return
        
        # Mevcut sonuçları temizle
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        results = []
        total_files = 0  # Toplam dosya sayısı
        
        # Arama terimini ayrıştır
        ordered_words, include_words, exclude_words, is_wildcard = self._parse_search_term(search_term)
        
        if self.subfolders_var.get():
            # Alt klasörlerle birlikte ara
            if is_wildcard:
                # Wildcard ile arama
                search_pattern = os.path.join(self.source_path, '**', search_term)
                files = glob.glob(search_pattern, recursive=True)
                
                # Toplam dosya sayısını say (tüm dosyaları say)
                for root, dirs, filenames in os.walk(self.source_path):
                    total_files += len(filenames)
            else:
                # Gelişmiş arama kriterleri ile ara
                files = []
                for root, dirs, filenames in os.walk(self.source_path):
                    total_files += len(filenames)  # Tüm dosyaları say
                    for filename in filenames:
                        if self._matches_search_criteria(filename, ordered_words, include_words, exclude_words):
                            files.append(os.path.join(root, filename))
        else:
            # Sadece kaynak klasörde ara
            if is_wildcard:
                # Wildcard ile arama
                search_pattern = os.path.join(self.source_path, search_term)
                files = glob.glob(search_pattern)
                
                # Toplam dosya sayısını say
                if os.path.exists(self.source_path):
                    total_files = sum(1 for f in os.listdir(self.source_path) 
                                     if os.path.isfile(os.path.join(self.source_path, f)))
            else:
                # Gelişmiş arama kriterleri ile ara
                files = []
                if os.path.exists(self.source_path):
                    for filename in os.listdir(self.source_path):
                        filepath = os.path.join(self.source_path, filename)
                        if os.path.isfile(filepath):
                            total_files += 1  # Tüm dosyaları say
                            if self._matches_search_criteria(filename, ordered_words, include_words, exclude_words):
                                files.append(filepath)
        
        # Sonuçları işle
        for filepath in files:
            if os.path.isfile(filepath):
                filename = os.path.basename(filepath)
                folder = os.path.dirname(filepath)
                size = os.path.getsize(filepath)
                size_str = self._format_size(size)
                # Dosya değiştirilme tarihi
                mtime = os.path.getmtime(filepath)
                from datetime import datetime
                date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                
                results.append((filename, folder, date_str, size_str, filepath, size, mtime))
        
        # Sonuçları sakla (sıralama için)
        self.search_results = results
        
        # Sonuçları treeview'e ekle (dosya adına göre sırala)
        results.sort(key=lambda x: x[0].lower())
        self.sort_state = {'column': 'Dosya Adı', 'reverse': False}
        
        for filename, folder, date_str, size_str, filepath, size, mtime in results:
            # filepath, size ve mtime'ı tag olarak sakla
            self.results_tree.insert('', 'end', 
                                    values=(filename, folder, date_str, size_str),
                                    tags=(filepath, str(size), str(mtime)))
        
        # Sonuç sayısını güncelle - toplam dosya sayısı ile birlikte
        if total_files > 0:
            self.result_label.configure(
                text=f"Sonuç: {len(results)} dosya (toplam {total_files} dosyadan)"
            )
        else:
            self.result_label.configure(text=f"Sonuç: {len(results)} dosya")
    
    def _format_size(self, size: int) -> str:
        """Dosya boyutunu formatla"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def _sort_by_column(self, column):
        """Sütuna göre sırala"""
        # Aynı sütuna tekrar tıklanırsa sıralamayı tersine çevir
        if self.sort_state['column'] == column:
            self.sort_state['reverse'] = not self.sort_state['reverse']
        else:
            self.sort_state['column'] = column
            self.sort_state['reverse'] = False
        
        # Tüm öğeleri al
        items = []
        for item in self.results_tree.get_children():
            values = self.results_tree.item(item, 'values')
            tags = self.results_tree.item(item, 'tags')
            items.append((values, tags))
        
        # Sıralama anahtarı belirle
        if column == 'Dosya Adı':
            items.sort(key=lambda x: x[0][0].lower(), reverse=self.sort_state['reverse'])
        elif column == 'Klasör':
            items.sort(key=lambda x: x[0][1].lower(), reverse=self.sort_state['reverse'])
        elif column == 'Tarih':
            # mtime tag'inden al (sayısal sıralama için)
            items.sort(key=lambda x: float(x[1][2]) if len(x[1]) > 2 else 0, reverse=self.sort_state['reverse'])
        elif column == 'Boyut':
            # size tag'inden al (sayısal sıralama için)
            items.sort(key=lambda x: int(x[1][1]) if len(x[1]) > 1 else 0, reverse=self.sort_state['reverse'])
        
        # Treeview'i yeniden doldur
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        for values, tags in items:
            self.results_tree.insert('', 'end', values=values, tags=tags)
        
        # Sütun başlığını güncelle (sıralama yönünü göster)
        for col in ('Dosya Adı', 'Klasör', 'Tarih', 'Boyut'):
            if col == column:
                arrow = ' ▼' if self.sort_state['reverse'] else ' ▲'
                self.results_tree.heading(col, text=col + arrow)
            else:
                self.results_tree.heading(col, text=col)
    
    def _show_context_menu(self, event):
        """Sağ tık context menüsünü göster"""
        # Tıklanan satırı seç
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _open_file_with_app(self):
        """Seçili dosyayı varsayılan uygulama ile aç"""
        import os
        
        selection = self.results_tree.selection()
        if not selection:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir dosya seçin!")
            return
        
        item = selection[0]
        tags = self.results_tree.item(item, 'tags')
        
        if tags and len(tags) > 0:
            filepath = tags[0]
            if os.path.exists(filepath):
                try:
                    os.startfile(filepath)
                except Exception as e:
                    ConfirmDialog.show_error(self, "Hata", f"Dosya açılamadı:\n{str(e)}")
            else:
                ConfirmDialog.show_error(self, "Hata", f"Dosya bulunamadı:\n{filepath}")
    
    def _open_file(self, event=None):
        """Seçili dosyayı Windows gezgininde aç"""
        import subprocess
        import os
        
        selection = self.results_tree.selection()
        if not selection:
            print("DEBUG: Hiçbir satır seçilmedi")
            if event is None:  # Düğmeye basıldıysa uyarı göster
                ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir dosya seçin!")
            return
        
        item = selection[0]
        values = self.results_tree.item(item, 'values')
        tags = self.results_tree.item(item, 'tags')
        
        print(f"DEBUG: Seçili item değerleri: {values}")
        print(f"DEBUG: Seçili item tags: {tags}")
        
        if tags and len(tags) > 0:
            filepath = tags[0]
            print(f"DEBUG: Dosya yolu (tag'den): {filepath}")
            print(f"DEBUG: Dosya var mı: {os.path.exists(filepath)}")
            print(f"DEBUG: Dosya mı: {os.path.isfile(filepath)}")
            
            # Windows gezgininde dosyayı seçili olarak aç
            try:
                # Yolu normalize et
                filepath = os.path.normpath(filepath)
                print(f"DEBUG: Normalize edilmiş yol: {filepath}")
                
                # explorer komutu
                cmd = ['explorer', '/select,', filepath]
                print(f"DEBUG: Çalıştırılacak komut: {cmd}")
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(f"DEBUG: Komut sonucu - Return code: {result.returncode}")
                print(f"DEBUG: Stdout: {result.stdout}")
                print(f"DEBUG: Stderr: {result.stderr}")
            except Exception as e:
                print(f"DEBUG: Hata oluştu: {e}")
                ConfirmDialog.show_error(self, "Hata", f"Dosya açılamadı:\n{str(e)}")
        else:
            print("DEBUG: Tag bulunamadı!")
    
    @staticmethod
    def show(parent, source_path: str, include_subfolders: bool = True):
        """Dialog'u göster"""
        dialog = SourceSearchDialog(parent, source_path, include_subfolders)
        dialog.wait_window()
