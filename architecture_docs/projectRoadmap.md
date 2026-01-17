# Project Roadmap

## Project Overview
ESC/POS Thermal Printer System - A Flask-based API service that integrates TickTick task management with an ESC/POS thermal printer to print daily news, tasks, quotes, and journal prompts.

## High-Level Goals

### Core Functionality
- [x] Print daily news from RSS feeds (Heidelberg News, Tagesschau)
- [x] Print tasks from TickTick with due dates
- [x] Print daily philosophical quotes (Marc Aurel)
- [x] Print journal prompts for daily reflection
- [x] Print sunrise/sunset times

### Task Management Integration
- [x] Integrate with TickTick API
- [x] OAuth2 authentication for TickTick
- [x] Filter tasks by due date (overdue and due today)
- [x] Group tasks by tags
- [x] Sort task groups alphabetically
- [x] Filter #sap tasks to weekdays only
- [ ] Add support for task priorities in display
- [ ] Add support for completed task tracking

### Printing Features
- [x] Basic text printing
- [x] Custom headline and text endpoint
- [x] Date and time formatting
- [x] Task list formatting
- [x] Journal prompt printing with scales
- [ ] Add QR code support for tasks
- [ ] Add image printing capabilities

### User Experience
- [x] Web API endpoints for all print functions
- [x] Error handling and logging
- [x] Multiple print modes (news, tasks, journal)
- [ ] Scheduled automatic printing
- [ ] Web interface for manual triggering

## Completion Criteria

### Phase 1: Basic Functionality ✅
- Set up Flask API server
- Connect to ESC/POS printer
- Print basic text and RSS feeds
- Integrate TickTick API

### Phase 2: Enhanced Task Management ✅
- Tag-based task grouping
- Weekday filtering for work tasks
- Alphabetical sorting of task groups
- Due date filtering

### Phase 3: Future Enhancements
- [ ] Scheduled printing via cron/systemd timer
- [ ] Task completion tracking
- [ ] Historical data logging
- [ ] Web dashboard for configuration

## Completed Tasks

### 2026-01-17
- ✅ Fixed tag recognition to use TickTick's tag field
- ✅ Implemented tag-based task grouping
- ✅ Added alphabetical sorting of task groups
- ✅ Implemented weekday filtering for #sap tasks
- ✅ Created architecture_docs directory structure

### Earlier Work
- ✅ Initial Flask API setup
- ✅ ESC/POS printer integration
- ✅ TickTick OAuth2 authentication
- ✅ RSS feed parsing and printing
- ✅ Marc Aurel quote system
- ✅ Journal prompt printing
