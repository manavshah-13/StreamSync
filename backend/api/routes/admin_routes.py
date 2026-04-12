from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from db.database import get_db
from models.schema import Product, User
from api.routes.auth import oauth2_scheme
from jose import jwt, JWTError
from api.auth_utils import SECRET_KEY, ALGORITHM
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin Management"])

# Helper dependency to check if user is admin
def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    return user

# Pydantic models for product management
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    base_price: Optional[float] = None
    current_price: Optional[float] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None

class ProductCreate(BaseModel):
    id: str
    name: str
    category: str
    base_price: float
    current_price: float
    brand: str
    description: Optional[str] = ""
    image: Optional[str] = ""

@router.post("/products")
def create_product(product: ProductCreate, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/products/{product_id}")
def update_product(product_id: str, product_update: ProductUpdate, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}")
def delete_product(product_id: str, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}
