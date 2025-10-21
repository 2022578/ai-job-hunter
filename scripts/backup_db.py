"""
Database Backup Script for GenAI Job Assistant
Automates database backup with rotation and compression
"""

import os
import sys
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime
import gzip

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config_manager import ConfigManager
from database.db_manager import DatabaseManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Handles database backup operations"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize database backup handler
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Get database path from config
        self.db_path = Path(self.config.database.path)
        
        # Get backup directory from config or use default
        backup_dir = getattr(self.config.database, 'backup_directory', 'data/backups')
        self.backup_dir = Path(backup_dir)
        
        # Get retention settings
        self.max_backups = getattr(self.config.database, 'max_backups', 7)
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, compress: bool = True) -> Path:
        """
        Create a backup of the database
        
        Args:
            compress: Whether to compress the backup with gzip
            
        Returns:
            Path to the created backup file
        """
        try:
            # Check if database exists
            if not self.db_path.exists():
                raise FileNotFoundError(f"Database not found: {self.db_path}")
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"job_assistant_backup_{timestamp}.db"
            
            if compress:
                backup_filename += ".gz"
            
            backup_path = self.backup_dir / backup_filename
            
            logger.info(f"Creating backup: {backup_path}")
            
            # Create backup
            if compress:
                # Compress while copying
                with open(self.db_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # Simple copy
                shutil.copy2(self.db_path, backup_path)
            
            # Get file size
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            
            logger.info(f"Backup created successfully: {backup_path} ({size_mb:.2f} MB)")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, backup_path: Path, force: bool = False) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
            force: Skip confirmation prompt
            
        Returns:
            True if restore successful
        """
        try:
            # Check if backup exists
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup not found: {backup_path}")
            
            # Confirm restore
            if not force:
                response = input(f"Restore database from {backup_path}? This will overwrite current database. (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Restore cancelled")
                    return False
            
            # Create backup of current database before restore
            if self.db_path.exists():
                logger.info("Creating backup of current database before restore...")
                current_backup = self.backup_dir / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(self.db_path, current_backup)
                logger.info(f"Current database backed up to: {current_backup}")
            
            logger.info(f"Restoring from backup: {backup_path}")
            
            # Restore based on file type
            if backup_path.suffix == '.gz':
                # Decompress while restoring
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(self.db_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # Simple copy
                shutil.copy2(backup_path, self.db_path)
            
            logger.info("Database restored successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise
    
    def list_backups(self) -> list:
        """
        List all available backups
        
        Returns:
            List of backup file paths sorted by date (newest first)
        """
        backups = []
        
        # Find all backup files
        for pattern in ['*.db', '*.db.gz']:
            backups.extend(self.backup_dir.glob(pattern))
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return backups
    
    def cleanup_old_backups(self) -> int:
        """
        Remove old backups beyond retention limit
        
        Returns:
            Number of backups deleted
        """
        try:
            backups = self.list_backups()
            
            if len(backups) <= self.max_backups:
                logger.info(f"No cleanup needed. Current backups: {len(backups)}, Max: {self.max_backups}")
                return 0
            
            # Delete oldest backups
            backups_to_delete = backups[self.max_backups:]
            deleted_count = 0
            
            for backup in backups_to_delete:
                logger.info(f"Deleting old backup: {backup}")
                backup.unlink()
                deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old backup(s)")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            raise
    
    def display_backups(self):
        """Display list of available backups"""
        backups = self.list_backups()
        
        if not backups:
            print("\nNo backups found.")
            return
        
        print(f"\nAvailable backups ({len(backups)}):")
        print("-" * 80)
        
        for i, backup in enumerate(backups, 1):
            size_mb = backup.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            compressed = " (compressed)" if backup.suffix == '.gz' else ""
            
            print(f"{i}. {backup.name}")
            print(f"   Size: {size_mb:.2f} MB{compressed}")
            print(f"   Date: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Database backup utility for GenAI Job Assistant"
    )
    
    parser.add_argument(
        'action',
        choices=['backup', 'restore', 'list', 'cleanup'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--backup-file',
        type=str,
        help='Backup file path (for restore action)'
    )
    
    parser.add_argument(
        '--no-compress',
        action='store_true',
        help='Do not compress backup (for backup action)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize backup handler
        backup_handler = DatabaseBackup(config_path=args.config)
        
        # Execute action
        if args.action == 'backup':
            logger.info("=" * 60)
            logger.info("Database Backup")
            logger.info("=" * 60)
            
            backup_path = backup_handler.create_backup(compress=not args.no_compress)
            
            # Cleanup old backups
            backup_handler.cleanup_old_backups()
            
            logger.info("=" * 60)
            logger.info("Backup completed successfully")
            logger.info("=" * 60)
        
        elif args.action == 'restore':
            logger.info("=" * 60)
            logger.info("Database Restore")
            logger.info("=" * 60)
            
            if not args.backup_file:
                # Show available backups
                backup_handler.display_backups()
                
                # Prompt for selection
                backups = backup_handler.list_backups()
                if backups:
                    choice = input("\nEnter backup number to restore (or 'q' to quit): ")
                    if choice.lower() == 'q':
                        logger.info("Restore cancelled")
                        return
                    
                    try:
                        index = int(choice) - 1
                        if 0 <= index < len(backups):
                            backup_path = backups[index]
                        else:
                            logger.error("Invalid backup number")
                            return
                    except ValueError:
                        logger.error("Invalid input")
                        return
                else:
                    logger.error("No backups available")
                    return
            else:
                backup_path = Path(args.backup_file)
            
            success = backup_handler.restore_backup(backup_path, force=args.force)
            
            if success:
                logger.info("=" * 60)
                logger.info("Restore completed successfully")
                logger.info("=" * 60)
        
        elif args.action == 'list':
            logger.info("=" * 60)
            logger.info("Available Backups")
            logger.info("=" * 60)
            
            backup_handler.display_backups()
        
        elif args.action == 'cleanup':
            logger.info("=" * 60)
            logger.info("Cleanup Old Backups")
            logger.info("=" * 60)
            
            deleted = backup_handler.cleanup_old_backups()
            
            logger.info("=" * 60)
            logger.info(f"Cleanup completed. Deleted {deleted} backup(s)")
            logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
