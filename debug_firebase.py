"""
Examen simple du contenu Firebase pour debug
"""
import sys

sys.path.append('.')

from datetime import datetime, timedelta

from utils.firebase_logger import FirebaseLogger


def examine_firebase():
    """Examine le contenu brut de Firebase"""
    
    try:
        firebase_logger = FirebaseLogger()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        print("🔍 Contenu Firebase brut:")
        print("=" * 40)
        
        docs = firebase_logger.firestore_db.collection("trades").where(
            "timestamp", ">=", start_date.isoformat()
        ).where(
            "timestamp", "<=", end_date.isoformat()
        ).stream()
        
        for i, doc in enumerate(docs, 1):
            data = doc.to_dict()
            print(f"\n📄 Document #{i}:")
            for key, value in data.items():
                print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    examine_firebase()

if __name__ == "__main__":
    examine_firebase()
