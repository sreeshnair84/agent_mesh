#!/usr/bin/env python3
"""
User Management Script
Command-line utility for managing users in Agent Mesh
"""

import asyncio
import sys
import os
from typing import Optional

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.core.database import get_async_session
from app.core.user_manager import user_manager
from app.core.default_user import default_user_service
from app.models.user import UserRole


async def create_default_user():
    """Create or update default user in database"""
    async with get_async_session() as db:
        try:
            user = await default_user_service.get_or_create_default_user(db)
            print(f"✅ Default user created/updated successfully!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Role: {user.role.value}")
            print(f"   Active: {user.is_active}")
            return user
        except Exception as e:
            print(f"❌ Error creating default user: {e}")
            return None


async def show_user_info(user_identifier: str):
    """Show information about a user"""
    async with get_async_session() as db:
        try:
            # Try to get user by ID first, then by email, then by username
            user = None
            if user_identifier:
                user = await user_manager.get_user_by_id(user_identifier, db)
                if not user:
                    user = await user_manager.get_user_by_email(user_identifier, db)
                if not user:
                    user = await user_manager.get_user_by_username(user_identifier, db)
            
            if not user:
                print(f"❌ User not found: {user_identifier}")
                return
            
            print(f"📋 User Information:")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Full Name: {user.full_name}")
            print(f"   Role: {user.role.value}")
            print(f"   Active: {user.is_active}")
            print(f"   Verified: {user.is_verified}")
            print(f"   Default User: {user_manager.is_default_user(user)}")
            print(f"   Created: {user.created_at}")
            print(f"   Last Login: {user.last_login}")
            print(f"   Login Count: {user.login_count}")
            
            # Show permissions
            permissions = user_manager.get_user_permissions(user)
            print(f"   Permissions:")
            for perm, value in permissions.items():
                print(f"     {perm}: {value}")
            
        except Exception as e:
            print(f"❌ Error getting user info: {e}")


async def list_users(limit: int = 10):
    """List all users"""
    async with get_async_session() as db:
        try:
            users = await user_manager.get_all_users(limit=limit, db=db)
            
            if not users:
                print("📋 No users found in database")
                return
            
            print(f"📋 Users (showing {len(users)} users):")
            print("-" * 80)
            
            for user in users:
                default_marker = "🔧" if user_manager.is_default_user(user) else "👤"
                status = "✅" if user.is_active else "❌"
                print(f"{default_marker} {user.username} ({user.email}) - {user.role.value} {status}")
                print(f"   ID: {user.id}")
                print(f"   Created: {user.created_at}")
                print("-" * 80)
                
        except Exception as e:
            print(f"❌ Error listing users: {e}")


async def check_default_user_status():
    """Check default user system status"""
    print("🔍 Default User System Status:")
    print(f"   Enabled: {settings.USE_DEFAULT_USER}")
    print(f"   Default User ID: {settings.DEFAULT_USER_ID}")
    print(f"   Default User Email: {settings.DEFAULT_USER_EMAIL}")
    print(f"   Default User Username: {settings.DEFAULT_USER_USERNAME}")
    print(f"   Default User Role: {settings.DEFAULT_USER_ROLE}")
    print(f"   Default User Full Name: {settings.DEFAULT_USER_FULL_NAME}")
    
    if settings.USE_DEFAULT_USER:
        async with get_async_session() as db:
            try:
                user = await user_manager.get_user_by_id(settings.DEFAULT_USER_ID, db)
                if user:
                    print(f"   Status: ✅ Default user exists in database")
                else:
                    print(f"   Status: ⚠️ Default user not found in database")
            except Exception as e:
                print(f"   Status: ❌ Error checking database: {e}")


async def change_user_role(user_identifier: str, new_role: str):
    """Change user role"""
    async with get_async_session() as db:
        try:
            # Validate role
            try:
                role = UserRole(new_role)
            except ValueError:
                print(f"❌ Invalid role: {new_role}")
                print(f"   Valid roles: {[r.value for r in UserRole]}")
                return
            
            # Find user
            user = await user_manager.get_user_by_id(user_identifier, db) or \
                   await user_manager.get_user_by_email(user_identifier, db) or \
                   await user_manager.get_user_by_username(user_identifier, db)
            
            if not user:
                print(f"❌ User not found: {user_identifier}")
                return
            
            # Change role
            success = await user_manager.change_user_role(str(user.id), role, db)
            if success:
                print(f"✅ User role changed successfully!")
                print(f"   User: {user.username} ({user.email})")
                print(f"   New Role: {role.value}")
            else:
                print(f"❌ Failed to change user role")
                
        except Exception as e:
            print(f"❌ Error changing user role: {e}")


def print_help():
    """Print help information"""
    print("🔧 Agent Mesh User Management Tool")
    print("")
    print("Usage: python scripts/user_management.py <command> [args]")
    print("")
    print("Commands:")
    print("  create-default    Create or update default user")
    print("  status           Check default user system status")
    print("  list             List all users")
    print("  info <user>      Show user information (by ID, email, or username)")
    print("  role <user> <role>  Change user role (admin, developer, viewer)")
    print("  help             Show this help message")
    print("")
    print("Examples:")
    print("  python scripts/user_management.py create-default")
    print("  python scripts/user_management.py status")
    print("  python scripts/user_management.py list")
    print("  python scripts/user_management.py info default@agentmesh.dev")
    print("  python scripts/user_management.py role defaultuser admin")


async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "create-default":
        await create_default_user()
    elif command == "status":
        await check_default_user_status()
    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        await list_users(limit)
    elif command == "info":
        if len(sys.argv) < 3:
            print("❌ Please provide user identifier")
            return
        await show_user_info(sys.argv[2])
    elif command == "role":
        if len(sys.argv) < 4:
            print("❌ Please provide user identifier and new role")
            return
        await change_user_role(sys.argv[2], sys.argv[3])
    elif command == "help":
        print_help()
    else:
        print(f"❌ Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    asyncio.run(main())
