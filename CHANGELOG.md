AndroSH Changelog

Version 2025.09.24 - New Release

🚀 New Features

Command Line Interface

· Advanced Argument Parser: Completely redesigned CLI with intuitive command structure
· Global Access Script: Install a system-wide script for launching from any terminal
· Flexible Distro Management: Comprehensive suite for distro lifecycle management
  · setup: Create new Alpine Linux environments with custom locations
  · remove: Safely remove existing distributions
  · launch: Start existing distro instances
  · clean: Clean temporary files and cache
  · list: View all available distributions with detailed information

Database & Performance

· SQL Database Integration: Replaced file-based storage with SQLite for enhanced performance
· Optimized Data Management: Faster distro lookup, better metadata handling
· Persistent Session Management: Remember last used distro for quick access

User Experience

· Intelligent Default Behavior: Running python main.py without arguments launches last used distro
· Verbose Output Control: Multi-level logging with --verbose and --quiet options
· Custom Base Directory: Install distros anywhere using --base-dir parameter
· Enhanced UI/UX: Improved terminal interface with better feedback and progress indicators

🔧 Technical Improvements

Core Architecture

· Refactored Database Layer: Optimized queries and connection management
· Enhanced Shizuku API: More reliable ADB access and process management
· Streamlined Setup Process: Modular installation with better error handling

Reliability & Error Handling

· File Integrity Verification: Checksum validation for downloaded files
· Comprehensive Error Handling: Graceful recovery from installation failures
· Network Resilience: Improved download retry mechanisms and progress tracking

🐛 Bug Fixes

Critical Issues Resolved

· Setup Process Stability: Fixed race conditions and permission issues during installation
· Shizuku API Reliability: Resolved service connection and privilege escalation problems
· Database Integrity: Fixed data corruption issues and improved transaction safety
· File System Checks: Pre-download validation to prevent corrupted installations

📊 Enhanced Functionality

Distro Management

· Multi-Distro Support: Manage multiple Alpine instances simultaneously
· Custom Installation Paths
· Automatic Dependency Resolution: Smart package management and conflict resolution

System Integration

· Android Integration: Better compatibility with various Android versions and devices
· Resource Optimization: Reduced memory footprint and improved performance
· Cross-Platform Scripting: Consistent behavior across different terminal emulators

🔒 Security Enhancements

· Isolated Environments: Improved process isolation using proot
· Permission Management: Enhanced security model for privileged operations
· Secure File Handling: Validated downloads and integrity checks

📈 Performance Optimizations

· Faster Startup: Reduced initialization time by 40%
· Memory Efficiency: Optimized resource usage for low-memory devices
· Database Performance: 60% faster distro listing and management operations
