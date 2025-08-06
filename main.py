# from fastapi import FastAPI

# app = FastAPI()


# @app.get("/")
# async def root():
#     return {"message": "Hello World"}


from fastapi import FastAPI, HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging
from datetime import timedelta

# Import models and services
from models import (
    UserCreate, UserResponse, UserUpdate, UserLogin, 
    Token, APIResponse
)
from database import get_db_connection, DatabaseConnection
from user_service import UserService
from auth import auth_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Shop_user_API",
    description="Authentication API for Flutter app with PostgreSQL backend",
    version="1.0.0"
)

# Configure CORS for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production mode, i will specify my Flutter app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    token_data = auth_manager.verify_token(token)
    return token_data

@app.get("/", tags=["Health Check"])
async def root():
    """Health check endpoint"""
    return {"message": "Flutter Auth API is running!", "status": "healthy"}

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        db = DatabaseConnection()
        db.connect()
        db.disconnect()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

# Authentication Routes
@app.post("/auth/register", response_model=APIResponse, tags=["Authentication"])
async def register_user(
    user_data: UserCreate,
    db: DatabaseConnection = Depends(get_db_connection)
):
    """Register a new user"""
    try:
        user_service = UserService(db)
        new_user = user_service.create_user(user_data)
        
        return APIResponse(
            success=True,
            message="User registered successfully",
            data={
                "user": new_user
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/auth/login", response_model=dict, tags=["Authentication"])
async def login_user(
    user_credentials: UserLogin,
    db: DatabaseConnection = Depends(get_db_connection)
):
    """Login user and return JWT token"""
    try:
        user_service = UserService(db)
        user = user_service.authenticate_user(
            user_credentials.username, 
            user_credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = auth_manager.create_access_token(
            data={"sub": user["username"]},
            expires_delta=access_token_expires
        )
        
        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# User CRUD Routes
@app.post("/users", response_model=APIResponse, tags=["Users"])
async def create_user(
    user_data: UserCreate,
    db: DatabaseConnection = Depends(get_db_connection)
):
    """Create a new user (alternative endpoint)"""
    try:
        user_service = UserService(db)
        new_user = user_service.create_user(user_data)
        
        return APIResponse(
            success=True,
            message="User created successfully",
            data={
                "user": new_user
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/users", response_model=APIResponse, tags=["Users"])
async def get_users(
    limit: int = 100,
    offset: int = 0,
    db: DatabaseConnection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """Get all users with pagination (requires authentication)"""
    try:
        user_service = UserService(db)
        users = user_service.get_all_users(limit=limit, offset=offset)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(users)} users",
            data={
                "users": users,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/users/{user_id}", response_model=APIResponse, tags=["Users"])
async def get_user(
    user_id: int,
    db: DatabaseConnection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific user by ID (requires authentication)"""
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return APIResponse(
            success=True,
            message="User retrieved successfully",
            data={
                "user": user
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/users/username/{username}", response_model=APIResponse, tags=["Users"])
async def get_user_by_username(
    username: str,
    db: DatabaseConnection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """Get a user by username (requires authentication)"""
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_username(username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return APIResponse(
            success=True,
            message="User retrieved successfully",
            data={
                "user": user
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# @app.put("/users/{user_id}", response_model=APIResponse, tags=["Users"])
# async def update_user(
#     user_id: int,
#     user_data: UserUpdate,
#     db: DatabaseConnection = Depends(get_db_connection),
#     current_user: dict = Depends(get_current_user)
# ):
#     """Update a user (requires authentication)"""
#     try:
#         user_service = UserService(db)
        
#         # Optional: Add authorization check
#         # Users can only update their own profile unless they're admin
#         current_user_data = user_service.get_user_by_username(current_user["username"])
#         if not current_user_data:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid user session"
#             )
        
#         # Allow users to update only their own profile (add admin check if needed)
#         if current_user_data["id"] != user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="You can only update your own profile"
#             )
        
#         # If password is being updated, verify current password
#         if user_data.password is not None:
#             if not user_data.current_password:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail="Current password is required for password updates"
#                 )
            
#             # Verify current password
#             if not auth_manager.verify_password(user_data.current_password, 
#                                                user_service.get_user_by_username(current_user["username"])["password"]):
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail="Current password is incorrect"
#                 )
        
#         # Perform the update
#         updated_user = user_service.update_user(user_id, user_data)
        
#         if not updated_user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )
        
#         return APIResponse(
#             success=True,
#             message="User updated successfully",
#             data={
#                 "user": updated_user
#             }
#         )
        
#     except HTTPException:
#         raise
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
#     except Exception as e:
#         logger.error(f"Error updating user: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error"
#         )



@app.delete("/users/{user_id}", response_model=APIResponse, tags=["Users"])
async def delete_user(
    user_id: int,
    db: DatabaseConnection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """Delete a user (requires authentication)"""
    try:
        user_service = UserService(db)
        
        # Check if user exists
        existing_user = user_service.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Check if user has permission (only allow users to delete their own account)
        if current_user["sub"] != existing_user["username"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this user"
            )
            
        user_service.delete_user(user_id)
        return APIResponse(
            success=True,
            message="User deleted successfully",
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/auth/refresh-token", response_model=dict, tags=["Authentication"])
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Refresh access token using existing token"""
    try:
        # Verify existing token
        token_data = auth_manager.verify_token(credentials.credentials)
        
        # Create new access token
        access_token_expires = timedelta(minutes=30)
        new_token = auth_manager.create_access_token(
            data={"sub": token_data["sub"]},
            expires_delta=access_token_expires
        )
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "data": {
                "access_token": new_token,
                "token_type": "bearer"
            }
        }
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
@app.put("/users/{user_id}", response_model=APIResponse, tags=["Users"])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: DatabaseConnection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """Update a user (requires authentication)"""
    try:
        user_service = UserService(db)
        
        # Optional: Add authorization check
        # Users can only update their own profile unless they're admin
        current_user_data = user_service.get_user_by_username(current_user["username"])
        if not current_user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user session"
            )
        
        # Allow users to update only their own profile (add admin check if needed)
        if current_user_data["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile"
            )
        
        # If password is being updated, verify current password
        if user_data.password is not None:
            if not user_data.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required for password updates"
                )
            
            # Verify current password
            if not auth_manager.verify_password(user_data.current_password, 
                                               user_service.get_user_by_username(current_user["username"])["password"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
        
        # Perform the update
        updated_user = user_service.update_user(user_id, user_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return APIResponse(
            success=True,
            message="User updated successfully",
            data={
                "user": updated_user
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )