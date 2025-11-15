#!/usr/bin/env python3
"""
Changelog system for tracking data source updates.
This module provides functions to create and manage changelogs for data updates.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Changelog file
CHANGELOG_FILE = Path("data/CHANGELOG.json")


def load_changelog() -> List[Dict]:
    """Load changelog from file."""
    if CHANGELOG_FILE.exists():
        try:
            with open(CHANGELOG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_changelog(changelog: List[Dict]):
    """Save changelog to file."""
    CHANGELOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHANGELOG_FILE, 'w') as f:
        json.dump(changelog, f, indent=2, default=str)


def add_changelog_entry(
    source_name: str,
    action: str,
    details: Optional[Dict] = None,
    version: Optional[str] = None
) -> Dict:
    """Add a new entry to the changelog."""
    changelog = load_changelog()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "source_name": source_name,
        "action": action,  # "updated", "validated", "processed", "checked"
        "version": version,
        "details": details or {}
    }
    
    changelog.append(entry)
    
    # Keep only last 100 entries
    if len(changelog) > 100:
        changelog = changelog[-100:]
    
    save_changelog(changelog)
    
    logging.info(f"Added changelog entry: {source_name} - {action}")
    
    return entry


def get_changelog_entries(
    source_name: Optional[str] = None,
    action: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """Get changelog entries, optionally filtered by source or action."""
    changelog = load_changelog()
    
    # Filter entries
    if source_name:
        changelog = [e for e in changelog if e.get("source_name") == source_name]
    
    if action:
        changelog = [e for e in changelog if e.get("action") == action]
    
    # Sort by timestamp (newest first)
    changelog.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Limit results
    if limit:
        changelog = changelog[:limit]
    
    return changelog


def format_changelog_entry(entry: Dict) -> str:
    """Format a changelog entry as a human-readable string."""
    timestamp = entry.get("timestamp", "")
    source_name = entry.get("source_name", "Unknown")
    action = entry.get("action", "unknown")
    version = entry.get("version")
    details = entry.get("details", {})
    
    # Parse timestamp
    try:
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        time_str = timestamp
    
    # Build message
    parts = [f"[{time_str}] {source_name}: {action}"]
    
    if version:
        parts.append(f"(version: {version})")
    
    if details:
        detail_strs = []
        if "file_path" in details:
            detail_strs.append(f"file: {details['file_path']}")
        if "row_count" in details:
            detail_strs.append(f"rows: {details['row_count']}")
        if "schema_changes" in details:
            changes = details["schema_changes"]
            if changes.get("added_columns"):
                detail_strs.append(f"added columns: {', '.join(changes['added_columns'])}")
            if changes.get("removed_columns"):
                detail_strs.append(f"removed columns: {', '.join(changes['removed_columns'])}")
        
        if detail_strs:
            parts.append(" | " + ", ".join(detail_strs))
    
    return " ".join(parts)


def print_changelog(
    source_name: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 20
):
    """Print changelog entries to console."""
    entries = get_changelog_entries(source_name=source_name, action=action, limit=limit)
    
    if not entries:
        print("No changelog entries found.")
        return
    
    print("=" * 70)
    print("CHANGELOG")
    print("=" * 70)
    
    for entry in entries:
        print(format_changelog_entry(entry))


def create_notification(
    source_name: str,
    message: str,
    level: str = "info"  # "info", "warning", "error"
) -> Dict:
    """Create a notification entry."""
    notification = {
        "timestamp": datetime.now().isoformat(),
        "source_name": source_name,
        "message": message,
        "level": level,
        "read": False
    }
    
    # Save to notifications file
    notifications_file = Path("data/notifications.json")
    notifications = []
    
    if notifications_file.exists():
        try:
            with open(notifications_file, 'r') as f:
                notifications = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Failed to load notifications file: {e}. Starting with empty list.")
            notifications = []
    
    notifications.append(notification)
    
    # Keep only last 50 notifications
    if len(notifications) > 50:
        notifications = notifications[-50:]
    
    notifications_file.parent.mkdir(parents=True, exist_ok=True)
    with open(notifications_file, 'w') as f:
        json.dump(notifications, f, indent=2, default=str)
    
    # Log notification
    if level == "error":
        logging.error(f"{source_name}: {message}")
    elif level == "warning":
        logging.warning(f"{source_name}: {message}")
    else:
        logging.info(f"{source_name}: {message}")
    
    return notification


def get_unread_notifications() -> List[Dict]:
    """Get all unread notifications."""
    notifications_file = Path("data/notifications.json")
    
    if not notifications_file.exists():
        return []
    
    try:
        with open(notifications_file, 'r') as f:
            notifications = json.load(f)
        return [n for n in notifications if not n.get("read", False)]
    except (json.JSONDecodeError, IOError):
        return []


def mark_notification_read(notification_timestamp: str):
    """Mark a notification as read."""
    notifications_file = Path("data/notifications.json")
    
    if not notifications_file.exists():
        return
    
    try:
        with open(notifications_file, 'r') as f:
            notifications = json.load(f)
        
        for notification in notifications:
            if notification.get("timestamp") == notification_timestamp:
                notification["read"] = True
        
        with open(notifications_file, 'w') as f:
            json.dump(notifications, f, indent=2, default=str)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to update notification read status: {e}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="View changelog and notifications")
    parser.add_argument(
        "--source",
        type=str,
        help="Filter by source name"
    )
    parser.add_argument(
        "--action",
        type=str,
        help="Filter by action"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit number of entries (default: 20)"
    )
    parser.add_argument(
        "--notifications",
        action="store_true",
        help="Show unread notifications"
    )
    
    args = parser.parse_args()
    
    if args.notifications:
        notifications = get_unread_notifications()
        if notifications:
            print("=" * 70)
            print("UNREAD NOTIFICATIONS")
            print("=" * 70)
            for notification in notifications:
                level = notification.get("level", "info").upper()
                timestamp = notification.get("timestamp", "")
                source = notification.get("source_name", "Unknown")
                message = notification.get("message", "")
                
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    time_str = timestamp
                
                print(f"[{time_str}] [{level}] {source}: {message}")
        else:
            print("No unread notifications.")
    else:
        print_changelog(
            source_name=args.source,
            action=args.action,
            limit=args.limit
        )


if __name__ == "__main__":
    main()

