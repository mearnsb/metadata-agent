from pathlib import Path

class DataPaths:
    """Class to manage application data paths"""
    
    @classmethod
    def get_root_dir(cls) -> Path:
        """Get the root directory of the application"""
        return Path(__file__).parent.parent.parent.parent
    
    @classmethod
    def get_data_dir(cls) -> Path:
        """Get the data directory path"""
        data_dir = cls.get_root_dir() / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir
    
    @classmethod
    def get_logs_dir(cls) -> Path:
        """Get the logs directory path"""
        logs_dir = cls.get_root_dir() / "logs"
        logs_dir.mkdir(exist_ok=True)
        return logs_dir

    @staticmethod
    def get_metadata_path():
        """Get the metadata CSV file path"""
        return str(DataPaths.get_data_dir() / 'connection_schema.csv')

    @staticmethod
    def get_actions_path():
        """Get the actions CSV file path"""
        return str(DataPaths.get_data_dir() / 'actions_with_embeddings.csv') 