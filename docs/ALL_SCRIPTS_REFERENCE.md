# All Scripts Reference Guide
## Complete List of Operational Scripts

## Database Scripts

### Migrations
```bash
alembic upgrade head              # Run all migrations
alembic downgrade -1              # Rollback one migration
alembic current                   # Check current version
```

### Seeding
```bash
python scripts/seed_quests.py     # Generate weekly quests
python scripts/seed_resources.py  # Seed mental health resources
python scripts/seed_counselors.py # Seed counselor contacts (UPDATE FIRST!)
```

### Optimization
```bash
psql mental_health < scripts/database_optimization.sql  # Add indexes, create views
python scripts/performance_analysis.py                   # Identify slow queries
```

## Deployment Scripts

### Production Deployment
```bash
make deploy                       # Full deployment (tests, push, verify)
./scripts/deploy_production.sh   # Detailed deployment with checks
./scripts/validate_deployment.sh  # Pre-deploy validation
```

### Rollback
```bash
make rollback                     # Quick rollback
./scripts/rollback_deployment.sh  # Detailed rollback with confirmation
```

### Initialization
```bash
./scripts/initialize_production.sh  # First-time production setup
```

## Monitoring Scripts

### Daily Operations
```bash
python scripts/daily_health_check.py    # System health snapshot
python scripts/cleanup_old_data.py      # Delete old data per retention policy
./scripts/backup_database.sh            # Backup database
```

### Weekly Operations
```bash
python scripts/generate_pilot_report.py 1 4           # University 1, Week 4
python scripts/generate_weekly_report.py 1 4 email@   # With email delivery
python scripts/analyze_engagement.py 1                # Engagement analysis
```

### Monthly Operations
```bash
python scripts/calculate_outcomes.py 1     # Calculate symptom reduction
python scripts/export_pilot_data.py 1 data.csv  # Export for analysis
```

## Testing Scripts

### Validation
```bash
python scripts/run_validation_suite.py  # Run 30-scenario validation
./scripts/test_all.sh                   # All tests with coverage
make test                               # Quick test run
```

### Crisis Testing
```bash
python scripts/test_crisis_alerts.py    # Test alert delivery
pytest tests/test_crisis_comprehensive.py -v  # All crisis keywords
```

### Integration Testing
```bash
pytest tests/test_integration_complete.py -v  # All API endpoints
pytest tests/test_quest_system.py -v          # Quest system
pytest tests/test_alert_system.py -v          # Alert system
```

## Configuration Scripts

### University Setup
```bash
python scripts/load_university_config.py config/university_configs/umich.json
```

### Email Testing
```bash
python scripts/send_test_email.py your@email.com  # Test SendGrid
```

## Automation (Cron)

### Daily Tasks
```bash
# Add to crontab: 0 2 * * * /path/to/cron/daily_tasks.sh
./cron/daily_tasks.sh  # Health check, cleanup, backup
```

## Makefile Commands

```bash
make help       # Show all commands
make setup      # Install + migrate + seed
make run        # Start development server
make test       # Run tests
make deploy     # Deploy to production
make rollback   # Rollback deployment
make health     # Health check
make clean      # Cleanup old data
make backup     # Backup database
make perf       # Performance analysis
make security   # Security audit
make monitor    # Setup monitoring
```

## Script Categories

**Database (6):** Migrations, seeding, optimization, analysis
**Deployment (4):** Deploy, rollback, validate, initialize
**Monitoring (7):** Health check, cleanup, backup, pilot reports, engagement, outcomes, export
**Testing (4):** Validation suite, crisis alerts, integration, comprehensive
**Configuration (2):** University config, email testing
**Automation (1):** Daily tasks cron

**Total: 24 operational scripts**

## Common Workflows

### First-Time Setup
```bash
make setup
./scripts/initialize_production.sh
```

### Daily Operations
```bash
make health
make clean
```

### Weekly Pilot Management
```bash
python scripts/generate_weekly_report.py 1 4 director@university.edu
python scripts/analyze_engagement.py 1
```

### Pre-Deployment
```bash
./scripts/validate_deployment.sh
make test
```

### Deployment
```bash
make deploy
# Monitor logs
# Verify health
```

### Emergency Rollback
```bash
make rollback
# Check health
# Investigate issue
```

**All scripts documented. 24 operational scripts ready. Makefile provides shortcuts. Complete workflows for setup, daily ops, pilot management, deployment, rollback.**
