from app.services.qdrant_service import qdrant_service

qdrant_service.delete_collection()
qdrant_service.create_collection()

print("Collection reset successfully.")