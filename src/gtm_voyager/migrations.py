"""
GTM Voyager Platform - Database Migrations
Database initialization, schema creation, and default data setup.
"""

import logging
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .models import (
    Base, User, Role, Permission, UserStatus,
    user_roles, role_permissions, create_default_roles_and_permissions
)
from .config import engine, get_session_context
from ..utils.security import SecurityManager

logger = logging.getLogger(__name__)

def init_database(drop_existing: bool = False) -> bool:
    """
    Initialize database schema and create tables.
    
    Args:
        drop_existing: Whether to drop existing tables first
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if drop_existing:
            logger.warning("Dropping existing database tables")
            Base.metadata.drop_all(bind=engine)
        
        logger.info("Creating database tables")
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def create_default_permissions(session: Session) -> List[Permission]:
    """Create default system permissions"""
    default_permissions, _ = create_default_roles_and_permissions()
    created_permissions = []
    
    for perm_name, display_name, description, resource, action in default_permissions:
        # Check if permission already exists
        existing = session.query(Permission).filter_by(name=perm_name).first()
        if existing:
            logger.info(f"Permission '{perm_name}' already exists, skipping")
            created_permissions.append(existing)
            continue
        
        permission = Permission(
            name=perm_name,
            display_name=display_name,
            description=description,
            resource=resource,
            action=action,
            is_system_permission=True
        )
        
        session.add(permission)
        created_permissions.append(permission)
        logger.info(f"Created permission: {perm_name}")
    
    return created_permissions

def create_default_roles(session: Session, permissions: List[Permission]) -> List[Role]:
    """Create default system roles with appropriate permissions"""
    _, default_roles = create_default_roles_and_permissions()
    created_roles = []
    
    # Permission mappings for each role
    role_permissions_map = {
        "super_admin": [p.name for p in permissions],  # All permissions
        "system_admin": [
            "users.read", "users.write", "users.delete",
            "roles.read", "roles.write", "roles.delete", 
            "audit.read", "system.admin"
        ],
        "security_admin": [
            "users.read", "audit.read", "security.monitor"
        ],
        "practice_owner": [
            "users.read", "users.write", "users.delete",
            "dental_records.read", "dental_records.write", "dental_records.delete",
            "voice.process", "voice.transcribe"
        ],
        "dentist": [
            "dental_records.read", "dental_records.write",
            "voice.process", "voice.transcribe"
        ],
        "dental_hygienist": [
            "dental_records.read", "dental_records.write",
            "voice.process", "voice.transcribe"
        ],
        "office_manager": [
            "users.read", "dental_records.read", "dental_records.write"
        ],
        "receptionist": [
            "dental_records.read"
        ],
        "patient": [
            "dental_records.read"  # Only their own records
        ]
    }
    
    for role_name, display_name, description, is_system in default_roles:
        # Check if role already exists
        existing = session.query(Role).filter_by(name=role_name).first()
        if existing:
            logger.info(f"Role '{role_name}' already exists, skipping")
            created_roles.append(existing)
            continue
        
        role = Role(
            name=role_name,
            display_name=display_name,
            description=description,
            is_system_role=is_system,
            tenant_id=None  # Global roles
        )
        
        # Add permissions to role
        role_perms = role_permissions_map.get(role_name, [])
        for perm_name in role_perms:
            permission = next((p for p in permissions if p.name == perm_name), None)
            if permission:
                role.permissions.append(permission)
        
        session.add(role)
        created_roles.append(role)
        logger.info(f"Created role: {role_name} with {len(role_perms)} permissions")
    
    return created_roles

def create_default_admin_user(session: Session, roles: List[Role]) -> User:
    """Create default system administrator user"""
    admin_email = "admin@gtmvoyager.com"
    
    # Check if admin user already exists
    existing = session.query(User).filter_by(email=admin_email).first()
    if existing:
        logger.info("Default admin user already exists")
        return existing
    
    # Create admin user
    security_manager = SecurityManager()
    admin_password = "GTMVoyager2024!"  # Change this in production!
    
    admin_user = User(
        email=admin_email,
        username="admin",
        password_hash=security_manager.hash_password(admin_password),
        first_name="System",
        last_name="Administrator",
        status=UserStatus.ACTIVE.value,
        is_email_verified=True,
        tenant_id="system",
        organization="GTM Voyager Platform"
    )
    
    # Assign super_admin role
    super_admin_role = next((r for r in roles if r.name == "super_admin"), None)
    if super_admin_role:
        admin_user.roles.append(super_admin_role)
    
    session.add(admin_user)
    logger.info(f"Created default admin user: {admin_email}")
    logger.warning(f"Default admin password: {admin_password} - CHANGE THIS IN PRODUCTION!")
    
    return admin_user

def create_demo_tenant_data(session: Session, roles: List[Role]) -> List[User]:
    """Create demo tenant data for testing"""
    demo_users = []
    security_manager = SecurityManager()
    
    # Demo dental practice users
    demo_user_data = [
        {
            "email": "dr.smith@demopractice.com",
            "username": "dr_smith",
            "first_name": "John",
            "last_name": "Smith",
            "role": "dentist",
            "tenant_id": "demo_practice"
        },
        {
            "email": "hygienist@demopractice.com", 
            "username": "sarah_hygienist",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "role": "dental_hygienist",
            "tenant_id": "demo_practice"
        },
        {
            "email": "manager@demopractice.com",
            "username": "office_manager",
            "first_name": "Lisa",
            "last_name": "Brown",
            "role": "office_manager", 
            "tenant_id": "demo_practice"
        }
    ]
    
    for user_data in demo_user_data:
        # Check if user already exists
        existing = session.query(User).filter_by(email=user_data["email"]).first()
        if existing:
            continue
        
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            password_hash=security_manager.hash_password("Demo123!"),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            status=UserStatus.ACTIVE.value,
            is_email_verified=True,
            tenant_id=user_data["tenant_id"],
            organization="Demo Dental Practice"
        )
        
        # Assign role
        role = next((r for r in roles if r.name == user_data["role"]), None)
        if role:
            user.roles.append(role)
        
        session.add(user)
        demo_users.append(user)
        logger.info(f"Created demo user: {user_data['email']}")
    
    return demo_users

def create_default_data(include_demo: bool = True) -> bool:
    """
    Create default permissions, roles, and users.
    
    Args:
        include_demo: Whether to include demo tenant data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_session_context() as session:
            logger.info("Creating default permissions...")
            permissions = create_default_permissions(session)
            session.flush()  # Ensure permissions are saved before creating roles
            
            logger.info("Creating default roles...")
            roles = create_default_roles(session, permissions)
            session.flush()  # Ensure roles are saved before creating users
            
            logger.info("Creating default admin user...")
            admin_user = create_default_admin_user(session, roles)
            
            if include_demo:
                logger.info("Creating demo tenant data...")
                demo_users = create_demo_tenant_data(session, roles)
            
            session.commit()
            logger.info("Default data creation completed successfully")
            return True
            
    except IntegrityError as e:
        logger.error(f"Database integrity error during default data creation: {e}")
        return False
    except Exception as e:
        logger.error(f"Default data creation failed: {e}")
        return False

def reset_database(include_demo: bool = True) -> bool:
    """
    Reset database by dropping and recreating all tables and data.
    WARNING: This will delete all existing data!
    
    Args:
        include_demo: Whether to include demo tenant data
        
    Returns:
        True if successful, False otherwise
    """
    logger.warning("RESETTING DATABASE - ALL DATA WILL BE LOST!")
    
    try:
        # Drop and recreate tables
        if not init_database(drop_existing=True):
            return False
        
        # Create default data
        if not create_default_data(include_demo=include_demo):
            return False
        
        logger.info("Database reset completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False

def upgrade_database() -> bool:
    """
    Upgrade database schema and data for new versions.
    Add migration logic here for future schema changes.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Checking for database upgrades...")
        
        # Create tables if they don't exist (safe operation)
        Base.metadata.create_all(bind=engine)
        
        # Add any future migration logic here
        # Example:
        # if not _check_column_exists("users", "new_column"):
        #     _add_column("users", "new_column", "VARCHAR(255)")
        
        logger.info("Database upgrade completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database upgrade failed: {e}")
        return False

# CLI-style functions for database management
def main():
    """Main function for running database operations from command line"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m gtm_voyager.database.migrations <command>")
        print("Commands: init, reset, upgrade, create-data")
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        success = init_database()
        print(f"Database initialization: {'SUCCESS' if success else 'FAILED'}")
    
    elif command == "reset":
        success = reset_database()
        print(f"Database reset: {'SUCCESS' if success else 'FAILED'}")
    
    elif command == "upgrade":
        success = upgrade_database()
        print(f"Database upgrade: {'SUCCESS' if success else 'FAILED'}")
    
    elif command == "create-data":
        success = create_default_data()
        print(f"Default data creation: {'SUCCESS' if success else 'FAILED'}")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
