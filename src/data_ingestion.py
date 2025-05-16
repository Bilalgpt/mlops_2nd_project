import os
import pandas as pd
from google.cloud import storage
from src.logger import get_logger
from src.custom_exception import CustomException

from utils.common_functions import read_yaml
from config.paths_config import *

logger = get_logger(__name__)

class DataIngestion:
    def __init__(self, config):

        self.config = config['data_ingestion']
        self.bucket_name = self.config['bucket_name']
        self.file_names= self.config['bucket_file_name']

        
        
        os.makedirs(RAW_DIR, exist_ok=True)
        logger.info(f"Created directory {RAW_DIR} for storing raw data")

    def download_csv_from_gcp(self):
        try:
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            
            for file_name in self.file_names:
                file_path=os.path.join(RAW_DIR, file_name)
                if file_name== "animelist.csv":
                    blob = bucket.blob(file_name)
                    blob.download_to_filename(file_path)

                    data =pd.read_csv(file_path, nrows=5000000)
                    data.to_csv(file_path, index=False)

                    logger.info(f"Downloaded {file_name} from GCP to {file_path}")    
                
                else:
                    blob = bucket.blob(file_name)
                    blob.download_to_filename(file_path)
                    logger.info(f"Downloaded {file_name} from GCP to {file_path}")

        except Exception as e:
            logger.error("Error while downloading CSV files from GCP")
            raise CustomException("Failed to download CSV files from GCP", e)

    def run(self):
        try:
            logger.info("Data ingestion started")
            self.download_csv_from_gcp()
            logger.info("Data ingestion completed successfully")
        except Exception as ce:
            logger.error("Error in data ingestion")
            raise CustomException("Data ingestion failed", ce)
        finally:
            logger.info("Data ingestion process finished")

if __name__ == "__main__":
    try:
        config = read_yaml(CONFIG_PATH)
        data_ingestion = DataIngestion(config)
        data_ingestion.run()
    except Exception as e:
        logger.error("Error in main function of data ingestion")
        raise CustomException("Failed to run data ingestion", e)            

        