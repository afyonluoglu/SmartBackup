"""
Smart Backup - Eşleştirme İşlemleri Mixin
Tarih: 3 Ocak 2026
Yazar: Dr. Mustafa Afyonluoğlu

Bu modül SmartBackupApp sınıfı için eşleştirme işlemlerini içerir.
"""

import os
from sm_ui_components import MappingDialog, ConfirmDialog, SourceSearchDialog


class MappingMixin:
    """Eşleştirme işlemleri için mixin sınıfı"""
    
    # ==================== EŞLEŞME İŞLEMLERİ ====================
    
    def _load_mappings(self):
        """Eşleşmeleri listele"""
        # Mevcut verileri temizle
        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)
        
        if not self.current_project_id:
            return
        
        # Erişilemeyen sürücü için turuncu arka plan tag'i oluştur
        self.mapping_tree.tag_configure('inaccessible', background='#FF8C00', foreground='black')
        # Seçili turuncu satır için koyu turuncu
        self.mapping_tree.tag_configure('inaccessible_selected', background='#CC6600', foreground='white')
        
        # Eşleşmeleri getir
        mappings = self.db.get_mappings_by_project(self.current_project_id)
        
        for mapping in mappings:
            subdirs = "Evet" if mapping['include_subdirs'] else "Hayır"
            exclude_text = mapping.get('exclude_filter', '') or '-'
            
            # Bu eşleştirmenin erişilemeyen sürücüleri var mı kontrol et
            inaccessible = self._get_inaccessible_drives_for_mapping(
                self.current_project_id, mapping['id']
            )
            
            # Tag'i belirle
            tags = ('inaccessible',) if inaccessible else ()
            
            self.mapping_tree.insert("", "end", values=(
                mapping['id'],
                mapping['source_path'],
                mapping['file_filter'],
                exclude_text,
                subdirs,
                mapping['target_path']
            ), tags=tags)
        
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
            # Hedef sürücü kontrolünü güncelle
            self._check_all_target_drives()
            self._load_mappings()
            # Proje butonlarını güncelle (turuncu renk için)
            self._update_project_button_colors()
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
            # Hedef sürücü kontrolünü güncelle
            self._check_all_target_drives()
            self._load_mappings()
            # Proje butonlarını güncelle (turuncu renk için)
            self._update_project_button_colors()
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
            # Hedef sürücü kontrolünü güncelle
            self._check_all_target_drives()
            self._load_mappings()
            # Proje butonlarını güncelle (turuncu renk için)
            self._update_project_button_colors()
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
            # Hedef sürücü kontrolünü güncelle
            self._check_all_target_drives()
            self._load_mappings()
            # Proje butonlarını güncelle (turuncu renk için)
            self._update_project_button_colors()
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
    
    def _search_in_source(self):
        """Seçili eşleştirmenin kaynak klasöründe arama yap"""
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
        include_subdirs = bool(mapping['include_subdirs'])
        
        # Klasörün varlığını kontrol et
        if not os.path.exists(source_path):
            ConfirmDialog.show_warning(
                self, 
                "Klasör Bulunamadı", 
                f"Kaynak klasör mevcut değil:\n\n{source_path}"
            )
            return
        
        # Arama dialog'unu aç
        SourceSearchDialog.show(self, source_path, include_subdirs)
    
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
            
            # Seçili eşleştirmenin erişilemeyen sürücüleri var mı kontrol et
            values = self.mapping_tree.item(item, 'values')
            if values:
                # Treeview'dan gelen değer string olabilir, int'e çevir
                mapping_id = int(values[0])
                inaccessible = self._get_inaccessible_drives_for_mapping(
                    self.current_project_id, mapping_id
                )
                # Menüyü yeniden oluştur - erişilemeyen sürücülere göre dinamik
                self._rebuild_mapping_context_menu(has_inaccessible=bool(inaccessible))
            
            # Context menüyü göster
            try:
                self.mapping_context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.mapping_context_menu.grab_release()
    
    def _rebuild_mapping_context_menu(self, has_inaccessible: bool = False):
        """Eşleştirme context menüsünü yeniden oluştur"""
        # Mevcut menüyü temizle
        self.mapping_context_menu.delete(0, 'end')
        
        # Temel seçenekleri ekle
        self.mapping_context_menu.add_command(label="Eşleştirme Düzenle", command=self._edit_mapping)
        self.mapping_context_menu.add_command(label="Sil", command=self._delete_mapping)
        self.mapping_context_menu.add_separator()
        self.mapping_context_menu.add_command(label="Çoğalt", command=self._duplicate_mapping)
        self.mapping_context_menu.add_command(label="Kopyala", command=self._copy_mapping)
        self.mapping_context_menu.add_separator()
        self.mapping_context_menu.add_command(label="Kaynak Klasörde Ara", command=self._search_in_source)
        self.mapping_context_menu.add_command(label="Kaynak Klasörü Aç", command=self._open_source_folder)
        
        # Hedef ve Revision seçeneklerini sadece erişilebilir sürücülerde göster
        if not has_inaccessible:
            self.mapping_context_menu.add_command(label="Hedef Klasörü Aç", command=self._open_target_folder)
            self.mapping_context_menu.add_command(label="Revision'ları Aç", command=self._open_revisions_folder)
