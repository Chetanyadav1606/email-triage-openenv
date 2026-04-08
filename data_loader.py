"""
Dataset loading and management for real-world email triage data.

Supports:
- Kaggle API integration for Enron/SpamAssassin datasets
- Local CSV files
- Fallback synthetic data for development

Usage:
    from data_loader import DatasetLoader
    
    loader = DatasetLoader()
    emails = loader.load_enron_emails(limit=100)  # Real Enron dataset
    # or
    emails = loader.load_local_csv("emails.csv")  # CSV file
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from models import Email
import random

logger = logging.getLogger(__name__)


class DatasetLoader:
    """Load email datasets from various sources"""

    DATA_DIR = Path("data")

    def __init__(self):
        """Initialize the data loader"""
        self.data_dir = self.DATA_DIR
        self.data_dir.mkdir(exist_ok=True)
        logger.info(f"Data directory: {self.data_dir}")

    def load_kaggle_dataset(self, dataset_name: str, limit: Optional[int] = None) -> List[Email]:
        """
        Load datasets from Kaggle.
        
        Requires kaggle API setup:
        1. Install: pip install kaggle
        2. Get API key: https://www.kaggle.com/settings/account
        3. Place ~/.kaggle/kaggle.json
        
        Args:
            dataset_name: Kaggle dataset identifier (e.g., 'wcukierski/enron-email-dataset')
            limit: Maximum number of emails to load
            
        Returns:
            List of Email objects
        """
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
        except ImportError:
            logger.warning("Kaggle API not installed. Install with: pip install kaggle")
            return self._get_fallback_emails()

        try:
            api = KaggleApi()
            api.authenticate()
            
            # Download dataset
            logger.info(f"Downloading {dataset_name} from Kaggle...")
            dataset_path = self.data_dir / dataset_name.split('/')[-1]
            api.dataset_download_files(dataset_name, path=dataset_path, unzip=True)
            
            logger.info(f"Downloaded to {dataset_path}")
            return self._parse_kaggle_dataset(dataset_path, limit)
            
        except Exception as e:
            logger.error(f"Failed to load Kaggle dataset: {e}")
            logger.info("Using fallback dataset instead")
            return self._get_fallback_emails()

    def load_enron_emails(self, limit: Optional[int] = None) -> List[Email]:
        """
        Load Enron email dataset from Kaggle.
        This is one of the largest publicly available email datasets.
        
        Dataset: https://www.kaggle.com/datasets/wcukierski/enron-email-dataset
        
        Args:
            limit: Max emails to load
            
        Returns:
            List of Email objects
        """
        # Try to load from local cache first
        cache_file = self.data_dir / "enron_emails.json"
        if cache_file.exists():
            logger.info("Loading Enron emails from cache...")
            return self._load_json_cache(cache_file, limit)

        # Otherwise download from Kaggle
        logger.info("Enron dataset cache not found. Download via Kaggle:")
        logger.info("1. pip install kaggle")
        logger.info("2. Download api key from https://www.kaggle.com/settings/account")
        logger.info("3. Place in ~/.kaggle/kaggle.json")
        logger.info("4. Download: kaggle datasets download -d wcukierski/enron-email-dataset")
        
        return self._get_fallback_emails()

    def load_spamassassin_emails(self, limit: Optional[int] = None) -> List[Email]:
        """
        Load SpamAssassin dataset (spam vs ham emails).
        
        Dataset: https://www.kaggle.com/datasets/wanderfj/spam-e-mail-detection-dataset
        
        Args:
            limit: Max emails to load
            
        Returns:
            List of Email objects with spam classification
        """
        cache_file = self.data_dir / "spamassassin_emails.json"
        if cache_file.exists():
            logger.info("Loading SpamAssassin emails from cache...")
            return self._load_json_cache(cache_file, limit)

        logger.info("SpamAssassin dataset cache not found. Using fallback...")
        return self._get_fallback_emails()

    def load_local_csv(self, csv_path: str, limit: Optional[int] = None) -> List[Email]:
        """
        Load emails from a local CSV file.
        
        Expected columns: id, subject, body, customer_id, customer_tier, 
                         true_label, true_priority, true_response
        
        Args:
            csv_path: Path to CSV file
            limit: Max rows to load
            
        Returns:
            List of Email objects
        """
        path = Path(csv_path)
        if not path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return self._get_fallback_emails()

        logger.info(f"Loading emails from {csv_path}...")
        emails = []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    
                    try:
                        email = Email(
                            id=row.get('id', str(i)),
                            subject=row.get('subject', 'No subject'),
                            body=row.get('body', ''),
                            customer_id=row.get('customer_id', f'C{i}'),
                            customer_tier=row.get('customer_tier', 'free'),
                            true_label=row.get('true_label', 'general'),
                            true_priority=row.get('true_priority', 'medium'),
                            true_response=row.get('true_response', 'Thank you for contacting us.')
                        )
                        emails.append(email)
                    except Exception as e:
                        logger.warning(f"Skipped row {i}: {e}")
                        continue
            
            logger.info(f"Loaded {len(emails)} emails from CSV")
            return emails
            
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return self._get_fallback_emails()

    def load_json_dataset(self, json_path: str, limit: Optional[int] = None) -> List[Email]:
        """
        Load emails from JSON file.
        
        Args:
            json_path: Path to JSON file
            limit: Max emails to load
            
        Returns:
            List of Email objects
        """
        path = Path(json_path)
        if not path.exists():
            logger.error(f"JSON file not found: {json_path}")
            return self._get_fallback_emails()

        logger.info(f"Loading emails from {json_path}...")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            emails = []
            items = data if isinstance(data, list) else data.get('emails', [])
            
            for i, item in enumerate(items):
                if limit and i >= limit:
                    break
                
                try:
                    email = Email(
                        id=item.get('id', str(i)),
                        subject=item.get('subject', 'No subject'),
                        body=item.get('body', ''),
                        customer_id=item.get('customer_id', f'C{i}'),
                        customer_tier=item.get('customer_tier', 'free'),
                        true_label=item.get('true_label', 'general'),
                        true_priority=item.get('true_priority', 'medium'),
                        true_response=item.get('true_response', 'Thank you.')
                    )
                    emails.append(email)
                except Exception as e:
                    logger.warning(f"Skipped item {i}: {e}")
                    continue
            
            logger.info(f"Loaded {len(emails)} emails from JSON")
            return emails
            
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            return self._get_fallback_emails()

    def _get_fallback_emails(self, limit: Optional[int] = None) -> List[Email]:
        """Get synthetic fallback emails for development/testing"""
        from tasks import load_tasks
        emails = load_tasks()
        
        if limit:
            emails = emails[:limit]
        
        logger.info(f"Using {len(emails)} fallback email(s)")
        return emails

    def _load_json_cache(self, cache_file: Path, limit: Optional[int] = None) -> List[Email]:
        """Load cached JSON emails"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            emails = [Email(**item) for item in data]
            if limit:
                emails = emails[:limit]
            
            logger.info(f"Loaded {len(emails)} cached emails")
            return emails
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return self._get_fallback_emails(limit)

    def _parse_kaggle_dataset(self, dataset_path: Path, limit: Optional[int] = None) -> List[Email]:
        """Parse Kaggle dataset files into Email objects"""
        emails = []
        
        # Look for CSV or JSON files
        for file_path in dataset_path.glob("**/*.csv"):
            emails.extend(self.load_local_csv(str(file_path), limit))
            if limit and len(emails) >= limit:
                break
        
        if not emails:
            for file_path in dataset_path.glob("**/*.json"):
                emails.extend(self.load_json_dataset(str(file_path), limit))
                if limit and len(emails) >= limit:
                    break
        
        if not emails:
            logger.warning("No emails found in Kaggle dataset")
            emails = self._get_fallback_emails(limit)
        
        return emails[:limit] if limit else emails

    def augment_emails_with_labels(self, emails: List[Email]) -> List[Email]:
        """
        Augment emails with realistic labels if they're missing.
        Uses heuristics based on subject and body content.
        
        Args:
            emails: List of emails potentially missing labels
            
        Returns:
            List of emails with assigned labels
        """
        keywords = {
            "billing": ["payment", "invoice", "charge", "refund", "subscription", "card", "price", "cost"],
            "technical": ["bug", "crash", "error", "issue", "not working", "problem", "broken", "fail", "exception"],
            "feature": ["feature", "request", "suggest", "add", "implement", "enhancement", "would like", "can you"],
            "general": []
        }
        
        priorities = {
            "high": ["urgent", "asap", "emergency", "critical", "down", "lose"],
            "medium": ["soon", "help", "issue", "problem"],
            "low": ["suggestion", "feedback", "question", "inquiry"]
        }
        
        for email in emails:
            text = (email.subject + " " + email.body).lower()
            
            # Assign label
            if not email.true_label or email.true_label == "general":
                for label, words in keywords.items():
                    if any(word in text for word in words):
                        email.true_label = label
                        break
                if not email.true_label or email.true_label == "general":
                    email.true_label = "general"
            
            # Assign priority
            if not email.true_priority or email.true_priority == "medium":
                for priority, words in priorities.items():
                    if any(word in text for word in words):
                        email.true_priority = priority
                        break
                if not email.true_priority or email.true_priority == "medium":
                    email.true_priority = "medium"
        
        logger.info(f"Augmented {len(emails)} emails with labels")
        return emails

    @staticmethod
    def split_train_test(emails: List[Email], train_ratio: float = 0.8) -> Tuple[List[Email], List[Email]]:
        """
        Split emails into train and test sets.
        
        Args:
            emails: List of emails
            train_ratio: Ratio for training (0.0-1.0)
            
        Returns:
            Tuple of (train_emails, test_emails)
        """
        random.shuffle(emails)
        split_idx = int(len(emails) * train_ratio)
        return emails[:split_idx], emails[split_idx:]
