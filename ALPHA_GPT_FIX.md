# Fix for alpha-gpt GitHub Actions Workflow Failure

## Problem
The GitHub Actions workflow at https://github.com/Ajay-NooB143/alpha-gpt/actions/runs/24543688982 fails with:
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

## Root Cause
The `AlphaGPTCheckpointer.__init__` method in `src/agent/database/checkpointer_api.py` calls `create_tables(self.engine)` which immediately tries to connect to PostgreSQL. Even though there's a fallback to `MemorySaver` in `_create_postgres_saver()`, the database connection fails during table creation.

## Solution Option 1: Handle Database Connection Gracefully (Recommended)

Modify `src/agent/database/checkpointer_api.py` in the alpha-gpt repository:

```python
def __init__(self, postgres_saver: Union[PostgresSaver, AsyncPostgresSaver] = None):
    """
    Initialize the AlphaGPT checkpointer with a PostgreSQL saver.

    Args:
        postgres_saver: The LangGraph PostgreSQL saver to use
    """
    self.postgres_saver = postgres_saver or self._create_postgres_saver()
    
    # Only create tables if we're using PostgreSQL, not MemorySaver
    try:
        from langgraph.checkpoint.memory import MemorySaver
        if not isinstance(self.postgres_saver, MemorySaver):
            self.engine = get_db_engine()
            create_tables(self.engine)
        else:
            self.engine = None
    except Exception as e:
        print(f"Warning: Could not initialize database tables: {str(e)}")
        print("Continuing with MemorySaver fallback")
        self.engine = None
```

Also update methods that use `self.engine` to check if it's None:

```python
def save_state(self, config: RunnableConfig, state_values: Dict[str, Any]) -> None:
    """
    Save all state data to our custom database tables

    Args:
        config: LangGraph config
        state_values: The current state values
    """
    # Skip if using MemorySaver
    if self.engine is None:
        return
        
    thread_id = config.get("configurable", {}).get("thread_id")
    checkpoint_id = config.get("configurable", {}).get("checkpoint_id")

    if not thread_id or not checkpoint_id:
        return

    # Save hypothesis first
    hypothesis = save_hypothesis(thread_id, checkpoint_id, state_values)

    # Save alphas if we have a hypothesis
    if hypothesis:
        save_alphas(thread_id, checkpoint_id, state_values, hypothesis.id)

    # Save backtest results
    save_backtest_results(thread_id, checkpoint_id, state_values)
```

## Solution Option 2: Add PostgreSQL Service to Workflow

Modify `.github/workflows/trading-bot.yml` in the alpha-gpt repository:

```yaml
name: Trading Bot

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 * * * *' # every hour
  workflow_dispatch:

jobs:
  run-trading-bot:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    
    # Add PostgreSQL service
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: alphagpt
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    env:
      BINANCE_API_KEY: ${{ secrets.BINANCE_API_KEY }}
      BINANCE_API_SECRET: ${{ secrets.BINANCE_API_SECRET }}
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
      # Add PostgreSQL connection parameters
      POSTGRES_HOST: localhost
      POSTGRES_PORT: 5432
      POSTGRES_DB: alphagpt
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip setuptools wheel build

      - name: Install dependencies
        run: |
          if [ -f pyproject.toml ]; then
            pip install -e '.[dev]' || pip install . || echo "Failed to install with pip install .[dev], proceeding without install"
          else
            echo "No pyproject.toml found, skipping install"
          fi

      - name: Run trading bot
        run: |
          python bot/main.py

      - name: Upload logs on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: trading-bot-logs
          path: ./logs || true
```

## Recommendation

**Use Option 1** - it's more robust and doesn't require running a PostgreSQL service in CI for every run, which would slow down the workflow. The MemorySaver fallback is already implemented; we just need to ensure it's properly utilized when the database is unavailable.

## Files to Modify in alpha-gpt Repository

1. `src/agent/database/checkpointer_api.py` - Update the `AlphaGPTCheckpointer` class
2. Optionally: `.github/workflows/trading-bot.yml` - if choosing Option 2

## Testing

After applying the fix, the workflow should:
1. Start without errors
2. Use MemorySaver when PostgreSQL is unavailable
3. Continue to work with PostgreSQL when it's available (production)
