"""
Smart Backup - Ana Uygulama
Tarih: 19 Kasım 2025
Yazar: Dr. Mustafa Afyonluoğlu

Gerekli Kütüphaneler:
    - customtkinter (pip install customtkinter)
    - tkinter (standart kütüphane)
    - sqlite3 (standart kütüphane)
    - os (standart kütüphane)
    - shutil (standart kütüphane)
    - glob (standart kütüphane)
    - datetime (standart kütüphane)
    - pathlib (standart kütüphane)
"""

import customtkinter as ctk
from tkinter import ttk, Menu, PanedWindow, VERTICAL
import threading
import time
import os
from typing import Optional

from sm_database import DatabaseManager
from sm_settings import SettingsManager
from sm_backup_engine import BackupEngine
from sm_ui_components import (ProjectDialog, MappingDialog, ProgressDialog, 
                               ConfirmDialog, BackupSelectionDialog, AnalysisSelectionDialog)
from sm_history_window import HistoryWindow
from sm_deleted_files_dialog import DeletedFilesConfirmDialog


class SmartBackupApp(ctk.CTk):
    """Smart Backup Ana Uygulama"""
    
    def __init__(self):
        super().__init__()
        
        # Veritabanı ve ayarlar
        self.db = DatabaseManager()
        self.settings = SettingsManager(self.db)
        self.backup_engine = BackupEngine()
        
        # Tema ayarlarını uygula
        ctk.set_appearance_mode(self.settings.get_appearance_mode())
        ctk.set_default_color_theme(self.settings.get_theme())
        
        # Pencere ayarları
        self.title("Smart Backup - Akıllı Yedekleme Aracı")
        width, height = self.settings.get_window_size()
        self.geometry(f"{width}x{height}+100+10")
        # MUSTAFA self._center_window()
        
        # ESC tuşu ile kapat (onay ile)
        self.bind('<Escape>', lambda e: self._confirm_quit())
        
        # Seçili proje
        self.current_project_id: Optional[int] = None
        self.project_buttons = {}  # Proje butonlarını saklamak için
        
        # Eşleştirme panosu (kopyala/yapıştır için)
        self.clipboard_mapping = None  # Panodaki eşleştirme verisi
        
        # Analiz sonuçları - yedekleme için kullanılacak
        self.analysis_results = None  # {mapping_id: {'files_to_backup': [...], 'excluded_files': [...]}}
        
        # Son yedekleme bilgisi - detay kaydetme için
        self.last_backup_id = None
        self.last_backup_files = None  # Yedeklenen dosyaların listesi
        
        self._create_widgets()
        self._load_projects()
        
        # Splitter konumunu yükle (pencere render edildikten sonra)
        self.after(100, self._apply_splitter_position)
        
        # Splitter konumu değiştiğinde kaydet
        self.bind('<ButtonRelease-1>', self._on_splitter_released)
        
        # Son seçilen projeyi yükle
        last_project_id = self.settings.get_last_project_id()
        if last_project_id > 0:
            self._select_project_by_id(last_project_id)
    
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
        # Ana container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # # Üst panel - Başlık ve tema
        # top_panel = ctk.CTkFrame(main_container, fg_color="transparent")
        # top_panel.pack(fill="x", pady=(0, 20))
        
        # title_label = ctk.CTkLabel(top_panel, 
        #                            text="Smart Backup - Akıllı Yedekleme Aracı",
        #                            font=("", 24, "bold"))
        # title_label.pack(side="left")
        
        # # Tema seçici
        # theme_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        # theme_frame.pack(side="right")
        
        # ctk.CTkLabel(theme_frame, text="Tema:").pack(side="left", padx=(0, 5))
        # self.appearance_menu = ctk.CTkOptionMenu(
        #     theme_frame,
        #     values=["Light", "Dark", "System"],
        #     command=self._change_appearance,
        #     width=100
        # )
        # self.appearance_menu.set(self.settings.get_appearance_mode())
        # self.appearance_menu.pack(side="left")
        
        # Sol panel - Proje listesi
        left_panel = ctk.CTkFrame(main_container, width=300)
        left_panel.pack(side="left", fill="both", pady=(0, 0), padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Proje listesi başlık
        project_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        project_header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(project_header, text="Projeler", 
                    font=("", 16, "bold")).pack(side="left")
        
        # Proje butonları
        project_buttons = ctk.CTkFrame(left_panel, fg_color="transparent")
        project_buttons.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(project_buttons, text="Yeni Proje", 
                     command=self._add_project, width=90).pack(side="left", padx=(0, 5))
        ctk.CTkButton(project_buttons, text="Düzenle", 
                     command=self._edit_project, width=80).pack(side="left", padx=(0, 5))
        ctk.CTkButton(project_buttons, text="Sil", 
                     command=self._delete_project, width=60,
                     fg_color="red", hover_color="darkred").pack(side="left")
        
        # Proje listesi
        list_frame = ctk.CTkFrame(left_panel)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.project_listbox = ctk.CTkScrollableFrame(list_frame)
        self.project_listbox.pack(fill="both", expand=True)
        
        # Proje listesi için context menü
        self.project_context_menu = Menu(self, 
                                        tearoff=0,
                                        background="#333333", 
                                        foreground="white", 
                                        activebackground="#1F6AA5"
                                         )
        self.project_context_menu.add_command(label="Proje Düzenle", command=self._edit_project)
        self.project_context_menu.add_command(label="Proje Sil", command=self._delete_project)
        self.project_context_menu.add_separator()
        self.project_context_menu.add_command(label="Proje Çoğalt", command=self._duplicate_project)

        list_font = ("Segoe UI", 13) 
        self.project_context_menu.config(font=list_font)    
        
        # Tema seçici - Sol panelin altında
        theme_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 0))
        
        ctk.CTkLabel(theme_frame, text="Tema:", font=("", 12)).pack(side="left", padx=(5, 5))
        self.appearance_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Light", "Dark", "System"],
            command=self._change_appearance,
            width=180
        )
        self.appearance_menu.set(self.settings.get_appearance_mode())
        self.appearance_menu.pack(side="left", padx=(0, 5))
        
        # Sağ panel - Eşleşmeler
        right_panel = ctk.CTkFrame(main_container)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Eşleşme başlık
        mapping_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        mapping_header.pack(fill="x", pady=(0, 10))
        
        self.mapping_title = ctk.CTkLabel(mapping_header, 
                                         text="Eşleşmeler (Proje seçin)",
                                         font=("", 16, "bold"))
        self.mapping_title.pack(side="left")
        
        # Eşleşme butonları
        mapping_buttons = ctk.CTkFrame(right_panel, fg_color="transparent")
        mapping_buttons.pack(fill="x", pady=(0, 10))
        
        self.add_mapping_btn = ctk.CTkButton(mapping_buttons, text="Yeni Eşleşme",
                                            command=self._add_mapping, width=110,
                                            state="disabled")
        self.add_mapping_btn.pack(side="left", padx=(0, 5))
        
        self.edit_mapping_btn = ctk.CTkButton(mapping_buttons, text="Düzenle",
                                             command=self._edit_mapping, width=80,
                                             state="disabled")
        self.edit_mapping_btn.pack(side="left", padx=(0, 5))
        
        self.delete_mapping_btn = ctk.CTkButton(mapping_buttons, text="Sil",
                                               command=self._delete_mapping, width=60,
                                               fg_color="red", hover_color="darkred",
                                               state="disabled")
        self.delete_mapping_btn.pack(side="left")
        
        # Yapıştır butonu - sadece panoda eşleştirme varsa görünecek
        self.paste_mapping_btn = ctk.CTkButton(mapping_buttons, text="Yapıştır",
                                               command=self._paste_mapping, width=80,
                                               fg_color="#FF8C00", hover_color="#FF6600")
        # Başlangıçta gizli - pack yapılmadı
        
        # PanedWindow - Eşleştirme tablosu ve Yedekleme detayları arasında splitter
        self.paned_window = PanedWindow(right_panel, orient=VERTICAL, 
                                        sashwidth=8, sashrelief="raised",
                                        bg="#3B8ED0")
        self.paned_window.pack(fill="both", expand=True, pady=(0, 5))
        
        # Üst panel - Eşleşme tablosu
        tree_frame = ctk.CTkFrame(self.paned_window)
        self.paned_window.add(tree_frame, minsize=100)
        
        # Scrollbar'lar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview için style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", 
                       fieldbackground="#ffebb4", borderwidth=0,
                       font=("Arial", 14),
                       rowheight=40)  # <-- Satır yüksekliğini arttırır (varsayılan ~20)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white",
                       font=("Arial", 15, "bold")) 
        
        style.map("Treeview.Heading",
                 background=[('active', '#5a5a5a')])  # Hover color for headers

        # Treeview
        columns = ("ID", "Kaynak", "Filtre", "Hariç Tutulanlar", "Alt Klasörler", "Hedef")
        self.mapping_tree = ttk.Treeview(tree_frame, columns=columns, 
                                        show="headings",
                                        height=6,  # ←  (satır sayısı cinsinden)
                                        yscrollcommand=vsb.set,
                                        xscrollcommand=hsb.set)
        
        # Sütun başlıkları
        self.mapping_tree.heading("ID", text="ID")
        self.mapping_tree.heading("Kaynak", text="Kaynak Klasör")
        self.mapping_tree.heading("Filtre", text="Dosya")
        self.mapping_tree.heading("Hariç Tutulanlar", text="Hariç Tutulanlar")
        self.mapping_tree.heading("Alt Klasörler", text="Alt Klasörler")
        self.mapping_tree.heading("Hedef", text="Hedef Klasör")
        
        # Sütun genişlikleri
        self.mapping_tree.column("ID", width=50, stretch=False, anchor="center")
        self.mapping_tree.column("Kaynak", stretch=False, width=500)
        self.mapping_tree.column("Filtre", stretch=False, width=100)
        self.mapping_tree.column("Hariç Tutulanlar", stretch=False, width=180)
        self.mapping_tree.column("Alt Klasörler", stretch=False, width=100, anchor="center")
        self.mapping_tree.column("Hedef", stretch=False, width=700)
        
        # Scrollbar yapılandırması
        vsb.config(command=self.mapping_tree.yview)
        hsb.config(command=self.mapping_tree.xview)
        
        # Grid yerleşimi
        self.mapping_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Çift tıklama ile düzenle
        self.mapping_tree.bind('<Double-Button-1>', lambda e: self._edit_mapping())
        self.mapping_tree.bind("<<TreeviewSelect>>", lambda e: self._update_mapping_buttons())
        
        # Eşleştirme listesi için context menü
        self.mapping_context_menu = Menu(self,
                                         tearoff=0,
                                         background="#333333", 
                                        foreground="white", 
                                        activebackground="#1F6AA5"
                                         )
        self.mapping_context_menu.add_command(label="Eşleştirme Düzenle", command=self._edit_mapping)
        self.mapping_context_menu.add_command(label="Sil", command=self._delete_mapping)
        self.mapping_context_menu.add_separator()
        self.mapping_context_menu.add_command(label="Çoğalt", command=self._duplicate_mapping)
        self.mapping_context_menu.add_command(label="Kopyala", command=self._copy_mapping)
        self.mapping_context_menu.add_separator()
        self.mapping_context_menu.add_command(label="Kaynak Klasörü Aç", command=self._open_source_folder)
        self.mapping_context_menu.add_command(label="Hedef Klasörü Aç", command=self._open_target_folder)
        self.mapping_context_menu.add_command(label="Revision'ları Aç", command=self._open_revisions_folder)
        self.mapping_context_menu.config(font=list_font)   

        # Sağ tık için binding
        self.mapping_tree.bind('<Button-3>', self._show_mapping_context_menu)
        
        # Alt panel - Log paneli (Yedekleme detayları)
        log_frame = ctk.CTkFrame(self.paned_window)
        self.paned_window.add(log_frame, minsize=100)
        
        log_label = ctk.CTkLabel(log_frame, text="Yedekleme Detayları",
                                font=("", 12, "bold"), anchor="w")
        log_label.pack(fill="x", padx=10, pady=(5, 0))
        
        # Scrollable text box
        self.log_textbox = ctk.CTkTextbox(log_frame, height=110, 
                                         font=("Arial", 12),
                                         wrap="word",
                                         fg_color="#000000",
                                         text_color="#FFFFFF")
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_textbox.configure(state="disabled")  # Read-only
        
        # İstatistik paneli
        stats_frame = ctk.CTkFrame(right_panel)
        stats_frame.pack(fill="x", pady=(0, 10))
        
        self.stats_label = ctk.CTkLabel(stats_frame, 
                                        text="İstatistikler: -",
                                        font=("", 12))
        self.stats_label.pack(pady=5)

        # Aksiyon butonları
        action_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        action_frame.pack(fill="x")
        
        self.calculate_btn = ctk.CTkButton(action_frame, text="Hesapla",
                                          command=self._calculate, width=100,
                                          state="disabled")
        self.calculate_btn.pack(side="left", padx=(0, 5))
        
        self.analyze_btn = ctk.CTkButton(action_frame, text="Analiz",
                                        command=self._analyze, width=100,
                                        state="disabled")
        self.analyze_btn.pack(side="left", padx=(0, 5))
        
        self.backup_btn = ctk.CTkButton(action_frame, text="Yedekle",
                                       command=self._backup, width=100,
                                       fg_color="green", hover_color="darkgreen",
                                       state="disabled")
        self.backup_btn.pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(action_frame, text="Geçmiş",
                     command=self._show_history, width=100).pack(side="left", padx=(0, 5))
        
        # Detayları Kaydet butonu - yedekleme tamamlandığında görünür olacak
        self.save_details_btn = ctk.CTkButton(action_frame, text="Detayları Kaydet",
                                             command=self._save_backup_file_details, width=120,
                                             fg_color="#FF8C00", hover_color="#FF6600")
        # Başlangıçta gizli - pack yapılmadı
        
        # Kapat butonu sağ alt
        ctk.CTkButton(action_frame, text="Kapat", command=self.quit,
                     width=100).pack(side="right")
    
    def _apply_splitter_position(self):
        """Kaydedilmiş splitter konumunu uygula"""
        try:
            position = self.settings.get_splitter_position()
            self.update_idletasks()
            total_height = self.paned_window.winfo_height()
            if total_height > 0:
                sash_position = int(total_height * position)
                self.paned_window.sash_place(0, 0, sash_position)
        except Exception:
            pass  # İlk yüklemede hata olabilir
    
    def _on_splitter_released(self, event):
        """Splitter sürüklemesi bırakıldığında konumu kaydet"""
        try:
            # PanedWindow'un sash konumunu al
            sash_info = self.paned_window.sash_coord(0)
            if sash_info:
                sash_y = sash_info[1]
                total_height = self.paned_window.winfo_height()
                if total_height > 0:
                    position = sash_y / total_height
                    # Geçerli bir pozisyon ise kaydet (0.1 - 0.9 arası)
                    if 0.1 <= position <= 0.9:
                        self.settings.set_splitter_position(position)
        except Exception:
            pass  # Sash bulunamazsa hata olabilir
    
    def _update_mapping_buttons(self):
        """Eşleşme butonlarını güncelle"""
        has_selection = len(self.mapping_tree.selection()) > 0
        state = "normal" if has_selection else "disabled"
        self.edit_mapping_btn.configure(state=state)
        self.delete_mapping_btn.configure(state=state)
            
    def _change_appearance(self, mode: str):
        """Görünüm modunu değiştir"""
        ctk.set_appearance_mode(mode)
        self.settings.set_appearance_mode(mode)
    
    def _log_clear(self):
        """Log alanını temizle"""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
    
    def _log_write(self, message: str, color: str = None):
        """Log alanına mesaj yaz"""
        self.log_textbox.configure(state="normal")
        if color:
            # Renkli metin için tag kullan
            tag_name = f"color_{color}"
            self.log_textbox.tag_config(tag_name, foreground=color)
            self.log_textbox.insert("end", message + "\n", tag_name)
        else:
            self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")  # Otomatik scroll
        self.log_textbox.configure(state="disabled")
    
    # ==================== PROJE İŞLEMLERİ ====================
    
    def _load_projects(self):
        """Projeleri listele"""
        # Mevcut widget'ları temizle
        for widget in self.project_listbox.winfo_children():
            widget.destroy()
        
        # Projeleri getir
        projects = self.db.get_all_projects()
        
        # Proje butonlarını saklamak için dict
        self.project_buttons = {}
        
        for project in projects:
            btn = ctk.CTkButton(
                self.project_listbox,
                text=project['name'],
                command=lambda p=project: self._select_project(p),
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30")
            )
            btn.pack(fill="x", pady=2)
            
            # Sağ tık için binding
            btn.bind('<Button-3>', lambda e, pid=project['id']: self._show_project_context_menu(e, pid))
            
            self.project_buttons[project['id']] = btn
    
    def _select_project(self, project):
        """Proje seç"""
        self.current_project_id = project['id']
        self.settings.set_last_project_id(project['id'])
        
        # Analiz sonuçlarını sıfırla (proje değişti)
        self.analysis_results = None
        
        # Detayları Kaydet butonunu gizle (proje değişti)
        self._hide_save_details_button()
        
        # Tüm proje butonlarını normal renge çevir
        for proj_id, btn in self.project_buttons.items():
            if proj_id == project['id']:
                # Seçili proje - vurgulu renk
                btn.configure(fg_color=("#3B8ED0", "#1F6AA5"))
            else:
                # Seçili değil - normal renk
                btn.configure(fg_color="transparent")
        
        # Başlığı güncelle
        self.mapping_title.configure(text=f"Eşleşmeler - {project['name']}")
        
        # Butonları aktif et
        self.add_mapping_btn.configure(state="normal")
        self.calculate_btn.configure(state="normal")
        self.analyze_btn.configure(state="normal")
        self.backup_btn.configure(state="normal")
        
        # Eşleşmeleri yükle
        self._load_mappings()
    
    def _select_project_by_id(self, project_id: int):
        """ID ile proje seç"""
        project = self.db.get_project_by_id(project_id)
        if project:
            self._select_project(project)
    
    def _add_project(self):
        """Yeni proje ekle"""
        dialog = ProjectDialog(self, "Yeni Proje")
        self.wait_window(dialog)
        
        if dialog.result:
            name, desc = dialog.result
            try:
                project_id = self.db.add_project(name, desc)
                self._load_projects()
                self._select_project_by_id(project_id)
                ConfirmDialog.show_info(self, "Başarılı", "Proje başarıyla oluşturuldu.")
            except Exception as e:
                ConfirmDialog.show_error(self, "Hata", f"Proje oluşturulamadı: {str(e)}")
    
    def _edit_project(self):
        """Proje düzenle"""
        if not self.current_project_id:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir proje seçin!")
            return
        
        project = self.db.get_project_by_id(self.current_project_id)
        dialog = ProjectDialog(self, "Proje Düzenle", 
                              project['name'], project['description'])
        self.wait_window(dialog)
        
        if dialog.result:
            name, desc = dialog.result
            try:
                self.db.update_project(self.current_project_id, name, desc)
                self._load_projects()
                self._select_project_by_id(self.current_project_id)
                ConfirmDialog.show_info(self, "Başarılı", "Proje başarıyla güncellendi.")
            except Exception as e:
                ConfirmDialog.show_error(self, "Hata", f"Proje güncellenemedi: {str(e)}")
    
    def _delete_project(self):
        """Proje sil"""
        if not self.current_project_id:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir proje seçin!")
            return
        
        project = self.db.get_project_by_id(self.current_project_id)
        
        if not ConfirmDialog.ask(self, "Onay",
                                f"'{project['name']}' projesini ve tüm eşleşmelerini "
                                f"silmek istediğinizden emin misiniz?"):
            return
        
        self.db.delete_project(self.current_project_id)
        self.current_project_id = None
        self._load_projects()
        self._clear_mappings()
        ConfirmDialog.show_info(self, "Başarılı", "Proje başarıyla silindi.")
    
    def _duplicate_project(self):
        """Proje ve eşleştirmelerini çoğalt"""
        if not self.current_project_id:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir proje seçin!")
            return
        
        # Mevcut projeyi al
        project = self.db.get_project_by_id(self.current_project_id)
        
        # Yeni isim iste
        dialog = ProjectDialog(self, "Proje Çoğalt", 
                              f"{project['name']} (Kopya)", project['description'])
        self.wait_window(dialog)
        
        if dialog.result:
            name, desc = dialog.result
            try:
                # Yeni proje oluştur
                new_project_id = self.db.add_project(name, desc)
                
                # Eski projenin eşleştirmelerini al
                mappings = self.db.get_mappings_by_project(self.current_project_id)
                
                # Eşleştirmeleri yeni projeye kopyala
                for mapping in mappings:
                    self.db.add_mapping(
                        new_project_id,
                        mapping['source_path'],
                        mapping['file_filter'],
                        mapping.get('exclude_filter', ''),
                        bool(mapping['include_subdirs']),
                        mapping['target_path']
                    )
                
                self._load_projects()
                self._select_project_by_id(new_project_id)
                ConfirmDialog.show_info(self, "Başarılı", 
                                       f"Proje ve {len(mappings)} eşleştirme başarıyla çoğaltıldı.")
            except Exception as e:
                ConfirmDialog.show_error(self, "Hata", f"Proje çoğaltılamadı: {str(e)}")
    
    def _show_project_context_menu(self, event, project_id):
        """Proje context menüsünü göster"""
        # Önce projeyi seç
        self._select_project_by_id(project_id)
        
        # Context menüyü göster
        try:
            self.project_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.project_context_menu.grab_release()
    
    # ==================== EŞLEŞME İŞLEMLERİ ====================
    
    def _load_mappings(self):
        """Eşleşmeleri listele"""
        # Mevcut verileri temizle
        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)
        
        if not self.current_project_id:
            return
        
        # Eşleşmeleri getir
        mappings = self.db.get_mappings_by_project(self.current_project_id)
        
        for mapping in mappings:
            subdirs = "Evet" if mapping['include_subdirs'] else "Hayır"
            exclude_text = mapping.get('exclude_filter', '') or '-'
            self.mapping_tree.insert("", "end", values=(
                mapping['id'],
                mapping['source_path'],
                mapping['file_filter'],
                exclude_text,
                subdirs,
                mapping['target_path']
            ))
        
        # Butonları güncelle
        self._update_mapping_buttons()
        
        # İstatistikleri temizle
        self.stats_label.configure(text="İstatistikler: -")
        
        # Analiz sonuçlarını sıfırla (eşleşmeler değişti)
        self.analysis_results = None
    
    def _clear_mappings(self):
        """Eşleşmeleri temizle"""
        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)
        
        self.mapping_title.configure(text="Eşleşmeler (Proje seçin)")
        self.add_mapping_btn.configure(state="disabled")
        self.edit_mapping_btn.configure(state="disabled")
        self.delete_mapping_btn.configure(state="disabled")
        self.calculate_btn.configure(state="disabled")
        self.analyze_btn.configure(state="disabled")
        self.backup_btn.configure(state="disabled")
        self.stats_label.configure(text="İstatistikler: -")
    
    def _update_mapping_buttons(self):
        """Eşleşme butonlarını güncelle"""
        has_selection = len(self.mapping_tree.selection()) > 0
        state = "normal" if has_selection else "disabled"
        self.edit_mapping_btn.configure(state=state)
        self.delete_mapping_btn.configure(state=state)
    
    def _add_mapping(self):
        """Yeni eşleşme ekle"""
        if not self.current_project_id:
            return
        
        dialog = MappingDialog(self, "Yeni Eşleşme")
        self.wait_window(dialog)
        
        if dialog.result:
            source, filter_str, exclude_str, subdirs, target = dialog.result
            self.db.add_mapping(self.current_project_id, source, filter_str, 
                              exclude_str, subdirs, target)
            self._load_mappings()
            ConfirmDialog.show_info(self, "Başarılı", "Eşleşme başarıyla eklendi.")
    
    def _edit_mapping(self):
        """Eşleşme düzenle"""
        selection = self.mapping_tree.selection()
        if not selection:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir eşleşme seçin!")
            return
        
        item = self.mapping_tree.item(selection[0])
        mapping_id = item['values'][0]
        
        mapping = self.db.get_mapping_by_id(mapping_id)
        dialog = MappingDialog(self, "Eşleşme Düzenle",
                              mapping['source_path'],
                              mapping['file_filter'],
                              mapping.get('exclude_filter', ''),
                              bool(mapping['include_subdirs']),
                              mapping['target_path'])
        self.wait_window(dialog)
        
        if dialog.result:
            source, filter_str, exclude_str, subdirs, target = dialog.result
            self.db.update_mapping(mapping_id, source, filter_str, exclude_str, 
                                 subdirs, target)
            self._load_mappings()
            ConfirmDialog.show_info(self, "Başarılı", "Eşleşme başarıyla güncellendi.")
    
    def _delete_mapping(self):
        """Eşleşme sil"""
        selection = self.mapping_tree.selection()
        if not selection:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir eşleşme seçin!")
            return
        
        if not ConfirmDialog.ask(self, "Onay",
                                "Seçili eşleşmeyi silmek istediğinizden emin misiniz?"):
            return
        
        item = self.mapping_tree.item(selection[0])
        mapping_id = item['values'][0]
        
        self.db.delete_mapping(mapping_id)
        self._load_mappings()
        ConfirmDialog.show_info(self, "Başarılı", "Eşleşme başarıyla silindi.")
    
    def _duplicate_mapping(self):
        """Eşleşmeyi çoğalt"""
        selection = self.mapping_tree.selection()
        if not selection:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir eşleşme seçin!")
            return
        
        item = self.mapping_tree.item(selection[0])
        mapping_id = item['values'][0]
        
        # Mevcut eşleşmeyi al
        mappings = self.db.get_mappings_by_project(self.current_project_id)
        mapping = next((m for m in mappings if m['id'] == mapping_id), None)
        
        if not mapping:
            return
        
        # Yeni eşleşme ekle (aynı bilgilerle)
        try:
            self.db.add_mapping(
                self.current_project_id,
                mapping['source_path'],
                mapping['file_filter'],
                mapping.get('exclude_filter', ''),
                bool(mapping['include_subdirs']),
                mapping['target_path']
            )
            self._load_mappings()
            ConfirmDialog.show_info(self, "Başarılı", "Eşleşme başarıyla çoğaltıldı.")
        except Exception as e:
            ConfirmDialog.show_error(self, "Hata", f"Eşleşme çoğaltılamadı: {str(e)}")
    
    def _copy_mapping(self):
        """Seçili eşleştirmeyi panoya kopyala"""
        selection = self.mapping_tree.selection()
        if not selection:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir eşleşme seçin!")
            return
        
        item = self.mapping_tree.item(selection[0])
        mapping_id = item['values'][0]
        
        # Eşleştirmeyi al
        mapping = self.db.get_mapping_by_id(mapping_id)
        
        if not mapping:
            return
        
        # Panoya kopyala (proje bağımsız)
        self.clipboard_mapping = {
            'source_path': mapping['source_path'],
            'file_filter': mapping['file_filter'],
            'exclude_filter': mapping.get('exclude_filter', ''),
            'include_subdirs': bool(mapping['include_subdirs']),
            'target_path': mapping['target_path']
        }
        
        # Yapıştır butonunu göster
        self._show_paste_button()
        
        ConfirmDialog.show_info(self, "Kopyalandı", "Eşleştirme panoya kopyalandı.")
    
    def _paste_mapping(self):
        """Panodaki eşleştirmeyi mevcut projeye yapıştır"""
        if not self.current_project_id:
            ConfirmDialog.show_warning(self, "Uyarı", "Lütfen bir proje seçin!")
            return
        
        if not self.clipboard_mapping:
            ConfirmDialog.show_warning(self, "Uyarı", "Panoda kopyalanmış eşleştirme yok!")
            return
        
        try:
            self.db.add_mapping(
                self.current_project_id,
                self.clipboard_mapping['source_path'],
                self.clipboard_mapping['file_filter'],
                self.clipboard_mapping['exclude_filter'],
                self.clipboard_mapping['include_subdirs'],
                self.clipboard_mapping['target_path']
            )
            self._load_mappings()
            ConfirmDialog.show_info(self, "Başarılı", "Eşleştirme başarıyla yapıştırıldı.")
        except Exception as e:
            ConfirmDialog.show_error(self, "Hata", f"Eşleştirme yapıştırılamadı: {str(e)}")
    
    def _show_paste_button(self):
        """Yapıştır butonunu göster"""
        try:
            self.paste_mapping_btn.pack(side="left", padx=(5, 0))
        except:
            pass
    
    def _hide_paste_button(self):
        """Yapıştır butonunu gizle"""
        try:
            self.paste_mapping_btn.pack_forget()
        except:
            pass

    def _open_source_folder(self):
        """Seçili eşleştirmenin kaynak klasörünü aç"""
        selection = self.mapping_tree.selection()
        if not selection:
            return
        
        item = self.mapping_tree.item(selection[0])
        mapping_id = item['values'][0]
        
        # Eşleştirmeyi al
        mappings = self.db.get_mappings_by_project(self.current_project_id)
        mapping = next((m for m in mappings if m['id'] == mapping_id), None)
        
        if not mapping:
            return
        
        source_path = mapping['source_path']
        
        # Klasörün varlığını kontrol et
        if not os.path.exists(source_path):
            ConfirmDialog.show_warning(
                self, 
                "Klasör Bulunamadı", 
                f"Kaynak klasör mevcut değil:\n\n{source_path}"
            )
            return
        
        # Windows gezgininde aç
        try:
            os.startfile(source_path)
        except Exception as e:
            ConfirmDialog.show_error(
                self, 
                "Hata", 
                f"Klasör açılamadı:\n\n{str(e)}"
            )
    
    def _open_target_folder(self):
        """Seçili eşleştirmenin hedef klasörünü aç"""
        selection = self.mapping_tree.selection()
        if not selection:
            return
        
        item = self.mapping_tree.item(selection[0])
        mapping_id = item['values'][0]
        
        # Eşleştirmeyi al
        mappings = self.db.get_mappings_by_project(self.current_project_id)
        mapping = next((m for m in mappings if m['id'] == mapping_id), None)
        
        if not mapping:
            return
        
        target_path = mapping['target_path']
        
        # Klasörün varlığını kontrol et
        if not os.path.exists(target_path):
            ConfirmDialog.show_warning(
                self, 
                "Klasör Bulunamadı", 
                f"Hedef klasör mevcut değil:\n\n{target_path}\n\nLütfen harici diskin bağlı olduğundan emin olun."
            )
            return
        
        # Windows gezgininde aç
        try:
            os.startfile(target_path)
        except Exception as e:
            ConfirmDialog.show_error(
                self, 
                "Hata", 
                f"Klasör açılamadı:\n\n{str(e)}"
            )
    
    def _open_revisions_folder(self):
        """Seçili eşleştirmenin _REVISIONS klasörünü aç"""
        selection = self.mapping_tree.selection()
        if not selection:
            return
        
        item = self.mapping_tree.item(selection[0])
        mapping_id = item['values'][0]
        
        # Eşleştirmeyi al
        mappings = self.db.get_mappings_by_project(self.current_project_id)
        mapping = next((m for m in mappings if m['id'] == mapping_id), None)
        
        if not mapping:
            return
        
        target_path = mapping['target_path']
        revisions_path = os.path.join(target_path, '_REVISIONS')
        
        # _REVISIONS klasörünün varlığını kontrol et
        if not os.path.exists(revisions_path):
            ConfirmDialog.show_warning(
                self, 
                "Klasör Bulunamadı", 
                f"_REVISIONS klasörü mevcut değil:\n\n{revisions_path}\n\nHenüz hiç dosya arşivlenmemiş olabilir."
            )
            return
        
        # Windows gezgininde aç
        try:
            os.startfile(revisions_path)
        except Exception as e:
            ConfirmDialog.show_error(
                self, 
                "Hata", 
                f"Klasör açılamadı:\n\n{str(e)}"
            )
    
    def _show_mapping_context_menu(self, event):
        """Eşleştirme context menüsünü göster"""
        # Tıklanan öğeyi seç
        item = self.mapping_tree.identify_row(event.y)
        if item:
            self.mapping_tree.selection_set(item)
            
            # Context menüyü göster
            try:
                self.mapping_context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.mapping_context_menu.grab_release()
    
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
        self._log_write("HESAPLAMA İŞLEMİ", "#A9E4FF")
        self._log_write("=" * 80, "#00A0E9")
        
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
            # Log'a eşleşme bilgisi yaz
            self._log_write(f"\n[{idx}/{len(selected_mappings)}] {mapping['source_path']}", "#FFAE35")
            self._log_write(f"    Hedef: {mapping['target_path']}", "#ADADAD")
            self._log_write(f"    Filtre: {mapping['file_filter']}", "#ADADAD")
            if mapping.get('exclude_filter'):
                self._log_write(f"    Hariç: {mapping.get('exclude_filter')}", "#ADADAD")
            
            # Detaylı analiz yap
            # print(f"Gösterilecek dosya sayısı: {max_files_to_show}")
            result = self.backup_engine.analyze_mapping_detailed(
                mapping['source_path'],
                mapping['file_filter'],
                mapping.get('exclude_filter', ''),
                bool(mapping['include_subdirs']),
                mapping['target_path'],
                max_files_to_show
            )
            
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
                    self._log_write(f"    → Silinecek (kaynakta yok): {deleted_count:,} dosya ({BackupEngine.format_size(deleted_size)})", "#FF6B6B")
            
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
                self._log_write(f"SİLİNEN DOSYALAR (Kaynakta olmayan) (İlk {min(max_files_to_show, len(all_deleted_files))} / {total_deleted_count})", "#A9E4FF")
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
        
        size_str = BackupEngine.format_size(total_size)
        excluded_str = BackupEngine.format_size(total_excluded_size)

        # Toplam dosya sayısı: yedeklenecek + atlanan + hariç tutulan
        grand_total = total_files + total_skipped + total_excluded
        summary = f"Toplam dosya: {grand_total}  | Yedeklenecek: {total_files}  | Atlanan: {total_skipped} | Hariç tutulan: {total_excluded}  | Silinecek: {total_deleted} | Arşivlenen: {total_revision_count}"

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
                
                # Yedekleme başarılı --> detay kaydetme butonunu göster
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
    
    def _show_history(self):
        """Geçmiş penceresini göster"""
        HistoryWindow(self, self.db)
    
    def _confirm_quit(self):
        """Kapat onayı iste"""
        if ConfirmDialog.ask(self, "Kapat", "Uygulamayı kapatmak istediğinizden emin misiniz?"):
            self.quit()
    
    def quit(self):
        """Uygulamadan çık"""
        # Pencere boyutunu kaydet
        width = self.winfo_width()
        height = self.winfo_height()
        # MUSTAFA self.settings.set_window_size(width, height)
        
        # Veritabanını kapat
        self.db.close()
        
        # Uygulamayı kapat
        self.destroy()


def main():
    """Ana fonksiyon"""
    app = SmartBackupApp()
    app.mainloop()


if __name__ == "__main__":
    main()
