from prometheus_client import Counter, generate_latest
from prometheus_client import CollectorRegistry, multiprocess


# Prometheus Metrics
METRICS = {
    'posts': Counter(
        'aiops_publisher_post_requests_total',
        'The total number of post data requests',
        ['ppid', 'pid']
    ),
    'post_successes': Counter(
        'aiops_publisher_post_requests_successful',
        'The total number of successful post data requests',
        ['ppid', 'pid']
    ),
    'post_errors': Counter(
        'aiops_publisher_post_requests_exceptions',
        'The total number of post data request exceptions',
        ['ppid', 'pid']
    ),
}


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)


def generate_aggregated_metrics():
    """Generate Aggregated Metrics for multiple processes."""
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return generate_latest(registry)
