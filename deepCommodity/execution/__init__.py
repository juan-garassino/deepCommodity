from deepCommodity.execution.broker import BrokerAdapter, OrderRequest, OrderResult, get_broker

__all__ = ["BrokerAdapter", "OrderRequest", "OrderResult", "get_broker"]

# Adapter registry (lazy-imported via get_broker). Names here document the
# venues we know about — adding a new one means: write the adapter, route it
# in get_broker, and add its env vars to .env.sample.
KNOWN_BROKERS = ("binance", "bitfinex", "alpaca")
