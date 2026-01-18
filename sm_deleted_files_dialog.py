"""
Smart Backup - Deleted Files Confirmation Dialog
Tarih: 23 Kasım 2025
Yazar: Dr. Mustafa Afyonluoğlu
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
import fnmatch
import os


class DeletedFilesConfirmDialog:
    """Silinen dosyaları göster ve seçim yaptır"""
    
    def __init__(self, parent, deleted_files_data):
        """
        Args:
            parent: Ana pencere
            deleted_files_data: Dict {mapping_id: {'deleted_files': [...], 'mapping_name': '...'}}
        """
        self.result = None
        self.deleted_files_data = deleted_files_data
        
        # Tüm dosyaları tek listede topla
        self.all_files = []
        for mapping_id, data in deleted_files_data.items():
            for file_info in data.get('deleted_files', []):
                self.all_files.append({
                    'mapping_id': mapping_id,
                    'mapping_name': data.get('mapping_name', ''),
                    'path': file_info['path'],
                    'size': file_info['size'],
                    'selected': True  # Varsayılan olarak seçili
                })
        
        # Dialog oluştur
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Silinen Dosyalar - Onay")
        self.dialog.geometry("1150x600")
        
        # Modal yap
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # ESC tuşu ile kapat
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Widget'ları oluştur"""
        # Ana frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"Silinecek Dosyalar ({len(self.all_files)} dosya)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Açıklama
        desc_label = ctk.CTkLabel(
            main_frame,
            text="Aşağıdaki dosyalar hedefte var ancak kaynakta yok. Seçili dosyalar arşive taşınacak.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        desc_label.pack(pady=(0, 10))
        
        # Üst kontrol paneli
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Filtre girişi
        filter_frame = ctk.CTkFrame(control_frame)
        filter_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(filter_frame, text="Filtre:").pack(side="left", padx=(5, 5))
        
        self.filter_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Örn: *.txt, -*.log (- ile hariç tut)"
        )
        self.filter_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        filter_btn = ctk.CTkButton(
            filter_frame,
            text="Filtrele",
            width=100,
            command=self._apply_filter
        )
        filter_btn.pack(side="left", padx=5)
        
        # Seçim butonları
        select_frame = ctk.CTkFrame(control_frame)
        select_frame.pack(side="right")
        
        select_all_btn = ctk.CTkButton(
            select_frame,
            text="Tümünü Seç",
            width=100,
            command=self._select_all
        )
        select_all_btn.pack(side="left", padx=5)
        
        deselect_all_btn = ctk.CTkButton(
            select_frame,
            text="Hiçbirini Seçme",
            width=120,
            command=self._deselect_all
        )
        deselect_all_btn.pack(side="left", padx=5)
        
        # Progress bar (yükleme sırasında gösterilecek)
        self.progress_frame = ctk.CTkFrame(main_frame)
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Dosyalar yükleniyor...",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)
        
        # Treeview için frame
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        # Treeview oluştur
        style = ttk.Style()
        style.theme_use('clam')
        
        # Dark mode için renkler
        style.configure("Treeview",
                       background="#2b2b2b",
                       foreground="white",
                       fieldbackground="#2b2b2b",
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background="#1f538d",
                       foreground="white",
                       borderwidth=1)
        style.map('Treeview',
                 background=[('selected', '#1f538d')])
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("seçim", "dosya", "boyut", "mapping"),
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="extended"
        )
        scrollbar.config(command=self.tree.yview)
        
        # Sütun başlıkları
        self.tree.heading("seçim", text="✓", anchor="center")
        self.tree.heading("dosya", text="Dosya Adı", anchor="w")
        self.tree.heading("boyut", text="Boyut", anchor="e")
        self.tree.heading("mapping", text="Hedef Konum", anchor="w")
        
        # Sütun genişlikleri
        self.tree.column("seçim", width=40, stretch=False, anchor="center")
        self.tree.column("dosya", width=550, stretch=False, anchor="w")
        self.tree.column("boyut", width=120, stretch=False, anchor="e")
        self.tree.column("mapping", width=700, stretch=True, anchor="w")
        
        self.tree.pack(fill="both", expand=True)
        
        # Tıklama ile seçim toggle
        self.tree.bind('<Button-1>', self._on_tree_click)
        self.tree.bind('<space>', self._on_tree_space)
        
        # Alt butonlar
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="İptal",
            width=120,
            command=self._on_cancel,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="left", padx=5)
        
        # Seçili dosya sayısı
        self.status_label = ctk.CTkLabel(
            button_frame,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left", expand=True)
        
        continue_btn = ctk.CTkButton(
            button_frame,
            text="Devam Et",
            width=120,
            command=self._on_continue,
            fg_color="green",
            hover_color="darkgreen"
        )
        continue_btn.pack(side="right", padx=5)
        
        # Dosyaları yükle (async benzeri)
        self.dialog.after(100, self._populate_tree)
    
    def _populate_tree(self):
        """Treeview'i doldur - her 50 dosyada progress güncelle"""
        # Progress bar göster
        self.progress_frame.pack(fill="x", pady=10)
        
        total_files = len(self.all_files)
        batch_size = 50
        
        def load_batch(start_idx):
            # Batch yükle
            end_idx = min(start_idx + batch_size, total_files)
            
            for i in range(start_idx, end_idx):
                file_data = self.all_files[i]
                filename = os.path.basename(file_data['path'])
                size_text = self._format_size(file_data['size'])
                # Hedef konumdaki tam dosya yolu
                full_path = file_data['path']
                
                # İlk sütunda seçim durumu (✓ veya ✗)
                check_mark = "✓" if file_data['selected'] else "✗"
                
                # Satır ekle
                item_id = self.tree.insert(
                    "",
                    "end",
                    values=(check_mark, filename, size_text, full_path),
                    tags=('selected' if file_data['selected'] else 'unselected',)
                )
                
                # Item ID'yi file_data ile eşleştir
                file_data['tree_item_id'] = item_id
            
            # Progress güncelle
            progress = end_idx / total_files
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"Yükleniyor... {end_idx}/{total_files} dosya")
            
            # Devam et
            if end_idx < total_files:
                self.dialog.after(10, lambda: load_batch(end_idx))
            else:
                # Tamamlandı
                self.progress_frame.pack_forget()
                self._update_status()
        
        # Yüklemeye başla
        load_batch(0)
    
    def _on_tree_click(self, event):
        """Treeview'de tıklama olayı"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            
            # Seçim sütununa tıklandıysa toggle yap
            if column == "#1" and item:  # İlk sütun
                self._toggle_selection(item)
    
    def _on_tree_space(self, event):
        """Space tuşu ile seçim toggle"""
        selected_items = self.tree.selection()
        for item in selected_items:
            self._toggle_selection(item)
    
    def _toggle_selection(self, item_id):
        """Bir item'ın seçim durumunu değiştir"""
        # File data'yı bul
        file_data = None
        for fd in self.all_files:
            if fd.get('tree_item_id') == item_id:
                file_data = fd
                break
        
        if file_data:
            # Seçimi toggle
            file_data['selected'] = not file_data['selected']
            
            # Görünümü güncelle
            check_mark = "✓" if file_data['selected'] else "✗"
            values = self.tree.item(item_id, 'values')
            self.tree.item(item_id, values=(check_mark, values[1], values[2], values[3]))
            
            # Tag'i güncelle
            if file_data['selected']:
                self.tree.item(item_id, tags=('selected',))
            else:
                self.tree.item(item_id, tags=('unselected',))
            
            self._update_status()
    
    def _update_status(self):
        """Seçili dosya sayısını güncelle"""
        selected_count = sum(1 for f in self.all_files if f['selected'])
        total_size = sum(f['size'] for f in self.all_files if f['selected'])
        
        self.status_label.configure(
            text=f"Seçili: {selected_count} / {len(self.all_files)} dosya ({self._format_size(total_size)})"
        )
    
    def _select_all(self):
        """Tümünü seç"""
        for file_data in self.all_files:
            file_data['selected'] = True
            if 'tree_item_id' in file_data:
                item_id = file_data['tree_item_id']
                values = self.tree.item(item_id, 'values')
                self.tree.item(item_id, values=("✓", values[1], values[2], values[3]))
                self.tree.item(item_id, tags=('selected',))
        self._update_status()
    
    def _deselect_all(self):
        """Hiçbirini seçme"""
        for file_data in self.all_files:
            file_data['selected'] = False
            if 'tree_item_id' in file_data:
                item_id = file_data['tree_item_id']
                values = self.tree.item(item_id, 'values')
                self.tree.item(item_id, values=("✗", values[1], values[2], values[3]))
                self.tree.item(item_id, tags=('unselected',))
        self._update_status()
    
    def _apply_filter(self):
        """Filtreyi uygula - mevcut seçimler üzerinde işlem yapar"""
        filter_text = self.filter_entry.get().strip()
        
        if not filter_text:
            messagebox.showinfo(
                "Bilgi",
                "Lütfen bir filtre girin.\n\nÖrnekler:\n  *.txt - Sadece .txt dosyaları seç\n  -*.log - .log dosyalarının seçimini kaldır\n  *.txt -*.tmp - .txt seç ama .tmp hariç",
                parent=self.dialog
            )
            return
        
        # Birden fazla pattern olabilir (boşlukla ayrılmış)
        # Önemli: "- *.zip" yerine "-*.zip" olarak düzelt
        patterns = []
        parts = filter_text.split()
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            # Tek başına "-" ise, bir sonraki pattern ile birleştir
            if part == '-' and i + 1 < len(parts):
                patterns.append('-' + parts[i + 1])
                i += 2  # İki pattern'i atla
            else:
                patterns.append(part)
                i += 1
        
        # print("\n" + "="*80)
        # print(f"🔍 FİLTRE UYGULANACAK: '{filter_text}'")
        # print(f"📋 Düzeltilmiş pattern listesi: {patterns}")
        
        # Pozitif ve negatif filtreleri ayır
        positive_patterns = [p for p in patterns if not p.startswith('-')]
        negative_patterns = [p[1:] for p in patterns if p.startswith('-') and len(p) > 1]
        
        # print(f"✅ Pozitif filtreler: {positive_patterns if positive_patterns else 'YOK'}")
        # print(f"❌ Negatif filtreler: {negative_patterns if negative_patterns else 'YOK'}")
        # print("="*80)
        
        changed_count = 0
        selected_before = sum(1 for f in self.all_files if f['selected'])
        
        # Negatif filtre için eşleşen dosyaları logla
        # if negative_patterns:
        #     print(f"\n🔎 Negatif filtre ile eşleşme kontrolü başlıyor...")
        #     print(f"   Pattern(ler): {negative_patterns}")
        
        # Her dosya için filtreyi uygula
        for file_data in self.all_files:
            filename = os.path.basename(file_data['path'])
            original_state = file_data['selected']
            
            # Pozitif filtre varsa: sadece eşleşenleri SEÇ
            if positive_patterns:
                matches_any_positive = any(fnmatch.fnmatch(filename, pattern) for pattern in positive_patterns)
                if matches_any_positive and not file_data['selected']:
                    file_data['selected'] = True
                    changed_count += 1
                    print(f"   ✓ SEÇİLDİ: {filename}")
            
            # Negatif filtre varsa: eşleşenlerin seçimini KALDIR
            if negative_patterns:
                # Her pattern için test et
                for pattern in negative_patterns:
                    matches = fnmatch.fnmatch(filename, pattern)
                    
                    if matches and file_data['selected']:
                        # print(f"   Test: '{filename}' ~= '{pattern}' → ✓ EŞLEŞME! (Seçim kaldırılıyor)")
                        file_data['selected'] = False
                        changed_count += 1
                        break
            
            # Görünümü güncelle (sadece değiştiyse)
            if original_state != file_data['selected'] and 'tree_item_id' in file_data:
                item_id = file_data['tree_item_id']
                values = self.tree.item(item_id, 'values')
                check_mark = "✓" if file_data['selected'] else "✗"
                self.tree.item(item_id, values=(check_mark, values[1], values[2], values[3]))
                self.tree.item(item_id, tags=('selected' if file_data['selected'] else 'unselected',))
        
        selected_after = sum(1 for f in self.all_files if f['selected'])
        
        print("\n" + "="*80)
        print(f"📊 SONUÇ:")
        print(f"   Önceki seçili: {selected_before}")
        print(f"   Sonraki seçili: {selected_after}")
        print(f"   Değiştirilen: {changed_count}")
        print("="*80 + "\n")
        
        self._update_status()
    
    def _log_write(self, message):
        """Debug log yazmak için - şimdilik print"""
        print(message)
    
    def _format_size(self, size_bytes):
        """Boyutu okunabilir formata çevir"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def _on_continue(self):
        """Devam Et butonuna basıldı"""
        selected_files = {}
        
        # Seçili dosyaları mapping'lere göre grupla
        for file_data in self.all_files:
            if file_data['selected']:
                mapping_id = file_data['mapping_id']
                if mapping_id not in selected_files:
                    selected_files[mapping_id] = []
                
                selected_files[mapping_id].append({
                    'path': file_data['path'],
                    'size': file_data['size']
                })
        
        if not selected_files:
            messagebox.showwarning(
                "Uyarı",
                "En az bir dosya seçmelisiniz!",
                parent=self.dialog
            )
            return
        
        self.result = selected_files
        self.dialog.destroy()
    
    def _on_cancel(self):
        """İptal butonuna basıldı"""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Dialog'u göster ve sonucu döndür"""
        self.dialog.wait_window()
        return self.result
