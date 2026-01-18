"""
Smart Backup - Settings Manager
Tarih: 19 Kasım 2025
Yazar: Dr. Mustafa Afyonluoğlu

Gerekli Kütüphaneler:
    - sm_database (proje modülü)
"""

from sm_database import DatabaseManager


class SettingsManager:
    """Uygulama ayarlarını yöneten sınıf"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Varsayılan ayarları oluştur"""
        defaults = {
            'theme': 'blue',
            'appearance_mode': 'System',
            'window_width': '1200',
            'window_height': '950',
            'last_project_id': '0',
            'splitter_position': '0.4'  # Eşleştirme listesi / Yedekleme detayları splitter konumu (0-1 arası)
        }
        
        for key, value in defaults.items():
            if not self.db.get_setting(key):
                self.db.set_setting(key, value)
    
    # ==================== TEMA AYARLARI ====================
    
    def get_theme(self) -> str:
        """Tema rengini getir (blue, green, dark-blue)"""
        return self.db.get_setting('theme', 'blue')
    
    def set_theme(self, theme: str):
        """Tema rengini kaydet"""
        self.db.set_setting('theme', theme)
    
    def get_appearance_mode(self) -> str:
        """Görünüm modunu getir (Light, Dark, System)"""
        return self.db.get_setting('appearance_mode', 'System')
    
    def set_appearance_mode(self, mode: str):
        """Görünüm modunu kaydet"""
        self.db.set_setting('appearance_mode', mode)
    
    # ==================== PENCERE AYARLARI ====================
    
    def get_window_size(self) -> tuple:
        """Pencere boyutunu getir"""
        width = int(self.db.get_setting('window_width', '1200'))
        height = int(self.db.get_setting('window_height', '950'))
        return (width, height)
    
    def set_window_size(self, width: int, height: int):
        """Pencere boyutunu kaydet"""
        self.db.set_setting('window_width', str(width))
        self.db.set_setting('window_height', str(height))
    
    # ==================== SON KULLANIM AYARLARI ====================
    
    def get_last_project_id(self) -> int:
        """Son seçilen proje ID'sini getir"""
        return int(self.db.get_setting('last_project_id', '0'))
    
    def set_last_project_id(self, project_id: int):
        """Son seçilen proje ID'sini kaydet"""
        self.db.set_setting('last_project_id', str(project_id))
    
    # ==================== SPLITTER AYARLARI ====================
    
    def get_splitter_position(self) -> float:
        """Splitter konumunu getir (0-1 arası oran)"""
        return float(self.db.get_setting('splitter_position', '0.4'))
    
    def set_splitter_position(self, position: float):
        """Splitter konumunu kaydet"""
        self.db.set_setting('splitter_position', str(position))
