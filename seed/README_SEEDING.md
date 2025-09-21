# Database Seeding

This document explains how to seed the database with test data for development.

## Usage

```bash
# Make sure you're in the API directory
cd Longivitate.AI/api

# Run the seeding script
cd seed
python seed_database.py
```

## Environment Variables

The script uses the same environment variables as defined in `docker-compose.yml`:

- `DATABASE_URL`: Full PostgreSQL connection string (automatically set in Docker)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`: Individual components for local development

## What Gets Seeded

### Users

| Email | Password | Role | Purpose |
|-------|----------|------|---------|
| super@admin.com | devpass | superadmin | Full system access |
| admin@admin.com | devpass | admin | Administrative access |
| customer@customer.com | devpass | customer | Regular customer we aren't using this right now|
| user@user.com | devpass | user | Regular user (no subscription) |
| user_subscribed@user.com | devpass | user | User with active subscription |
| member1@usersubscribed.com | devpass | user | User belongs to the non solo organization that user_subscribed@user.com owns  |
| member2@usersubscribed.com | devpass | user | User belongs to the non solo organization that user_subscribed@user.com owns  |
| member3@usersubscribed.com | devpass | user | User belongs to the non solo organization that user_subscribed@user.com owns  |
| member4@usersubscribed.com | devpass | user | User belongs to the non solo organization that user_subscribed@user.com owns  |


### Subscriptions
| User | Status | Purpose |
|------|--------|---------|
| user_subscribed@user.com | active | Testing active subscription features |

qwen instructions on how to seed this: 

every user belongs to a is_solo=true organization. They only have another organization is_solo=false if they subscribe to a paid plan. for example member1@usersubscribed.com should belong to a is_solo=true organization that they own, and should also be a member of the organization that user_subscribed@user.com owns. user_subscribed@user.com should own 2 organizations one is_solo=true, and another is_solo=false with an associated subscription. lets set the center_quantity to 3 for user_subscribed@user.com's subscription. 

## Docker Usage

```bash
# Run migrations first
docker exec -it fastapi_app alembic upgrade head

# Run seeding
docker exec -it fastapi_app python seed/seed_database.py
```

## Notes

- The script is safe to run multiple times - it checks for existing data before creating duplicates
- Users must be created before subscriptions (dependency order is handled automatically) 
