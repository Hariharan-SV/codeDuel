"""
Mock database service for development without Firestore credentials
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class MockFirestoreDB:
    """Mock database that stores data in memory for development"""
    
    def __init__(self):
        self.collections = {}
        print("Mock Firestore client initialized successfully")
    
    async def create_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Create a document in a collection"""
        try:
            if collection not in self.collections:
                self.collections[collection] = {}
            
            self.collections[collection][doc_id] = data.copy()
            print(f"Created document {doc_id} in collection {collection}")
            return True
        except Exception as e:
            print(f"Error creating document: {e}")
            return False
    
    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document from a collection"""
        try:
            if collection in self.collections and doc_id in self.collections[collection]:
                return self.collections[collection][doc_id].copy()
            return None
        except Exception as e:
            print(f"Error getting document: {e}")
            return None
    
    async def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update a document in a collection"""
        try:
            if collection not in self.collections:
                self.collections[collection] = {}
            
            if doc_id in self.collections[collection]:
                self.collections[collection][doc_id].update(data)
            else:
                self.collections[collection][doc_id] = data.copy()
            
            print(f"Updated document {doc_id} in collection {collection}")
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False
    
    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document from a collection"""
        try:
            if collection in self.collections and doc_id in self.collections[collection]:
                del self.collections[collection][doc_id]
                print(f"Deleted document {doc_id} from collection {collection}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    async def query_collection(self, collection: str, filters: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """Query a collection with optional filters"""
        try:
            if collection not in self.collections:
                return []
            
            results = []
            for doc_id, data in self.collections[collection].items():
                # Add document ID to the data
                doc_data = data.copy()
                doc_data['id'] = doc_id
                results.append(doc_data)
            
            # Apply simple filters if provided
            if filters:
                for field, operator, value in filters:
                    if operator == '==':
                        results = [doc for doc in results if doc.get(field) == value]
                    elif operator == '!=':
                        results = [doc for doc in results if doc.get(field) != value]
                    elif operator == '>':
                        results = [doc for doc in results if doc.get(field, 0) > value]
                    elif operator == '<':
                        results = [doc for doc in results if doc.get(field, 0) < value]
            
            return results
        except Exception as e:
            print(f"Error querying collection: {e}")
            return []
    
    async def add_to_subcollection(self, collection: str, doc_id: str, subcollection: str, data: Dict[str, Any]) -> bool:
        """Add document to a subcollection (mock implementation)"""
        try:
            # Create nested structure: collection -> doc_id -> subcollection -> items
            if collection not in self.collections:
                self.collections[collection] = {}
            
            if doc_id not in self.collections[collection]:
                self.collections[collection][doc_id] = {}
            
            if subcollection not in self.collections[collection][doc_id]:
                self.collections[collection][doc_id][subcollection] = []
            
            # Add data with a unique ID
            item_id = f"{subcollection}_{len(self.collections[collection][doc_id][subcollection])}"
            data_with_id = {"id": item_id, **data}
            self.collections[collection][doc_id][subcollection].append(data_with_id)
            
            print(f"Added to subcollection {collection}/{doc_id}/{subcollection}")
            return True
        except Exception as e:
            print(f"Error adding to subcollection: {e}")
            return False
    
    async def get_subcollection(self, collection: str, doc_id: str, subcollection: str) -> List[Dict[str, Any]]:
        """Get all documents from a subcollection (mock implementation)"""
        try:
            if (collection in self.collections and 
                doc_id in self.collections[collection] and 
                subcollection in self.collections[collection][doc_id]):
                return self.collections[collection][doc_id][subcollection].copy()
            return []
        except Exception as e:
            print(f"Error getting subcollection: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about collections (for debugging)"""
        stats = {}
        for collection, docs in self.collections.items():
            stats[collection] = len(docs)
        return stats
