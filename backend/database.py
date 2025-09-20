import os
from google.cloud import firestore
from google.oauth2 import service_account
import json
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FirestoreDB:
    def __init__(self):
        self.db = None
        self._initialize_firestore()
    
    def _initialize_firestore(self):
        """Initialize Firestore client"""
        try:
            # Try to get credentials from environment variable
            credentials_path = os.getenv("FIRESTORE_CREDENTIALS")
            
            if credentials_path and os.path.exists(credentials_path):
                # Use service account file
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.db = firestore.Client(credentials=credentials)
            else:
                # Use default credentials (for local development or cloud deployment)
                self.db = firestore.Client()
            
            print("Firestore client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Firestore: {e}")
            # For development, create a mock client
            self.db = None
    
    async def create_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Create a document in Firestore"""
        try:
            if not self.db:
                logger.warning("Firestore not initialized, using mock data")
                return True
            
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.set(data)
            return True
        except Exception as e:
            print(f"Error creating document: {e}")
            return False
    
    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document from Firestore"""
        try:
            if not self.db:
                logger.warning("Firestore not initialized, returning None")
                return None
            
            doc_ref = self.db.collection(collection).document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting document: {e}")
            return None
    
    async def update_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Update a document in Firestore"""
        try:
            if not self.db:
                logger.warning("Firestore not initialized, using mock data")
                return True
            
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False
    
    async def delete_document(self, collection: str, document_id: str) -> bool:
        """Delete a document from Firestore"""
        try:
            if not self.db:
                logger.warning("Firestore not initialized, using mock data")
                return True
            
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    async def query_collection(self, collection: str, filters: List[tuple] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Query a collection with optional filters"""
        try:
            if not self.db:
                logger.warning("Firestore not initialized, returning empty list")
                return []
            
            query = self.db.collection(collection)
            
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            return [{"id": doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            print(f"Error querying collection: {e}")
            return []
    
    async def add_to_subcollection(self, collection: str, document_id: str, subcollection: str, data: Dict[str, Any]) -> Optional[str]:
        """Add a document to a subcollection"""
        try:
            if not self.db:
                logger.warning("Firestore not initialized, using mock data")
                return "mock_id"
            
            subcol_ref = self.db.collection(collection).document(document_id).collection(subcollection)
            doc_ref = subcol_ref.add(data)
            return doc_ref[1].id
        except Exception as e:
            print(f"Error adding to subcollection: {e}")
            return None
    
    async def get_subcollection(self, collection: str, document_id: str, subcollection: str) -> List[Dict[str, Any]]:
        """Get all documents from a subcollection"""
        try:
            if not self.db:
                logger.warning("Firestore not initialized, returning empty list")
                return []
            
            subcol_ref = self.db.collection(collection).document(document_id).collection(subcollection)
            docs = subcol_ref.stream()
            return [{"id": doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            print(f"Error getting subcollection: {e}")
            return []
    
    def create_batch(self):
        """Create a batch for atomic operations"""
        if not self.db:
            return None
        return self.db.batch()
    
    async def commit_batch(self, batch) -> bool:
        """Commit a batch operation"""
        try:
            if not batch:
                return True
            batch.commit()
            return True
        except Exception as e:
            print(f"Error committing batch: {e}")
            return False
