from typing import Dict, Optional, List
from app.services.database import SessionLocal, Contact

class ContactService:
    """Manage contact aliases"""
    
    async def add_contact(
        self, 
        alias: str, 
        email: str, 
        name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Add a new contact alias
        
        Args:
            alias: Short name (e.g., "john")
            email: Email address
            name: Full name (optional)
            notes: Additional notes (optional)
        """
        db = SessionLocal()
        
        try:
            # Check if alias already exists
            existing = db.query(Contact).filter(Contact.alias == alias.lower()).first()
            
            if existing:
                return {
                    "success": False,
                    "error": f"Alias '{alias}' already exists for {existing.email}"
                }
            
            # Create new contact
            contact = Contact(
                alias=alias.lower(),
                email=email,
                name=name,
                notes=notes
            )
            
            db.add(contact)
            db.commit()
            
            return {
                "success": True,
                "message": f"Contact '{alias}' added successfully",
                "contact": {
                    "alias": contact.alias,
                    "email": contact.email,
                    "name": contact.name
                }
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": f"Failed to add contact: {str(e)}"
            }
        finally:
            db.close()
    
    async def get_contact(self, alias: str) -> Optional[Dict[str, any]]:
        """
        Get contact by alias
        
        Args:
            alias: Contact alias to search for
        
        Returns:
            Contact details or None if not found
        """
        db = SessionLocal()
        
        try:
            contact = db.query(Contact).filter(Contact.alias == alias.lower()).first()
            
            if not contact:
                return None
            
            return {
                "alias": contact.alias,
                "email": contact.email,
                "name": contact.name,
                "notes": contact.notes
            }
            
        finally:
            db.close()
    
    async def list_contacts(self, limit: int = 50) -> List[Dict[str, any]]:
        """List all contacts"""
        db = SessionLocal()
        
        try:
            contacts = db.query(Contact).order_by(Contact.alias).limit(limit).all()
            
            return [{
                "alias": c.alias,
                "email": c.email,
                "name": c.name,
                "notes": c.notes
            } for c in contacts]
            
        finally:
            db.close()
    
    async def update_contact(
        self, 
        alias: str, 
        email: Optional[str] = None,
        name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, any]:
        """Update an existing contact"""
        db = SessionLocal()
        
        try:
            contact = db.query(Contact).filter(Contact.alias == alias.lower()).first()
            
            if not contact:
                return {
                    "success": False,
                    "error": f"Contact '{alias}' not found"
                }
            
            # Update fields
            if email:
                contact.email = email
            if name:
                contact.name = name
            if notes:
                contact.notes = notes
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Contact '{alias}' updated successfully",
                "contact": {
                    "alias": contact.alias,
                    "email": contact.email,
                    "name": contact.name
                }
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": f"Failed to update contact: {str(e)}"
            }
        finally:
            db.close()
    
    async def delete_contact(self, alias: str) -> Dict[str, any]:
        """Delete a contact"""
        db = SessionLocal()
        
        try:
            contact = db.query(Contact).filter(Contact.alias == alias.lower()).first()
            
            if not contact:
                return {
                    "success": False,
                    "error": f"Contact '{alias}' not found"
                }
            
            db.delete(contact)
            db.commit()
            
            return {
                "success": True,
                "message": f"Contact '{alias}' deleted successfully"
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": f"Failed to delete contact: {str(e)}"
            }
        finally:
            db.close()


# Create global instance
contact_service = ContactService()